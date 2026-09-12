from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.outcome import AuditLog
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])


@router.get("")
def list_audit_logs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lead_id: Optional[str] = None,
    event_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    query = db.query(AuditLog)
    if lead_id:
        query = query.filter(AuditLog.lead_id == lead_id)
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    total = query.count()
    items = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {
                "id": i.id,
                "lead_id": i.lead_id,
                "event_type": i.event_type,
                "input": i.input,
                "output": i.output,
                "model_version": i.model_version,
                "prompt_version": i.prompt_version,
                "weights_version": i.weights_version,
                "actor": i.actor,
                "timestamp": i.timestamp,
            }
            for i in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
