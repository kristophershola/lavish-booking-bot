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
