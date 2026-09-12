from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, ConfigDict

from app.models.lead import LeadStatus


class LeadIntakeRequest(BaseModel):
    source: str
    raw_text: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    company_hint: Optional[str] = None


class LeadManualCreate(BaseModel):
    source: str = "manual"
    company: Optional[str] = None
    contact_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    service: Optional[str] = None
    deliverables: Optional[str] = None
    location: Optional[str] = None
    target_dates: Optional[str] = None
    budget: Optional[float] = None
    deadline: Optional[str] = None
    raw_text: Optional[str] = None


class LeadUpdate(BaseModel):
    service: Optional[str] = None
    deliverables: Optional[str] = None
    location: Optional[str] = None
    target_dates: Optional[str] = None
    budget: Optional[float] = None
    deadline: Optional[str] = None
    status: Optional[LeadStatus] = None


class LeadOut(BaseModel):
    id: str
    account_id: Optional[str]
    contact_id: Optional[str]
    source: str
    raw_text: Optional[str]
    received_at: datetime
    service: Optional[str]
    deliverables: Optional[str]
    quantity: Optional[str]
    location: Optional[str]
    target_dates: Optional[str]
    budget: Optional[float]
    deadline: Optional[str]
    field_confidence: Optional[Dict[str, Any]]
    field_sources: Optional[Dict[str, Any]]
    language: Optional[str]
    status: LeadStatus
    ai_degraded: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
