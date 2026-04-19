# ⚔️ AEGIS — Autonomous Chargeback Defense System

> *Named after the aegis — the divine shield of Zeus and Athena in Greek mythology. Unbreakable. Carried into every battle.*

**Chargebacks cost merchants $125 billion annually. Responding to each one requires a paralegal-level understanding of card network rules, evidence law, and dispute strategy — taking hours per case. AEGIS replicates that entire defense workflow autonomously — classifying the dispute, gathering evidence, building a legal strategy, drafting a formal response, and reviewing it — producing a submission-ready `.docx` document with a **verdict (FIGHT / ACCEPT / ESCALATE), winability score, and full argument set** in under 10 seconds.**

[![Tests](https://img.shields.io/badge/Tests-7%2F7-10B981?style=flat)](/)
[![Evals](https://img.shields.io/badge/Evals-15%2F15-10B981?style=flat)](/)
[![CI](https://img.shields.io/badge/CI-Passing-10B981?style=flat)](/)
[![Live](https://img.shields.io/badge/Live-Railway-7C5CBF?style=flat)](https://aegis-production-1d9a.up.railway.app)



## 🔴 Live API

**`https://aegis-production-1d9a.up.railway.app`** — Live on Railway.  
Full Swagger docs at [`/docs`](https://aegis-production-1d9a.up.railway.app/docs)

---

## The Problem

When a customer files a chargeback, the merchant has 7–30 days to respond with a legally structured dispute package. That package must:

- Correctly identify the chargeback reason code and its burden of proof
- Pull together delivery records, device fingerprints, auth history, and cardholder communications
- Build a winning legal argument based on card network rules
- Draft a formal response document meeting network submission standards
- Pass internal quality review before submission

Most merchants lose by default — not because they have a bad case, but because they don't have the people or process to respond in time. AEGIS solves it.

---

## What AEGIS Does

A dispute is submitted via REST API. Five specialized agents process it in sequence:

```
Intake → Evidence Collector → Strategy → Writer → Reviewer
```

| Agent | Role |
|---|---|
| **Intake** | Classifies dispute category and urgency from Visa reason code + rules engine |
| **Evidence Collector** | Gathers order details, delivery proof, device fingerprint, auth history, cardholder comms |
| **Strategy** | Decides FIGHT / ACCEPT / ESCALATE with a 0–1 winability score and argument set |
| **Writer** | Drafts a formal, submission-ready dispute response document |
| **Reviewer** | Reviews the draft for completeness and triggers a revision loop if needed |

The Reviewer → Writer loop runs until the response passes review or hits the revision limit — the same way a human paralegal would iterate on a draft.

---

## Evaluation Results

```
============================================================
  AEGIS EVAL HARNESS — 15 Scenarios
============================================================
  EVAL-001  13.1 · $250  · Item not received
            ✅ expected=FIGHT     got=FIGHT     win=0.85  review=True
  EVAL-002  13.1 · $450  · Item not received
            ✅ expected=FIGHT     got=FIGHT     win=0.85  review=True
  EVAL-003  13.3 · $99   · Item not as described
            ✅ expected=ANY       got=FIGHT     win=0.75  review=True
  EVAL-004  10.4 · $175  · Fraudulent transaction
            ✅ expected=FIGHT     got=FIGHT     win=0.80  review=True
  EVAL-005  13.1 · $320  · Package not delivered
            ✅ expected=FIGHT     got=FIGHT     win=0.85  review=True
  EVAL-006  10.4 · $540  · Fraud claim
            ✅ expected=FIGHT     got=FIGHT     win=0.80  review=True
  EVAL-007  12.6 · $89   · Duplicate processing
            ✅ expected=FIGHT     got=FIGHT     win=0.75  review=True
  EVAL-008  13.7 · $1200 · Cancelled merchandise
            ✅ expected=ANY       got=ACCEPT    win=0.33  review=None
  EVAL-009  13.2 · $850  · Cancelled recurring
            ✅ expected=ANY       got=FIGHT     win=0.70  review=True
  EVAL-010  13.6 · $2200 · Credit not processed
            ✅ expected=ANY       got=FIGHT     win=0.80  review=True
  EVAL-011  10.5 · $5000 · Visa fraud monitoring
            ✅ expected=ESCALATE  got=ESCALATE  win=0.00  review=None
  EVAL-012  10.4 · $7500 · High value fraud
            ✅ expected=ANY       got=FIGHT     win=0.80  review=True
  EVAL-013  13.3 · $130  · Wrong item shipped
            ✅ expected=ANY       got=FIGHT     win=0.75  review=True
  EVAL-014  13.1 · $420  · Delayed delivery claim
            ✅ expected=FIGHT     got=FIGHT     win=0.85  review=True
  EVAL-015  10.4 · $670  · No authorization claim
            ✅ expected=FIGHT     got=FIGHT     win=0.80  review=True
============================================================
  15/15 passed — EVAL PASSED
============================================================
```

---

## Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                        CLIENT / API                          │
│              POST /dispute  {chargeback payload}             │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                   FastAPI (api/main.py)                      │
│              Pydantic schema validation                      │
│              Request routing + error handling                │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│        LangGraph Orchestrator (agents/orchestrator.py)       │
│                                                              │
│  [START]                                                     │
│     → intake_agent                                           │
│     → evidence_collector_agent                               │
│     → strategy_agent                                         │
│     → writer_agent  ←───────────────────────────┐            │
│     → reviewer_agent                            │            │
│          │ review_passed?                       │            │
│          ├── YES → document_generator → END     │            │
│          └── NO  → (revision loop) ─────────────┘            │
│                                                              │
└──────────────────────────────┬───────────────────────────────┘
                               │
        ┌──────────────────────┴──────────────────────┐
        │                                             │
┌───────▼──────────────┐              ┌───────────────▼──────────┐
│  Reason Code         │              │        Groq LLM          │
│  Rules Engine        │              │    (llama-instant)       │
│  data/               │              │    Agent reasoning       │
│  reason_codes.json   │              │    + JSON output         │
└──────────────────────┘              └──────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│              document_generator (tools/)                     │
│         Produces formatted .docx → generated_docs/           │
└──────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                       LangSmith                              │
│   Full trace of every agent run — LLM calls, tool results,   │
│   revision loops, token usage, latency per step              │
└──────────────────────────────────────────────────────────────┘
---

## API Reference

### `POST /dispute`

Submit a chargeback for autonomous defense analysis.

**Request:**
```json
{
  "chargeback_id": "CB-001",
  "merchant_id": "MERCH-001",
  "transaction_id": "TXN-456",
  "amount": 450.00,
  "reason_code": "13.1",
  "reason_description": "Item not received"
}
```

**Response:**
```json
{
  "chargeback_id": "CB-001",
  "verdict": "FIGHT",
  "winability_score": 0.85,
  "strategy_reasoning": "Strong delivery confirmation with carrier scan and customer signature. Evidence package supports a high-confidence defense.",
  "recommended_arguments": [
    "Delivery confirmation and customer signature prove merchandise was received.",
    "Order details provide a clear record of the transaction and fulfillment.",
    "Customer accepted terms and conditions at time of purchase."
  ],
  "review_passed": true,
  "dispute_category": "not_received",
  "urgency": "HIGH",
  "agent_trace": [
    "IntakeAgent: classified as not_received | urgency=HIGH",
    "EvidenceCollector: strength=0.85 | missing=[]",
    "StrategyAgent: verdict=DisputeVerdict.FIGHT | winability=0.85",
    "WriterAgent: drafted response (revision 0)",
    "ReviewerAgent: passed=True | feedback=''"
  ],
  "document_path": "generated_docs/CB-001.docx",
  "escalation_reason": null
}
```

### `GET /dispute/{chargeback_id}/download`

Download the generated `.docx` dispute response — ready for card network submission.

### `GET /health`

Health check.

---

## Supported Reason Codes

| Code | Description | Default Strategy |
|---|---|---|
| 13.1 | Merchandise Not Received | FIGHT with delivery proof |
| 13.3 | Not as Described | FIGHT with product evidence |
| 13.7 | Cancelled Merchandise | ACCEPT unless policy violation |
| 13.2 | Cancelled Recurring | ACCEPT unless prior notice given |
| 13.6 | Credit Not Processed | FIGHT with refund records |
| 10.4 | Fraudulent Transaction | FIGHT with auth + device data |
| 10.5 | Visa Fraud Monitoring | ESCALATE — legal review required |
| 12.6 | Duplicate Processing | FIGHT with transaction records |

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Agent framework | LangGraph | Explicit state machine — inspectable, debuggable, revision loops |
| LLM | Groq (`llama-3.1-8b-instant`) | Fast inference, reliable JSON output |
| Backend | FastAPI + Pydantic v2 | Fully typed, async, automatic OpenAPI docs |
| Document generation | python-docx | Submission-ready `.docx` output |
| Rules engine | JSON reason code rules | Deterministic guardrail on top of LLM reasoning |
| Observability | LangSmith | Full agent trace per dispute |
| Containerization | Docker + docker-compose | One-command local setup |
| Deployment | Railway | Zero-config hosting |
| CI/CD | GitHub Actions | Lint → test → build on every push |
| Code quality | ruff | Zero lint warnings enforced |

---

## Running Locally

```bash
# 1. Clone
git clone https://github.com/GowravSai26/aegis
cd aegis

# 2. Set environment variables
cp .env.example .env
# Add GROQ_API_KEY and LANGCHAIN_API_KEY

# 3. Start everything (API + Postgres + Redis)
docker compose up --build

# 4. Test it
curl -X POST http://localhost:8000/dispute \
  -H "Content-Type: application/json" \
  -d '{
    "chargeback_id": "CB-001",
    "merchant_id": "MERCH-001",
    "transaction_id": "TXN-456",
    "amount": 450.00,
    "reason_code": "13.1",
    "reason_description": "Item not received"
  }'
```

---

## Running Tests

```bash
# Unit tests — mocked, no API calls needed
pytest tests/unit/ -v

# Eval harness — requires running API
python tests/evals/eval_scenarios.py
```

---

## Project Structure

```
aegis/
├── agents/
│   ├── state.py                     # AegisState TypedDict + DisputeVerdict enum
│   ├── orchestrator.py              # LangGraph StateGraph — all 5 agents + edges
│   ├── intake_agent.py              # Dispute classification + urgency
│   ├── evidence_collector_agent.py  # Evidence gathering across 5 tools
│   ├── strategy_agent.py            # FIGHT / ACCEPT / ESCALATE + winability
│   ├── writer_agent.py              # Formal dispute response drafting
│   └── reviewer_agent.py            # Quality review + revision loop
├── api/
│   ├── main.py                      # FastAPI app + CORS
│   ├── schemas.py                   # Pydantic request/response models
│   └── routes/
│       ├── disputes.py              # POST /dispute + GET /dispute/{id}/download
│       └── health.py                # GET /health
├── tools/
│   ├── reason_code_rules.py         # Visa reason code rules engine
│   ├── document_generator.py        # .docx generation
│   └── evidence tools               # order_lookup, delivery_proof, device_fingerprint,
│                                    # auth_history, cardholder_comms
├── data/
│   └── reason_codes.json            # 8 Visa reason codes with evidence requirements
├── tests/
│   ├── unit/                        # Per-agent mocked unit tests (7 tests)
│   └── evals/                       # 15-scenario end-to-end eval harness
├── frontend/                        # UI (WIP)
├── generated_docs/                  # Output .docx files
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## CI/CD

Every push to `main` triggers:

1. **Ruff** — lint + format check
2. **pytest** — 7 unit tests across all 5 agents
3. **Docker build** — confirms image builds cleanly

Railway auto-deploys on every successful push to `main`.

---

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for LLM inference |
| `LANGCHAIN_API_KEY` | LangSmith API key for tracing |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith tracing (`true` / `false`) |
| `LANGCHAIN_PROJECT` | LangSmith project name |

---

## The Name — AEGIS

In Greek mythology, the **aegis** (αἰγίς) was the divine shield — carried by Zeus and Athena into battle. It was said to be so powerful that merely displaying it would strike fear into enemies and protect those behind it.

Merchants face $125 billion in annual chargeback losses — attacked by fraudulent claims, exploited by policy abuse, and lost by default due to lack of resources. AEGIS is that shield. Autonomous. Unbreakable. Always ready.

---

## Author

**Gowrav Sai Veeramallu**  
Agentic AI Engineer · Gen AI

[LinkedIn](https://www.linkedin.com/in/Gowrav-Sai-Veeramallu) · [GitHub](https://github.com/GowravSai26)
```

---

```bash
git add README.md
git commit -m "docs: full README with architecture, evals, and mythology"
git push
```
