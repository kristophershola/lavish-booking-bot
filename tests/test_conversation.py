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
