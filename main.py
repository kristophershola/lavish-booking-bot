from fastapi import FastAPI, Request, Response
import os
import json
import requests

app = FastAPI()

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)

def fetch_latest_conversation_message():
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
        print("No conversations found")
        return None, None

    conversation_id = conversations[0].get("id")

    message_url = f"https://graph.facebook.com/v21.0/{conversation_id}"
    message_params = {
        "fields": "messages.limit(1){message,from,created_time}",
        "access_token": PAGE_ACCESS_TOKEN
    }
    message_response = requests.get(message_url, params=message_params)
    message_data = message_response.json()

    messages = message_data.get("messages", {}).get("data", [])
    if not messages:
        return None, None

    latest = messages[0]
    sender_id = latest.get("from", {}).get("id")
    text = latest.get("message")

    return sender_id, text

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

@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()

    for entry in payload.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            sender = messaging_event.get("sender", {})
            sender_id = sender.get("id")

            message = messaging_event.get("message")
            if message and message.get("text"):
                text = message.get("text")
                print(f"Message from {sender_id}: {text}")
                send_message(sender_id, f"You said: {text}")
                continue

            message_edit = messaging_event.get("message_edit")
            if message_edit:
                fetched_sender_id, fetched_text = fetch_latest_conversation_message()
                if fetched_text:
                    print(f"Message from {fetched_sender_id}: {fetched_text}")
                    send_message(fetched_sender_id, f"You said: {fetched_text}")

    return Response(status_code=200)
