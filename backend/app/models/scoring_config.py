from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Float, JSON

from app.core.database import Base


def _default_target_verticals():
    return ["technology", "fmcg", "retail", "fashion", "food & beverage", "telecom", "banking"]


def _default_capability_set():
    return ["commercial production", "corporate video", "social media content", "tvc", "documentary", "photography"]


def _default_channel_weights():
    return {"referral": 20, "email": 14, "whatsapp": 14, "website": 10, "outbound": 4, "manual": 8}


def _default_seniority_weights():
    return {"executive": 20, "senior": 15, "manager": 10, "junior": 4}


def _default_tier_weights():
    return {"enterprise": 15, "mid": 10, "small": 5}


class ScoringConfig(Base):
    """Singleton row (id='default') holding every business-tunable weight, threshold
    and lookup table the scoring engine uses. Nothing here is hardcoded in Python -
    all of it is editable at runtime via /api/settings/scoring without a code deploy."""

    __tablename__ = "scoring_config"

    id = Column(String, primary_key=True, default="default")
    fit_weight = Column(Float, nullable=False, default=0.35)
    intent_weight = Column(Float, nullable=False, default=0.40)
    deliverability_weight = Column(Float, nullable=False, default=0.25)

    proposal_threshold = Column(Float, nullable=False, default=75)
    nurture_threshold = Column(Float, nullable=False, default=45)
    min_project_value = Column(Float, nullable=False, default=1000)
    confidence_threshold = Column(Float, nullable=False, default=0.65)
    high_score_threshold = Column(Float, nullable=False, default=70)
    medium_score_threshold = Column(Float, nullable=False, default=45)

    enterprise_min_budget = Column(Float, nullable=False, default=15000)
    mid_min_budget = Column(Float, nullable=False, default=5000)

    target_verticals = Column(JSON, nullable=False, default=_default_target_verticals)
    capability_set = Column(JSON, nullable=False, default=_default_capability_set)
    channel_weights = Column(JSON, nullable=False, default=_default_channel_weights)
    seniority_weights = Column(JSON, nullable=False, default=_default_seniority_weights)
    tier_weights = Column(JSON, nullable=False, default=_default_tier_weights)

    version = Column(String, nullable=False, default="v1")
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
