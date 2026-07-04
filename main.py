from fastapi import FastAPI, Request, Response
import os
import json
import requests

app = FastAPI()

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
BOT_ACCOUNT_ID = os.getenv("BOT_ACCOUNT_ID")

processed_message_ids = set()

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)

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
                text = message.get("text")
                print(f"Message from {sender_id}: {text}")
                send_message(sender_id, f"You said: {text}")
                continue

            message_edit = messaging_event.get("message_edit")
            if message_edit:
                recent_messages = fetch_recent_conversation_messages(limit=5)

                # oldest first, so replies go out in the order messages arrived
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
                        print(f"Message from {msg_sender}: {msg_text}")
                        send_message(msg_sender, f"You said: {msg_text}")

    return Response(status_code=200)
