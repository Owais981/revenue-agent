"""Fuzzy account/contact matching so the same company or person never creates a
duplicate account. Pure Python (difflib) - no external dependency needed for MVP."""
import re
from difflib import SequenceMatcher
from typing import Optional

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.contact import Contact

NAME_MATCH_THRESHOLD = 0.85


def _normalize(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"\b(pvt|ltd|llc|inc|co|company|limited|private)\b\.?", "", name)
    name = re.sub(r"[^a-z0-9 ]", "", name)
    return re.sub(r"\s+", " ", name).strip()


def _domain_from_email(email: Optional[str]) -> Optional[str]:
    if not email or "@" not in email:
        return None
    return email.split("@")[-1].lower().strip()


def name_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def find_matching_account(
    db: Session,
    company_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> Optional[Account]:
    domain = _domain_from_email(email)

    if domain:
        match = db.query(Account).filter(Account.domain == domain).first()
        if match:
            return match

    if phone:
        contact = db.query(Contact).filter(Contact.phone == phone).first()
        if contact and contact.account_id:
            account = db.query(Account).filter(Account.id == contact.account_id).first()
            if account:
                return account

    if email:
        contact = db.query(Contact).filter(Contact.email == email).first()
        if contact and contact.account_id:
            account = db.query(Account).filter(Account.id == contact.account_id).first()
            if account:
                return account

    if company_name:
        candidates = db.query(Account).all()
        best_score = 0.0
        best_account = None
        for candidate in candidates:
            score = name_similarity(company_name, candidate.name)
            if score > best_score:
                best_score = score
                best_account = candidate
        if best_score >= NAME_MATCH_THRESHOLD:
            return best_account

    return None


def find_matching_contact(
    db: Session, account_id: Optional[str], email: Optional[str], phone: Optional[str], name: Optional[str]
) -> Optional[Contact]:
    if email:
        match = db.query(Contact).filter(Contact.email == email).first()
        if match:
            return match
    if phone:
        match = db.query(Contact).filter(Contact.phone == phone).first()
        if match:
            return match
    if account_id and name:
        candidates = db.query(Contact).filter(Contact.account_id == account_id).all()
        for candidate in candidates:
            if candidate.name and name_similarity(name, candidate.name) >= NAME_MATCH_THRESHOLD:
                return candidate
    return None
