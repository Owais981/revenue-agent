"""Builds a cited research pack for a lead's account.

Cite-or-omit rule: every claim either carries a source_url / internal record id and is
marked verified=True, or it is marked verified=False ("unverified") and MUST be
excluded from scoring (enforced in scoring_engine.py, which only reads verified claims).

Caching: firmographic claims are cached per-account for 30 days, news for 3 days, to
control enrichment cost, per FR-2.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.lead import Lead
from app.models.research import ResearchPack, ResearchCache
from app.services.adapters import MockKnowledgeAdapter

FIRMOGRAPHICS_TTL = timedelta(days=30)
NEWS_TTL = timedelta(days=3)


def _cache_get(db: Session, account_id: str, kind: str, ttl: timedelta) -> Optional[dict]:
    entry = (
        db.query(ResearchCache)
        .filter(ResearchCache.account_id == account_id, ResearchCache.kind == kind)
        .order_by(ResearchCache.fetched_at.desc())
        .first()
    )
    if entry and entry.fetched_at.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc) - ttl:
        return entry.payload
    return None


def _cache_set(db: Session, account_id: str, kind: str, payload: dict):
    entry = ResearchCache(account_id=account_id, kind=kind, payload=payload)
    db.add(entry)
    db.commit()


def _claim(text: str, source_url: Optional[str] = None, internal_record_id: Optional[str] = None) -> dict:
    verified = bool(source_url or internal_record_id)
    return {
        "text": text,
        "source_url": source_url,
        "internal_record_id": internal_record_id,
        "verified": verified,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


async def build_research_pack(db: Session, lead: Lead, account: Optional[Account]) -> ResearchPack:
    claims: list[dict] = []

    if account:
        firmo = _cache_get(db, account.id, "firmographics", FIRMOGRAPHICS_TTL)
        if firmo is None:
            firmo = {
                "industry": account.industry,
                "size": account.size,
                "tier": account.tier,
            }
            _cache_set(db, account.id, "firmographics", firmo)

        if account.industry:
            claims.append(_claim(f"Industry on file: {account.industry}", internal_record_id=f"account:{account.id}"))
        if account.size:
            claims.append(_claim(f"Company size on file: {account.size}", internal_record_id=f"account:{account.id}"))
        if account.tier:
            claims.append(_claim(f"Account tier: {account.tier}", internal_record_id=f"account:{account.id}"))
        if account.credit_flag:
            claims.append(
                _claim("Outstanding overdue invoice on file", internal_record_id=f"account:{account.id}")
            )
        else:
            claims.append(_claim("No outstanding overdue invoices on file", internal_record_id=f"account:{account.id}"))
    else:
        claims.append(_claim("No existing account record - new company, no internal history available."))

    knowledge = MockKnowledgeAdapter()
    case_study = await knowledge.find_similar_case_study(lead.service, account.industry if account else None)
    if case_study:
        claims.append(
            _claim(
                f"Similar past work found: {case_study['title']}",
                internal_record_id=case_study["internal_record_id"],
            )
        )

    # Anything the model or a scraper might add without a source is intentionally
    # left unverified so it cannot influence scoring, e.g. speculative trigger events.
    if lead.raw_text and len(lead.raw_text) > 0:
        claims.append(_claim("Unconfirmed: no external web/news enrichment configured for this lead yet."))

    pack = ResearchPack(lead_id=lead.id, account_id=account.id if account else None, claims=claims)
    db.add(pack)
    db.commit()
    db.refresh(pack)
    return pack
