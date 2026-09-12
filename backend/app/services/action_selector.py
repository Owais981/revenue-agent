"""Selects exactly one action from the fixed catalogue (app.models.action.ActionType).
Selection is rule-based and deterministic; an LLM may only be used later to phrase the
`reason` more naturally or generate a draft, never to invent a new action name."""
from dataclasses import dataclass, field
from typing import Optional

from app.models.action import ActionType

# Last-resort defaults only, used if a caller omits them (e.g. a unit test). In the
# live pipeline these come from ScoringConfig.high_score_threshold /
# medium_score_threshold, editable at /api/settings/scoring without a code deploy.
_FALLBACK_HIGH = 70
_FALLBACK_MEDIUM = 45


@dataclass
class ActionDecision:
    action_type: ActionType
    reason: str
    evidence: list = field(default_factory=list)
    confidence: float = 0.7
    missing_fields: list = field(default_factory=list)


REQUIRED_BRIEF_FIELDS = ["service", "target_dates", "budget", "deadline"]


def select_action(
    *,
    fit: float,
    intent: float,
    deliverability: float,
    composite: float,
    lead_features: dict,
    hard_rule: Optional[dict],
    proposal_threshold: float,
    nurture_threshold: float,
    high_threshold: float = _FALLBACK_HIGH,
    medium_threshold: float = _FALLBACK_MEDIUM,
) -> ActionDecision:
    HIGH = high_threshold
    MEDIUM = medium_threshold
    if hard_rule:
        return ActionDecision(
            action_type=ActionType(hard_rule["action_type"]),
            reason=hard_rule["reason"],
            evidence=[hard_rule["reason"]],
            confidence=0.99,
        )

    missing = [f for f in REQUIRED_BRIEF_FIELDS if not lead_features.get(f)]
    has_deadline = bool(lead_features.get("deadline"))
    brief_complete = len(missing) == 0

    if composite < nurture_threshold:
        return ActionDecision(
            action_type=ActionType.DISQUALIFY,
            reason=f"Composite score ({composite}) is below the qualification floor ({nurture_threshold})",
            evidence=[f"Composite {composite} < floor {nurture_threshold}"],
            confidence=0.85,
        )

    if intent >= HIGH and fit >= HIGH and has_deadline:
        return ActionDecision(
            action_type=ActionType.CALL_NOW,
            reason="High intent and strong fit with a time-sensitive deadline",
            evidence=[f"Intent {intent}", f"Fit {fit}", "Deadline provided"],
            confidence=0.9,
        )

    # Whether we can even deliver is checked before asking for more brief detail -
    # no point collecting a fuller brief if crew/kit/location can't be confirmed.
    if fit >= HIGH and deliverability < MEDIUM:
        return ActionDecision(
            action_type=ActionType.CHECK_CAPACITY,
            reason="Fit is strong but deliverability (crew/kit/location) needs confirmation",
            evidence=[f"Fit {fit}", f"Deliverability {deliverability}"],
            confidence=0.8,
        )

    if intent >= MEDIUM and not brief_complete:
        return ActionDecision(
            action_type=ActionType.REQUEST_BRIEF_DETAIL,
            reason="Intent is meaningful but the brief is missing key details",
            evidence=[f"Intent {intent}"],
            confidence=0.85,
            missing_fields=missing,
        )

    if composite >= proposal_threshold and brief_complete:
        return ActionDecision(
            action_type=ActionType.ROUTE_TO_PROPOSAL_AGENT,
            reason=f"Composite score ({composite}) is above the proposal threshold and the brief is complete",
            evidence=[f"Composite {composite} >= {proposal_threshold}", "Brief complete"],
            confidence=0.9,
        )

    if fit >= HIGH and lead_features.get("credibility_gap"):
        return ActionDecision(
            action_type=ActionType.SEND_CASE_STUDY,
            reason="Fit is good but there is a credibility gap - a comparable case study should help",
            evidence=[f"Fit {fit}"],
            confidence=0.75,
        )

    if fit >= MEDIUM:
        return ActionDecision(
            action_type=ActionType.SEND_INTRO_EMAIL,
            reason="Reasonable fit but the contact is cold or unresponsive",
            evidence=[f"Fit {fit}", f"Intent {intent}"],
            confidence=0.65,
        )

    return ActionDecision(
        action_type=ActionType.NURTURE,
        reason="Real opportunity but not currently ready to progress",
        evidence=[f"Composite {composite}"],
        confidence=0.6,
    )
