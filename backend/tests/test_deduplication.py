from app.models.account import Account
from app.models.contact import Contact
from app.services.deduplication import find_matching_account, find_matching_contact, name_similarity


def test_matches_by_domain(db_session):
    account = Account(name="Acme Media", domain="acmemedia.com")
    db_session.add(account)
    db_session.commit()

    match = find_matching_account(db_session, email="someone@acmemedia.com")
    assert match is not None
    assert match.id == account.id


def test_matches_by_similar_company_name(db_session):
    account = Account(name="Acme Media Pvt Ltd", domain="acmemedia.com")
    db_session.add(account)
    db_session.commit()

    match = find_matching_account(db_session, company_name="Acme Media")
    assert match is not None
    assert match.id == account.id


def test_does_not_match_unrelated_company(db_session):
    account = Account(name="Acme Media", domain="acmemedia.com")
    db_session.add(account)
    db_session.commit()

    match = find_matching_account(db_session, company_name="Totally Different Corp")
    assert match is None


def test_matches_contact_by_email(db_session):
    account = Account(name="Acme Media", domain="acmemedia.com")
    db_session.add(account)
    db_session.commit()
    contact = Contact(account_id=account.id, name="Jane Doe", email="jane@acmemedia.com")
    db_session.add(contact)
    db_session.commit()

    match = find_matching_contact(db_session, account.id, email="jane@acmemedia.com", phone=None, name=None)
    assert match is not None
    assert match.id == contact.id


def test_matches_contact_by_phone(db_session):
    account = Account(name="Acme Media", domain="acmemedia.com")
    db_session.add(account)
    db_session.commit()
    contact = Contact(account_id=account.id, name="Jane Doe", phone="+923001234567")
    db_session.add(contact)
    db_session.commit()

    match = find_matching_contact(db_session, account.id, email=None, phone="+923001234567", name=None)
    assert match is not None
    assert match.id == contact.id


def test_name_similarity_ignores_legal_suffixes():
    assert name_similarity("Acme Media Pvt Ltd", "Acme Media") > 0.9
