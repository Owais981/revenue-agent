from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON

from app.core.database import Base
from app.models.user import gen_id


class Score(Base):
    __tablename__ = "scores"

    id = Column(String, primary_key=True, default=gen_id)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False, index=True)

    fit = Column(Float, nullable=False, default=0)
    intent = Column(Float, nullable=False, default=0)
    deliverability = Column(Float, nullable=False, default=0)
    composite = Column(Float, nullable=False, default=0)

    factors = Column(JSON, nullable=False, default=list)  # [{name, value, weight, contribution, reason, category}]

    model_version = Column(String, nullable=True)
    weights_version = Column(String, nullable=True)
    degraded = Column(String, nullable=True)  # reason if computed in degraded mode

    computed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
