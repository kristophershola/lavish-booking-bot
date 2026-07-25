# Button Menu Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the bot's open-ended Q&A start with structured button menus that guide guests through booking flows.

**Architecture:** Lightweight state machine (per-user `menu` + `context` dict) sits in front of the existing Groq AI. Button taps advance state and inject context as system notes; free-text falls through to the AI unchanged.

**Tech Stack:** Python 3.14+, FastAPI, Instagram Graph API v21.0

## Global Constraints

- Python 3.14+ standard library only (no new dependencies)
- Follow existing code patterns: in-memory dicts for state (same as `state/conversation.py`)
- Instagram Quick Reply payload format: `{"content_type": "text", "title": "...", "payload": "..."}`
- All button payloads are UPPER_SNAKE_CASE strings
- System notes injected to AI use `[System: ...]` bracket format
- Send main menu on first message (when `get_state()` returns `None`)

---

### Task 1: User State Model

**Files:**
- Create: `state/user_state.py`
- Create: `tests/test_user_state.py`

**Interfaces:**
- Produces: `get_state(sender_id) -> dict or None`, `set_state(sender_id, menu, context)`, `clear_state(sender_id)`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_user_state.py
from state.user_state import get_state, set_state, clear_state


def test_get_state_returns_none_for_new_user():
    assert get_state("unknown_sender") is None


def test_set_and_get_state():
    set_state("sender_1", "APARTMENT_QUIET_PARTY", {"service": "apartment"})
    state = get_state("sender_1")
    assert state["menu"] == "APARTMENT_QUIET_PARTY"
    assert state["context"] == {"service": "apartment"}


def test_clear_state():
    set_state("sender_1", "APARTMENT_QUIET_PARTY", {})
    clear_state("sender_1")
    assert get_state("sender_1") is None


def test_clear_state_unknown_sender_does_not_raise():
    clear_state("never_set")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```
python -c "from state.user_state import get_state; print('module not found' if not get_state else 'unexpected')"
```
Expected: `ModuleNotFoundError: No module named 'state.user_state'`

- [ ] **Step 3: Write minimal implementation**

```python
# state/user_state.py

_user_state = {}


def get_state(sender_id):
    return _user_state.get(sender_id)


def set_state(sender_id, menu, context=None):
    _user_state[sender_id] = {
        "menu": menu,
        "context": context or {}
    }


def clear_state(sender_id):
    _user_state.pop(sender_id, None)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_user_state.py -v
```
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add state/user_state.py tests/test_user_state.py
git commit -m "feat: add user state model for menu navigation"
```

---

### Task 2: Menu Definitions

**Files:**
- Create: `services/menu.py`
- Create: `tests/test_menu.py`

**Interfaces:**
- Produces: `MAIN_MENU`, `QUIET_OR_PARTY` dicts, `RESPONSES` dict mapping payload to response text

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_menu.py
from services.menu import MAIN_MENU, QUIET_OR_PARTY, RESPONSES


def test_main_menu_has_three_buttons():
    assert len(MAIN_MENU["buttons"]) == 3


def test_main_menu_buttons_have_required_fields():
    for btn in MAIN_MENU["buttons"]:
        assert "title" in btn
        assert "payload" in btn


def test_quiet_or_party_has_two_buttons():
    assert len(QUIET_OR_PARTY["buttons"]) == 2


def test_responses_has_all_payloads():
    all_payloads = {"BOOK_APARTMENT", "BOOK_CINEMA", "SOMETHING_ELSE", "QUIET_STAY", "PARTY"}
    for p in all_payloads:
        assert p in RESPONSES, f"Missing response for {p}"
```

- [ ] **Step 2: Run tests to verify they fail**

Expected: ModuleNotFoundError

- [ ] **Step 3: Write minimal implementation**

```python
# services/menu.py

MAIN_MENU = {
    "text": "Welcome to Lavish! How can we help you?",
    "buttons": [
        {"title": "Book an Apartment", "payload": "BOOK_APARTMENT"},
        {"title": "Book Cinema", "payload": "BOOK_CINEMA"},
        {"title": "Something Else?", "payload": "SOMETHING_ELSE"},
    ]
}

QUIET_OR_PARTY = {
    "text": "Will this be a quiet stay or a party?",
    "buttons": [
        {"title": "Quiet Stay", "payload": "QUIET_STAY"},
        {"title": "Party", "payload": "PARTY"},
    ]
}

RESPONSES = {
    "QUIET_STAY": None,  # handled by system note + AI
    "PARTY": None,       # handled by system note + AI
    "BOOK_CINEMA": "What date(s) would you like to book? So we can check availability",
    "SOMETHING_ELSE": "We're setting up our FAQ section. In the meantime, feel free to ask me anything!",
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_menu.py -v
```
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add services/menu.py tests/test_menu.py
git commit -m "feat: add menu and button definitions"
```

---

### Task 3: Quick Reply Sending Function

**Files:**
- Modify: `services/instagram.py`
- Create: `tests/test_instagram.py`

**Interfaces:**
- Consumes: uses `PAGE_ACCESS_TOKEN` and `IG_ACCOUNT_ID` from `config.py`
- Produces: `send_quick_reply(recipient_id, text, buttons)` — sends text with up to 3 quick reply buttons

- [ ] **Step 1: Write the failing test**

```python
# tests/test_instagram.py
from services.instagram import build_quick_reply_payload


def test_build_quick_reply_payload():
    buttons = [
        {"title": "Quiet Stay", "payload": "QUIET_STAY"},
        {"title": "Party", "payload": "PARTY"},
    ]
    payload = build_quick_reply_payload("recip_1", "Will this be a quiet stay or a party?", buttons)
    assert payload["recipient"]["id"] == "recip_1"
    assert payload["message"]["text"] == "Will this be a quiet stay or a party?"
    assert len(payload["message"]["quick_replies"]) == 2
    assert payload["message"]["quick_replies"][0]["content_type"] == "text"
    assert payload["message"]["quick_replies"][0]["title"] == "Quiet Stay"
    assert payload["message"]["quick_replies"][0]["payload"] == "QUIET_STAY"
```

- [ ] **Step 2: Run test to verify it fails**

Expected: ModuleNotFoundError or ImportError

- [ ] **Step 3: Write minimal implementation**

Add to `services/instagram.py`:

```python
def build_quick_reply_payload(recipient_id, text, buttons):
    """Build a message payload with quick reply buttons.
    buttons is a list of {"title": str, "payload": str}.
    """
    return {
        "recipient": {"id": recipient_id},
        "message": {
            "text": text,
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": btn["title"],
                    "payload": btn["payload"]
                }
                for btn in buttons
            ]
        }
    }


def send_quick_reply(recipient_id, text, buttons):
    """Send a text message with quick reply buttons via Instagram Graph API."""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_ACCOUNT_ID}/messages"
    payload = build_quick_reply_payload(recipient_id, text, buttons)
    params = {"access_token": PAGE_ACCESS_TOKEN}
    response = requests.post(url, params=params, json=payload)
    result = response.json()
    print("SEND QUICK REPLY RESPONSE:", json.dumps(result, indent=2))
    return result
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_instagram.py -v
```
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add services/instagram.py tests/test_instagram.py
git commit -m "feat: add send_quick_reply function"
```

---

### Task 4: System Note Helper

**Files:**
- Modify: `state/conversation.py`
- Create: `tests/test_conversation.py`

**Interfaces:**
- Produces: `append_system_note(sender_id, note_text)` — appends a system message to the conversation history

- [ ] **Step 1: Write the failing test**

```python
# tests/test_conversation.py
from state.conversation import append_system_note, get_history


def test_append_system_note():
    append_system_note("sender_sys", "[System: test note]")
    history = get_history("sender_sys")
    assert len(history) >= 1
    assert history[-1]["role"] == "system"
    assert history[-1]["content"] == "[System: test note]"


def test_append_system_note_does_not_affect_other_users():
    append_system_note("sender_sys_2", "[System: note]")
    history = get_history("sender_sys_2")
    assert len(history) == 1
    assert get_history("other_sender") == []
```

- [ ] **Step 2: Run test to verify it fails**

Expected: ImportError for `append_system_note`

- [ ] **Step 3: Write minimal implementation**

Add to `state/conversation.py`:

```python
def append_system_note(sender_id, note_text):
    history = _conversation_history.get(sender_id, [])
    history.append({"role": "system", "content": note_text})
    _conversation_history[sender_id] = history
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_conversation.py -v
```
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add state/conversation.py tests/test_conversation.py
git commit -m "feat: add append_system_note for injecting AI context"
```

---

### Task 5: Webhook Routing with State Machine

**Files:**
- Modify: `routes/webhook.py`

**Interfaces:**
- Consumes: `get_state`, `set_state`, `clear_state` from `state/user_state`; `append_system_note` from `state/conversation`; `MAIN_MENU`, `QUIET_OR_PARTY`, `RESPONSES` from `services/menu`; `send_quick_reply`, `send_message` from `services/instagram`; `generate_ai_reply` from `ai/groq_client`
- Modifies: `handle_customer_message` to add state routing before AI call

- [ ] **Step 1: Read current webhook.py to understand existing code**

- [ ] **Step 2: Add state-routing logic**

Replace `handle_customer_message` and the webhook POST handler in `routes/webhook.py`:

```python
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
```

- [ ] **Step 3: Deploy and test**

- [ ] **Step 4: Commit**

```bash
git add routes/webhook.py
git commit -m "feat: add button-driven menu routing before AI call"
```

---

### Task 6: Integration Test (Manual)

- [ ] **Step 1: Start the server locally or deploy to Heroku**
- [ ] **Step 2: Send a DM to the bot from Instagram**
  - Expected: Main menu buttons appear ("Book an Apartment", "Book Cinema", "Something Else?")
- [ ] **Step 3: Tap "Book an Apartment"**
  - Expected: "Will this be a quiet stay or a party?" with "Quiet Stay" and "Party" buttons
- [ ] **Step 4: Tap "Quiet Stay"**
  - Expected: AI responds starting from tier determination
- [ ] **Step 5: Tap "Book Cinema"**
  - Expected: AI asks for preferred date
- [ ] **Step 6: Tap "Something Else?"**
  - Expected: FAQ placeholder message and AI handles free-text
- [ ] **Step 7: Type a free-text question**
  - Expected: AI responds as before
