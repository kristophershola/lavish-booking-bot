import json
import re
import time

import requests

from config import GROQ_API_KEY, GROQ_MODEL
from ai.prompts import build_full_system_prompt
from ai.tools import TOOL_DECLARATIONS, execute_tool
from state.conversation import get_history, append_turn

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MAX_TOOL_HOPS = 3

FALLBACK_REPLY = "Thanks for reaching out, a team member will be with you shortly."

RETRY_DELAY_PATTERN = re.compile(r"try again in ([\d.]+)s", re.IGNORECASE)

# Smaller, faster models occasionally hallucinate a fake textual function
# call instead of using the real tool_calls mechanism, something like
# <function=name>{"arg": "value"}</function>. This pattern catches that so
# we can still execute the real tool rather than let the raw text through.
FAKE_FUNCTION_CALL_PATTERN = re.compile(
    r"<function=([a-zA-Z_][a-zA-Z0-9_]*)>\s*(\{.*?\})\s*</?function>",
    re.DOTALL
)


def _extract_suggested_delay(error_data, fallback=2.0):
    """Groq's rate limit errors include the actual wait time needed, e.g.
    'Please try again in 6.13s'. Using this instead of a fixed delay means
    retries actually succeed instead of hitting the same window again.
    """
    try:
        message = error_data.get("error", {}).get("message", "")
    except AttributeError:
        return fallback

    match = RETRY_DELAY_PATTERN.search(message)
    if match:
        return float(match.group(1)) + 0.5  # small buffer on top

    return fallback


def _call_groq(messages, retries=2):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": GROQ_MODEL,
        "messages": messages,
        "tools": TOOL_DECLARATIONS,
        "tool_choice": "auto"
    }

    for attempt in range(retries + 1):
        response = requests.post(GROQ_URL, headers=headers, json=body)
        data = response.json()

        if "choices" in data:
            return data

        print(f"GROQ ATTEMPT {attempt + 1} FAILED:", json.dumps(data, indent=2))
        if attempt < retries:
            delay = _extract_suggested_delay(data)
            print(f"Waiting {delay}s before retrying, per Groq's suggested delay")
            time.sleep(delay)

    return None


def _extract_fake_function_call(content):
    """Detects the hallucinated <function=name>{...}</function> pattern in
    plain text content. Returns (name, args_dict) if found, else None.
    """
    if not content:
        return None

    match = FAKE_FUNCTION_CALL_PATTERN.search(content)
    if not match:
        return None

    name = match.group(1)
    raw_args = match.group(2)
    try:
        args = json.loads(raw_args)
    except json.JSONDecodeError:
        print(f"Could not parse fake function call args: {raw_args!r}")
        return None

    return name, args


def _sanitize_reply(reply_text):
    """Last line of defense. Never let raw model artifacts like a leaked
    function call tag reach a real customer, even if something slips past
    the earlier detection above.
    """
    if not reply_text or "<function" in reply_text or "functionCall" in reply_text:
        print(f"SANITIZE: rejected suspicious reply text: {reply_text!r}")
        return FALLBACK_REPLY
    return reply_text


def generate_ai_reply(sender_id, customer_message):
    history = get_history(sender_id)
    system_message = {"role": "system", "content": build_full_system_prompt()}
    messages = [system_message] + history + [{"role": "user", "content": customer_message}]

    for hop in range(MAX_TOOL_HOPS):
        data = _call_groq(messages)

        if data is None:
            return FALLBACK_REPLY

        message = data["choices"][0]["message"]
        tool_calls = message.get("tool_calls")
        content = message.get("content")

        # Real tool call path, this is what should normally happen.
        if tool_calls:
            messages.append(message)

            for call in tool_calls:
                name = call["function"]["name"]
                try:
                    args = json.loads(call["function"]["arguments"])
                except (json.JSONDecodeError, TypeError):
                    args = {}

                print(f"GROQ TOOL CALL: {name} with args {json.dumps(args)}")
                result = execute_tool(name, args)
                print(f"TOOL RESULT for {name}: {json.dumps(result)}")

                # If tool returned a date format error, inject a correction note
                # so the model retries with the correct ISO format
                if result.get("error_type") == "date_format":
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": json.dumps(result)
                    })
                    messages.append({
                        "role": "user",
                        "content": f"[System: The tool requires ISO date format YYYY-MM-DD. The date '{args.get('date')}' was invalid. Please retry the tool call with the correct ISO format from the DATE CONTEXT.]"
                    })
                    continue

                messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(result)
                })

            continue

        # Fallback path, the model hallucinated a fake textual function call
        # instead of a real one. Parse it, actually run the tool, and feed
        # the result back in as if it had called it properly, rather than
        # ever sending this raw text to the customer.
        fake_call = _extract_fake_function_call(content)
        if fake_call:
            name, args = fake_call
            print(f"DETECTED FAKE FUNCTION CALL TEXT, recovering: {name} with args {json.dumps(args)}")
            result = execute_tool(name, args)
            print(f"TOOL RESULT for {name} (recovered): {json.dumps(result)}")

            messages.append({"role": "assistant", "content": content})
            messages.append({
                "role": "user",
                "content": f"[System note: your previous response contained an invalid function call format. Here is the actual result: {json.dumps(result)}. Please respond to the customer normally using this information, without any function call syntax.]"
            })
            continue

        # Genuine final text answer.
        reply_text = _sanitize_reply(content)
        append_turn(sender_id, customer_message, reply_text)
        return reply_text

    return FALLBACK_REPLY
