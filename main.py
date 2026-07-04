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

@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    print("RAW PAYLOAD:", json.dumps(payload, indent=2))

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "messages":
                continue

            value = change.get("value", {})
            sender = value.get("sender", {})
            sender_id = sender.get("id")
            message_text = value.get("message", {}).get("text")

            if sender_id and message_text:
                print(f"Message from {sender_id}: {message_text}")

    return Response(status_code=200)
