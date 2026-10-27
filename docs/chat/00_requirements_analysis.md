# Requirements Analysis & Verification (Chatbot Gateway + Chat Module)
**Module Owner:** Aroon (LLM Chatbot Gateway & Chat)  
**Document Ref:** `/docs/chat/00_requirements_analysis.md`  
**Master Specification:** *NeuralCFO + Moonshot Mode: Unified Project Documentation v0.1*  
**Date:** October 25, 2026  
**Status:** Step 0 Verification Complete — Awaiting Review

---

## 1. Executive Summary & Module Boundaries

In accordance with Prompt 3 of 3 for the Open Agent Hackathon 2026:
- **Product:** NeuralCFO + Moonshot Mode (Unified Platform)
- **Team Split:**
  - **Sharjeel:** NeuralCFO finance engine (`/services/api/app/cfo`, migrations `0100-0199`)
  - **Aleena:** Moonshot Mode strategy engine (`/services/api/app/moonshot`, migrations `0200-0299`)
  - **Aroon (This Module):** LLM Chatbot gateway + chat (`/services/api/app/chat`, migrations `0300-0399`, Web Shell `/apps/web`, shared provider contracts)
- **Core Principle:** The model understands and explains, tools calculate, code verifies, and every number and quote traces to a source.
- **Strict Boundary Rules:**
  - The LLM **never** directly accesses the database, server secrets, or writes UI/dashboard code.
  - The LLM calls **only registered, typed tools** with server-validated schemas.
  - Every tool and API route enforces `org_id` and role permissions in backend Python code derived exclusively from the authenticated JWT session context (never from user input, query params, or model parameters).
  - Cross-module communication occurs exclusively via typed service interfaces in `/packages/contracts` and HTTP API routes under `/v1`. No internal table imports or cross-module direct database reads.
  - Until Sharjeel publishes the Foundation Kit (`foundation-v1`), Aroon builds against `/packages/contracts`, `FakeFinanceService`, and `FakeMoonshotWorkflow`, without writing core `0001-0099` migrations or duplicating core tables.

---

## 2. Requirements Touching the Chatbot (By Spec Section)

### Section 1: Product Overview & Canonical Demo Story
- **Reference:** PDF §1 (pp. 1–3)
- **Requirement:** The Chatbot serves as the conversational gateway across two modes (`neuralcfo` and `moonshot`):
  - In **CFO Mode**, handle queries regarding historical spend, cash balance, runway, driver explanations, and scenario simulations ("Can we hire two developers if our biggest client pays 30 days late?").
  - In **Moonshot Mode**, handle bold strategic goal exploration ("What bold move could fix this instead?"), forward the goal to `moonshot.run`, collect missing constraints via structured tappable options (max 2 rounds), stream stage execution progress, and render the final ranked report with disclaimer, cash impacts, and skeptic sections.
  - **Hero Demo Journey Requirements:**
    1. Upload CSVs, display the quality report, resolve mapping ambiguities.
    2. View baseline cash position and forecast; alert on cash floor/reserve breach.
    3. Process scenario questions; execute baseline, hire, delay, and combined scenarios via `finance.run_scenario`.
    4. Support deep citation inspection via the Evidence Drawer.
    5. Handle Moonshot goal intake and clarification questions.
    6. Render ranked strategies, failed gate reasons, cash impact with run IDs, skeptic analysis, and weight sensitivity.
    7. Propose dashboard modifications (`add_chart`) via the action lifecycle (propose -> preview -> approve -> apply -> audit).
    8. Export reports with mandatory disclaimers; demonstrate cross-session memory recall in a second session.
- **Non-Goals:** Not an accounting platform, no live bank connections, no autonomous payments or hiring, no formal legal/investment advice, no user simulation / persona imposture, no online fine-tuning on user data.

### Section 5: Scope and MVP Tiers
- **Reference:** PDF §5 (pp. 10–11)
- **Chatbot Tiers:**
  - **Must:** Chat with SSE streaming, message persistence per org/user; router and tool calling; tool-result envelope handling; evidence drawer component and citation resolution (`GET /v1/citations/{id}`); verifier with claim tags (Cited, Computed, Inferred, Commentary); CSV upload forwarding to finance import contract; memory proposal/confirmation with Meterless adapter (+ Postgres fallback).
  - **Should:** Dashboard actions (`add_chart`, `set_date_range`, `add_kpi`, `reorder_widget`, `create_report`) with approval flow; Document RAG (`POST /v1/documents`, chunking ~500 tokens with overlap + page extraction, pgvector hybrid search, org_id pre-filtering); 20-question evaluation runner (`eval_cases`, `eval_runs`, `eval_results`); thumbs feedback (`POST /v1/feedback`).
  - **Could:** Voice input via push-to-talk (`POST /v1/stt/transcribe`); web search for context (`web.search`, marked untrusted); extra dashboard actions.
  - **Won't:** Fine-tuning or model self-training; live bank sync; delete or share actions; text-to-speech; LLM writing UI code.

### Section 6: Unified Architecture & Architectural Invariants
- **Reference:** PDF §6 (p. 12)
- **Requirement:** 
  - Web UI (Next.js 14+ / React) communicates over HTTPS and SSE.
  - FastAPI Gateway handles JWT authentication, org scoping, rate limiting, request IDs, and append-only audit logging.
  - Chatbot core components: `router` -> `agent runtime` (`neuralcfo` | `moonshot`) -> `tool registry` -> `guardrails` -> `verifier` -> `response composer`.
  - External adapters with fakes: `LLMProvider`, `MemoryStore`, `EmbeddingProvider`, `SttProvider`, `SearchProvider`.
  - All tenant data separated by `org_id`.
  - Failures are explicit: result statuses are `verified | warning | unverified | failed`.

### Section 7.1: Chat Request Path
- **Reference:** PDF §7.1 (pp. 13–14)
- **Requirement:** 6-step request execution pipeline:
  1. **Receive:** Authenticate bearer JWT, resolve `(user_id, org_id, role)`, assign `request_id`, persist incoming user message in `messages`.
  2. **Route:** Classify intent and select active agent (`neuralcfo` or `moonshot`) and its permitted tool subset. Rule-based fast routing first, LLM routing fallback.
  3. **Retrieve and Calculate:** Agent tool-calling loop executes registered tools (`finance.*`, `moonshot.run`, `rag.search`, `memory.*`, `dashboard.propose_action`).
  4. **Verify:** Deterministic verifier executes checks (V1–V9) against tool outputs; guardrails evaluate action risk and policy bounds.
  5. **Respond:** Compose and stream response over SSE (`token`, `tool_start`, `tool_result`, `citation`, `chart`, `action_proposal`, `stage`, `error`, `done`).
  6. **Learn:** Propose memory writes for explicit user confirmation; write audit log entry (IDs and decisions only); record feedback.

### Section 7.2: Intent Routing Table
- **Reference:** PDF §7.2 (p. 14)
- **Requirement:**
  - Spend / revenue queries -> `finance.get_metric`
  - Period change analysis ("Why did cash drop?") -> `finance.explain_change`
  - Hiring / late payment scenarios -> `finance.run_scenario`
  - Company policy / plan questions -> `rag.search`
  - Bold strategic goal -> `moonshot.run`
  - Modify dashboard -> `dashboard.propose_action`
  - Remember facts / assumptions -> `memory.write` (propose only)
  - Destructive requests ("Delete all my transactions") -> Refuse or enforce strict policy guardrail.

### Section 7.5: Seam Between Modes
- **Reference:** PDF §7.5 (p. 16)
- **Requirement:**
  - Chat interacts with Moonshot Mode via **one tool**: `moonshot.run`.
  - `moonshot.run` streams execution stages (Card 1 through Card 6) surfaced to the client as SSE `stage` events.
  - If Moonshot requires user clarification, `moonshot.run` returns a `needs_input` result containing structured clarification questions and tappable options (max 2 rounds).
  - Clarification responses are delivered back via `POST /v1/moonshot/requests/{id}/answers`.
  - Final output is a structured Moonshot Report; Chatbot renders it verbatim with citations, run IDs, and mandatory disclaimer without modifying figures or rankings.
  - CFO flags (e.g., cash floor breach) can pre-populate Moonshot intake.

### Section 10: Chatbot Specification
- **Reference:** PDF §10 (pp. 24–27)
- **10.1 Features & Tiers:** Streaming chat, history, upload routing (CSV -> finance import, documents -> RAG), memory management.
- **10.2 Tool Registry:**
  - Unified envelope for all tools:
    `{"status": "ok|warning|failed", "data": {}, "sources": [], "warnings": [], "run_id": "uuid|null"}`
  - Registered tools: `finance.get_metric`, `finance.run_scenario`, `finance.list_source_rows`, `finance.explain_change`, `moonshot.run`, `rag.search`, `memory.read`, `memory.write`, `dashboard.propose_action`, `web.search`.
  - If a tool returns `warning` or `failed`, agent explains what is missing (e.g., missing salary, start date) rather than guessing.
- **10.3 Endpoints & SSE Events:**
  - `POST /v1/conversations`, `GET /v1/conversations/{id}`
  - `POST /v1/conversations/{id}/messages` (SSE stream)
  - `POST /v1/documents`, `GET /v1/documents/{id}/status`
  - `GET /v1/citations/{id}`
  - `POST /v1/actions/{id}/approve`, `POST /v1/actions/{id}/reject`
  - `GET /v1/memories`, `PATCH /v1/memories/{id}`, `DELETE /v1/memories/{id}`
  - `POST /v1/feedback`
  - SSE events: `token`, `tool_start`, `tool_result`, `citation`, `chart`, `action_proposal`, `stage`, `error`, `done`.
- **10.4 Dashboard Action Lifecycle:**
  - States: `proposed` -> `validated` -> (`awaiting_approval` | `auto-apply` if low risk & opted-in) -> `approved` -> `applied`.
  - Failure/rejection states: `rejected`, `expired`, `failed`.
  - Risk categorization:
    - *Low:* `set_date_range`, `add_chart`, `add_kpi`, `reorder_widget` (optional confirmation).
    - *Medium:* `create_report` (preview required).
    - *High:* `update_assumption`, `import_transactions` (always confirm; admin/owner required).
    - *Refused:* `delete_*`, `share_*` (not supported in v1).
- **10.5 Retrieval Dispatch:**
  - Policy/prose -> Document RAG (pgvector, ~500 tokens, overlap, page number metadata, org_id pre-filter).
  - Financial figures -> Structured finance queries/engine (RAG is not a calculator).
  - Strategic moves -> Curated Moonshot cards (handled by Moonshot engine).
  - External trends -> Web search (context only, untrusted, dated URL).

### Section 11: Data Model & Chatbot Table Ownership
- **Reference:** PDF §11 (pp. 27–30)
- **Conventions:** PostgreSQL 16 + pgvector, UUID PKs (`gen_random_uuid()`), `org_id UUID NOT NULL` indexed first on all tenant tables, NUMERIC(18,2) money, explicit dates, status CHECK constraints, append-only audit logging.
- **Chatbot Owned Tables (Migrations 0300–0399):**
  1. `agents` (id, key, name, description, system_prompt, allowed_tools)
  2. `conversations` (id, org_id, user_id, agent_id, title, created_at, updated_at)
  3. `messages` (id, org_id, conversation_id, sender, content, token_count, created_at) — append-only
  4. `tool_calls` (id, org_id, message_id, decision_run_id, tool_name, arguments_jsonb, status, duration_ms, result_status, created_at) — no raw financial dumps
  5. `action_proposals` (id, org_id, conversation_id, action_type, payload_jsonb, risk_level, status, approved_by_user_id, executed_at, created_at)
  6. `voice_transcripts` (id, org_id, conversation_id, audio_duration_sec, raw_transcript, edited_transcript, created_at)
  7. `documents` (id, org_id, filename, file_size_bytes, mime_type, content_hash, storage_path, created_at, UNIQUE(org_id, content_hash))
  8. `ingestion_jobs` (id, org_id, document_id, status, error_message, progress_pct, created_at, updated_at)
  9. `document_chunks` (id, org_id, document_id, chunk_index, page_number, content, token_count, embedding vector(1536), created_at)
  10. `web_sources` (id, org_id, url, title, snippet, retrieved_at)
  11. `memories` (id, org_id, user_id, category, key, value, status, source_message_id, created_at, updated_at)
  12. `feedback` (id, org_id, user_id, message_id, score, comment, eval_case_id, created_at)
  13. `eval_cases` (id, category, question, expected_tools, expected_facts, expected_risk, active)
  14. `eval_runs` (id, model_name, git_commit, started_at, completed_at, summary_metrics)
  15. `eval_results` (id, eval_run_id, eval_case_id, tool_choice_score, fact_score, citation_score, latency_ms, passed)
  16. `dashboards` (id, org_id, title, layout_jsonb, created_at, updated_at)
  17. `dashboard_widgets` (id, org_id, dashboard_id, widget_type, config_jsonb, position_idx, created_at)
  18. `verification_checks` (id, org_id, decision_run_id, message_id, check_type, status, details_jsonb, created_at)
- **Core Tables Consumed via Core Helpers (Never Re-created):**
  `organizations`, `users`, `memberships`, `audit_logs`, `decision_runs`, `claims`, `evidence_links`.
  Target resolvers registered for `document_chunk` and `web_source` in `app/core/evidence.py`.

### Section 12: Evidence, Claims, and Verification
- **Reference:** PDF §12 (pp. 30–31)
- **12.1 Claim Tags & Targets:**
  - Tags: `cited`, `computed`, `inferred`, `commentary`.
  - Targets: Exactly one target per `evidence_link` row (`source_row`, `financial_record`, `forecast_run`, `forecast_point`, `finance_assumption`, `goal_assumption`, `document_chunk`, `web_source`, `kb_excerpt`, `strategy_score`, `base_rate`).
  - Untraceable remarks must be tagged `commentary`, never presented as fact.
- **12.2 Verifier Checks (V1–V9):**
  - **V1 Numbers:** Every number in answer must match a tool result from the current turn; otherwise flag as `unverified` and log.
  - **V2 Quotes:** Every quote must match stored excerpt hash and be $\le 300$ characters. Remove quotes failing check. Paraphrases never in quotation marks.
  - **V3 Citations:** Every referenced source exists and belongs to the caller's `org_id`.
  - **V4 Scenarios:** Scenarios share the baseline; only declared levers modified.
  - **V5 Units:** Currency code, signs, dates, and forecast periods are consistent.
  - **V6 Gates:** Disqualified strategies never appear in ranked recommendations.
  - **V7 Tags:** Every claim has a valid tag and at least one verifiable evidence link.
  - **V8 Disclaimer:** Moonshot and forecast outputs contain mandatory decision-support disclaimer.
  - **V9 Regenerate Once:** On verification failure, trigger one regeneration pass; if still failing, emit clear caveat and mark `unverified`.
- **12.3 Moonshot Report Presentation:** Render the 9 standard sections without altering figures or rankings.

### Section 13: Security and Privacy
- **Reference:** PDF §13 (pp. 31–32)
- **Authentication & RBAC:** Bearer JWT verified on every route; resolve `(user_id, org_id, role)`.
  - Roles: `viewer` (read-only), `member` (read + chat + scenario run), `admin` / `owner` (full + high-risk approvals).
- **Prompt Injection Defense:** External texts (documents, CSV cells, web snippets, KB cards) treated as untrusted data, never instructions. Tool authorization governed strictly by server-side policy.
- **Upload Safety:** File type and payload size limits, local/private storage, no public execution.
- **Zero Secrets Leakage:** Secrets stored in environment only; never present in prompts, logs, or UI responses.
- **Audit Logging:** Record event IDs and decisions only — no financial records or sensitive document text in audit logs.
- **Memory Privacy:** Memories are scoped per user and per org, viewable, correctable, deletable; never used for LLM fine-tuning.

### Section 14: Sponsor Technologies & Event Requirements
- **Reference:** PDF §14 (pp. 33–34)
- **Meterless:** Planned for `MemoryStore` and execution tracing. Real adapter + labeled Postgres fallback with identical protocol. Smoke test: write, read, trace one memory item.
- **NVIDIA / LLMProvider:** Swappable model interface (`LLMProvider`) supporting streaming and schema-validated tool calling. Model name configurable via env var. Benchmark harness comparing candidate models on reliability, latency, and cost.
- **Zetaris:** Owned by Sharjeel (`FinanceDataSource`). Chat consumes only through `finance.*` tools.
- **Cursor vs Antigravity:** PDF notes conflict F1. Handled by modular code structure and documented rules verification.

### Section 15: Testing and Evaluation
- **Reference:** PDF §15 (pp. 34–36)
- **Test Levels:** Unit tests, agent & tool tests, security & isolation tests, integration tests, contract tests against `/packages/contracts`, demo rehearsal (3 clean runs on fresh database).
- **Evaluation Set:** 20-question canonical test suite covering finance (1–5, 10, 11, 15), dashboard actions (6, 7), documents (8, 9), strategy (12, 14, 16), web research (13), memory (17, 18), and safety (19, 20). Plus Moonshot integration checks M1–M10.

### Section 16 & 17: Build Plan & Risks
- **Reference:** PDF §16–17 (pp. 37–39)
- **Build Plan Sequence:** Foundation & adapters with fakes -> Core chat & streaming -> Tool registry & agent loop -> Verifier & evidence drawer -> Moonshot integration -> Memory & evaluation -> Demo hardening.
- **Risks & Mitigations:** Contract drift (single frozen contract), hallucinated arithmetic (tool-only calculations), cross-org leakage (code-level tenant filters & tests), prompt injection (data framing & policy enforcement).

---

## 3. Comprehensive Traceability Matrix

| Req Ref | Description | Planned Component | Planned Test File |
| :--- | :--- | :--- | :--- |
| **§1, §7.1** | Conversational gateway with SSE streaming | `app/chat/api/router.py`, `app/chat/runtime/streamer.py` | `tests/chat/test_streaming.py` |
| **§1, §7.5** | Moonshot intake & clarification options | `app/chat/agents/moonshot_agent.py`, `app/chat/tools/moonshot_tool.py` | `tests/chat/test_moonshot_integration.py` |
| **§1, §10.4** | Dashboard action proposal & approval | `app/chat/actions/action_manager.py`, `app/chat/api/actions.py` | `tests/chat/test_dashboard_actions.py` |
| **§1, §10.1** | Cross-session memory persistence | `app/chat/memory/store.py`, `app/chat/memory/meterless_store.py` | `tests/chat/test_memory.py` |
| **§6, §13** | JWT authentication & RBAC enforcement | `app/core/auth.py`, `app/chat/guardrails/rbac.py` | `tests/chat/test_security_rbac.py` |
| **§6, §13** | Strict multi-tenant `org_id` isolation | `app/core/org.py`, SQL repository queries | `tests/chat/test_org_isolation.py` |
| **§7.1, §7.2** | Intent routing (rules + LLM fallback) | `app/chat/router/intent_router.py` | `tests/chat/test_router.py` |
| **§7.1, B2.1** | Swappable LLMProvider protocol & Fake | `app/chat/adapters/llm/provider.py`, `fake_llm.py` | `tests/chat/test_llm_provider.py` |
| **§10.2** | Tool Registry & unified envelope | `app/chat/tools/registry.py`, `app/core/envelope.py` | `tests/chat/test_tool_registry.py` |
| **§10.2, A5** | Finance tool wrappers (`finance.*`) | `app/chat/tools/finance_tools.py` | `tests/chat/test_finance_tools.py` |
| **§10.3** | REST API endpoints (`/v1/conversations`, etc.) | `app/chat/api/conversations.py` | `tests/chat/test_api_conversations.py` |
| **§10.5, §11** | Document ingestion & RAG hybrid search | `app/chat/rag/ingestion.py`, `app/chat/rag/retriever.py` | `tests/chat/test_document_rag.py` |
| **§11.2** | Chat database schema (0300–0399 migrations) | `services/api/migrations/versions/0300_chat_core.py` | `tests/chat/test_schema_integrity.py` |
| **§12.1, §12.2** | Verifier engine checks (V1–V9) | `app/chat/verifier/verifier.py` | `tests/chat/test_verifier.py` |
| **§12.1, A3** | Evidence Drawer resolution (`/v1/citations`) | `app/chat/api/citations.py`, `app/core/evidence.py` | `tests/chat/test_citations.py` |
| **§13** | Prompt injection defense in documents/cards | `app/chat/guardrails/injection.py` | `tests/chat/test_prompt_injection.py` |
| **§13** | Logging IDs & decisions without raw content | `app/core/audit.py`, `app/chat/runtime/logger.py` | `tests/chat/test_audit_logging.py` |
| **§14** | Meterless MemoryStore adapter & fake | `app/chat/adapters/memory/meterless.py` | `tests/chat/test_meterless_memory.py` |
| **§15.2** | 20-Question Evaluation Runner | `app/chat/eval/runner.py`, `eval_cases` | `tests/chat/test_eval_runner.py` |
| **§15.2** | Moonshot integration test suite (M1–M10) | `tests/integration/test_moonshot_suite.py` | `tests/integration/test_moonshot_suite.py` |

---

## 4. PDF Findings (Conflicts & Gaps F1–F16) and Resolution

| Finding ID | Severity | PDF Finding Summary | Impact on Chatbot | Part A / Part B Resolution |
| :--- | :--- | :--- | :--- | :--- |
| **F1** | High | Rules & Dev Tool unresolved: Event notes mandate Cursor; other docs mention Antigravity. Models/APIs allowed marked unknown. | Chat development environment, tool calling, and LLMProvider compatibility. | **[OPEN] in D1/D2.** Part B provides a modular `LLMProvider` protocol with configurable model name and benchmark runner. Code adheres to standard CLI/Docker/Next.js/FastAPI stack runnable from any IDE. |
| **F2** | High | Three incompatible CFO engine contracts across source docs. | Chat tools `finance.run_scenario` and `finance.get_metric` parameterization. | **Resolved by Part A5:** Single frozen contract v1. Standard `ScenarioRunRequest`, weekly cash series, 3 cases (`expected`, `best`, `worst`), and lever registry. |
| **F3** | High | Three overlapping data models, conflicting tenant keys (`company_id` vs `org_id`), and duplicate tables. | Chat tables, conversation scoping, evidence tables. | **Resolved by Part A2, A3:** Single Postgres schema, UUID PKs, `org_id` everywhere. Chat migrations live exclusively in `0300–0399`. Core tables used for audit, claims, evidence links. |
| **F4** | High | Moonshot scoring conflict between MS (LLM Fit) and MP (rules/bands). | Rendering of strategy scores in chat. | **Resolved by MP wins (Part A):** Chatbot receives structured report from `moonshot.run` and renders it verbatim without modifying scores or rankings. |
| **F5** | High | Scope exceeds hackathon window (60 tables, voice, web, etc.). | Scope explosion across chat features. | **Resolved by Part B2:** Strict prioritization. Must (core chat, streaming, tool loop, verifier, memory) built first. Should (RAG, actions, evals) secondary. Voice/Web in Could. |
| **F6** | Med | Two Moonshot designs: free tool loop vs gated 6-card pipeline. | Chat agent orchestration and tool registry. | **Resolved by Part B2.7:** Chat Moonshot agent calls **exactly one tool**: `moonshot.run`. No free-form card execution from chat. Web search is context only, never strategy generation. |
| **F7** | Med | Orchestration framework undecided (LangGraph vs Meterless Swarms vs custom loop). | Agent runtime architecture and latency. | **Resolved by Part B1, D4:** Custom typed Python tool-calling loop. Deterministic, inspectable, zero external framework overhead. |
| **F8** | Med | Sponsor roles inconsistent & unverified. | Meterless and Zetaris integration boundaries. | **Resolved by Part A1, B0, B2.10:** Zetaris handled entirely by Sharjeel in CFO. Meterless encapsulated in `MemoryStore` with Postgres fallback. Real adapter + fake provided. |
| **F9** | Med | Scenario vs case terminology confusion. | Chat scenario display and chart event generation. | **Resolved by Part A5:** A scenario represents changed business levers; each scenario run evaluates three distinct cases (`expected`, `best`, `worst`). |
| **F10** | Med | Granularity & cash floor representation. | Unit verifier (V5) and scenario summary text. | **Resolved by Part A5:** Weekly forecast series is canonical. Cash floor checks both currency reserve and runway weeks. |
| **F11** | Med | Evidence modeled three ways across documents. | Evidence drawer API (`/v1/citations/{id}`) and claim validation. | **Resolved by Part A3, §12.1:** Unified core `claims` and `evidence_links` (each link points to exactly one target UUID). Chat registers resolvers for `document_chunk` and `web_source`. |
| **F12** | Med | Ownership gaps (dashboard UI, config API, QA, card curation). | Dashboard actions and web shell ownership. | **Resolved by Part A1, B0:** Aroon owns the Next.js web shell, chat UI, dashboard action state machine, and evidence drawer host. Sharjeel and Aleena contribute sub-pages and card curators. |
| **F13** | Low | Naming clash: `assumption` (Moonshot) vs `BusinessAssumption` (CFO). | Memory write proposals and evidence target resolution. | **Resolved by Part A3:** Explicitly separated as `goal_assumptions` (Moonshot) and `finance_assumptions` (CFO). |
| **F14** | Low | Retrieval described three ways (tags vs pgvector vs semantic score). | Strategy card retrieval vs document RAG. | **Resolved by Part B2.8, B2.13:** Two independent paths: Moonshot owns card retrieval (tags/keywords/re-rank); Chatbot owns user document RAG using pgvector hybrid search with pre-filtering by `org_id`. |
| **F15** | Low | Unverified base rates in Moonshot documentation. | Citations rendered in chat reports. | **Resolved by Part A8:** Unverified base rates excluded from demo data unless backed by verifiable sources. |
| **F16** | Info | Architecture strengths to preserve (hard rules, claim tags, deterministic engine). | Verifier engine and system design. | **Preserved:** All 12 hard rules and checks V1–V9 enforced deterministically in chat backend. |

---

## 5. Architectural Assumptions & Status Classification

| Assumption / Decision Item | Category | Status Tag | Description & Decision Basis |
| :--- | :--- | :--- | :--- |
| **Allowed Models & Endpoints** | Environment | `[OPEN, D1]` | Model selection must be verified against Hackathon Rules. Implemented via swappable `LLMProvider` behind an environment variable (`MODEL_NAME`). |
| **Development Tooling** | Environment | `[OPEN, D2]` | Event notes mention Cursor requirement while earlier specs used Antigravity. Project is structured portably so development runs cleanly across either tool. |
| **Application Tech Stack** | Architecture | `[DECIDED, D3]` | FastAPI (Python 3.12), PostgreSQL 16 + pgvector, Redis, Next.js 14+ (TypeScript). Docker Compose deployment. |
| **Agent Orchestration** | Architecture | `[DECIDED, D4]` | Custom typed Python tool-calling loop in `app/chat/runtime/loop.py`. No LangGraph or Swarms dependencies. |
| **Finance Engine Contract** | Interface | `[DECIDED, D5]` | Single frozen contract v1 as detailed in Part A5. Weekly series, three cases, fixed lever registry. |
| **Moonshot Interface in Chat** | Interface | `[DECIDED, F6]` | Single tool `moonshot.run`. Stage progression emitted as SSE `stage` events. Structured `needs_input` returned for clarification questions. |
| **Moonshot Needs-Input Shape** | Interface | `[PROPOSED, D13]` | Tappable options schema: `{"question_id": str, "prompt": str, "options": list[str], "allows_custom": bool}`. |
| **Evidence & Claim Data Model** | Data Model | `[DECIDED, F11]` | Core `claims` and `evidence_links` tables. `evidence_links` contains `target_type` and `target_id`. No duplicate chat evidence tables. |
| **Chatbot Migration Range** | Data Model | `[DECIDED, A3]` | Migrations strictly numbered `0300–0399`. Core tables (`0001–0099`) referenced by foreign key only after `foundation-v1` tag. |
| **Meterless Integration** | Integration | `[PROPOSED, D14]` | `MeterlessMemoryStore` implementing `MemoryStore` protocol. Backed by `PostgresMemoryStore` fake/fallback until official credentials/SDK are verified. |
| **Zetaris Integration Boundary** | Integration | `[DECIDED, F8]` | Sharjeel owns Zetaris integration in NeuralCFO. Chat accesses Zetaris data exclusively via `finance.get_metric` and `finance.list_source_rows`. |
| **Verifier Invariants (V1–V9)** | Verification | `[DECIDED, §12.2]` | Deterministic checks run post-turn. Any number not traceable to a current-turn tool result is tagged `unverified`. One regeneration pass allowed (V9). |
| **Dashboard Action Security** | Security | `[DECIDED, §10.4]` | Model only proposes typed action payloads. High-risk actions (`update_assumption`, `import_transactions`) strictly require human admin/owner approval. |
| **Evaluation Question Suite** | Evaluation | `[PROPOSED, §15.2]` | Canonical 20-question suite drafted from CH2 §9 categories, to be updated if the user provides the verbatim source list. |

---

## 6. Verification of Binding Principles

1. **Model Understands, Tools Calculate, Code Verifies:**
   - The LLM receives zero arithmetic responsibilities. All cash balances, runways, scenarios, and scores are derived by `finance.*` and `moonshot.run`.
   - The verifier (`V1`) scans final textual responses against extracted numeric floats/integers from tool results of the identical turn.
2. **Strict Multi-Tenancy & Data Security:**
   - Client and model outputs cannot dictate `org_id`.
   - All tool functions receive `org_id` directly from `AuthContext` injected by FastAPI dependencies.
3. **External Service Isolation:**
   - Standalone testing is guaranteed via `FakeLLMProvider`, `FakeFinanceService`, `FakeMoonshotWorkflow`, and `FakeMemoryStore`.
4. **Idempotency & Auditing:**
   - Audit logging occurs on every tool invocation, action state transition, and document upload using `app/core/audit.py`.
   - Document uploads require `Idempotency-Key` and enforce `UNIQUE(org_id, content_hash)`.

---
*End of Requirements Analysis — Ready for Step 0 Verification Review.*
