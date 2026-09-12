from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AccountOut(BaseModel):
    id: str
    name: str
    domain: Optional[str]
    industry: Optional[str]
    size: Optional[str]
    tier: Optional[str]
    credit_flag: bool
    blacklisted: bool
    owner: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountUpdate(BaseModel):
    industry: Optional[str] = None
    size: Optional[str] = None
    tier: Optional[str] = None
    credit_flag: Optional[bool] = None
    blacklisted: Optional[bool] = None
    owner: Optional[str] = None
