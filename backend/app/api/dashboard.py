from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.lead import Lead, LeadStatus
from app.models.action import Action, ActionType
from app.models.outcome import Outcome
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total_leads = db.query(Lead).count()

    def count_status(s: LeadStatus):
        return db.query(Lead).filter(Lead.status == s).count()

    won = db.query(Outcome).filter(Outcome.won == True).count()
    lost = db.query(Outcome).filter(Outcome.won == False, Outcome.stage == "lost").count()

    high_priority = (
        db.query(Lead)
        .join(Action, Action.lead_id == Lead.id)
        .filter(Action.action_type == ActionType.CALL_NOW)
        .distinct()
        .count()
    )

    return {
        "total_leads": total_leads,
        "new_leads": count_status(LeadStatus.NEW),
        "qualified_leads": count_status(LeadStatus.QUALIFIED),
        "high_priority_leads": high_priority,
        "nurture": count_status(LeadStatus.NURTURE),
        "finance_holds": count_status(LeadStatus.FINANCE_HOLD),
        "routed_to_proposal": count_status(LeadStatus.ROUTED_TO_PROPOSAL),
        "won": won,
        "lost": lost,
    }
