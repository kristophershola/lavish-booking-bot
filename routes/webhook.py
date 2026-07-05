from fastapi import APIRouter, Request, Response

from config import VERIFY_TOKEN
from ai.gemini import generate_ai_reply
from services.instagram import fetch_recent_conversation_messages, send_message, is_our_own_account
from state.conversation import is_processed, mark_processed

router = APIRouter()


def handle_customer_message(sender_id, text):
    print(f"Message from {sender_id}: {text}")
    reply = generate_ai_reply(sender_id, text)
    print(f"Reply to {sender_id}: {reply}")
    send_message(sender_id, reply)


@router.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)


@router.post("/webhook")
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

                for msg in recent_messages:
                    msg_id = msg.get("id")
                    msg_sender = msg.get("from", {}).get("id")
                    msg_text = msg.get("message")

                    if not msg_id or is_processed(msg_id):
                        continue

                    mark_processed(msg_id)

                    if is_our_own_account(msg_sender, entry_id):
                        continue

                    if msg_text:
                        handle_customer_message(msg_sender, msg_text)

    return Response(status_code=200)
