import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Enum as SAEnum

from app.core.database import Base


class UserRole(str, enum.Enum):
    SALES_REP = "SALES_REP"
    HEAD_OF_SALES = "HEAD_OF_SALES"
    PRODUCER = "PRODUCER"
    FINANCE = "FINANCE"
    ADMIN = "ADMIN"


def gen_id():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.SALES_REP, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
