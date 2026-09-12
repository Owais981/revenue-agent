from app.services.action_selector import select_action
from app.models.action import ActionType

COMMON = dict(proposal_threshold=75, nurture_threshold=45, high_threshold=70, medium_threshold=45)


def test_call_now_for_high_intent_fit_with_deadline():
    decision = select_action(
        fit=85, intent=80, deliverability=70, composite=79,
        lead_features={"deadline": "2026-01-01", "service": "x", "target_dates": "y", "budget": 5000},
        hard_rule=None, **COMMON,
    )
    assert decision.action_type == ActionType.CALL_NOW


def test_request_brief_detail_when_fields_missing():
    decision = select_action(
        fit=60, intent=60, deliverability=60, composite=60,
        lead_features={"service": None, "target_dates": None, "budget": None, "deadline": None},
        hard_rule=None, **COMMON,
    )
    assert decision.action_type == ActionType.REQUEST_BRIEF_DETAIL
    assert "service" in decision.missing_fields


def test_route_to_proposal_when_composite_above_threshold_and_brief_complete():
    decision = select_action(
        fit=80, intent=50, deliverability=80, composite=76,
        lead_features={"service": "x", "target_dates": "y", "budget": 5000, "deadline": "2026-01-01"},
        hard_rule=None, **COMMON,
    )
    assert decision.action_type == ActionType.ROUTE_TO_PROPOSAL_AGENT


def test_disqualify_below_floor():
    decision = select_action(
        fit=10, intent=10, deliverability=10, composite=10,
        lead_features={}, hard_rule=None, **COMMON,
    )
    assert decision.action_type == ActionType.DISQUALIFY


def test_hard_rule_always_wins():
    decision = select_action(
        fit=95, intent=95, deliverability=95, composite=95,
        lead_features={"service": "x", "target_dates": "y", "budget": 5000, "deadline": "2026-01-01"},
        hard_rule={"action_type": "FINANCE_HOLD", "reason": "Overdue invoice"},
        **COMMON,
    )
    assert decision.action_type == ActionType.FINANCE_HOLD
    assert decision.confidence > 0.9


def test_check_capacity_when_deliverability_uncertain():
    decision = select_action(
        fit=85, intent=50, deliverability=30, composite=60,
        lead_features={"service": "x", "target_dates": "y", "budget": 5000, "deadline": None},
        hard_rule=None, **COMMON,
    )
    assert decision.action_type == ActionType.CHECK_CAPACITY


def test_action_type_is_always_from_fixed_catalogue():
    decision = select_action(
        fit=55, intent=55, deliverability=55, composite=55,
        lead_features={"service": "x", "target_dates": "y", "budget": 5000, "deadline": "2026-01-01"},
        hard_rule=None, **COMMON,
    )
    assert decision.action_type in list(ActionType)
