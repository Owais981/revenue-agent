import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SAEnum, JSON, Float

from app.core.database import Base
from app.models.user import gen_id


class LeadStatus(str, enum.Enum):
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    QUALIFIED = "QUALIFIED"
    NURTURE = "NURTURE"
    DISQUALIFIED = "DISQUALIFIED"
    FINANCE_HOLD = "FINANCE_HOLD"
    ROUTED_TO_PROPOSAL = "ROUTED_TO_PROPOSAL"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=gen_id)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=True, index=True)
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=True, index=True)

    source = Column(String, nullable=False)  # website, email, whatsapp, referral, manual, outbound
    raw_text = Column(Text, nullable=True)
    received_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # extracted / structured fields (nullable - never guessed)
    service = Column(String, nullable=True)
    deliverables = Column(String, nullable=True)
    quantity = Column(String, nullable=True)
    location = Column(String, nullable=True)
    target_dates = Column(String, nullable=True)
    budget = Column(Float, nullable=True)
    deadline = Column(String, nullable=True)

    field_confidence = Column(JSON, nullable=True, default=dict)  # {field: confidence}
    field_sources = Column(JSON, nullable=True, default=dict)  # {field: source}
    language = Column(String, nullable=True)  # en / ur / roman-ur

    status = Column(SAEnum(LeadStatus), default=LeadStatus.NEW, nullable=False, index=True)
    ai_degraded = Column(String, nullable=True)  # reason if AI processing was degraded

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
