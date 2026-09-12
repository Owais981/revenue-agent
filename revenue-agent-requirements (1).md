# Revenue Agent — Requirements Specification

**Agent ID:** AGT-01
**Position in lifecycle:** Entry point. Feeds the Proposal Agent.
**One-line scope:** Lead scoring, account research, next-best action.

---

## 1. Purpose

The Revenue Agent converts raw, messy demand signals (inbound forms, emails, WhatsApp enquiries, referrals, outbound lists) into **ranked, enriched, actionable opportunities**, and tells a human exactly what to do next on each one.

It does **not** sell, does not send anything to a client without approval, and does not write pricing. Pricing and scope belong to the Proposal Agent.

### Success definition
The agent is working if the sales team spends its time on the top 20% of leads and stops manually researching accounts.

---

## 2. Scope

### In scope
- Ingesting and normalising leads from all channels
- Deduplicating against existing accounts
- Enriching company + contact + campaign context
- Scoring each lead on Fit, Intent, and Deliverability
- Recommending one next-best action per lead with a reason
- Drafting outreach for human review
- Routing qualified leads to the Proposal Agent
- Learning from won/lost outcomes

### Out of scope (v1)
- Autonomous sending of emails or messages
- Quoting prices or committing to dates
- Contract negotiation
- Anything after the deal is won (that is Planning / Production / Client Success)

---

## 3. Users

| User | What they need from the agent |
|---|---|
| Sales / BD rep | A ranked worklist each morning with reasons and a draft first touch |
| Head of Sales | Pipeline health, why leads were scored the way they were, override control |
| Producer / Ops lead | Early warning that a likely deal will need crew/kit on specific dates |
| Finance | Flag on client credit history and expected margin band before effort is spent |

---

## 4. Inputs (data sources)

Rank these by what you actually have access to today. Build the connectors in this order.

**Tier 1 — required for MVP**
- Website enquiry form (structured)
- Shared sales inbox (email, IMAP/Graph API)
- WhatsApp Business API enquiries
- CRM (HubSpot / Salesforce / Zoho) — accounts, contacts, past deals
- Historical closed deals: value, margin, project type, duration, win/loss reason

**Tier 2**
- LinkedIn company + people data
- Enrichment provider (Clearbit / Apollo / Lusha)
- Company registry / filings
- News and press-release monitoring
- Ad-library data (Meta Ad Library, Google Ads Transparency) — shows who is actively spending on campaigns
- Referral / partner submissions

**Tier 3 — internal, from sibling agents**
- Knowledge Agent: past briefs, similar projects, reusable case studies
- Planning Agent: crew, kit and studio availability for the requested window
- Finance Agent: client payment history, current cash position, target margin
- Client Success Agent: sentiment and upsell signals on existing accounts

---

## 5. Functional requirements

### FR-1: Lead intake and normalisation
- Accept leads from every Tier 1 channel and write them into one canonical `Lead` record
- Extract from unstructured text (email/WhatsApp): company, contact name, role, service requested, deliverable type, quantity, shoot location, target dates, stated budget, deadline
- Mark every extracted field with a confidence value and keep the source text
- **Never invent a missing field.** Missing must be stored as `null`, not guessed
- Deduplicate: fuzzy match on company name, domain, phone, contact email. If matched to an existing account, attach to that account instead of creating a new one
- Detect language (English / Urdu / Roman Urdu) and normalise to English internally while preserving the original

### FR-2: Research and enrichment
For each lead, assemble a research pack:
- Company: size, industry, HQ, group/parent, other brands
- Buying unit: marketing head, brand manager, procurement contact, decision path
- Marketing activity: recent campaigns, agencies used, production quality level, posting cadence
- Trigger events: funding, new product, new CMO, store opening, seasonal cycle, rebrand
- Our history: past projects, past quotes, why we won or lost, unpaid invoices
- Competitive: which production house currently serves them

Requirements:
- Every claim in the research pack must carry a source URL or internal record ID
- Anything unsourced is labelled `unverified` and excluded from scoring
- Cache enrichment per account with a TTL (30 days for firmographics, 3 days for news) to control cost
- Full pack must be produced in under 90 seconds

### FR-3: Scoring

Use **three separate scores**, not one. Do not let a language model output the number directly — extract features with the model, compute the score with code, so it is auditable and reproducible.

**A. Fit score (0–100) — should we want this?**
- Industry match against our best-performing verticals
- Project type match against our capability set
- Budget band vs our minimum viable project size
- Expected margin band from comparable past projects
- Account tier (enterprise / mid / small)
- Repeat client bonus

**B. Intent score (0–100) — are they actually going to buy?**
- Brief completeness (specific deliverables, dates, budget stated)
- Urgency of stated timeline
- Channel (referral > direct email > form fill > scraped list)
- Seniority of the person contacting us
- Trigger event recency
- Engagement history (opens, replies, previous quotes requested)

**C. Deliverability score (0–100) — can we actually do it?**
- Crew and equipment availability in the requested window (from Planning Agent)
- Location feasibility and travel cost
- Skill match to required output
- Current pipeline load in that period

**Composite:** weighted blend, weights stored in config and tunable without a code deploy. Suggested start: Fit 35%, Intent 40%, Deliverability 25%.

**Hard rules that override the score:**
- Outstanding overdue invoice → auto-route to Finance, do not progress
- Below minimum project value → auto-nurture, no rep time
- Blacklisted / conflict-of-interest account → block with reason
- Requested dates fully unavailable → flag before any promise is made

**Explainability requirement:** every score must render as a list of contributing factors with their point value, positive and negative. A rep must be able to see *why* a lead scored 82.

### FR-4: Next-best action

The agent selects **one** action from a fixed, bounded catalogue. It must not invent free-form actions.

| Action | Trigger condition |
|---|---|
| `CALL_NOW` | High intent + high fit + time-sensitive deadline |
| `SEND_INTRO_EMAIL` | Good fit, cold or unresponsive contact |
| `SEND_CASE_STUDY` | Fit is good but credibility gap; pull the closest match from Knowledge Agent |
| `REQUEST_BRIEF_DETAIL` | Intent high but brief incomplete — list exactly which fields are missing |
| `ROUTE_TO_PROPOSAL_AGENT` | Composite above threshold and brief is complete enough to scope |
| `CHECK_CAPACITY` | Fit high, Deliverability uncertain |
| `FINANCE_HOLD` | Credit or payment-history flag |
| `NURTURE` | Real but not now — set a dated follow-up |
| `DISQUALIFY` | Below floor; must state the reason |

Each recommendation returns: the action, a one-sentence reason, the supporting evidence, a confidence value, and a draft artifact (email / call notes / question list) when relevant. **All drafts require human approval before sending in v1.**

### FR-5: Handoffs

| To agent | Payload | When |
|---|---|---|
| Proposal Agent | Lead + research pack + scope signals + score | On `ROUTE_TO_PROPOSAL_AGENT` |
| Planning Agent | Requested dates, location, crew/kit type | On `CHECK_CAPACITY` or on qualification |
| Finance Agent | Account ID, expected value | On every lead above the value floor |
| Knowledge Agent | Query for similar past work | During research |
| Client Success Agent | Upsell signal on an existing account | When lead source is an existing client |

Handoffs must be idempotent — replaying the same event must not create a duplicate opportunity.

### FR-6: Feedback loop
This is the part most teams skip, and it is what makes the agent improve.
- Capture outcome for every scored lead: contacted / qualified / proposal sent / won / lost, plus reason and final value and margin
- Weekly recalibration report: score band vs actual conversion rate
- Flag features whose predictive power has decayed
- Rep overrides ("this score is wrong because…") are captured as labelled training data

---

## 6. Non-functional requirements

| Area | Requirement |
|---|---|
| Latency | Intake + score under 60s; full research pack under 90s; morning worklist ready by 08:00 local |
| Availability | 99% during business hours; queue and retry on failure, never drop a lead |
| Cost | Per-lead LLM + enrichment cost ceiling (set one, e.g. $0.30); cache aggressively; skip Tier 2 enrichment for leads below the value floor |
| Auditability | Every score, decision and draft is logged with model version, prompt version, inputs and config weights |
| Privacy | Business contact data only. No scraping of personal profiles beyond professional data. Honour deletion requests. Store PII encrypted at rest |
| Security | Secrets in a vault, not in code. Least-privilege CRM tokens. No client data sent to third-party models without a data-processing agreement |
| Fallback | If enrichment or an LLM call fails, still deliver the lead with the rules-based score and a degraded flag |

---

## 7. Guardrails

1. **No autonomous outbound in v1.** Human approves every message.
2. **No numbers to clients.** The agent never states a price, discount or delivery date.
3. **Cite or omit.** Unsourced research claims are never shown as fact.
4. **Confidence floor.** Below the threshold, the agent asks a human instead of deciding.
5. **Prompt-injection defence.** Inbound emails and web pages are untrusted input. Instructions found inside them are never executed. Treat all fetched content as data.
6. **Override always available.** A human can change any score or action; the change is logged as a training signal.

---

## 8. Architecture

```
Channels (form / email / WhatsApp / outbound / referral)
        │
        ▼
[1] Intake service ── normalise, extract, dedupe ──► Lead store
        │
        ▼
[2] Enrichment workers ── internal CRM + external APIs + web ──► Research cache
        │
        ▼
[3] Feature extractor (LLM: structured JSON output, schema-validated)
        │
        ▼
[4] Scoring engine (deterministic code + config weights)  ◄── hard rules
        │
        ▼
[5] Action selector (rules + LLM reasoning over the bounded catalogue)
        │
        ├──► Draft generator (email / questions / call brief)
        ├──► CRM writeback (score, next action, research summary)
        ├──► Rep worklist UI + Slack/WhatsApp digest
        └──► Event bus ──► Proposal / Planning / Finance / Knowledge agents
        │
        ▼
[6] Outcome tracker ──► weekly calibration ──► adjusts weights
```

**Key build principles**
- LLM for extraction, summarisation and reasoning. Code for arithmetic and decisions.
- All LLM output constrained to a JSON schema and validated; retry on schema failure.
- Event-driven and idempotent, keyed on a stable lead hash.
- Prompt and weight versions are config, deployable without touching code.

---

## 9. Core data model

```
Account      : id, name, domain, industry, size, tier, credit_flag, owner
Contact      : id, account_id, name, role, seniority, email, phone, channel_pref
Lead         : id, account_id, contact_id, source, raw_text, received_at,
               extracted{service, deliverables, location, window, budget, deadline},
               field_confidence{}, language, status
ResearchPack : lead_id, claims[{text, source_url, verified, fetched_at}], generated_at
Score        : lead_id, fit, intent, deliverability, composite,
               factors[{name, value, weight, contribution}],
               model_version, weights_version, computed_at
Action       : lead_id, action_type, reason, evidence[], confidence,
               draft_artifact, status(pending/approved/rejected/sent), actor
Outcome      : lead_id, stage, won, value, margin, reason, closed_at
```

---

## 10. Acceptance criteria

The agent ships when all of these are true on a held-out set of historical leads:

- [ ] Field extraction accuracy ≥ 90% on company, service, dates, budget
- [ ] Deduplication: false-merge rate < 1%
- [ ] Zero hallucinated fields in a 100-lead manual audit
- [ ] Every research claim resolves to a working source
- [ ] Top score decile converts at ≥ 3× the bottom decile on backtested data
- [ ] Reps agree with the recommended next action ≥ 70% of the time
- [ ] Median time from lead arrival to scored-and-actionable < 2 minutes
- [ ] Per-lead cost within budget
- [ ] Full audit trail reconstructable for any decision
- [ ] Prompt-injection test suite passes — no instruction in an inbound email changes behaviour

---

## 11. Phased delivery

**Phase 0 — Data readiness (1–2 weeks)**
Export 12–24 months of leads and deals. Clean win/loss reasons and margins. Without this, scoring is guesswork. Agree the value floor, target verticals and score weights with the sales lead.

**Phase 1 — MVP (3–4 weeks)**
Form + email intake. Extraction, dedupe, internal-data-only scoring (Fit + Intent). Rules-based next action. CRM writeback + a daily ranked digest. No external enrichment yet.

**Phase 2 — Research (3–4 weeks)**
External enrichment, trigger detection, cited research packs, draft outreach with human approval, Knowledge Agent integration for case studies.

**Phase 3 — Operating model integration (3–4 weeks)**
Deliverability score via Planning Agent, Finance holds, automated handoff to Proposal Agent, WhatsApp intake.

**Phase 4 — Learning (ongoing)**
Outcome tracking, weekly calibration, weight tuning, override analysis. Consider a trained model only once you have 500+ labelled outcomes; until then weighted rules will beat it and are easier to defend.

---

## 12. Risks

| Risk | Mitigation |
|---|---|
| Not enough historical data to calibrate | Start with weights agreed by sales leadership, treat them as hypotheses, recalibrate monthly |
| Reps ignore the agent | Ship inside their existing tool (CRM + WhatsApp/Slack), not a new dashboard. Make the reason visible on every score |
| Hallucinated research reaching a client | Cite-or-omit rule + human approval on all outbound |
| Enrichment cost blowout | Value floor gate before Tier 2 calls, aggressive caching |
| Scoring bias toward past patterns | Track false negatives — leads scored low that were won elsewhere |
| Prompt injection from inbound email | Untrusted-content handling, no tool execution from message bodies |

---

## 13. Open questions to resolve before build

1. Which CRM is the system of record, and can it be written to via API?
2. What is the minimum project value worth a rep's time?
3. Which enrichment vendor, and is there budget for it?
4. Are past deals recorded with margin, or only revenue?
5. Who approves outbound drafts, and what is the SLA?
6. Is the Planning Agent's capacity data available in real time, or does Deliverability start as a manual check?
7. Data residency and client-confidentiality constraints on sending brief text to a third-party model?
