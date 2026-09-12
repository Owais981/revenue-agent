from typing import Optional, List, Dict

from pydantic import BaseModel, ConfigDict


class ScoringConfigOut(BaseModel):
    fit_weight: float
    intent_weight: float
    deliverability_weight: float
    proposal_threshold: float
    nurture_threshold: float
    min_project_value: float
    confidence_threshold: float
    high_score_threshold: float
    medium_score_threshold: float
    enterprise_min_budget: float
    mid_min_budget: float
    target_verticals: List[str]
    capability_set: List[str]
    channel_weights: Dict[str, float]
    seniority_weights: Dict[str, float]
    tier_weights: Dict[str, float]
    version: str

    model_config = ConfigDict(from_attributes=True)


class ScoringConfigUpdate(BaseModel):
    fit_weight: Optional[float] = None
    intent_weight: Optional[float] = None
    deliverability_weight: Optional[float] = None
    proposal_threshold: Optional[float] = None
    nurture_threshold: Optional[float] = None
    min_project_value: Optional[float] = None
    confidence_threshold: Optional[float] = None
    high_score_threshold: Optional[float] = None
    medium_score_threshold: Optional[float] = None
    enterprise_min_budget: Optional[float] = None
    mid_min_budget: Optional[float] = None
    target_verticals: Optional[List[str]] = None
    capability_set: Optional[List[str]] = None
    channel_weights: Optional[Dict[str, float]] = None
    seniority_weights: Optional[Dict[str, float]] = None
    tier_weights: Optional[Dict[str, float]] = None
