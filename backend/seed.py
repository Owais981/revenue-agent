"""Demo data seed script for the Revenue Agent.

Run with: python seed.py
Creates a demo admin user plus accounts, contacts, leads, scores, actions and
outcomes so the dashboard looks functional immediately. All demo data is tagged
with source values / owner names that make it obvious it is not real production data.
"""
import asyncio
import random
from datetime import datetime, timedelta, timezone

from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app import models  # noqa: F401
from app.models.user import User, UserRole
from app.models.account import Account
from app.models.contact import Contact
from app.models.lead import Lead, LeadStatus
from app.models.score import Score
from app.models.action import Action, ActionType, ActionStatus
from app.models.outcome import Outcome
from app.services.scoring_engine import ScoringEngine, MODEL_VERSION
from app.services.lead_pipeline import get_scoring_config

random.seed(42)
Base.metadata.create_all(bind=engine)

COMPANIES = [
    ("Zenith FMCG Pakistan", "zenithfmcg.demo", "fmcg", "enterprise"),
    ("Northline Telecom", "northlinetel.demo", "telecom", "enterprise"),
    ("Vantage Retail Group", "vantageretail.demo", "retail", "mid"),
    ("Coastal Fashion House", "coastalfashion.demo", "fashion", "mid"),
    ("BrewCraft Beverages", "brewcraft.demo", "food & beverage", "mid"),
    ("Alpine Bank Ltd", "alpinebank.demo", "banking", "enterprise"),
    ("Pixel Forge Technology", "pixelforge.demo", "technology", "small"),
    ("Metro Realty Partners", "metrorealty.demo", "real estate", "small"),
    ("Harvest Foods Co", "harvestfoods.demo", "food & beverage", "mid"),
    ("Skyline Motors", "skylinemotors.demo", "automotive", "mid"),
]

SERVICES = ["Commercial production", "TVC", "Corporate video", "Social media content", "Documentary", "Photography"]
SOURCES = ["website", "email", "whatsapp", "referral", "outbound"]
SENIORITIES = ["executive", "senior", "manager", "junior"]
ROLES = ["Marketing Manager", "Brand Manager", "CMO", "Procurement Lead", "Founder"]

STATUSES_POOL = [
    LeadStatus.NEW, LeadStatus.QUALIFIED, LeadStatus.NURTURE, LeadStatus.DISQUALIFIED,
    LeadStatus.FINANCE_HOLD, LeadStatus.ROUTED_TO_PROPOSAL, LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST,
]


def main():
    db = SessionLocal()
    engine_ = ScoringEngine()

    admin = db.query(User).filter(User.email == "admin@revenueagentdemo.com").first()
    if not admin:
        admin = User(
            name="Demo Admin",
            email="admin@revenueagentdemo.com",
            password_hash=hash_password("DemoPass123!"),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        rep = User(
            name="Demo Sales Rep",
            email="rep@revenueagentdemo.com",
            password_hash=hash_password("DemoPass123!"),
            role=UserRole.SALES_REP,
        )
        db.add(rep)
        db.commit()
        print("Created demo users: admin@revenueagentdemo.com / rep@revenueagentdemo.com (password: DemoPass123!)")

    config = get_scoring_config(db)
    weights = {"fit": config.fit_weight, "intent": config.intent_weight, "deliverability": config.deliverability_weight}

    accounts = []
    for name, domain, industry, tier in COMPANIES:
        existing = db.query(Account).filter(Account.domain == domain).first()
        if existing:
            accounts.append(existing)
            continue
        account = Account(
            name=name,
            domain=domain,
            industry=industry,
            size=random.choice(["11-50", "51-200", "201-1000", "1000+"]),
            tier=tier,
            credit_flag=random.random() < 0.1,
            blacklisted=False,
            owner="Demo Sales Rep",
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        accounts.append(account)
    print(f"Accounts: {len(accounts)}")

    contacts = []
    for account in accounts:
        for _ in range(random.choice([1, 2])):
            contact = Contact(
                account_id=account.id,
                name=f"Contact {random.randint(100,999)}",
                role=random.choice(ROLES),
                seniority=random.choice(SENIORITIES),
                email=f"contact{random.randint(1000,9999)}@{account.domain}",
                phone=f"+92300{random.randint(1000000,9999999)}",
                channel_pref=random.choice(["email", "whatsapp", "phone"]),
            )
            db.add(contact)
            contacts.append(contact)
    db.commit()
    print(f"Contacts: {len(contacts)}")

    existing_leads = db.query(Lead).count()
    if existing_leads >= 20:
        print(f"Leads already seeded ({existing_leads}). Skipping lead generation.")
        db.close()
        return

    leads_created = 0
    for i in range(20):
        account = random.choice(accounts)
        contact = random.choice([c for c in contacts if c.account_id == account.id])
        source = random.choice(SOURCES)
        service = random.choice(SERVICES)
        has_budget = random.random() > 0.15
        budget = random.choice([3000, 6000, 12000, 18000, 25000, 40000]) if has_budget else None
        has_deadline = random.random() > 0.3
        deadline = (datetime.now(timezone.utc) + timedelta(days=random.randint(7, 60))).strftime("%Y-%m-%d") if has_deadline else None

        lead = Lead(
            account_id=account.id,
            contact_id=contact.id,
            source=source,
            raw_text=f"[DEMO DATA] Enquiry from {account.name} for {service}.",
            service=service,
            deliverables=random.choice(["3x 30s videos", "1x TVC", "10x social clips", None]),
            location=random.choice(["Karachi", "Lahore", "Islamabad", None]),
            target_dates=random.choice(["Next month", "Q3", None]),
            budget=budget,
            deadline=deadline,
            field_confidence={"service": 0.9, "budget": 0.85 if budget else 0.0},
            field_sources={"service": "raw_text", "budget": "raw_text" if budget else None},
            language="en",
            status=random.choice(STATUSES_POOL),
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        features = {
            "industry": account.industry,
            "service": service,
            "budget": budget,
            "min_project_value": config.min_project_value,
            "target_verticals": config.target_verticals,
            "capability_set": config.capability_set,
            "enterprise_min_budget": config.enterprise_min_budget,
            "mid_min_budget": config.mid_min_budget,
            "channel_weights": config.channel_weights,
            "seniority_weights": config.seniority_weights,
            "tier_weights": config.tier_weights,
            "expected_margin_band": random.choice(["high", "medium", "low"]),
            "account_tier": account.tier,
            "is_repeat_client": random.random() > 0.6,
            "deadline": deadline,
            "source": source,
            "contact_seniority": contact.seniority,
            "trigger_event_recent": random.random() > 0.7,
            "engagement_score": random.randint(0, 5),
            "crew_available": random.random() > 0.2,
            "equipment_available": random.random() > 0.1,
            "location_requires_travel": random.random() > 0.6,
            "skill_match": random.random() > 0.15,
            "pipeline_load_pct": random.randint(20, 95),
        }

        fit_result = engine_.calculate_fit(features)
        intent_result = engine_.calculate_intent(features)
        deliverability_result = engine_.calculate_deliverability(features)
        composite = engine_.calculate_composite(fit_result.score, intent_result.score, deliverability_result.score, weights)

        score = Score(
            lead_id=lead.id,
            fit=fit_result.score,
            intent=intent_result.score,
            deliverability=deliverability_result.score,
            composite=composite,
            factors=fit_result.to_dicts() + intent_result.to_dicts() + deliverability_result.to_dicts(),
            model_version=MODEL_VERSION,
            weights_version=config.version,
        )
        db.add(score)

        action_type = random.choice(list(ActionType))
        action = Action(
            lead_id=lead.id,
            action_type=action_type,
            reason="[DEMO DATA] Generated by seed script for dashboard demonstration",
            evidence=[f"Composite {composite}"],
            confidence=round(random.uniform(0.5, 0.95), 2),
            draft_artifact="Demo draft - review before sending." if action_type in (ActionType.SEND_INTRO_EMAIL, ActionType.SEND_CASE_STUDY) else None,
            status=random.choice(list(ActionStatus)),
            actor="system",
        )
        db.add(action)
        db.commit()

        if lead.status in (LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST):
            won = lead.status == LeadStatus.CLOSED_WON
            outcome = Outcome(
                lead_id=lead.id,
                stage="won" if won else "lost",
                won=won,
                value=budget if won else None,
                margin=round(budget * random.uniform(0.15, 0.35), 2) if won and budget else None,
                reason=None if won else random.choice(["Went with competitor", "Budget cut", "Timeline slipped"]),
                closed_at=datetime.now(timezone.utc),
            )
            db.add(outcome)
            db.commit()

        leads_created += 1

    print(f"Leads created: {leads_created}")
    db.close()
    print("Seed complete.")


if __name__ == "__main__":
    main()
