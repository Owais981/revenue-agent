from app.services.lead_extraction import rule_based_extract, detect_language


def test_detects_english():
    assert detect_language("We need a commercial shoot next month") == "en"


def test_detects_roman_urdu():
    assert detect_language("humein aik commercial shoot karwana hai Lahore mein") == "roman-ur"


def test_detects_urdu_script():
    assert detect_language("ہمیں ایک اشتہار بنانا ہے") == "ur"


def test_rule_based_extract_never_guesses_missing_fields():
    extraction = rule_based_extract("Hello, just saying hi with no details at all.")
    assert extraction.company.value is None
    assert extraction.company.confidence == 0.0
    assert extraction.budget.value is None
    assert extraction.deadline.value is None


def test_rule_based_extract_finds_email_and_budget():
    text = "Please reach me at jane@example.com. Budget is Rs. 15,000 for this project."
    extraction = rule_based_extract(text)
    assert extraction.contact_email.value == "jane@example.com"
    assert extraction.budget.value == "15000"
    assert extraction.contact_email.confidence > 0
    # fields with no textual evidence must remain null, not guessed
    assert extraction.deadline.value is None
    assert extraction.company.value is None


def test_rule_based_extract_missing_budget_stays_null():
    extraction = rule_based_extract("We'd like a corporate video, no budget mentioned yet.")
    assert extraction.budget.value is None
    assert extraction.budget.confidence == 0.0
