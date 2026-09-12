from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON

from app.core.database import Base
from app.models.user import gen_id


class ResearchPack(Base):
    __tablename__ = "research_packs"

    id = Column(String, primary_key=True, default=gen_id)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False, index=True)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=True, index=True)
    claims = Column(JSON, nullable=False, default=list)  # [{text, source_url, verified, fetched_at}]
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ResearchCache(Base):
    """Cache of enrichment results per account, keyed by kind (firmographics/news)."""

    __tablename__ = "research_cache"

    id = Column(String, primary_key=True, default=gen_id)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False, index=True)
    kind = Column(String, nullable=False)  # firmographics | news
    payload = Column(JSON, nullable=False, default=dict)
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
