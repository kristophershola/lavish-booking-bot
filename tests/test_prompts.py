from ai.prompts import build_full_system_prompt

PROMPT = build_full_system_prompt()


def test_business_info_present():
    assert "5 M.M Alkali Street" in PROMPT
    assert "Gwarimpa" in PROMPT
    assert "lavishliving.ng" in PROMPT


def test_payment_details_present():
    assert "1219550382" in PROMPT
    assert "Zenith" in PROMPT
    assert "Moniepoint" in PROMPT


def test_apartment_pricing_present():
    assert "90,000" in PROMPT
    assert "100,000" in PROMPT
    assert "200,000" in PROMPT
    assert "2,100,000" in PROMPT or "2.1m" in PROMPT.lower()


def test_cinema_packages_present():
    assert "Crunch and Drink" in PROMPT
    assert "Slice and Wine" in PROMPT
    assert "Executive" in PROMPT
    assert "BYOF" in PROMPT


def test_house_rules_present():
    assert "Quiet hours" in PROMPT or "quiet hours" in PROMPT
    assert "no smoking" in PROMPT.lower() or "No smoking" in PROMPT
    assert "no pets" in PROMPT.lower() or "No pets" in PROMPT


def test_cinema_rules_present():
    assert "Hall 1" in PROMPT
    assert "Hall 2" in PROMPT
    assert "max 4" in PROMPT.lower() or "maximum of 4" in PROMPT.lower()


def test_date_context_present():
    assert "DATE CONTEXT" in PROMPT


def test_payment_flow_instructions():
    assert "receipt" in PROMPT.lower()
    assert "screenshot" in PROMPT.lower()


def test_reschedule_fee_present():
    assert "15,000" in PROMPT or "15000" in PROMPT or "15k" in PROMPT


def test_monthly_rate_present():
    assert "2,100,000" in PROMPT or "2.1m" in PROMPT.lower() or "2.1M" in PROMPT
