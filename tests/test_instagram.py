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
