from app.services.scoring_engine import ScoringEngine

engine = ScoringEngine()

BASE_FEATURES = {
    "industry": "technology",
    "service": "commercial production",
    "budget": 20000,
    "min_project_value": 1000,
    "expected_margin_band": "high",
    "account_tier": "enterprise",
    "is_repeat_client": True,
    "deadline": "2026-12-01",
    "target_dates": "next month",
    "deliverables": "3 videos",
    "source": "referral",
    "contact_seniority": "executive",
    "trigger_event_recent": True,
    "engagement_score": 5,
    "crew_available": True,
    "equipment_available": True,
    "location_requires_travel": False,
    "skill_match": True,
    "pipeline_load_pct": 20,
}


def test_fit_score_rewards_strong_matches():
    result = engine.calculate_fit(BASE_FEATURES)
    assert result.score > 80
    assert all("category" not in f.to_dict() or f.category == "fit" for f in result.factors)


def test_fit_score_low_for_unknown_everything():
    result = engine.calculate_fit({})
    assert result.score < 20


def test_intent_score_high_for_complete_urgent_brief():
    result = engine.calculate_intent(BASE_FEATURES)
    assert result.score > 70


def test_intent_score_low_for_empty_brief():
    result = engine.calculate_intent({})
    assert result.score < 30


def test_deliverability_penalizes_unavailable_crew():
    available = engine.calculate_deliverability(BASE_FEATURES)
    unavailable = engine.calculate_deliverability({**BASE_FEATURES, "crew_available": False})
    assert unavailable.score < available.score


def test_composite_uses_configured_weights():
    weights = {"fit": 0.35, "intent": 0.40, "deliverability": 0.25}
    composite = engine.calculate_composite(100, 0, 0, weights)
    assert composite == 35.0


def test_every_score_returns_factors_not_just_number():
    result = engine.calculate_fit(BASE_FEATURES)
    assert len(result.factors) > 0
    for factor in result.factors:
        d = factor.to_dict()
        assert "name" in d and "contribution" in d and "reason" in d
