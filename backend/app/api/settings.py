from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.settings import ScoringConfigOut, ScoringConfigUpdate
from app.api.deps import get_current_user
from app.services.lead_pipeline import get_scoring_config
from app.services import audit

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/scoring", response_model=ScoringConfigOut)
def get_scoring_settings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_scoring_config(db)


@router.put("/scoring", response_model=ScoringConfigOut)
def update_scoring_settings(payload: ScoringConfigUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    config = get_scoring_config(db)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(config, field, value)

    weight_sum = config.fit_weight + config.intent_weight + config.deliverability_weight
    if abs(weight_sum - 1.0) > 0.01:
        # normalise rather than reject, so the UI stays forgiving
        config.fit_weight = round(config.fit_weight / weight_sum, 4)
        config.intent_weight = round(config.intent_weight / weight_sum, 4)
        config.deliverability_weight = round(config.deliverability_weight / weight_sum, 4)

    db.commit()
    db.refresh(config)
    audit.log_event(db, "SETTINGS_UPDATED", actor=user.id, output_data=updates)
    return config
