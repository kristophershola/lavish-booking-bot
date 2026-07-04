from fastapi import FastAPI, Request, Response
import os
import json
import requests

app = FastAPI()

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
BOT_ACCOUNT_ID = os.getenv("BOT_ACCOUNT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

processed_message_ids = set()

SYSTEM_PROMPT = """You are the booking assistant for Lavish Apartments & Cinema, a premium hospitality business in Nigeria. You handle Instagram DM enquiries for both apartment bookings and cinema bookings.

CORE RULE: You never confirm a booking as reserved. Availability does not guarantee a reservation. Payment must be received and verified before anything is confirmed. Booking flow is always: Enquiry, Availability Checked, Awaiting Payment, Payment Receipt Submitted, Availability Rechecked, Payment Verified, Confirmed by staff.

You ask only one question at a time. Never stack multiple questions in one message.

You never mention internal unit names (A1, B1, B2, C1, C2) or internal hall names (Hall 1, Hall 2) to customers. These are hidden operational details.

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

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)

def generate_ai_reply(customer_message):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": customer_message}
        ],
        "max_tokens": 300
    }
    response = requests.post(url, headers=headers, json=body)
    data = response.json()
    print("OPENAI RESPONSE:", json.dumps(data, indent=2))

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
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

    return message_data.get("messages", {}).get("data", [])

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
    reply = generate_ai_reply(text)
    send_message(sender_id, reply)

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

                for msg in reversed(recent_messages):
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
