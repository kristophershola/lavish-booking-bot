import json
import time

import requests

from config import GEMINI_API_KEY
from ai.prompts import build_full_system_prompt
from state.conversation import get_history, append_turn

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


def generate_ai_reply(sender_id, customer_message, retries=2):
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    history = get_history(sender_id)
    contents = history + [{"role": "user", "parts": [{"text": customer_message}]}]

    print(f"HISTORY LENGTH for {sender_id}: {len(history)} prior turns")
    print(f"FULL CONTENTS SENT TO GEMINI for {sender_id}:", json.dumps(contents, indent=2))

    body = {
        "system_instruction": {
            "parts": [{"text": build_full_system_prompt()}]
        },
        "contents": contents
    }

    for attempt in range(retries + 1):
        response = requests.post(GEMINI_URL, headers=headers, json=body)
        data = response.json()

        if "candidates" in data:
            reply_text = data["candidates"][0]["content"]["parts"][0]["text"]
            append_turn(sender_id, customer_message, reply_text)
            return reply_text

        print(f"GEMINI ATTEMPT {attempt + 1} FAILED:", json.dumps(data, indent=2))

        if attempt < retries:
            time.sleep(2)

    return "Thanks for reaching out, a team member will be with you shortly."
