import glob
import json
import os
import requests
from config import BEEPER_BASE_URL, BEEPER_API_TOKEN


def get_beeper_token():
    """Dynamically reads the token from Antigravity/MCP auth directory,
    or falls back to the environment variable.
    """
    if BEEPER_API_TOKEN:
        return BEEPER_API_TOKEN

    auth_pattern = os.path.expanduser(
        r"~/.gemini/config/plugins/beeper/.mcp-auth/mcp-remote-*/*_tokens.json"
    )
    matches = glob.glob(auth_pattern)
    if matches:
        try:
            with open(matches[0], "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("access_token")
        except Exception as e:
            print(f"[Beeper] Error reading token file: {e}")

    return None


def _headers():
    token = get_beeper_token()
    if not token:
        raise ValueError("No Beeper API token found in config or .mcp-auth directory.")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def is_beeper_healthy():
    """Quick check if Beeper Desktop local server is reachable and authorized."""
    try:
        url = f"{BEEPER_BASE_URL}/v1/chats"
        resp = requests.get(url, headers=_headers(), params={"limit": 1}, timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def get_recent_chats(limit=15, unread_only=False):
    """Fetches recent chats sorted by latest activity descending."""
    url = f"{BEEPER_BASE_URL}/v1/chats"
    params = {"limit": limit}
    if unread_only:
        params["unreadOnly"] = "true"
    resp = requests.get(url, headers=_headers(), params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("items", [])


def get_chat_messages(chat_id, limit=5):
    """Fetches messages for a specific chat ID."""
    url = f"{BEEPER_BASE_URL}/v1/chats/{chat_id}/messages"
    params = {"limit": limit}
    resp = requests.get(url, headers=_headers(), params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("items", [])


def send_chat_message(chat_id, text):
    """Sends a text message to a specific Beeper chat."""
    url = f"{BEEPER_BASE_URL}/v1/chats/{chat_id}/messages"
    payload = {"text": text}
    resp = requests.post(url, headers=_headers(), json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def mark_chat_read(chat_id):
    """Marks a chat as read in Beeper."""
    url = f"{BEEPER_BASE_URL}/v1/chats/{chat_id}/read"
    try:
        requests.post(url, headers=_headers(), timeout=5)
    except Exception as e:
        print(f"[Beeper] Warning: failed to mark chat {chat_id} as read: {e}")
