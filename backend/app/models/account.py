from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Boolean

from app.core.database import Base
from app.models.user import gen_id


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False, index=True)
    domain = Column(String, nullable=True, index=True)
    industry = Column(String, nullable=True)
    size = Column(String, nullable=True)
    tier = Column(String, nullable=True)  # enterprise / mid / small
    credit_flag = Column(Boolean, default=False)  # True = overdue invoice / credit issue
    blacklisted = Column(Boolean, default=False)
    owner = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
