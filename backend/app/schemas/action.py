from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.action import ActionType, ActionStatus


class ActionOut(BaseModel):
    id: str
    lead_id: str
    action_type: ActionType
    reason: Optional[str]
    evidence: List
    confidence: Optional[float]
    draft_artifact: Optional[str]
    status: ActionStatus
    actor: Optional[str]
    is_override: Optional[str]
    override_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActionOverrideRequest(BaseModel):
    new_action_type: ActionType
    reason: str


class ActionEditDraftRequest(BaseModel):
    draft_artifact: str


class OutcomeIn(BaseModel):
    stage: str  # contacted / qualified / proposal_sent / won / lost
    won: Optional[bool] = None
    value: Optional[float] = None
    margin: Optional[float] = None
    reason: Optional[str] = None


class OutcomeOut(BaseModel):
    id: str
    lead_id: str
    stage: str
    won: Optional[bool]
    value: Optional[float]
    margin: Optional[float]
    reason: Optional[str]
    closed_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
