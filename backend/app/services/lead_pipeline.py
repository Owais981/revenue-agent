"""Orchestrates the full Revenue Agent flow described in the requirements:

intake -> normalise/extract -> dedupe -> research -> feature extraction ->
deterministic scoring -> hard rules -> next-best action -> draft -> (human approval).

This module ties the individual services together; it contains no scoring math and no
raw LLM calls itself.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.account import Account
from app.models.contact import Contact
from app.models.lead import Lead, LeadStatus
from app.models.score import Score
from app.models.action import Action, ActionStatus
from app.models.scoring_config import ScoringConfig
from app.schemas.extraction import LeadExtraction
from app.services import audit
from app.services.adapters import MockPlanningAdapter, MockFinanceAdapter
from app.services.deduplication import find_matching_account, find_matching_contact
from app.services.draft_generator import generate_draft
from app.services.lead_extraction import extract_lead_fields
from app.services.research_service import build_research_pack
from app.services.scoring_engine import ScoringEngine, MODEL_VERSION

engine = ScoringEngine()


def get_scoring_config(db: Session) -> ScoringConfig:
    config = db.query(ScoringConfig).filter(ScoringConfig.id == "default").first()
    if not config:
        config = ScoringConfig(
            id="default",
            fit_weight=settings.fit_weight,
            intent_weight=settings.intent_weight,
            deliverability_weight=settings.deliverability_weight,
            proposal_threshold=settings.proposal_threshold,
            nurture_threshold=settings.nurture_threshold,
            min_project_value=settings.min_project_value,
            confidence_threshold=settings.confidence_threshold,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def _to_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def get_or_create_account(db: Session, company_name: Optional[str], email: Optional[str], phone: Optional[str]) -> Optional[Account]:
    if not company_name and not email and not phone:
        return None
    account = find_matching_account(db, company_name=company_name, email=email, phone=phone)
    if account:
        return account
    if company_name:
        domain = email.split("@")[-1].lower() if email and "@" in email else None
        account = Account(name=company_name, domain=domain)
        db.add(account)
        db.commit()
        db.refresh(account)
        return account
    return None


def get_or_create_contact(
    db: Session, account_id: Optional[str], name: Optional[str], role: Optional[str], email: Optional[str], phone: Optional[str]
) -> Optional[Contact]:
    if not name and not email and not phone:
        return None
    contact = find_matching_contact(db, account_id, email, phone, name)
    if contact:
        return contact
    contact = Contact(account_id=account_id, name=name, role=role, email=email, phone=phone)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def create_lead_from_intake(db: Session, source: str, raw_text: str, contact_email: Optional[str] = None, contact_phone: Optional[str] = None) -> Lead:
    extraction, degraded, degraded_reason = extract_lead_fields(raw_text)

    audit.log_event(
        db,
        "LEAD_EXTRACTED",
        input_data={"raw_text": raw_text[:500]},
        output_data=extraction.model_dump(),
        model_version=settings.gemini_model if not degraded else "rule-based-fallback",
    )

    email = extraction.contact_email.value or contact_email
    phone = extraction.contact_phone.value or contact_phone

    account = get_or_create_account(db, extraction.company.value, email, phone)
    contact = get_or_create_contact(
        db, account.id if account else None, extraction.contact_name.value, extraction.role.value, email, phone
    )

    field_confidence = {}
    field_sources = {}
    for name, field_obj in extraction.model_dump().items():
        if isinstance(field_obj, dict) and "confidence" in field_obj:
            field_confidence[name] = field_obj["confidence"]
            field_sources[name] = field_obj["source"]

    lead = Lead(
        account_id=account.id if account else None,
        contact_id=contact.id if contact else None,
        source=source,
        raw_text=raw_text,
        service=extraction.service_requested.value,
        deliverables=extraction.deliverables.value,
        quantity=extraction.quantity.value,
        location=extraction.shoot_location.value,
        target_dates=extraction.target_dates.value,
        budget=_to_float(extraction.budget.value),
        deadline=extraction.deadline.value,
        field_confidence=field_confidence,
        field_sources=field_sources,
        language=extraction.language,
        status=LeadStatus.NEW,
        ai_degraded=degraded_reason,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    audit.log_event(db, "LEAD_CREATED", lead_id=lead.id, output_data={"account_id": lead.account_id})
    return lead


async def analyze_lead(db: Session, lead: Lead) -> dict:
    """Runs research -> scoring -> hard rules -> next-best action -> draft, and
    persists Score + Action records. Returns the full result payload."""
    lead.status = LeadStatus.PROCESSING
    db.commit()

    account = db.query(Account).filter(Account.id == lead.account_id).first() if lead.account_id else None
    contact = db.query(Contact).filter(Contact.id == lead.contact_id).first() if lead.contact_id else None

    research_pack = await build_research_pack(db, lead, account)
    audit.log_event(db, "RESEARCH_GENERATED", lead_id=lead.id, output_data={"claims": len(research_pack.claims)})

    planning = MockPlanningAdapter()
    finance = MockFinanceAdapter()
    capacity = await planning.check_capacity(lead.location, lead.target_dates)
    credit_status = await finance.get_credit_status(account.id if account else "")

    config = get_scoring_config(db)
    weights = {
        "fit": config.fit_weight,
        "intent": config.intent_weight,
        "deliverability": config.deliverability_weight,
    }

    verified_claims = [c for c in research_pack.claims if c.get("verified")]
    is_repeat_client = account is not None and any("history" in c["text"].lower() or "past" in c["text"].lower() for c in verified_claims)

    features = {
        "industry": account.industry if account else None,
        "service": lead.service,
        "budget": lead.budget,
        "min_project_value": config.min_project_value,
        "target_verticals": config.target_verticals,
        "capability_set": config.capability_set,
        "enterprise_min_budget": config.enterprise_min_budget,
        "mid_min_budget": config.mid_min_budget,
        "channel_weights": config.channel_weights,
        "seniority_weights": config.seniority_weights,
        "tier_weights": config.tier_weights,
        "expected_margin_band": credit_status.get("expected_margin_band", "unknown"),
        "account_tier": account.tier if account else None,
        "is_repeat_client": is_repeat_client,
        "target_dates": lead.target_dates,
        "deliverables": lead.deliverables,
        "deadline": lead.deadline,
        "source": lead.source,
        "contact_seniority": contact.seniority if contact else None,
        "trigger_event_recent": False,
        "engagement_score": 0,
        "crew_available": capacity.get("crew_available", True),
        "equipment_available": capacity.get("equipment_available", True),
        "location_requires_travel": bool(lead.location) and account is None,
        "skill_match": True,
        "pipeline_load_pct": capacity.get("pipeline_load_pct", 0),
        "account_blacklisted": account.blacklisted if account else False,
        "overdue_invoice": (account.credit_flag if account else False) or credit_status.get("overdue", False),
        "requested_dates_unavailable": not capacity.get("crew_available", True) and not capacity.get("equipment_available", True),
        "credibility_gap": account is None,
    }

    degraded_reason = lead.ai_degraded

    fit_result = engine.calculate_fit(features)
    intent_result = engine.calculate_intent(features)
    deliverability_result = engine.calculate_deliverability(features)
    composite = engine.calculate_composite(fit_result.score, intent_result.score, deliverability_result.score, weights)
    hard_rule = engine.apply_hard_rules(features)

    score = Score(
        lead_id=lead.id,
        fit=fit_result.score,
        intent=intent_result.score,
        deliverability=deliverability_result.score,
        composite=composite,
        factors=fit_result.to_dicts() + intent_result.to_dicts() + deliverability_result.to_dicts(),
        model_version=MODEL_VERSION,
        weights_version=config.version,
        degraded=degraded_reason,
    )
    db.add(score)
    db.commit()
    db.refresh(score)

    audit.log_event(
        db,
        "SCORE_COMPUTED",
        lead_id=lead.id,
        output_data={"fit": fit_result.score, "intent": intent_result.score, "deliverability": deliverability_result.score, "composite": composite},
        model_version=MODEL_VERSION,
        weights_version=config.version,
    )

    from app.services.action_selector import select_action

    decision = select_action(
        fit=fit_result.score,
        intent=intent_result.score,
        deliverability=deliverability_result.score,
        composite=composite,
        lead_features=features,
        hard_rule=hard_rule,
        proposal_threshold=config.proposal_threshold,
        nurture_threshold=config.nurture_threshold,
        high_threshold=config.high_score_threshold,
        medium_threshold=config.medium_score_threshold,
    )

    lead_context = {
        "company": account.name if account else None,
        "service": lead.service,
        "industry": account.industry if account else None,
    }
    draft = generate_draft(decision.action_type, lead_context, lead.raw_text or "", decision.missing_fields)
    if decision.missing_fields and not draft:
        draft = "Missing:\n" + "\n".join(f"- {f}" for f in decision.missing_fields)

    action = Action(
        lead_id=lead.id,
        action_type=decision.action_type,
        reason=decision.reason,
        evidence=decision.evidence,
        confidence=decision.confidence,
        draft_artifact=draft or None,
        status=ActionStatus.PENDING,
        actor="system",
    )
    db.add(action)

    status_map = {
        "DISQUALIFY": LeadStatus.DISQUALIFIED,
        "NURTURE": LeadStatus.NURTURE,
        "FINANCE_HOLD": LeadStatus.FINANCE_HOLD,
        "ROUTE_TO_PROPOSAL_AGENT": LeadStatus.ROUTED_TO_PROPOSAL,
    }
    lead.status = status_map.get(decision.action_type.value, LeadStatus.QUALIFIED)
    db.commit()
    db.refresh(action)
    db.refresh(lead)

    audit.log_event(
        db,
        "ACTION_SELECTED",
        lead_id=lead.id,
        output_data={"action_type": decision.action_type.value, "reason": decision.reason},
    )

    return {
        "lead": lead,
        "research_pack": research_pack,
        "score": score,
        "action": action,
    }
