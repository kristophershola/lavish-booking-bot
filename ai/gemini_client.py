import json
import re
import time

import requests

from config import GEMINI_API_KEY, GEMINI_MODEL
from ai.prompts import build_full_system_prompt
from ai.tools import GEMINI_TOOL_DECLARATIONS, execute_tool
from state.conversation import get_history, append_turn

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

MAX_TOOL_HOPS = 3

FALLBACK_REPLY = "Thanks for reaching out, a team member will be with you shortly."

# Same defensive pattern used in the Groq client, in case a model ever
# hallucinates a fake textual function call instead of using the real
# mechanism. Kept here too so switching providers doesn't lose this safety net.
FAKE_FUNCTION_CALL_PATTERN = re.compile(
    r"<function=([a-zA-Z_][a-zA-Z0-9_]*)>\s*(\{.*?\})\s*</?function>",
    re.DOTALL
)


def _history_to_gemini_contents(history):
    """Converts the neutral {"role": "user"/"assistant", "content": "..."}
    history format (shared with the Groq client) into Gemini's
    {"role": "user"/"model", "parts": [{"text": "..."}]} shape.
    """
    contents = []
    for turn in history:
        role = "model" if turn["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": turn["content"]}]})
    return contents


def _extract_fake_function_call(text):
    if not text:
        return None
    match = FAKE_FUNCTION_CALL_PATTERN.search(text)
    if not match:
        return None
    name = match.group(1)
    try:
        args = json.loads(match.group(2))
    except json.JSONDecodeError:
        return None
    return name, args


def _sanitize_reply(reply_text):
    if not reply_text or "<function" in reply_text or "functionCall" in reply_text:
        print(f"SANITIZE: rejected suspicious reply text: {reply_text!r}")
        return FALLBACK_REPLY
    return reply_text


def _call_gemini(contents, retries=2):
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    body = {
        "system_instruction": {
            "parts": [{"text": build_full_system_prompt()}]
        },
        "tools": GEMINI_TOOL_DECLARATIONS,
        "contents": contents
    }

    for attempt in range(retries + 1):
        response = requests.post(GEMINI_URL, headers=headers, json=body)
        data = response.json()

        if "candidates" in data:
            return data

        print(f"GEMINI ATTEMPT {attempt + 1} FAILED:", json.dumps(data, indent=2))
        if attempt < retries:
            time.sleep(2)

    return None


def generate_ai_reply(sender_id, customer_message):
    history = get_history(sender_id)
    contents = _history_to_gemini_contents(history) + [
        {"role": "user", "parts": [{"text": customer_message}]}
    ]

    for hop in range(MAX_TOOL_HOPS):
        data = _call_gemini(contents)

        if data is None:
            return FALLBACK_REPLY

        candidate = data["candidates"][0]
        parts = candidate.get("content", {}).get("parts", [])

        function_calls = [p["functionCall"] for p in parts if "functionCall" in p]
        text_parts = [p["text"] for p in parts if "text" in p]
        combined_text = "".join(text_parts)

        # Real tool call path, this is what should normally happen.
        if function_calls:
            contents.append({"role": "model", "parts": parts})

            response_parts = []
            for call in function_calls:
                name = call["name"]
                args = call.get("args", {})
                print(f"GEMINI TOOL CALL: {name} with args {json.dumps(args)}")
                result = execute_tool(name, args)
                print(f"TOOL RESULT for {name}: {json.dumps(result)}")
                response_parts.append({
                    "functionResponse": {
                        "name": name,
                        "response": result
                    }
                })

            contents.append({"role": "user", "parts": response_parts})
            continue

        # Fallback path, in case the model hallucinated a fake textual
        # function call instead of a real one.
        fake_call = _extract_fake_function_call(combined_text)
        if fake_call:
            name, args = fake_call
            print(f"DETECTED FAKE FUNCTION CALL TEXT, recovering: {name} with args {json.dumps(args)}")
            result = execute_tool(name, args)
            print(f"TOOL RESULT for {name} (recovered): {json.dumps(result)}")

            contents.append({"role": "model", "parts": [{"text": combined_text}]})
            contents.append({
                "role": "user",
                "parts": [{"text": f"[System note: your previous response contained an invalid function call format. Here is the actual result: {json.dumps(result)}. Please respond to the customer normally using this information, without any function call syntax.]"}]
            })
            continue

        # Genuine final text answer.
        reply_text = _sanitize_reply(combined_text)
        append_turn(sender_id, customer_message, reply_text)
        return reply_text

    return FALLBACK_REPLY
