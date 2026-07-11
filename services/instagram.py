import json

import requests

from config import PAGE_ACCESS_TOKEN, IG_ACCOUNT_ID, BOT_ACCOUNT_ID

GRAPH_API_VERSION = "v21.0"


def fetch_recent_conversation_messages(limit=5):
    """Fetches the most recently active conversation, then returns its last
    `limit` messages sorted oldest first by actual created_time, rather than
    assuming an order from the API response.
    """
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_ACCOUNT_ID}/conversations"
    params = {
        "platform": "instagram",
        "fields": "id,updated_time",
        "limit": 1,
        "access_token": PAGE_ACCESS_TOKEN
    }
    response = requests.get(url, params=params)
    data = response.json()

    conversations = data.get("data", [])
    if not conversations:
        return []

    conversation_id = conversations[0].get("id")

    message_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{conversation_id}"
    message_params = {
        "fields": f"messages.limit({limit}){{message,from,created_time}}",
        "access_token": PAGE_ACCESS_TOKEN
    }
    message_response = requests.get(message_url, params=message_params)
    message_data = message_response.json()

    messages = message_data.get("messages", {}).get("data", [])
    return sorted(messages, key=lambda m: m.get("created_time", ""))


def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_ACCOUNT_ID}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    params = {"access_token": PAGE_ACCESS_TOKEN}

    response = requests.post(url, params=params, json=payload)
    result = response.json()
    print("SEND MESSAGE RESPONSE:", json.dumps(result, indent=2))
    return result


def send_image(recipient_id, image_url):
    """Sends an image to a recipient via Instagram messaging."""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_ACCOUNT_ID}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "image",
                "payload": {"url": image_url}
            }
        }
    }
    params = {"access_token": PAGE_ACCESS_TOKEN}

    response = requests.post(url, params=params, json=payload)
    result = response.json()
    print("SEND IMAGE RESPONSE:", json.dumps(result, indent=2))
    return result


def is_our_own_account(sender_id, entry_id):
    """True if a message came from the bot's own account rather than a
    customer, whether identified by the webhook entry id or the account's
    Instagram scoped id seen when its own replies loop back through.
    """
    return sender_id == entry_id or sender_id == BOT_ACCOUNT_ID
