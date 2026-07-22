# Button Menu Flow — Design Spec

## Goal

Replace the bot's open-ended Q&A start with structured button menus. Guests see specific option buttons to tap, and the bot guides them through the booking flow with minimal free-text reliance.

## Architecture

Lightweight state machine sits in front of the existing AI. Button taps advance state and inject context; free-text falls through to the AI as before.

## State Model (`state/user_state.py`)

Per-user in-memory dictionary (same pattern as `conversation.py`):

| Key | Values | Purpose |
|-----|--------|---------|
| `menu` | `None`, `MAIN_MENU`, `APARTMENT_QUIET_PARTY`, `APARTMENT_BOOKING`, `CINEMA_BOOKING`, `SOMETHING_ELSE` | Current screen |
| `context` | `dict` | Accumulated booking details (`is_party`, `service`) |

Functions: `get_state(sender_id)`, `set_state(sender_id, menu, context=None)`, `clear_state(sender_id)`.

## Menu Definitions (`services/menu.py`)

```python
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
```

## Instagram Sending (`services/instagram.py`)

Add `send_quick_reply(recipient_id, text, buttons)` that sends the Instagram Quick Reply payload format:
```json
{
  "recipient": {"id": "<recipient_id>"},
  "message": {
    "text": "<text>",
    "quick_replies": [
      {"content_type": "text", "title": "<title>", "payload": "<payload>"},
      ...
    ]
  }
}
```

Existing `send_message` and `send_image` remain unchanged.

## Webhook Routing (`routes/webhook.py`)

`handle_customer_message` gains a routing layer before the AI call:

1. **Quick reply detected** (message has `quick_reply.payload`) → route by state machine
2. **Free-text** → pass to AI

### State Transitions

| Current `menu` | Payload | New `menu` | Action |
|---|---|---|---|
| `None` or any | `BOOK_APARTMENT` | `APARTMENT_QUIET_PARTY` | Send quiet/party buttons |
| `APARTMENT_QUIET_PARTY` | `QUIET_STAY` | `APARTMENT_BOOKING` | Inject system note, call AI |
| `APARTMENT_QUIET_PARTY` | `PARTY` | `APARTMENT_BOOKING` | Inject system note, call AI |
| Any | `BOOK_CINEMA` | `CINEMA_BOOKING` | Send "What date(s)?" text + menu image, call AI |
| Any | `SOMETHING_ELSE` | `SOMETHING_ELSE` | Send placeholder text, call AI |

### Button Responses

| Trigger | Bot Response |
|---------|-------------|
| First message / no state | Main menu buttons |
| `BOOK_APARTMENT` | Quiet or Party buttons |
| `QUIET_STAY` | System note injected, AI continues from STEP 4 |
| `PARTY` | System note injected, AI continues (special event rate) |
| `BOOK_CINEMA` | "What date(s) would you like to book? So we can check availability" |
| `SOMETHING_ELSE` | "We're setting up our FAQ section. In the meantime, feel free to ask me anything!" |

### System Notes Injected to AI

- Quiet Stay: `[System: Customer selected Book an Apartment — Quiet Stay. Proceed from tier determination.]`
- Party: `[System: Customer selected Book an Apartment — Party. Special Event rate (200k/night) applies. Skip tier question.]`
- Cinema: `[System: Customer selected Book Cinema. Ask for their preferred date to check availability.]`

## AI Prompt Changes (`ai/prompts.py`)

No changes needed. The existing apartment flow prompt remains intact for free-text users. Button-injected system notes naturally guide the AI.

## First Message Handling

When `get_state(sender_id)` returns `None` (new user or state cleared), the handler sends main menu buttons instead of passing to AI. After booking completion or explicit reset, state is cleared.

## Error Handling

- **Quick reply send fails**: Fall back to plain text with options listed (e.g. "Reply: 1 for Apartments, 2 for Cinema, 3 for Something Else")
- **Unknown payload**: Treat as free-text, pass to AI
- **Instagram API errors**: Logged, fallback to `send_message` with plain text options

## "Something Else?" FAQ

Placeholder for now. Sends the message above and passes to AI. Future work: dedicated FAQ buttons with programmed answers.

## Files Changed

| File | Change |
|------|--------|
| `state/user_state.py` | **New** — state model + management functions |
| `services/menu.py` | **New** — menu/button definitions |
| `services/instagram.py` | **Edit** — add `send_quick_reply()` function |
| `routes/webhook.py` | **Edit** — add state routing before AI call |
| `state/conversation.py` | **Minor edit** — add `append_system_note()` helper |

No changes to `ai/prompts.py`, `ai/groq_client.py`, `ai/tools.py`, `config.py`, or any booking logic.

## Rollout

1. Create `state/user_state.py`
2. Create `services/menu.py`
3. Add `send_buttons()` to `services/instagram.py`
4. Add `append_system_note()` to `state/conversation.py`
5. Add routing to `routes/webhook.py`
6. Deploy and test
