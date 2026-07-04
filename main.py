from fastapi import FastAPI, Request, Response
import os

app = FastAPI()

VERIFY_TOKEN = os.getenv("a91f3e2c8b0d4a7f1e6c9d2b5f8a3e7c")  # you choose this string yourself

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
    
    # Meta sends a batch of "entry" objects, each can contain messaging events
    for entry in payload.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            sender_id = messaging_event["sender"]["id"]
            message_text = messaging_event.get("message", {}).get("text")
            
            if message_text:
                # this is where you'd call your AI agent / booking engine
                print(f"Message from {sender_id}: {message_text}")

    return Response(status_code=200)
