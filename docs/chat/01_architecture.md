# Chatbot Gateway & Chat Module Architecture Specification
**Module:** LLM Chatbot Gateway & Chat (`app/chat`)  
**Owner:** Aroon  
**Document Ref:** `/docs/chat/01_architecture.md`  
**Master Spec:** *NeuralCFO + Moonshot Mode: Unified Project Documentation v0.1*  
**Status:** Approved for Implementation

---

## 1. Module Structure & Boundaries

The Chatbot module lives under `/services/api/app/chat` within the unified monolith repository. It provides the conversation gateway, intent routing, agent execution runtime, deterministic verifier, and the Next.js Web Shell (`/apps/web`).

```
services/api/app/chat/
├── __init__.py
├── api/                   # FastAPI route handlers
│   ├── __init__.py
│   ├── router.py          # Chatbot main API router (/v1 prefix)
│   ├── conversations.py   # POST /v1/conversations, GET /v1/conversations/{id}
│   ├── messages.py        # POST /v1/conversations/{id}/messages (SSE stream)
│   ├── documents.py       # POST /v1/documents, GET /v1/documents/{id}/status
│   ├── actions.py         # POST /v1/actions/{id}/approve, /reject
│   ├── memories.py        # GET, PATCH, DELETE /v1/memories
│   ├── citations.py       # GET /v1/citations/{id}
│   ├── feedback.py        # POST /v1/feedback
│   └── stt.py             # POST /v1/stt/transcribe (Could)
├── router/                # Intent classification & agent dispatch
│   ├── __init__.py
│   ├── intent_router.py   # Fast rule-based + LLM fallback router
│   └── rules.py           # Precompiled regex & keyword routing tables
├── agents/                # Agent definitions & system prompts
│   ├── __init__.py
│   ├── base.py            # BaseAgent abstract definition
│   ├── neuralcfo.py       # NeuralCFO Agent (finance focus)
│   └── moonshot.py        # Moonshot Agent (strategic goals)
├── tools/                 # Tool registry & wrappers
│   ├── __init__.py
│   ├── registry.py        # ToolRegistry (schema validation, timeout, RBAC)
│   ├── finance.py         # Wrappers for finance.* tools (via FinanceService)
│   ├── moonshot.py        # Wrapper for moonshot.run (via MoonshotWorkflow)
│   ├── rag.py             # Wrapper for rag.search
│   ├── memory.py          # Wrappers for memory.read, memory.write
│   ├── action.py          # Wrapper for dashboard.propose_action
│   └── search.py          # Wrapper for web.search (Could)
├── runtime/               # Agent loop & execution engine
│   ├── __init__.py
│   ├── loop.py            # Typed Python tool loop (max iterations, timeout)
│   ├── streamer.py        # SSE event streaming generator & formatter
│   └── context.py         # ExecutionContext (auth, decision_run, traces)
├── guardrails/            # Security & safety barriers
│   ├── __init__.py
│   ├── rbac.py            # Role permission validator
│   ├── injection.py       # Prompt injection data sanitzer
│   └── bounds.py          # Policy boundary checks (no autonomous hiring/money)
├── verifier/              # Deterministic post-turn verification (V1-V9)
│   ├── __init__.py
│   ├── engine.py          # VerifierEngine orchestrating V1-V9
│   ├── checks.py          # Individual check implementations
│   └── claim_tagger.py    # Tagging cited, computed, inferred, commentary
├── composer/              # Response composition & rendering
│   ├── __init__.py
│   ├── composer.py        # Merges tool outputs, citations, and verifier flags
│   └── moonshot_render.py # Renders Moonshot 9-section report verbatim
├── memory/                # Memory management & integration
│   ├── __init__.py
│   ├── manager.py         # Memory lifecycle & assumption bridge
│   ├── postgres_store.py  # PostgreSQL memory backend
│   └── meterless_store.py # Meterless memory adapter + fake
├── rag/                   # Document ingestion & vector retrieval
│   ├── __init__.py
│   ├── ingestion.py       # PDF/Text parser, chunker (~500 tokens), page tracking
│   ├── store.py           # pgvector chunk storage & indexing
│   └── retriever.py       # Hybrid vector + keyword search with org_id pre-filter
├── actions/               # Dashboard action state machine
│   ├── __init__.py
│   ├── manager.py         # Action proposal, validation, lifecycle
│   ├── schemas.py         # Typed schemas for low/medium/high actions
│   └── handlers.py        # Execution handlers for approved actions
├── adapters/              # External service adapters
│   ├── __init__.py
│   ├── llm/               # LLMProvider implementations
│   │   ├── protocol.py    # LLMProvider protocol
│   │   ├── fake.py        # FakeLLMProvider
│   │   └── openai_compat.py # OpenAI/NVIDIA compatible adapter
│   ├── embeddings/        # EmbeddingProvider (protocol + fake + real)
│   ├── stt/               # SttProvider (protocol + fake)
│   └── search/            # SearchProvider (protocol + fake)
└── schemas/               # Chat-specific Pydantic schemas
    ├── __init__.py
    ├── conversation.py
    ├── message.py
    ├── sse.py
    └── action.py
```

---

## 2. Request Execution Path & Lifecycle

Following PDF §7.1 and §7.2, each user message undergoes a strict 6-stage lifecycle:

```
[User Request]
       │
       ▼
1. RECEIVE ────────► Authenticate Bearer JWT -> get_auth_context() -> (user_id, org_id, role)
       │             Assign request_id; create decision_run(kind='chat')
       │             Persist message to `messages` (append-only)
       ▼
2. ROUTE ──────────► Rule-based regex match on message content
       │             Fallback to LLM intent classifier
       │             Select Agent (neuralcfo | moonshot) and ALLOWED tool subset
       ▼
3. RETRIEVE & ─────► Enter Typed Tool Loop:
   CALCULATE         • Model predicts tool calls with arguments
                     • ToolRegistry validates arguments against JSON Schema
                     • Injects org_id and user_id from auth context (never from LLM)
                     • Enforces RBAC permissions and execution timeout
                     • Executes tool (`finance.*`, `moonshot.run`, `rag.search`, etc.)
                     • Records `tool_calls` audit row (IDs and decisions, no raw data)
                     • Returns standardized A2 tool envelope
                     • Loop repeats until final answer or max iterations (default: 5)
       ▼
4. VERIFY ─────────► VerifierEngine runs checks V1-V9 on candidate response:
                     • V1 Numbers: every number traces to a tool result of current turn
                     • V2 Quotes: excerpt hash match, length <= 300 chars
                     • V3 Citations: sources exist and belong to caller's org_id
                     • V4 Scenarios: identical baseline, declared levers only
                     • V5 Units: currency, signs, and dates consistent
                     • V6 Gates: failed strategies never in ranked list
                     • V7 Tags: every claim has tag (cited/computed/inferred/commentary)
                     • V8 Disclaimer: mandatory decision-support disclaimer present
                     • V9 Regenerate Once: single retry on failure; else attach caveat
       ▼
5. RESPOND ────────► Stream SSE events to client:
                     token | tool_start | tool_result | citation | chart |
                     action_proposal | stage | error | done
       ▼
6. LEARN ──────────► Propose memory writes if new persistent facts detected (user confirms)
                     Log final audit record; capture feedback hooks
```

---

## 3. Agent Runtime: Custom Typed Tool Loop (No Heavyweight Framework)

Per Decision D4 and PDF §6:
- The agent loop is a deterministic, typed Python generator `AgentRuntimeLoop`.
- **Iteration Limits:** Maximum 5 iterations per turn. If max iterations exceeded, returns a structured error and a graceful fallback summary.
- **Timeout Limits:** Configurable per tool (default 10s; 30s for `moonshot.run`). Overall turn timeout: 60s.
- **State Maintenance:** The loop maintains an in-memory message list for the turn, injecting tool results as system/tool role messages following the standard OpenAI-compatible format.
- **Error Handling:** When a tool fails or returns a `warning`, the agent does **not** hallucinate or guess numbers; it directly informs the user what data is missing or what failed.

---

## 4. Tool Registry Specification

Every tool registered in `ToolRegistry` conforms strictly to:
- **Name:** Hierarchical namespace (`finance.<action>`, `moonshot.run`, `rag.search`, `memory.<action>`, `dashboard.propose_action`, `web.search`).
- **Input Schema:** Typed Pydantic model converted to JSON Schema.
- **Risk Level:** `LOW`, `MEDIUM`, `HIGH`.
- **Allowed Roles:** Subset of `["viewer", "member", "admin", "owner"]`.
- **Timeout:** Seconds before cancellation.
- **Org-Scoping:** `org_id` is automatically injected from FastAPI `AuthContext`.
- **Return Envelope (Part A2):**
  ```json
  {
    "status": "ok | warning | failed",
    "data": {},
    "sources": [],
    "warnings": [],
    "run_id": "uuid | null"
  }
  ```

### Tool Inventory Table:
| Tool Name | Owner Module | Service Provider | Risk | Minimum Role | Timeout | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `finance.get_metric` | CFO (Sharjeel) | `FinanceService` | LOW | viewer | 10s | Retrieve revenue, cash, burn, expenses with source rows |
| `finance.run_scenario` | CFO (Sharjeel) | `FinanceService` | LOW | member | 15s | Run A5 scenario contract against baseline (3 cases) |
| `finance.list_source_rows` | CFO (Sharjeel) | `FinanceService` | LOW | viewer | 10s | Get underlying raw rows behind a calculated figure |
| `finance.explain_change` | CFO (Sharjeel) | `FinanceService` | LOW | viewer | 10s | Period comparison & driver decomposition |
| `moonshot.run` | Moonshot (Aleena) | `MoonshotWorkflow`| LOW | member | 30s | Run 6-card pipeline or return `needs_input` |
| `rag.search` | Chat (Aroon) | `RagRetriever` | LOW | viewer | 5s | Hybrid semantic search over uploaded org documents |
| `memory.read` | Chat (Aroon) | `MemoryStore` | LOW | viewer | 5s | Read stored facts/assumptions for user & org |
| `memory.write` | Chat (Aroon) | `MemoryStore` | MEDIUM | member | 5s | Propose a fact/assumption for user confirmation |
| `dashboard.propose_action` | Chat (Aroon) | `ActionManager` | LOW-HIGH | member | 5s | Propose dashboard UI change with preview |
| `web.search` | Chat (Aroon) | `SearchProvider` | LOW | member | 10s | External context retrieval (marked untrusted) |

---

## 5. SSE Event Schema & Protocol

Chat streaming over `POST /v1/conversations/{id}/messages` uses standard HTTP Server-Sent Events (`text/event-stream`). Every message chunk has `event:` and `data: <json>` fields.

### Event Definitions:
1. `event: token`  
   `data: {"delta": "string"}` — Progressive text token stream.
2. `event: tool_start`  
   `data: {"tool_name": "string", "arguments": {}, "tool_call_id": "uuid"}` — Emitted before executing a tool.
3. `event: tool_result`  
   `data: {"tool_name": "string", "tool_call_id": "uuid", "status": "ok|warning|failed", "kind": "normal|needs_input", "warnings": []}` — Emitted upon tool completion. When `kind == "needs_input"`, contains tappable option payload.
4. `event: citation`  
   `data: {"id": "uuid", "claim_id": "uuid", "target_type": "string", "target_id": "uuid", "label": "string", "snippet": "string"}` — Clickable evidence citation.
5. `event: chart`  
   `data: {"chart_type": "line|bar|waterfall", "title": "string", "series": [], "cases": {}}` — Interactive chart payload.
6. `event: action_proposal`  
   `data: {"action_id": "uuid", "action_type": "string", "risk_level": "low|medium|high", "preview": {}, "requires_approval": bool}` — Proposal card.
7. `event: stage`  
   `data: {"stage_number": int, "stage_name": "string", "status": "started|completed|failed"}` — Moonshot execution pipeline progress.
8. `event: error`  
   `data: {"code": "string", "message": "string", "details": {}}` — Error termination.
9. `event: done`  
   `data: {"message_id": "uuid", "decision_run_id": "uuid", "status": "verified|warning|unverified|failed", "claims_count": int}` — Final clean termination event.

---

## 6. Database Schema (Migrations 0300–0399)

Every tenant table includes `org_id UUID NOT NULL` indexed first. Denormalized `org_id` on child tables is enforced.

### Table Definitions:

```sql
-- 1. agents
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(64) UNIQUE NOT NULL, -- 'neuralcfo' | 'moonshot' | 'router'
    name VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    allowed_tools JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    title VARCHAR(255) NOT NULL DEFAULT 'New Conversation',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_conversations_org_user ON conversations(org_id, user_id, updated_at DESC);

-- 3. messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender VARCHAR(16) NOT NULL CHECK (sender IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    token_count INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_messages_org_conv ON messages(org_id, conversation_id, created_at ASC);

-- 4. tool_calls
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    decision_run_id UUID REFERENCES decision_runs(id),
    tool_name VARCHAR(128) NOT NULL,
    arguments JSONB NOT NULL,
    status VARCHAR(32) NOT NULL CHECK (status IN ('started', 'completed', 'failed', 'timeout')),
    result_status VARCHAR(32) CHECK (result_status IN ('ok', 'warning', 'failed')),
    duration_ms INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_tool_calls_org_decision ON tool_calls(org_id, decision_run_id);

-- 5. action_proposals
CREATE TABLE action_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    action_type VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL,
    risk_level VARCHAR(16) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
    status VARCHAR(32) NOT NULL CHECK (status IN ('proposed', 'validated', 'awaiting_approval', 'approved', 'applied', 'rejected', 'expired', 'failed')),
    proposed_by_user_id UUID NOT NULL REFERENCES users(id),
    approved_by_user_id UUID REFERENCES users(id),
    executed_at TIMESTAMPTZ,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_action_proposals_org_status ON action_proposals(org_id, status);

-- 6. voice_transcripts
CREATE TABLE voice_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    audio_duration_sec NUMERIC(8,2) NOT NULL,
    raw_transcript TEXT NOT NULL,
    edited_transcript TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_voice_transcripts_org ON voice_transcripts(org_id);

-- 7. documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    filename VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    mime_type VARCHAR(128) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    storage_path TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_documents_org_hash UNIQUE (org_id, content_hash)
);
CREATE INDEX idx_documents_org ON documents(org_id);

-- 8. ingestion_jobs
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    status VARCHAR(32) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    progress_pct INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_ingestion_jobs_org ON ingestion_jobs(org_id, status);

-- 9. document_chunks
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    page_number INT NOT NULL,
    content TEXT NOT NULL,
    token_count INT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_document_chunks_org ON document_chunks(org_id, document_id);

-- 10. web_sources
CREATE TABLE web_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    url TEXT NOT NULL,
    title VARCHAR(255) NOT NULL,
    snippet TEXT NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_web_sources_org ON web_sources(org_id);

-- 11. memories
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    category VARCHAR(64) NOT NULL,
    key VARCHAR(128) NOT NULL,
    value TEXT NOT NULL,
    status VARCHAR(32) NOT NULL CHECK (status IN ('proposed', 'confirmed', 'rejected', 'archived')),
    source_message_id UUID REFERENCES messages(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_memories_org_user ON memories(org_id, user_id, status);

-- 12. feedback
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    message_id UUID NOT NULL REFERENCES messages(id),
    score INT NOT NULL CHECK (score IN (-1, 1)),
    comment TEXT,
    eval_case_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_feedback_org ON feedback(org_id);

-- 13. eval_cases
CREATE TABLE eval_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(64) NOT NULL,
    question TEXT NOT NULL,
    expected_tools JSONB NOT NULL DEFAULT '[]',
    expected_facts JSONB NOT NULL DEFAULT '[]',
    expected_risk VARCHAR(16) NOT NULL DEFAULT 'low',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 14. eval_runs
CREATE TABLE eval_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(128) NOT NULL,
    git_commit VARCHAR(64),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    summary_metrics JSONB NOT NULL DEFAULT '{}'
);

-- 15. eval_results
CREATE TABLE eval_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    eval_run_id UUID NOT NULL REFERENCES eval_runs(id) ON DELETE CASCADE,
    eval_case_id UUID NOT NULL REFERENCES eval_cases(id),
    tool_choice_score NUMERIC(5,2) NOT NULL,
    fact_score NUMERIC(5,2) NOT NULL,
    citation_score NUMERIC(5,2) NOT NULL,
    latency_ms INT NOT NULL,
    passed BOOLEAN NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 16. dashboards
CREATE TABLE dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    title VARCHAR(128) NOT NULL DEFAULT 'Main CFO Dashboard',
    layout JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_dashboards_org ON dashboards(org_id);

-- 17. dashboard_widgets
CREATE TABLE dashboard_widgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    dashboard_id UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    widget_type VARCHAR(64) NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    position_idx INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_dashboard_widgets_org ON dashboard_widgets(org_id, dashboard_id);

-- 18. verification_checks
CREATE TABLE verification_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    decision_run_id UUID NOT NULL REFERENCES decision_runs(id),
    message_id UUID NOT NULL REFERENCES messages(id),
    check_type VARCHAR(32) NOT NULL, -- 'V1_numbers' | 'V2_quotes' | 'V3_citations' | 'V5_units' | 'V7_tags' | 'V8_disclaimer'
    status VARCHAR(16) NOT NULL CHECK (status IN ('passed', 'failed', 'warning')),
    details JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_verification_checks_org_decision ON verification_checks(org_id, decision_run_id);
```

---

## 7. Document Ingestion & RAG Pipeline

1. **Upload:** Client uploads multipart file to `POST /v1/documents`. Requires `Idempotency-Key` header.
2. **Duplicate Check:** Computes SHA-256 `content_hash`. If `(org_id, content_hash)` matches existing document, returns 409 conflict prompting user: "Is this new data or a replacement?".
3. **Dispatch:**
   - If MIME type is CSV $\rightarrow$ forward payload to `FinanceService.import_csv()` and return import batch quality report.
   - If PDF/Text/Docx $\rightarrow$ enqueue `ingestion_job`.
4. **Extraction & Chunking:**
   - Extract text with per-page tracking.
   - Chunk text into ~500 tokens with 50-token overlap.
   - Attach metadata: `document_id`, `org_id`, `page_number`, `chunk_index`.
5. **Embedding & Storage:**
   - Embed chunks using `EmbeddingProvider` (1536-dim vectors).
   - Insert rows into `document_chunks`.
6. **Retrieval:**
   - Pre-filter: `WHERE org_id = :auth_org_id`.
   - Hybrid ranking: Vector cosine similarity combined with full-text search.
   - Answers cite exact page numbers and link to `document_chunks`.

---

## 8. Dashboard Action State Machine

The action lifecycle prevents autonomous code or database mutation:
```
[Model Tool Call: dashboard.propose_action]
                 │
                 ▼
          ┌─────────────┐
          │  PROPOSED   │
          └──────┬──────┘
                 │ Backend validates schema & parameters
                 ▼
          ┌─────────────┐
          │  VALIDATED  │
          └──────┬──────┘
                 ├─────────────────────────────────────────┐
                 │ Low Risk & User Opted-in                │ Medium / High Risk OR User Not Opted-in
                 ▼                                         ▼
          ┌─────────────┐                          ┌──────────────────┐
          │  AUTO-APPLY │                          │ AWAITING_APPROVAL│
          └──────┬──────┘                          └────────┬─────────┘
                 │                                          │
                 │                     User POST /approve   │   User POST /reject
                 │                                          ▼
                 │                                  ┌─────────────┐
                 ├─────────────────────────────────►│  APPROVED   │
                 │                                  └──────┬──────┘
                 │                                         │
                 │                                         ▼
                 ▼                                  ┌─────────────┐
          ┌─────────────┐                           │   APPLIED   │
          │   APPLIED   │                           └─────────────┘
          └─────────────┘
```

- **Risk Levels & Confirmation:**
  - `set_date_range`, `add_chart`, `add_kpi`, `reorder_widget`: Low risk. Confirmation optional.
  - `create_report`: Medium risk. Preview modal displayed.
  - `update_assumption`, `import_transactions`: High risk. Explicit approval required (Admin/Owner role required).
  - `delete_*`, `share_*`: Refused by backend policy.

---

## 9. Verifier Engine Specification (Deterministic V1–V9)

The verifier executes after the model finishes generation, prior to committing the message:
- **V1 (Numbers):** Regular expressions extract numeric tokens (currency, percentages, decimals, counts) from the candidate response. Every extracted number is checked against the numbers in tool results generated during the current turn. Any unmatched number is flagged `unverified`, logged in `verification_checks`, and marked with a warning pill in the UI.
- **V2 (Quotes):** Text inside quotation marks is extracted. Must match an excerpt content hash from `kb_excerpts` or `document_chunks` and be $\le 300$ characters. Paraphrased statements in quotes fail V2 and quotation marks are stripped.
- **V3 (Citations):** Every citation token references an `evidence_link` resolving to a valid target in the caller's `org_id` via `app/core/evidence.py`.
- **V4 (Scenarios):** Verifies that scenario runs maintain the identical baseline run ID.
- **V5 (Units):** Checks that currency codes (`USD`), signs (+/-), dates, and periods match tool definitions.
- **V6 (Gates):** Inspects Moonshot strategy output; verifies no strategy marked `gate_failed` appears in the top recommended list.
- **V7 (Claim Tags):** Every factual sentence receives a claim tag (`cited`, `computed`, `inferred`, `commentary`) linked to an evidence target.
- **V8 (Disclaimer):** Ensures the standard decision-support disclaimer is appended to any forecast or strategic report.
- **V9 (Regenerate Once):** If critical checks fail, the engine triggers one re-prompt with explicit error feedback. If the second pass fails, the answer is returned with an explicit status `warning` or `unverified` and a visible caveat.

---

## 10. Memory Lifecycle & Assumption Bridge

- `memory.write` only **proposes** memory items (`status = 'proposed'`).
- The UI displays a confirmation pill: *"Remember that payroll is on the 28th? [Confirm] [Dismiss]"*.
- User confirms $\rightarrow$ memory becomes `confirmed`.
- **Bridge to Finance Assumptions:** If a memory implies an active business assumption (e.g. payroll date shift or revenue expectation), the memory manager **never silently edits finance_assumptions**. Instead, it generates a High-Risk `action_proposal` (`update_assumption`), which requires explicit administrative approval before mutating CFO settings.
- Memory is isolated per-user and per-org, viewable, editable, and deletable via `/v1/memories`.

---

## 11. Security, Prompt Injection & RBAC

1. **Role-Based Access Control:**
   - `viewer`: Can chat and query metrics (`finance.get_metric`, `rag.search`). Cannot run scenarios, cannot propose/approve actions.
   - `member`: Can run scenarios (`finance.run_scenario`), invoke Moonshot (`moonshot.run`), propose actions, write memories. Cannot approve high-risk actions.
   - `admin` / `owner`: Can approve high-risk action proposals (`update_assumption`, `import_transactions`) and manage org settings.
2. **Prompt Injection Hardening:**
   - Uploaded documents, CSV contents, web snippets, and knowledge base cards are framed within strict XML delimiters (`<untrusted_document_data>...<untrusted_document_data>`).
   - Instructions embedded within data payloads are explicitly countermanded by system guardrail instructions.
   - Tool permissions and allowed actions are enforced entirely by server-side policy and cannot be altered by LLM text.
3. **Data Privacy:**
   - Zero financial numbers or document text recorded in append-only `audit_logs` — only entity IDs, actor IDs, timestamps, and decision outcomes.

---

## 12. Next.js Web Shell Architecture (`/apps/web`)

The Web Shell provides the common host for all three modules:
- `/apps/web/src/app/layout.tsx`: Root layout with tenant/session provider, navigation bar, and Evidence Drawer host modal.
- `/apps/web/src/app/chat/page.tsx`: Conversational interface with streaming message bubbles, tool-progress pills, inline chart renderers, action approval cards, and Moonshot report renderers.
- `/apps/web/src/components/evidence/EvidenceDrawer.tsx`: Shared slide-out drawer resolving citation UUIDs against `GET /v1/citations/{id}` and hosting modular renderers.
- Sub-routes for teammates:
  - `/apps/web/src/app/cfo/`: NeuralCFO pages (owned by Sharjeel).
  - `/apps/web/src/app/moonshot/`: Moonshot pages (owned by Aleena).

---
*End of Architecture Specification.*
