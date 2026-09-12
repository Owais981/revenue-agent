from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ScoreFactorOut(BaseModel):
    name: str
    value: float
    weight: float
    contribution: float
    reason: str
    category: str


class ScoreOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: str
    lead_id: str
    fit: float
    intent: float
    deliverability: float
    composite: float
    factors: List[dict]
    model_version: Optional[str]
    weights_version: Optional[str]
    degraded: Optional[str]
    computed_at: datetime


class ClaimOut(BaseModel):
    text: str
    source_url: Optional[str] = None
    internal_record_id: Optional[str] = None
    verified: bool
    fetched_at: str


class ResearchPackOut(BaseModel):
    id: str
    lead_id: str
    account_id: Optional[str]
    claims: List[dict]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
