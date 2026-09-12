from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey

from app.core.database import Base
from app.models.user import gen_id


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String, primary_key=True, default=gen_id)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=True, index=True)
    name = Column(String, nullable=True)
    role = Column(String, nullable=True)
    seniority = Column(String, nullable=True)  # junior / manager / senior / executive
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True, index=True)
    channel_pref = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
