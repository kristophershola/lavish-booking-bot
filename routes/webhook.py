from fastapi import APIRouter, Request, Response

from config import VERIFY_TOKEN
from ai.groq_client import generate_ai_reply
from services.instagram import (
    fetch_recent_conversation_messages,
    send_message,
    send_quick_reply,
    is_our_own_account,
)
from services.menu import MAIN_MENU, QUIET_OR_PARTY, RESPONSES
from state.conversation import is_processed, mark_processed, append_system_note
from state.user_state import get_state, set_state, clear_state

router = APIRouter()


def _get_payload(message):
    """Extract quick_reply payload from an Instagram message, or None."""
    quick_reply = message.get("quick_reply") if message else None
    return quick_reply.get("payload") if quick_reply else None


def _handle_button_press(sender_id, payload, message_text):
    """Route a quick-reply button press through the state machine.
    Returns True if the button was handled (no AI call needed).
    """
    state = get_state(sender_id)
    current_menu = state["menu"] if state else None

    # MAIN_MENU buttons
    if payload == "BOOK_APARTMENT":
        set_state(sender_id, "APARTMENT_QUIET_PARTY", {"service": "apartment"})
        send_quick_reply(sender_id, QUIET_OR_PARTY["text"], QUIET_OR_PARTY["buttons"])
        return True

    if payload == "BOOK_CINEMA":
        set_state(sender_id, "CINEMA_BOOKING", {"service": "cinema"})
        text = RESPONSES["BOOK_CINEMA"]
        send_message(sender_id, text)
        append_system_note(sender_id, "[System: Customer selected Book Cinema. Ask for their preferred date to check availability.]")
        return False  # hand to AI

    if payload == "SOMETHING_ELSE":
        set_state(sender_id, "SOMETHING_ELSE", {})
        text = RESPONSES["SOMETHING_ELSE"]
        send_message(sender_id, text)
        return False  # hand to AI

    # APARTMENT_QUIET_PARTY buttons
    if current_menu == "APARTMENT_QUIET_PARTY":
        if payload == "QUIET_STAY":
            set_state(sender_id, "APARTMENT_BOOKING", {"service": "apartment", "is_party": False})
            append_system_note(sender_id, "[System: Customer selected Book an Apartment — Quiet Stay. Proceed from tier determination.]")
            return False  # hand to AI

        if payload == "PARTY":
            set_state(sender_id, "APARTMENT_BOOKING", {"service": "apartment", "is_party": True})
            append_system_note(sender_id, "[System: Customer selected Book an Apartment — Party. Special Event rate (200k/night) applies. Skip tier question.]")
            return False  # hand to AI

    return False


def _show_main_menu(sender_id):
    """Send the main menu and set user state."""
    set_state(sender_id, "MAIN_MENU", {})
    send_quick_reply(sender_id, MAIN_MENU["text"], MAIN_MENU["buttons"])


def handle_customer_message(sender_id, text, message=None):
    print(f"Message from {sender_id}: {text}")

    # Check for quick reply payload first
    payload = _get_payload(message)
    if payload:
        handled = _handle_button_press(sender_id, payload, text)
        if handled:
            return

    # Show main menu to new users
    state = get_state(sender_id)
    if state is None:
        _show_main_menu(sender_id)
        return

    # For return visitors at MAIN_MENU, re-send buttons
    if state["menu"] == "MAIN_MENU":
        _show_main_menu(sender_id)
        return

    # Pass to AI for free-text
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
                handle_customer_message(
                    sender_id,
                    message.get("text"),
                    message=message
                )
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
