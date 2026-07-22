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
