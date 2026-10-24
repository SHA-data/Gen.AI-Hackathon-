# Foundation Kit v1 Specification & Integration Guide
**Open Agent Hackathon 2026 · NeuralCFO + Moonshot Mode**  
**Author:** Sharjeel (Senior Backend / CFO Lead)  
**Status:** PUBLISHED & FROZEN (`foundation-v1`)  
**Scope:** Part A (Foundation Kit, Phase 0)

---

## 1. Overview & Unblocking Notice

To: **Aleena (Moonshot Mode Lead)** and **Aroon (Chatbot & UI Lead)**  
From: **Sharjeel (NeuralCFO & Core Foundation Lead)**  

The **Foundation Kit (Part A, Phase 0)** is built, tested, and published to `main`. This document defines all shared contracts, database baselines, authentication protocols, and canned service fakes. You are now **fully unblocked** to build your modules concurrently.

> [!IMPORTANT]
> **Contract Freeze:** Core tables (`0001_core`) and `/packages/contracts` are now frozen. Any modification requires opening an issue tagged `contract-change` and obtaining approval from the respective module owners.

---

## 2. Repository Layout & Module Boundaries

The single repository is structured as a modular monolith:

```
├── apps/
│   └── web/                     # Next.js UI (Aroon owns shell; others add pages)
├── docs/
│   ├── cfo/                     # NeuralCFO documentation and test reports
│   └── FOUNDATION.md            # This document
├── packages/
│   └── contracts/               # Single source of truth for all schemas & interfaces
│       ├── envelope.py          # ErrorEnvelope, ToolResultEnvelope, ResultStatus
│       ├── finance.py           # ScenarioRunRequest/Data, CfoSnapshotData, Levers
│       ├── fake_service.py      # FakeFinanceService, FakeCfoSnapshotService
│       ├── schemas/             # Exported JSON schemas for cross-language validation
│       └── openapi/             # Exported OpenAPI specifications
├── services/
│   └── api/
│       ├── app/
│       │   ├── core/            # Foundation Kit: DB, auth, audit, errors, evidence
│       │   ├── cfo/             # NeuralCFO module (Sharjeel)
│       │   ├── moonshot/        # Moonshot module (Aleena)
│       │   └── chat/            # Chatbot module (Aroon)
│       ├── migrations/          # Alembic migrations (strictly partitioned ranges)
│       └── seed/                # Demo seeds and test credentials
└── tests/
    ├── core/                    # Core foundation tests (auth, isolation, audit)
    ├── contract/                # Shared contract verification tests
    ├── cfo/                     # NeuralCFO unit and integration tests
    └── integration/             # End-to-end multi-module tests
```

---

## 3. Database Strategy & Ownership Ranges

Database migrations use a single Alembic history with strictly partitioned numbering:
- `0001 - 0099`: **Core Foundation** (Owned by Sharjeel; `0001_core` is **FROZEN**)
- `0100 - 0199`: **NeuralCFO** (Owned by Sharjeel)
- `0200 - 0299`: **Moonshot Mode** (Owned by Aleena)
- `0300 - 0399`: **Chatbot & Ingestion** (Owned by Aroon)

### Core Tables in `0001_core`
1. **`organizations`**: Tenant anchor (`id UUID`, `name`, `base_currency CHAR(3)`, `created_at`).
2. **`users`**: Global identity (`id UUID`, `email`, `display_name`, `created_at`).
3. **`memberships`**: Tenant-user link with role constraint (`owner`, `admin`, `member`, `viewer`).
4. **`audit_logs`**: Append-only log. Database triggers (`trg_audit_logs_immutable`) strictly reject `UPDATE` and `DELETE`. Stores IDs, actions, and decisions only (no raw financials or secrets).
5. **`decision_runs`**: Unified execution records (`cfo`, `moonshot`, `chat`) with status (`verified`, `warning`, `unverified`, `failed`).
6. **`claims`**: Granular claims linked to runs with tags (`cited`, `computed`, `inferred`, `commentary`).
7. **`evidence_links`**: Strict 1:1 linkage from a claim to an evidence target (`target_type`, `target_id`).

---

## 4. Authentication & Multi-Tenancy

Authentication uses HS256 JWT tokens.

### Claims Structure
```json
{
  "sub": "user_id_uuid",
  "org_id": "org_id_uuid",
  "role": "owner | admin | member | viewer",
  "exp": 1729850000
}
```

### Dependency Injection
Every FastAPI endpoint must extract tenant context via `get_auth_context()`:
```python
from services.api.app.core.auth import get_auth_context, AuthContext
from fastapi import Depends

@router.get("/my-endpoint")
async def my_endpoint(auth: AuthContext = Depends(get_auth_context)):
    org_id = auth.org_id  # ALWAYS from JWT; NEVER from request body!
    user_id = auth.user_id
```

### Dev Token Minting
For testing and demo development, tokens can be minted via `POST /v1/dev/token` (active only when `ENV=dev`):
```bash
curl -X POST http://localhost:8000/v1/dev/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "10000000-0000-0000-0000-000000000001", "org_id": "00000000-0000-0000-0000-000000000001", "role": "admin"}'
```

---

## 5. Standardized Envelopes

### 1. Error Envelope (HTTP 4xx / 5xx)
```json
{
  "error": {
    "code": "UNAUTHORIZED | FORBIDDEN | NOT_FOUND | VALIDATION_ERROR | INTERNAL_SERVER_ERROR",
    "message": "Human readable explanation",
    "details": {},
    "request_id": "uuid-string"
  }
}
```

### 2. Tool Result Envelope (All Inter-Module & Agent Tools)
```json
{
  "status": "ok | warning | failed",
  "data": {},
  "sources": ["source_row_uuid_1", "source_row_uuid_2"],
  "warnings": ["Diagnostic warning if any"],
  "run_id": "uuid-or-null"
}
```

---

## 6. How Aleena & Aroon Integrate Right Now

You do not need to wait for the real finance engine to build Moonshot and Chatbot. Use the canned fakes in `packages.contracts`:

### 1. Moonshot Intake: Reading CFO Snapshot
```python
from packages.contracts import FakeCfoSnapshotService

# Returns cash, runway, ARR/MRR, payroll, baseline_run_id in ToolResultEnvelope
snapshot_env = FakeCfoSnapshotService.get(org_id)
baseline_id = snapshot_env.data["baseline_run_id"]
current_cash = snapshot_env.data["cash"]
```

### 2. Moonshot & Chatbot: Running Scenarios
```python
from packages.contracts import (
    FakeFinanceService,
    ScenarioRunRequest,
    ScenarioPayload,
    ScenarioChange,
)

req = ScenarioRunRequest(
    baseline_run_id=baseline_id,
    horizon_weeks=26,
    scenario=ScenarioPayload(
        name="staged_hire",
        origin="moonshot_card",
        changes=[
            ScenarioChange(lever="hire", op="set", value=2, params={"monthly_cost": "7000"}),
            ScenarioChange(lever="payment_delay", op="set", value=30, params={"client": "Apex Corp"}),
        ]
    )
)

result_env = FakeFinanceService.run_scenario(org_id, req)
# Access deterministic 3-case weekly cash flows
expected_cases = result_env.data["cases"]["expected"]
worst_cases = result_env.data["cases"]["worst"]
```

### 3. Tool Calls (Chatbot Gateway)
Aroon can wire tools directly to `FakeFinanceService`:
- `finance.get_metric(org_id, metric, from_date, to_date)`
- `finance.run_scenario(org_id, request)`
- `finance.list_source_rows(org_id, ref)`
- `finance.explain_change(org_id, metric, from_date, to_date)`

When NeuralCFO's real engine finishes, the service interface signatures will be identical.

---

## 7. Seed Data & Verification

Run the test suite and verify everything passes:
```bash
# 1. Run migrations
python -m alembic -c services/api/alembic.ini upgrade head

# 2. Seed demo organizations and users
python services/api/seed/seed_data.py

# 3. Run test suite
pytest tests/ -v
```

Pre-seeded tokens are stored in `services/api/seed/seeded_tokens.json` for:
- **Org 1 (`00000000-0000-0000-0000-000000000001`)**: Acme Digital Agency
  - Owner: `alice.owner@acme.test`
  - Admin: `bob.admin@acme.test`
  - Member: `charlie.member@acme.test`
  - Viewer: `dana.viewer@acme.test`
- **Org 2 (`00000000-0000-0000-0000-000000000002`)**: Globex Marketing
  - Users with identical role mapping for multi-tenant isolation tests.
