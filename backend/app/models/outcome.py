from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Text

from app.core.database import Base
from app.models.user import gen_id


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(String, primary_key=True, default=gen_id)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False, index=True)
    stage = Column(String, nullable=False)  # contacted / qualified / proposal_sent / won / lost
    won = Column(Boolean, nullable=True)
    value = Column(Float, nullable=True)
    margin = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_id)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=True, index=True)
    event_type = Column(String, nullable=False, index=True)
    input = Column(String, nullable=True)
    output = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    weights_version = Column(String, nullable=True)
    actor = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
