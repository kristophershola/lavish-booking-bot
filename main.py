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
    # Step 1: get just the id of the most recently active conversation
    url = f"https://graph.facebook.com/v21.0/{IG_ACCOUNT_ID}/conversations"
    params = {
        "platform": "instagram",
        "fields": "id,updated_time",
        "limit": 1,
        "access_token": PAGE_ACCESS_TOKEN
    }
    response = requests.get(url, params=params)
    data = response.json()
    print("CONVERSATIONS LIST RESPONSE:", json.dumps(data, indent=2))

    conversations = data.get("data", [])
    if not conversations:
        print("No conversations found")
        return

    conversation_id = conversations[0].get("id")

    # Step 2: fetch just the latest message from that one conversation
    message_url = f"https://graph.facebook.com/v21.0/{conversation_id}"
    message_params = {
        "fields": "messages.limit(1){message,from,created_time}",
        "access_token": PAGE_ACCESS_TOKEN
    }
    message_response = requests.get(message_url, params=message_params)
    message_data = message_response.json()
    print("LATEST MESSAGE RESPONSE:", json.dumps(message_data, indent=2))
    return message_data

@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    print("RAW PAYLOAD:", json.dumps(payload, indent=2))

    for entry in payload.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            print("MESSAGING EVENT:", json.dumps(messaging_event, indent=2))

            sender = messaging_event.get("sender", {})
            sender_id = sender.get("id")

            message = messaging_event.get("message")
            if message and message.get("text"):
                print(f"Message from {sender_id}: {message.get('text')}")
                continue

            message_edit = messaging_event.get("message_edit")
            if message_edit:
                fetch_latest_conversation_message()

    return Response(status_code=200)
