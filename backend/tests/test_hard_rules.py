from app.services.scoring_engine import ScoringEngine

engine = ScoringEngine()


def test_finance_hold_on_overdue_invoice():
    rule = engine.apply_hard_rules({"overdue_invoice": True})
    assert rule is not None
    assert rule["action_type"] == "FINANCE_HOLD"


def test_nurture_below_minimum_value():
    rule = engine.apply_hard_rules({"budget": 500, "min_project_value": 1000})
    assert rule is not None
    assert rule["action_type"] == "NURTURE"


def test_disqualify_blacklisted_account():
    rule = engine.apply_hard_rules({"account_blacklisted": True})
    assert rule is not None
    assert rule["action_type"] == "DISQUALIFY"


def test_check_capacity_when_dates_unavailable():
    rule = engine.apply_hard_rules({"requested_dates_unavailable": True})
    assert rule is not None
    assert rule["action_type"] == "CHECK_CAPACITY"


def test_no_hard_rule_for_healthy_lead():
    rule = engine.apply_hard_rules({"budget": 20000, "min_project_value": 1000})
    assert rule is None


def test_blacklist_takes_priority_over_other_rules():
    rule = engine.apply_hard_rules({"account_blacklisted": True, "overdue_invoice": True})
    assert rule["action_type"] == "DISQUALIFY"
