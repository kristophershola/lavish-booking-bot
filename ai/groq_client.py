import json
import time

import requests

from config import GROQ_API_KEY, GROQ_MODEL
from ai.prompts import build_full_system_prompt
from ai.tools import TOOL_DECLARATIONS, execute_tool
from state.conversation import get_history, append_turn

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MAX_TOOL_HOPS = 3


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
            time.sleep(2)

    return None


def generate_ai_reply(sender_id, customer_message):
    history = get_history(sender_id)
    system_message = {"role": "system", "content": build_full_system_prompt()}
    messages = [system_message] + history + [{"role": "user", "content": customer_message}]

    for hop in range(MAX_TOOL_HOPS):
        data = _call_groq(messages)

        if data is None:
            return "Thanks for reaching out, a team member will be with you shortly."

        message = data["choices"][0]["message"]
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            reply_text = message.get("content") or "Thanks for reaching out, a team member will be with you shortly."
            append_turn(sender_id, customer_message, reply_text)
            return reply_text

        # Model wants to call one or more tools before answering. Append its
        # own turn (the tool call request) to the running messages, then
        # append each tool's result as a "tool" role message, then loop back
        # to ask Groq again now that results are available.
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

            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": json.dumps(result)
            })

    # Exhausted tool call hops without a final text answer, fall back safely.
    return "Thanks for reaching out, a team member will be with you shortly."
