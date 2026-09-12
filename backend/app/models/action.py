import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON, Text, Enum as SAEnum

from app.core.database import Base
from app.models.user import gen_id


class ActionType(str, enum.Enum):
    CALL_NOW = "CALL_NOW"
    SEND_INTRO_EMAIL = "SEND_INTRO_EMAIL"
    SEND_CASE_STUDY = "SEND_CASE_STUDY"
    REQUEST_BRIEF_DETAIL = "REQUEST_BRIEF_DETAIL"
    ROUTE_TO_PROPOSAL_AGENT = "ROUTE_TO_PROPOSAL_AGENT"
    CHECK_CAPACITY = "CHECK_CAPACITY"
    FINANCE_HOLD = "FINANCE_HOLD"
    NURTURE = "NURTURE"
    DISQUALIFY = "DISQUALIFY"


class ActionStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SENT = "SENT"


class Action(Base):
    __tablename__ = "actions"

    id = Column(String, primary_key=True, default=gen_id)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False, index=True)
    action_type = Column(SAEnum(ActionType), nullable=False)
    reason = Column(Text, nullable=True)
    evidence = Column(JSON, nullable=False, default=list)
    confidence = Column(Float, nullable=True)
    draft_artifact = Column(Text, nullable=True)
    status = Column(SAEnum(ActionStatus), default=ActionStatus.PENDING, nullable=False)
    actor = Column(String, nullable=True)  # user id who approved/rejected, or "system"

    # override tracking
    is_override = Column(String, nullable=True)  # original action_type if overridden
    override_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
