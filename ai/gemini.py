import json
import time

import requests

from config import GEMINI_API_KEY
from ai.prompts import build_full_system_prompt
from ai.tools import TOOL_DECLARATIONS, execute_tool
from state.conversation import get_history, append_turn

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

MAX_TOOL_HOPS = 3


def _call_gemini(contents, retries=2):
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    body = {
        "system_instruction": {
            "parts": [{"text": build_full_system_prompt()}]
        },
        "tools": TOOL_DECLARATIONS,
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
    contents = history + [{"role": "user", "parts": [{"text": customer_message}]}]

    for hop in range(MAX_TOOL_HOPS):
        data = _call_gemini(contents)

        if data is None:
            return "Thanks for reaching out, a team member will be with you shortly."

        candidate = data["candidates"][0]
        parts = candidate.get("content", {}).get("parts", [])

        function_calls = [p["functionCall"] for p in parts if "functionCall" in p]
        text_parts = [p["text"] for p in parts if "text" in p]

        if not function_calls:
            reply_text = "".join(text_parts) if text_parts else "Thanks for reaching out, a team member will be with you shortly."
            append_turn(sender_id, customer_message, reply_text)
            return reply_text

        # Model wants to call one or more tools before answering.
        # Append its own turn (the function call request) to the running
        # contents, then append our function responses, then loop back to
        # ask Gemini again with the results available.
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

    # Exhausted tool call hops without a final text answer, fall back safely.
    return "Thanks for reaching out, a team member will be with you shortly."
