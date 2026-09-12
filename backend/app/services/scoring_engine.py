"""Deterministic scoring engine.

CRITICAL RULE: Gemini / any LLM never outputs a numeric score. This module computes
Fit, Intent, Deliverability and the Composite score from extracted features using
plain, auditable, reproducible Python arithmetic. Every score returns both the number
and the list of contributing factors (name, value, weight, contribution, reason) so a
rep can see exactly why a lead scored the way it did.
"""
from dataclasses import dataclass, field
from typing import Optional

MODEL_VERSION = "scoring-engine-v1"

# NOTE: business lookup tables (target verticals, capability set, budget bands,
# channel/seniority/tier weights) are NOT hardcoded here. They are read from
# `features` at call time, sourced from ScoringConfig (DB-backed, editable via
# /api/settings/scoring). The values below are only a last-resort default used if a
# caller forgets to pass them in (e.g. in a unit test).
_FALLBACK_TARGET_VERTICALS = {"technology", "fmcg", "retail", "fashion", "food & beverage", "telecom", "banking"}
_FALLBACK_CAPABILITY_SET = {"commercial production", "corporate video", "social media content", "tvc", "documentary", "photography"}
_FALLBACK_ENTERPRISE_MIN_BUDGET = 15000
_FALLBACK_MID_MIN_BUDGET = 5000
_FALLBACK_CHANNEL_WEIGHTS = {"referral": 20, "email": 14, "whatsapp": 14, "website": 10, "outbound": 4, "manual": 8}
_FALLBACK_SENIORITY_WEIGHTS = {"executive": 20, "senior": 15, "manager": 10, "junior": 4}
_FALLBACK_TIER_WEIGHTS = {"enterprise": 15, "mid": 10, "small": 5}


@dataclass
class ScoreFactor:
    name: str
    value: float
    weight: float
    contribution: float
    reason: str
    category: str  # fit | intent | deliverability

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value,
            "weight": self.weight,
            "contribution": self.contribution,
            "reason": self.reason,
            "category": self.category,
        }


@dataclass
class ScoreResult:
    score: float
    factors: list = field(default_factory=list)

    def to_dicts(self):
        return [f.to_dict() for f in self.factors]


class ScoringEngine:
    def calculate_fit(self, features: dict) -> ScoreResult:
        factors: list[ScoreFactor] = []
        total = 0.0

        target_verticals = set(v.lower() for v in features.get("target_verticals") or _FALLBACK_TARGET_VERTICALS)
        capability_set = set(v.lower() for v in features.get("capability_set") or _FALLBACK_CAPABILITY_SET)
        enterprise_min_budget = features.get("enterprise_min_budget", _FALLBACK_ENTERPRISE_MIN_BUDGET)
        mid_min_budget = features.get("mid_min_budget", _FALLBACK_MID_MIN_BUDGET)
        tier_weights = features.get("tier_weights") or _FALLBACK_TIER_WEIGHTS

        industry = (features.get("industry") or "").lower()
        if industry in target_verticals:
            pts = 20
            factors.append(ScoreFactor("Industry match", pts, 1.0, pts, f"'{industry}' matches a target vertical", "fit"))
        elif industry:
            pts = 8
            factors.append(ScoreFactor("Industry match", pts, 1.0, pts, f"'{industry}' is outside core target verticals", "fit"))
        else:
            pts = 0
            factors.append(ScoreFactor("Industry match", pts, 1.0, pts, "Industry unknown", "fit"))
        total += pts

        service = (features.get("service") or "").lower()
        if any(cap in service for cap in capability_set):
            pts = 20
            factors.append(ScoreFactor("Project type match", pts, 1.0, pts, "Requested service matches our capability set", "fit"))
        elif service:
            pts = 5
            factors.append(ScoreFactor("Project type match", pts, 1.0, pts, "Requested service only partially matches capabilities", "fit"))
        else:
            pts = 0
            factors.append(ScoreFactor("Project type match", pts, 1.0, pts, "Service requested is unknown", "fit"))
        total += pts

        budget = features.get("budget")
        if budget is None:
            pts = 0
            factors.append(ScoreFactor("Budget band", pts, 1.0, pts, "No budget stated", "fit"))
        elif budget >= enterprise_min_budget:
            pts = 20
            factors.append(ScoreFactor("Budget band", pts, 1.0, pts, "Enterprise-scale budget", "fit"))
        elif budget >= mid_min_budget:
            pts = 14
            factors.append(ScoreFactor("Budget band", pts, 1.0, pts, "Mid-size budget", "fit"))
        elif budget >= features.get("min_project_value", 1000):
            pts = 8
            factors.append(ScoreFactor("Budget band", pts, 1.0, pts, "Small but viable budget", "fit"))
        else:
            pts = 0
            factors.append(ScoreFactor("Budget band", pts, 1.0, pts, "Below minimum viable project size", "fit"))
        total += pts

        margin_band = features.get("expected_margin_band", "unknown")
        margin_points = {"high": 15, "medium": 10, "low": 4, "unknown": 5}
        pts = margin_points.get(margin_band, 5)
        factors.append(ScoreFactor("Expected margin band", pts, 1.0, pts, f"Comparable past projects: {margin_band} margin", "fit"))
        total += pts

        tier = (features.get("account_tier") or "").lower()
        pts = tier_weights.get(tier, 5)
        factors.append(ScoreFactor("Account tier", pts, 1.0, pts, f"Account tier: {tier or 'unknown'}", "fit"))
        total += pts

        if features.get("is_repeat_client"):
            pts = 10
            factors.append(ScoreFactor("Repeat client bonus", pts, 1.0, pts, "Existing client with prior history", "fit"))
            total += pts

        return ScoreResult(score=min(total, 100), factors=factors)

    def calculate_intent(self, features: dict) -> ScoreResult:
        factors: list[ScoreFactor] = []
        total = 0.0

        required_fields = ["service", "deliverables", "target_dates", "budget"]
        present = sum(1 for f in required_fields if features.get(f) not in (None, ""))
        pts = round((present / len(required_fields)) * 25)
        factors.append(ScoreFactor("Brief completeness", pts, 1.0, pts, f"{present}/{len(required_fields)} key brief fields provided", "intent"))
        total += pts

        deadline = features.get("deadline")
        if deadline:
            pts = 20
            factors.append(ScoreFactor("Urgency", pts, 1.0, pts, "Specific deadline provided", "intent"))
        else:
            pts = 5
            factors.append(ScoreFactor("Urgency", pts, 1.0, pts, "No specific deadline stated", "intent"))
        total += pts

        channel_weights = features.get("channel_weights") or _FALLBACK_CHANNEL_WEIGHTS
        source = (features.get("source") or "").lower()
        pts = channel_weights.get(source, 8)
        factors.append(ScoreFactor("Channel", pts, 1.0, pts, f"Lead source: {source or 'unknown'}", "intent"))
        total += pts

        seniority_weights = features.get("seniority_weights") or _FALLBACK_SENIORITY_WEIGHTS
        seniority = (features.get("contact_seniority") or "").lower()
        pts = seniority_weights.get(seniority, 6)
        factors.append(ScoreFactor("Contact seniority", pts, 1.0, pts, f"Contact seniority: {seniority or 'unknown'}", "intent"))
        total += pts

        if features.get("trigger_event_recent"):
            pts = 10
            factors.append(ScoreFactor("Trigger event recency", pts, 1.0, pts, "Recent trigger event detected", "intent"))
            total += pts

        engagement = features.get("engagement_score", 0)
        pts = min(engagement, 5)
        if pts:
            factors.append(ScoreFactor("Engagement history", pts, 1.0, pts, "Prior engagement on record", "intent"))
            total += pts

        return ScoreResult(score=min(total, 100), factors=factors)

    def calculate_deliverability(self, features: dict) -> ScoreResult:
        factors: list[ScoreFactor] = []
        total = 100.0

        if not features.get("crew_available", True):
            total -= 30
            factors.append(ScoreFactor("Crew availability", -30, 1.0, -30, "Crew not confirmed available for requested window", "deliverability"))
        else:
            factors.append(ScoreFactor("Crew availability", 0, 1.0, 0, "Crew available (DEMO / MANUAL CAPACITY DATA)", "deliverability"))

        if not features.get("equipment_available", True):
            total -= 20
            factors.append(ScoreFactor("Equipment availability", -20, 1.0, -20, "Required equipment not confirmed available", "deliverability"))

        if features.get("location_requires_travel"):
            total -= 8
            factors.append(ScoreFactor("Location feasibility", -8, 1.0, -8, "Requested location requires additional travel", "deliverability"))
        else:
            factors.append(ScoreFactor("Location feasibility", 0, 1.0, 0, "Location is local / low travel cost", "deliverability"))

        if not features.get("skill_match", True):
            total -= 15
            factors.append(ScoreFactor("Skill match", -15, 1.0, -15, "Requested output does not closely match our skill set", "deliverability"))

        pipeline_load = features.get("pipeline_load_pct", 0)
        if pipeline_load >= 85:
            total -= 20
            factors.append(ScoreFactor("Pipeline load", -20, 1.0, -20, f"Pipeline load high ({pipeline_load}%) for this period", "deliverability"))
        elif pipeline_load >= 60:
            total -= 8
            factors.append(ScoreFactor("Pipeline load", -8, 1.0, -8, f"Pipeline load moderate ({pipeline_load}%) for this period", "deliverability"))

        return ScoreResult(score=max(min(total, 100), 0), factors=factors)

    def calculate_composite(self, fit: float, intent: float, deliverability: float, weights: dict) -> float:
        return round(
            fit * weights["fit"] + intent * weights["intent"] + deliverability * weights["deliverability"],
            2,
        )

    def apply_hard_rules(self, lead_features: dict) -> Optional[dict]:
        """Hard rules override the composite score entirely. Returns a dict with
        {action_type, reason} if a hard rule fires, else None."""
        if lead_features.get("account_blacklisted"):
            return {"action_type": "DISQUALIFY", "reason": "Account is blacklisted / conflict of interest"}

        if lead_features.get("overdue_invoice"):
            return {"action_type": "FINANCE_HOLD", "reason": "Account has an outstanding overdue invoice"}

        budget = lead_features.get("budget")
        min_value = lead_features.get("min_project_value", 1000)
        if budget is not None and budget < min_value:
            return {"action_type": "NURTURE", "reason": f"Stated budget ({budget}) is below minimum viable project size ({min_value})"}

        if lead_features.get("requested_dates_unavailable"):
            return {"action_type": "CHECK_CAPACITY", "reason": "Requested dates are fully unavailable - must confirm before any promise is made"}

        return None
