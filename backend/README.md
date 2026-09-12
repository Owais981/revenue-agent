# Revenue Agent — Backend

FastAPI service implementing lead intake, deterministic scoring, hard rules, and
next-best-action selection. See the root [README.md](../README.md) for the full
setup guide. Quick reference:

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # then fill in GEMINI_API_KEY (optional)
uvicorn app.main:app --reload
python seed.py                 # optional: demo data
python -m pytest               # run tests
```

API docs: http://localhost:8000/docs

## Layout

- `app/models/` — SQLAlchemy tables (User, Account, Contact, Lead, ResearchPack, Score, Action, Outcome, AuditLog, ScoringConfig)
- `app/schemas/` — Pydantic request/response and Gemini structured-output contracts
- `app/services/` — business logic: `gemini_service`, `lead_extraction`, `deduplication`, `research_service`, `scoring_engine`, `action_selector`, `draft_generator`, `lead_pipeline` (orchestrator), `adapters` (mockable CRM/Planning/Finance/Knowledge interfaces)
- `app/api/` — FastAPI routers
- `tests/` — pytest suite covering extraction, dedup, scoring, hard rules, action selection, and prompt injection

## Key design rule

`scoring_engine.py` never lets an LLM output a numeric score — Gemini only extracts
features; Python computes Fit/Intent/Deliverability/Composite from those features plus
`ScoringConfig` (DB-backed weights/thresholds, editable at `/api/settings/scoring`).
