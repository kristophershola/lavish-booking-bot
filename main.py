from fastapi import FastAPI, Request, Response
import os
import json
import requests

app = FastAPI()

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
BOT_ACCOUNT_ID = os.getenv("BOT_ACCOUNT_ID")

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)

def fetch_message_by_id(mid):
    url = f"https://graph.facebook.com/v21.0/{mid}"
    params = {
        "fields": "message,from,created_time",
        "access_token": PAGE_ACCESS_TOKEN
    }
    response = requests.get(url, params=params)
    data = response.json()
    print("MESSAGE BY ID RESPONSE:", json.dumps(data, indent=2))

    text = data.get("message")
    sender_id = data.get("from", {}).get("id")
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
                print("Skipping event, this is our own outgoing message")
                continue

            message = messaging_event.get("message")
            if message and message.get("text"):
                text = message.get("text")
                print(f"Message from {sender_id}: {text}")
                send_message(sender_id, f"You said: {text}")
                continue

            message_edit = messaging_event.get("message_edit")
            if message_edit:
                mid = message_edit.get("mid")
                fetched_sender_id, fetched_text = fetch_message_by_id(mid)

                if fetched_sender_id and is_our_own_account(fetched_sender_id, entry_id):
                    print("Skipping event, this is our own outgoing message")
                    continue

                if fetched_text:
                    print(f"Message from {fetched_sender_id}: {fetched_text}")
                    send_message(fetched_sender_id, f"You said: {fetched_text}")
                else:
                    print(f"No text found for mid {mid}, raw fetch may have failed")

    return Response(status_code=200)
