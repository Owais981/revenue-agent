from typing import Optional

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    value: Optional[str] = None
    confidence: float = 0.0
    source: Optional[str] = None


class LeadExtraction(BaseModel):
    """Structured output contract for Gemini extraction. Every field is optional and
    must be null (not guessed) when the information is not present in the source text."""

    company: ExtractedField = Field(default_factory=ExtractedField)
    contact_name: ExtractedField = Field(default_factory=ExtractedField)
    role: ExtractedField = Field(default_factory=ExtractedField)
    contact_email: ExtractedField = Field(default_factory=ExtractedField)
    contact_phone: ExtractedField = Field(default_factory=ExtractedField)
    service_requested: ExtractedField = Field(default_factory=ExtractedField)
    deliverables: ExtractedField = Field(default_factory=ExtractedField)
    quantity: ExtractedField = Field(default_factory=ExtractedField)
    shoot_location: ExtractedField = Field(default_factory=ExtractedField)
    target_dates: ExtractedField = Field(default_factory=ExtractedField)
    budget: ExtractedField = Field(default_factory=ExtractedField)
    deadline: ExtractedField = Field(default_factory=ExtractedField)
    language: str = "en"
