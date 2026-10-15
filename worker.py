import argparse
import sys
import time
import traceback
from config import BEEPER_BASE_URL, BEEPER_POLL_INTERVAL, AI_PROVIDER, GEMINI_MODEL, GROQ_MODEL

if AI_PROVIDER == "groq":
    from ai.groq_client import generate_ai_reply
    ACTIVE_MODEL = GROQ_MODEL
else:
    from ai.gemini_client import generate_ai_reply
    ACTIVE_MODEL = GEMINI_MODEL
from services.beeper import (
    get_recent_chats,
    send_chat_message,
    mark_chat_read,
    is_beeper_healthy,
)
from state.conversation import is_processed, mark_processed, seed_processed_ids


def seed_existing_messages():
    """On worker startup, mark recent active message IDs as processed
    so the bot doesn't reply to historic conversation turns that happened
    while the bot was offline.
    """
    print("[Worker] Seeding recent chats on startup...")
    try:
        chats = get_recent_chats(limit=25)
        seeded_ids = []
        for chat in chats:
            preview = chat.get("preview")
            if preview and preview.get("id"):
                seeded_ids.append(str(preview["id"]))
        seed_processed_ids(seeded_ids)
    except Exception as e:
        print(f"[Worker] Warning: could not seed existing messages: {e}")


def poll_and_process_once():
    """Polls recent chats and processes any unhandled inbound customer messages."""
    chats = get_recent_chats(limit=15)
    processed_count = 0

    for chat in chats:
        chat_id = chat.get("id")
        preview = chat.get("preview")
        if not preview:
            continue

        # If latest message in thread is from us (isSender: true), it's already answered
        if preview.get("isSender", False):
            continue

        message_id = str(preview.get("id"))
        customer_text = (preview.get("text") or "").strip()

        if not customer_text or is_processed(message_id):
            continue

        chat_title = chat.get("title", chat_id)
        network = chat.get("network", "Chat")
        print(f"\n[Worker] New message in {network} [{chat_title}]: {customer_text}")

        # Mark processed before generating to prevent duplicate processing on slow AI response
        mark_processed(message_id)

        try:
            reply = generate_ai_reply(sender_id=chat_id, customer_message=customer_text)
            print(f"[Worker] Replying to {chat_title}: {reply}")
            send_chat_message(chat_id, reply)
            mark_chat_read(chat_id)
            processed_count += 1
        except Exception as e:
            print(f"[Worker] Error processing message {message_id}: {e}")
            traceback.print_exc()

    return processed_count


def run_worker():
    print(f"=================================================")
    print(f" Lavish Booking Bot - Beeper Worker Daemon       ")
    print(f" Target Endpoint: {BEEPER_BASE_URL}              ")
    print(f" AI Provider:     {AI_PROVIDER.upper()} ({ACTIVE_MODEL})")
    print(f" Poll Interval:   {BEEPER_POLL_INTERVAL}s        ")
    print(f"=================================================")

    # Wait for Beeper connection on start
    while not is_beeper_healthy():
        print(f"[Worker] Waiting for Beeper Desktop at {BEEPER_BASE_URL}...")
        time.sleep(3)

    print("[Worker] Connected to Beeper Desktop successfully.")
    seed_existing_messages()

    consecutive_errors = 0
    print(f"[Worker] Listening for incoming messages...")

    while True:
        try:
            poll_and_process_once()
            consecutive_errors = 0
            time.sleep(BEEPER_POLL_INTERVAL)
        except KeyboardInterrupt:
            print("\n[Worker] Stopping daemon...")
            sys.exit(0)
        except Exception as e:
            consecutive_errors += 1
            backoff = min(30, 2 ** min(consecutive_errors, 5))
            print(f"[Worker] API connection error (attempt {consecutive_errors}): {e}")
            print(f"[Worker] Retrying in {backoff} seconds...")
            time.sleep(backoff)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lavish Beeper Polling Worker")
    parser.add_argument("--once", action="store_true", help="Run a single poll iteration and exit")
    args = parser.parse_args()

    if args.once:
        poll_and_process_once()
    else:
        run_worker()
