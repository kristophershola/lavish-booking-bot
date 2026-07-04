from fastapi import FastAPI, Request, Response
import os
import json
import time
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

app = FastAPI()

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
BOT_ACCOUNT_ID = os.getenv("BOT_ACCOUNT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

processed_message_ids = set()
conversation_history = {}
MAX_HISTORY_TURNS = 10

LAGOS_TZ = ZoneInfo("Africa/Lagos")

SYSTEM_PROMPT = """You are the booking assistant for Lavish Apartments & Cinema, a premium hospitality business in Nigeria. You handle Instagram DM enquiries for both apartment bookings and cinema bookings.

CORE RULE: You never confirm a booking as reserved. Availability does not guarantee a reservation. Payment must be received and verified before anything is confirmed. Booking flow is always: Enquiry, Availability Checked, Awaiting Payment, Payment Receipt Submitted, Availability Rechecked, Payment Verified, Confirmed by staff.

You ask only one question at a time. Never stack multiple questions in one message.

You never mention internal unit names (A1, B1, B2, C1, C2) or internal hall names (Hall 1, Hall 2) to customers. These are hidden operational details.

TERMINOLOGY: The word "packages" always refers to cinema packages only. Apartments do not have packages, they have tiers (2 Bedroom, 3 Bedroom, Special Event). If a customer asks about packages, treat it as a cinema enquiry, do not ask whether they mean apartments or cinema.

Always use the ongoing conversation history to understand what the customer is referring to. Once a detail like a date has already been established earlier in the conversation, do not ask for it again, only ask for whatever information is still missing.

DATES: Use only the date information provided below in the DATE CONTEXT section for today's date and any relative date the customer mentions, such as "tomorrow" or "this weekend". Never calculate or guess dates yourself.

APARTMENTS
Two tiers: 2 Bedroom at 80,000 naira per night, 3 Bedroom at 90,000 naira per night. A 2 Bedroom booking blocks the entire unit regardless of headcount.
Special Event or Party rate is 200,000 naira per night, triggered whenever more than 10 people will be present at any one time, including visitors, not just overnight guests.
If a customer mentions birthday, party, celebration, bridal shower, or similar, assume Special Event pricing first and confirm total headcount before quoting a price.

CINEMA
Two halls exist internally but customers never choose one, the booking engine assigns it automatically.
Six daily sessions: 9:30 to 11:50am, 12:00 to 2:20pm, 2:30 to 4:50pm, 5:00 to 7:20pm, 7:30 to 9:50pm, 10:00pm to midnight.
Six package tiers: Crunch and Drink 25,000 naira, BYOF 25,000 naira, Crunch and Wine 30,000 naira, Slice and Drink 40,000 naira, Slice and Wine 45,000 naira, Executive 55,000 naira.
If a customer wants a double session (XTRA TIME), both consecutive slots must be available before you confirm availability.

TONE
Warm, professional, and concise, matching a premium hospitality brand. Keep replies short and natural for Instagram DM, not long paragraphs.

You do not have live access to the booking calendar in this test version, so if a customer asks for actual availability, say a team member will confirm the specific date shortly, rather than inventing an answer."""

def build_date_context():
    now = datetime.now(LAGOS_TZ)
    lines = [
        "DATE CONTEXT",
        f"Current date and time in Nigeria: {now.strftime('%A, %d %B %Y, %I:%M %p')} (West Africa Time).",
        "The next 7 days are:"
    ]
    for i in range(7):
        day = now + timedelta(days=i)
        label = "Today" if i == 0 else "Tomorrow" if i == 1 else day.strftime("%A")
        lines.append(f"{label}: {day.strftime('%A, %d %B %Y')}")
    return "\n".join(lines)

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)

def generate_ai_reply(sender_id, customer_message, retries=2):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    history = conversation_history.get(sender_id, [])
    contents = history + [{"role": "user", "parts": [{"text": customer_message}]}]

    print(f"HISTORY LENGTH for {sender_id}: {len(history)} prior turns")
    print(f"FULL CONTENTS SENT TO GEMINI for {sender_id}:", json.dumps(contents, indent=2))

    full_system_prompt = SYSTEM_PROMPT + "\n\n" + build_date_context()

    body = {
        "system_instruction": {
            "parts": [{"text": full_system_prompt}]
        },
        "contents": contents
    }

    for attempt in range(retries + 1):
        response = requests.post(url, headers=headers, json=body)
        data = response.json()

        if "candidates" in data:
            reply_text = data["candidates"][0]["content"]["parts"][0]["text"]

            history.append({"role": "user", "parts": [{"text": customer_message}]})
            history.append({"role": "model", "parts": [{"text": reply_text}]})
            conversation_history[sender_id] = history[-(MAX_HISTORY_TURNS * 2):]

            return reply_text

        print(f"GEMINI ATTEMPT {attempt + 1} FAILED:", json.dumps(data, indent=2))

        if attempt < retries:
            time.sleep(2)

    return "Thanks for reaching out, a team member will be with you shortly."

def fetch_recent_conversation_messages(limit=5):
    url = f"https://graph.facebook.com/v21.0/{IG_ACCOUNT_ID}/conversations"
    params = {
        "platform": "instagram",
        "fields": "id,updated_time",
        "limit": 1,
        "access_token": PAGE_ACCESS_TOKEN
    }
    response = requests.get(url, params=params)
    data = response.json()

    conversations = data.get("data", [])
    if not conversations:
        return []

    conversation_id = conversations[0].get("id")

    message_url = f"https://graph.facebook.com/v21.0/{conversation_id}"
    message_params = {
        "fields": f"messages.limit({limit}){{message,from,created_time}}",
        "access_token": PAGE_ACCESS_TOKEN
    }
    message_response = requests.get(message_url, params=message_params)
    message_data = message_response.json()

    messages = message_data.get("messages", {}).get("data", [])
    messages_sorted = sorted(messages, key=lambda m: m.get("created_time", ""))
    return messages_sorted

def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v21.0/{IG_ACCOUNT_ID}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    params = {"access_token": PAGE_ACCESS_TOKEN}

    response = requests.post(url, params=params, json=payload)
    result = response.json()
    print("SEND MESSAGE RESPONSE:", json.dumps(result, indent=2))
    return result

def is_our_own_account(sender_id, entry_id):
    return sender_id == entry_id or sender_id == BOT_ACCOUNT_ID

def handle_customer_message(sender_id, text):
    print(f"Message from {sender_id}: {text}")
    reply = generate_ai_reply(sender_id, text)
    print(f"Reply to {sender_id}: {reply}")
    send_message(sender_id, reply)

@app.on_event("startup")
async def seed_processed_messages_on_startup():
    recent_messages = fetch_recent_conversation_messages(limit=10)
    for msg in recent_messages:
        msg_id = msg.get("id")
        if msg_id:
            processed_message_ids.add(msg_id)
    print(f"Startup: seeded {len(processed_message_ids)} existing message ids as already processed")

@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()

    for entry in payload.get("entry", []):
        entry_id = entry.get("id")

        for messaging_event in entry.get("messaging", []):
            sender = messaging_event.get("sender", {})
            sender_id = sender.get("id")

            if sender_id and is_our_own_account(sender_id, entry_id):
                continue

            message = messaging_event.get("message")
            if message and message.get("text"):
                handle_customer_message(sender_id, message.get("text"))
                continue

            message_edit = messaging_event.get("message_edit")
            if message_edit:
                recent_messages = fetch_recent_conversation_messages(limit=5)

                for msg in recent_messages:
                    msg_id = msg.get("id")
                    msg_sender = msg.get("from", {}).get("id")
                    msg_text = msg.get("message")

                    if not msg_id or msg_id in processed_message_ids:
                        continue

                    processed_message_ids.add(msg_id)

                    if is_our_own_account(msg_sender, entry_id):
                        continue

                    if msg_text:
                        handle_customer_message(msg_sender, msg_text)

    return Response(status_code=200)
