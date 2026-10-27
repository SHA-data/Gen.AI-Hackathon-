# Chatbot Module Integration Guide
**Module:** LLM Chatbot Gateway & Chat (`app/chat`)  
**Owner:** Aroon  
**Target Audience:** Sharjeel (NeuralCFO), Aleena (Moonshot Mode), Hackathon Reviewers  
**Document Ref:** `/docs/chat/INTEGRATION.md`  
**Status:** Ready for Integration

---

## 1. Module Overview & Integration Architecture

The Chatbot module acts as the unified conversational gateway, API router, and Next.js Web Shell host for the application.

- **Shared Repository Layout:**
  - Web UI: `/apps/web` (Aroon owns layout, session handling, chat, and Evidence Drawer host; teammates add sub-pages under `/apps/web/cfo` and `/apps/web/moonshot`).
  - Shared Contracts: `/packages/contracts` (Single source of truth for Pydantic models, JSON schemas, and service interfaces).
  - Backend Gateway: `/services/api/app/chat`
  - Core Foundation: `/services/api/app/core` (Auth, config, audit logger, evidence registry).

---

## 2. API Endpoints Owned by Chatbot

| Method | Endpoint | Description | Role / Auth |
| :--- | :--- | :--- | :--- |
| `POST` | `/v1/conversations` | Create a new conversation session | Member, Admin, Owner |
| `GET` | `/v1/conversations/{id}` | Retrieve conversation history | Any (Org Scoped) |
| `POST` | `/v1/conversations/{id}/messages` | Send message and receive SSE event stream | Member, Admin, Owner |
| `POST` | `/v1/documents` | Upload CSV (finance) or PDF/Text (RAG) | Member, Admin, Owner |
| `GET` | `/v1/documents/{id}/status` | Check document ingestion status | Any (Org Scoped) |
| `POST` | `/v1/actions/{id}/approve` | Approve dashboard action proposal | Member (Low), Admin (High) |
| `POST` | `/v1/actions/{id}/reject` | Reject dashboard action proposal | Member, Admin, Owner |
| `GET` | `/v1/citations/{id}` | Resolve evidence lineage for Evidence Drawer | Any (Org Scoped) |
| `GET` | `/v1/memories` | List stored memories for user & org | Any (Org Scoped) |
| `PATCH`| `/v1/memories/{id}` | Update/correct a memory item | Member, Admin, Owner |
| `DELETE`| `/v1/memories/{id}` | Delete a memory item | Member, Admin, Owner |
| `POST` | `/v1/feedback` | Submit thumbs rating & comment | Member, Admin, Owner |
| `POST` | `/v1/stt/transcribe` | Transcribe push-to-talk audio (Could) | Member, Admin, Owner |
| `POST` | `/v1/dev/token` | Mint JWT token for demo users (dev only) | Public in dev |

---

## 3. SSE Event Stream Protocol

Every message turn sent to `POST /v1/conversations/{id}/messages` returns a Server-Sent Events stream (`text/event-stream`).

```
event: tool_start
data: {"tool_name": "finance.run_scenario", "arguments": {...}, "tool_call_id": "call_123"}

event: tool_result
data: {"tool_name": "finance.run_scenario", "tool_call_id": "call_123", "status": "ok", "kind": "normal", "warnings": []}

event: chart
data: {"chart_type": "line", "title": "Runway Forecast", "cases": {"expected": {...}, "best": {...}, "worst": {...}}}

event: citation
data: {"id": "uuid", "target_type": "forecast_point", "target_id": "uuid", "label": "Min Cash Point"}

event: stage
data: {"stage_number": 1, "stage_name": "Intake & Safety", "status": "completed"}

event: token
data: {"delta": "Based on the simulation..."}

event: done
data: {"message_id": "uuid", "decision_run_id": "uuid", "status": "verified", "claims_count": 3}
```

---

## 4. Tool-to-Service Mapping Table

All tools return the standard Part A2 envelope:  
`{"status": "ok|warning|failed", "data": {}, "sources": [], "warnings": [], "run_id": "uuid|null"}`

| Tool Name | Owner | Target Implementation | Backend Toggle Env Var |
| :--- | :--- | :--- | :--- |
| `finance.get_metric` | Sharjeel | `FinanceService.get_metric()` | `FINANCE_BACKEND=fake\|real` |
| `finance.run_scenario` | Sharjeel | `FinanceService.run_scenario()` | `FINANCE_BACKEND=fake\|real` |
| `finance.list_source_rows` | Sharjeel | `FinanceService.list_source_rows()` | `FINANCE_BACKEND=fake\|real` |
| `finance.explain_change` | Sharjeel | `FinanceService.explain_change()` | `FINANCE_BACKEND=fake\|real` |
| `moonshot.run` | Aleena | `MoonshotWorkflow.run()` | `MOONSHOT_BACKEND=fake\|real` |
| `rag.search` | Aroon | `RagRetriever.search()` | Built-in |
| `memory.read` | Aroon | `MemoryStore.read()` | `MEMORY_BACKEND=fake\|meterless` |
| `memory.write` | Aroon | `MemoryStore.propose()` | `MEMORY_BACKEND=fake\|meterless` |
| `dashboard.propose_action` | Aroon | `ActionManager.propose()` | Built-in |
| `web.search` | Aroon | `SearchProvider.search()` | Built-in |

---

## 5. Evidence Registry & Custom Renderers

Each module registers an `EvidenceResolver` with `evidence_registry` in `app/core/evidence.py`:
- **Sharjeel (CFO):** Registers resolvers for `source_row`, `financial_record`, `forecast_run`, `forecast_point`, `finance_assumption`.
- **Aleena (Moonshot):** Registers resolvers for `goal_assumption`, `kb_excerpt`, `strategy_score`, `base_rate`.
- **Aroon (Chat):** Registers resolvers for `document_chunk`, `web_source`.

When a user clicks an evidence badge in the Web Shell, the Evidence Drawer queries `GET /v1/citations/{id}` and renders the verified lineage snippet and metadata.

---

## 6. Database Tables Owned by Chatbot (0300–0399)

The Chatbot owns 18 tables defined in `services/api/migrations/versions/0300_chat_core.py`:
1. `agents`
2. `conversations`
3. `messages` (append-only)
4. `tool_calls` (IDs and decisions, no raw data)
5. `action_proposals`
6. `voice_transcripts`
7. `documents` (`UNIQUE(org_id, content_hash)`)
8. `ingestion_jobs`
9. `document_chunks` (pgvector 1536-dim)
10. `web_sources`
11. `memories`
12. `feedback`
13. `eval_cases`
14. `eval_runs`
15. `eval_results`
16. `dashboards`
17. `dashboard_widgets`
18. `verification_checks`

**Core Tables (Sharjeel 0001–0099):** Consumed via core helpers only (`organizations`, `users`, `memberships`, `audit_logs`, `decision_runs`, `claims`, `evidence_links`).

---

## 7. Environment Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `ENV` | `dev` | Environment mode (`dev`, `test`, `prod`) |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/neuralcfo` | PostgreSQL connection string |
| `JWT_SECRET` | `super-secret-hackathon-key-2026-very-secure-32bytes` | JWT HMAC-SHA256 signing key |
| `FINANCE_BACKEND` | `fake` | Switch between `fake` and `real` finance engine |
| `MOONSHOT_BACKEND` | `fake` | Switch between `fake` and `real` Moonshot workflow |
| `MEMORY_BACKEND` | `fake` | Switch between `fake`, `postgres`, and `meterless` |
| `MODEL_NAME` | `nvidia/nemotron-3-super` | Active LLM model identifier |
| `METERLESS_API_KEY` | *(optional)* | Production API key for Meterless |

---

## 8. Integration Checklist for Sharjeel & Aleena

### For Sharjeel (NeuralCFO):
- [ ] Verify your finance service implements the frozen Part A5 contract in `/packages/contracts/finance.py`.
- [ ] Confirm `POST /v1/finance/scenarios/run` returns three cases: `expected`, `best`, and `worst`.
- [ ] Connect your service to Chatbot by setting `FINANCE_BACKEND=real` and calling `set_finance_service(your_service)`.
- [ ] Place your CFO dashboard pages under `/apps/web/src/app/cfo/`.
- [ ] Register your target resolvers (`source_row`, `forecast_point`, etc.) with `evidence_registry`.

### For Aleena (Moonshot Mode):
- [ ] Verify your workflow implements the protocol in `/packages/contracts/moonshot.py`.
- [ ] Confirm your clarification questions conform to `NeedsInputResult` with tappable options.
- [ ] Connect your workflow to Chatbot by setting `MOONSHOT_BACKEND=real` and calling `set_moonshot_workflow(your_workflow)`.
- [ ] Place your Moonshot strategy pages under `/apps/web/src/app/moonshot/`.
- [ ] Register your target resolvers (`kb_excerpt`, `strategy_score`, etc.) with `evidence_registry`.

---

## 9. One-Command Demo Execution

To run the complete system in standalone demo mode:

```bash
make demo
```

This starts the FastAPI gateway on `http://localhost:8000` with all fake backends active, ready for live testing and demonstration.
