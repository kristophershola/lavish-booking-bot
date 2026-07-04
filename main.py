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

def fetch_latest_message_from_conversation(sender_id):
    url = f"https://graph.facebook.com/v21.0/{IG_ACCOUNT_ID}/conversations"
    params = {
        "platform": "instagram",
        "user_id": sender_id,
        "fields": "messages{message,from,created_time}",
        "access_token": PAGE_ACCESS_TOKEN
    }
    response = requests.get(url, params=params)
    data = response.json()
    print("CONVERSATIONS RESPONSE:", json.dumps(data, indent=2))
    return data

@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    print("RAW PAYLOAD:", json.dumps(payload, indent=2))

    for entry in payload.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            sender = messaging_event.get("sender", {})
            sender_id = sender.get("id")

            message = messaging_event.get("message")
            if message and message.get("text"):
                print(f"Message from {sender_id}: {message.get('text')}")
                continue

            message_edit = messaging_event.get("message_edit")
            if message_edit and sender_id:
                fetch_latest_message_from_conversation(sender_id)

    return Response(status_code=200)
