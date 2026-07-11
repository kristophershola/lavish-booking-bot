from config import MAX_HISTORY_TURNS

# NOTE: both of these live only in memory and reset on every container
# restart. This is fine for testing but should be replaced with a durable
# store (the Google Sheet, or a small database) before going live, so a
# redeploy mid conversation cannot cause messages to be replayed or
# conversation context to be lost for someone chatting at that moment.

_conversation_history = {}
_processed_message_ids = set()


def get_history(sender_id):
    """Returns this sender's history as a list of OpenAI-style messages,
    e.g. [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    return _conversation_history.get(sender_id, [])


def append_turn(sender_id, user_message, model_reply):
    history = _conversation_history.get(sender_id, [])
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": model_reply})
    _conversation_history[sender_id] = history[-(MAX_HISTORY_TURNS * 2):]


def is_processed(message_id):
    return message_id in _processed_message_ids


def mark_processed(message_id):
    _processed_message_ids.add(message_id)


def seed_processed_ids(message_ids):
    for message_id in message_ids:
        if message_id:
            _processed_message_ids.add(message_id)
    print(f"Startup: seeded {len(_processed_message_ids)} existing message ids as already processed")
