@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    print("RAW PAYLOAD:", json.dumps(payload, indent=2))

    for entry in payload.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            if "message" not in messaging_event:
                continue  # skip read receipts, reactions, etc.

            sender = messaging_event.get("sender", {})
            sender_id = sender.get("id")
            message_text = messaging_event.get("message", {}).get("text")

            if sender_id and message_text:
                print(f"Message from {sender_id}: {message_text}")

    return Response(status_code=200)
