from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.lead import Lead, LeadStatus
from app.models.score import Score
from app.models.action import Action, ActionStatus, ActionType
from app.models.research import ResearchPack
from app.models.outcome import Outcome
from app.models.user import User
from app.schemas.lead import LeadIntakeRequest, LeadManualCreate, LeadUpdate, LeadOut
from app.schemas.score import ScoreOut, ResearchPackOut
from app.schemas.action import ActionOut, ActionOverrideRequest, ActionEditDraftRequest, OutcomeIn, OutcomeOut
from app.api.deps import get_current_user
from app.services import audit
from app.services.lead_pipeline import create_lead_from_intake, analyze_lead

router = APIRouter(prefix="/api/leads", tags=["leads"])


def _error(message: str, code: str, status_code: int = 400):
    raise HTTPException(status_code=status_code, detail={"success": False, "message": message, "error_code": code})


@router.post("/intake", status_code=status.HTTP_201_CREATED)
async def intake_lead(payload: LeadIntakeRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not payload.raw_text or not payload.raw_text.strip():
        _error("raw_text is required", "MISSING_RAW_TEXT")
    try:
        lead = create_lead_from_intake(
            db, payload.source, payload.raw_text, payload.contact_email, payload.contact_phone
        )
        result = await analyze_lead(db, lead)
    except Exception as exc:
        _error(f"Unable to analyze lead: {exc}", "AI_SERVICE_ERROR", status.HTTP_502_BAD_GATEWAY)
    return {
        "lead": LeadOut.model_validate(result["lead"]),
        "research_pack": ResearchPackOut.model_validate(result["research_pack"]),
        "score": ScoreOut.model_validate(result["score"]),
        "action": ActionOut.model_validate(result["action"]),
    }


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LeadOut)
def create_manual_lead(payload: LeadManualCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.services.lead_pipeline import get_or_create_account, get_or_create_contact

    account = get_or_create_account(db, payload.company, payload.email, payload.phone)
    contact = get_or_create_contact(db, account.id if account else None, payload.contact_name, payload.role, payload.email, payload.phone)

    lead = Lead(
        account_id=account.id if account else None,
        contact_id=contact.id if contact else None,
        source=payload.source,
        raw_text=payload.raw_text,
        service=payload.service,
        deliverables=payload.deliverables,
        location=payload.location,
        target_dates=payload.target_dates,
        budget=payload.budget,
        deadline=payload.deadline,
        field_confidence={k: 1.0 for k in ["service", "deliverables", "location", "target_dates", "budget", "deadline"] if getattr(payload, k, None)},
        field_sources={k: "manual_entry" for k in ["service", "deliverables", "location", "target_dates", "budget", "deadline"] if getattr(payload, k, None)},
        language="en",
        status=LeadStatus.NEW,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    audit.log_event(db, "LEAD_CREATED", lead_id=lead.id, actor=user.id, output_data={"source": "manual"})
    return lead


@router.get("")
def list_leads(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status_filter: Optional[LeadStatus] = Query(None, alias="status"),
    source: Optional[str] = None,
    sort: str = Query("composite_desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(Lead)
    if status_filter:
        query = query.filter(Lead.status == status_filter)
    if source:
        query = query.filter(Lead.source == source)

    total = query.count()
    leads = query.offset((page - 1) * page_size).limit(page_size * 5).all()  # overfetch for score sort

    latest_scores = {}
    for lead in leads:
        score = db.query(Score).filter(Score.lead_id == lead.id).order_by(Score.computed_at.desc()).first()
        latest_scores[lead.id] = score

    def sort_key(lead: Lead):
        score = latest_scores.get(lead.id)
        composite = score.composite if score else -1
        fit = score.fit if score else -1
        intent = score.intent if score else -1
        if sort == "composite_desc":
            return -composite
        if sort == "fit_desc":
            return -fit
        if sort == "intent_desc":
            return -intent
        if sort == "newest":
            return -lead.created_at.timestamp()
        if sort == "oldest":
            return lead.created_at.timestamp()
        return -composite

    leads.sort(key=sort_key)
    leads = leads[:page_size]

    items = []
    for lead in leads:
        score = latest_scores.get(lead.id)
        latest_action = db.query(Action).filter(Action.lead_id == lead.id).order_by(Action.created_at.desc()).first()
        account = lead.account_id
        from app.models.account import Account as AccountModel

        account_obj = db.query(AccountModel).filter(AccountModel.id == lead.account_id).first() if lead.account_id else None
        items.append(
            {
                "id": lead.id,
                "company": account_obj.name if account_obj else None,
                "source": lead.source,
                "status": lead.status,
                "fit": score.fit if score else None,
                "intent": score.intent if score else None,
                "deliverability": score.deliverability if score else None,
                "composite": score.composite if score else None,
                "next_action": latest_action.action_type if latest_action else None,
                "created_at": lead.created_at,
            }
        )

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        _error("Lead not found", "LEAD_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    return lead


@router.put("/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: str, payload: LeadUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        _error("Lead not found", "LEAD_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        _error("Lead not found", "LEAD_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    db.delete(lead)
    db.commit()


@router.post("/{lead_id}/analyze")
async def trigger_analyze(lead_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        _error("Lead not found", "LEAD_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    try:
        result = await analyze_lead(db, lead)
    except Exception as exc:
        _error(f"Unable to analyze lead: {exc}", "AI_SERVICE_ERROR", status.HTTP_502_BAD_GATEWAY)
    return {
        "lead": LeadOut.model_validate(result["lead"]),
        "research_pack": ResearchPackOut.model_validate(result["research_pack"]),
        "score": ScoreOut.model_validate(result["score"]),
        "action": ActionOut.model_validate(result["action"]),
    }


@router.post("/{lead_id}/score", response_model=ScoreOut)
async def recompute_score(lead_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        _error("Lead not found", "LEAD_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    result = await analyze_lead(db, lead)
    return result["score"]


@router.post("/{lead_id}/research", response_model=ResearchPackOut)
async def trigger_research(lead_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.models.account import Account as AccountModel
    from app.services.research_service import build_research_pack

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        _error("Lead not found", "LEAD_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    account = db.query(AccountModel).filter(AccountModel.id == lead.account_id).first() if lead.account_id else None
    pack = await build_research_pack(db, lead, account)
    return pack


@router.get("/{lead_id}/research", response_model=ResearchPackOut)
def get_research(lead_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pack = db.query(ResearchPack).filter(ResearchPack.lead_id == lead_id).order_by(ResearchPack.generated_at.desc()).first()
    if not pack:
        _error("No research pack found for this lead", "RESEARCH_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    return pack


@router.get("/{lead_id}/score", response_model=ScoreOut)
def get_score(lead_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    score = db.query(Score).filter(Score.lead_id == lead_id).order_by(Score.computed_at.desc()).first()
    if not score:
        _error("No score found for this lead", "SCORE_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    return score


@router.get("/{lead_id}/actions")
def get_actions(lead_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    actions = db.query(Action).filter(Action.lead_id == lead_id).order_by(Action.created_at.desc()).all()
    return [ActionOut.model_validate(a) for a in actions]


@router.post("/{lead_id}/actions/{action_id}/approve", response_model=ActionOut)
def approve_action(lead_id: str, action_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    action = db.query(Action).filter(Action.id == action_id, Action.lead_id == lead_id).first()
    if not action:
        _error("Action not found", "ACTION_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    action.status = ActionStatus.APPROVED
    action.actor = user.id
    db.commit()
    db.refresh(action)
    audit.log_event(db, "ACTION_APPROVED", lead_id=lead_id, actor=user.id, output_data={"action_id": action_id})
    return action


@router.post("/{lead_id}/actions/{action_id}/reject", response_model=ActionOut)
def reject_action(lead_id: str, action_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    action = db.query(Action).filter(Action.id == action_id, Action.lead_id == lead_id).first()
    if not action:
        _error("Action not found", "ACTION_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    action.status = ActionStatus.REJECTED
    action.actor = user.id
    db.commit()
    db.refresh(action)
    audit.log_event(db, "ACTION_REJECTED", lead_id=lead_id, actor=user.id, output_data={"action_id": action_id})
    return action


@router.post("/{lead_id}/actions/{action_id}/edit-draft", response_model=ActionOut)
def edit_draft(lead_id: str, action_id: str, payload: ActionEditDraftRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    action = db.query(Action).filter(Action.id == action_id, Action.lead_id == lead_id).first()
    if not action:
        _error("Action not found", "ACTION_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    action.draft_artifact = payload.draft_artifact
    action.actor = user.id
    db.commit()
    db.refresh(action)
    return action


@router.post("/{lead_id}/actions/{action_id}/override", response_model=ActionOut)
def override_action(lead_id: str, action_id: str, payload: ActionOverrideRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    original = db.query(Action).filter(Action.id == action_id, Action.lead_id == lead_id).first()
    if not original:
        _error("Action not found", "ACTION_NOT_FOUND", status.HTTP_404_NOT_FOUND)

    new_action = Action(
        lead_id=lead_id,
        action_type=payload.new_action_type,
        reason=f"Overridden by user from {original.action_type.value}",
        evidence=original.evidence,
        confidence=original.confidence,
        status=ActionStatus.PENDING,
        actor=user.id,
        is_override=original.action_type.value,
        override_reason=payload.reason,
    )
    db.add(new_action)
    db.commit()
    db.refresh(new_action)
    audit.log_event(
        db,
        "ACTION_OVERRIDDEN",
        lead_id=lead_id,
        actor=user.id,
        input_data={"original": original.action_type.value},
        output_data={"new": payload.new_action_type.value, "reason": payload.reason},
    )
    return new_action


@router.post("/{lead_id}/outcome", response_model=OutcomeOut, status_code=status.HTTP_201_CREATED)
def record_outcome(lead_id: str, payload: OutcomeIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        _error("Lead not found", "LEAD_NOT_FOUND", status.HTTP_404_NOT_FOUND)
    if payload.stage == "lost" and not payload.reason:
        _error("Loss reason is required when stage is 'lost'", "MISSING_LOSS_REASON")

    outcome = Outcome(
        lead_id=lead_id,
        stage=payload.stage,
        won=payload.won,
        value=payload.value,
        margin=payload.margin,
        reason=payload.reason,
        closed_at=datetime.now(timezone.utc) if payload.stage in ("won", "lost") else None,
    )
    db.add(outcome)

    if payload.stage == "won":
        lead.status = LeadStatus.CLOSED_WON
    elif payload.stage == "lost":
        lead.status = LeadStatus.CLOSED_LOST

    db.commit()
    db.refresh(outcome)
    audit.log_event(db, "OUTCOME_UPDATED", lead_id=lead_id, actor=user.id, output_data=payload.model_dump())
    return outcome
