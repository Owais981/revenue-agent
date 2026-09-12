"""Turns raw lead text into structured fields.

Tries Gemini first. If Gemini is unavailable or misconfigured, falls back to a
conservative regex/keyword-based extractor that only fills fields it can find with
high confidence, and marks the lead as AI-degraded rather than failing.
"""
import logging
import re
from typing import Optional

from app.schemas.extraction import LeadExtraction, ExtractedField
from app.services.gemini_service import call_structured, build_extraction_prompt, GeminiUnavailableError

logger = logging.getLogger("revenue_agent.extraction")

ROMAN_URDU_MARKERS = ["hai", "karwana", "chahiye", "mein", "humein", "aik", "aap"]
URDU_RANGE = re.compile(r"[؀-ۿ]")

BUDGET_RE = re.compile(r"(?:PKR|Rs\.?|USD|\$)\s?([\d,]{3,})", re.IGNORECASE)
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*")
PHONE_RE = re.compile(r"(\+?\d[\d\- ]{7,}\d)")


def detect_language(text: str) -> str:
    if URDU_RANGE.search(text):
        return "ur"
    lowered = text.lower()
    if any(marker in lowered for marker in ROMAN_URDU_MARKERS):
        return "roman-ur"
    return "en"


def rule_based_extract(raw_text: str) -> LeadExtraction:
    """Conservative fallback used only when Gemini is unavailable. Never guesses -
    only fills a field when a clear pattern match exists."""
    language = detect_language(raw_text)

    def field(value: Optional[str], confidence: float) -> ExtractedField:
        return ExtractedField(value=value, confidence=confidence, source="raw_text" if value else None)

    email_match = EMAIL_RE.search(raw_text)
    phone_match = PHONE_RE.search(raw_text)
    budget_match = BUDGET_RE.search(raw_text)

    return LeadExtraction(
        company=field(None, 0.0),
        contact_name=field(None, 0.0),
        role=field(None, 0.0),
        contact_email=field(email_match.group(0) if email_match else None, 0.9 if email_match else 0.0),
        contact_phone=field(phone_match.group(0).strip() if phone_match else None, 0.8 if phone_match else 0.0),
        service_requested=field(None, 0.0),
        deliverables=field(None, 0.0),
        quantity=field(None, 0.0),
        shoot_location=field(None, 0.0),
        target_dates=field(None, 0.0),
        budget=field(budget_match.group(1).replace(",", "") if budget_match else None, 0.7 if budget_match else 0.0),
        deadline=field(None, 0.0),
        language=language,
    )


def extract_lead_fields(raw_text: str) -> tuple[LeadExtraction, bool, Optional[str]]:
    """Returns (extraction, degraded, degraded_reason)."""
    try:
        extraction = call_structured(build_extraction_prompt(raw_text), LeadExtraction)
        return extraction, False, None
    except GeminiUnavailableError as exc:
        logger.warning("Falling back to rule-based extraction: %s", exc)
        return rule_based_extract(raw_text), True, f"AI unavailable - degraded mode: {exc}"
