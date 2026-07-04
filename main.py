from fastapi import FastAPI, Request, Response
import os
import json

app = FastAPI()

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)

def extract_message(entry):
    results = []

    for messaging_event in entry.get("messaging", []):
        sender = messaging_event.get("sender", {})
        sender_id = sender.get("id")

        message = messaging_event.get("message")
        if message and message.get("text"):
            results.append((sender_id, message.get("text")))
            continue

        message_edit = messaging_event.get("message_edit")
        if message_edit and message_edit.get("text"):
            results.append((sender_id, message_edit.get("text")))

    for change in entry.get("changes", []):
        if change.get("field") != "messages":
            continue
        value = change.get("value", {})
        sender = value.get("sender", {})
        message = value.get("message", {})
        if message.get("text"):
            results.append((sender.get("id"), message.get("text")))

    return results

@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    print("RAW PAYLOAD:", json.dumps(payload, indent=2))

    for entry in payload.get("entry", []):
        for sender_id, message_text in extract_message(entry):
            print(f"Message from {sender_id}: {message_text}")

    return Response(status_code=200)
