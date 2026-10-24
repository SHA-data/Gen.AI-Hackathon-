# NeuralCFO Integration Guide & Handover
**Open Agent Hackathon 2026 · NeuralCFO (Sharjeel) Handover Document**  
**Audience:** Aleena (Moonshot Lead) & Aroon (Chatbot & UI Lead)  
**Status:** COMPLETE & INTEGRATION-READY

---

## 1. Quick Checklist for Aleena & Aroon

Run these three commands to verify everything works on your machine:
```bash
# 1. Run migrations (applies 0001_core and 0100_cfo_tables)
python -m alembic -c services/api/alembic.ini upgrade head

# 2. Seed demo organizations and dataset
python services/api/seed/seed_data.py
python services/api/seed/seed_demo_agency.py

# 3. Run complete test suite (44/44 tests must pass)
pytest tests/ -v
```

---

## 2. HTTP Endpoints Delivered (Under `/v1/finance/*`)

All endpoints require `Authorization: Bearer <JWT>` and extract `org_id` exclusively from auth context:

| Method | Path | Description | Access Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/v1/finance/imports` | Multipart CSV ingestion (invoices, payroll, transactions). Generates Quality Report. | `admin`, `owner` |
| `GET` | `/v1/finance/imports/{id}` | Inspect import batch quality report and flagged anomalies. | `viewer`+ |
| `POST` | `/v1/finance/baseline/run` | Generates immutable baseline forecast schedule. | `member`+ |
| `GET` | `/v1/finance/baseline` | Retrieve latest baseline forecast schedule. | `viewer`+ |
| `POST` | `/v1/finance/scenarios/run` | **Finance Contract v1**: Runs 3-case simulation (`expected`, `best`, `worst`). | `member`+ |
| `GET` | `/v1/finance/scenarios/{id}/compare` | Comparative inspection of baseline vs scenario cases. | `viewer`+ |
| `GET` | `/v1/finance/forecast-points/{id}/lineage` | Lineage resolver returning formula, active assumptions, and contributing source rows. | `viewer`+ |
| `GET` | `/v1/finance/metrics` | Retrieve financial metric (`cash`, `burn`, `revenue`, `receivables`, `payroll`, `runway`). | `viewer`+ |
| `GET` | `/v1/finance/source-rows` | List raw source rows with optional `ref` filter. | `viewer`+ |
| `GET` | `/v1/finance/snapshot` | **CFO Snapshot**: Read-only financial posture consumed by Moonshot Mode intake. | `viewer`+ |
| `GET` | `/v1/finance/settings` | Retrieve tenant finance settings. | `viewer`+ |
| `PATCH`| `/v1/finance/settings` | Update tenant reserve amount, cash floor weeks, or case ranges. | `admin`, `owner` |
| `GET` | `/v1/finance/zetaris/smoke-test` | Verifies the Zetaris sponsor adapter data path. | `viewer`+ |

---

## 3. Python Services & Tool Mappings

Chatbot and Moonshot can invoke these typed Python services directly:

### 1. `RealFinanceService` (`services/api/app/cfo/services/finance_service.py`)
Matches `FakeFinanceService` signatures 1:1:
- `finance.get_metric(session, org_id, metric, from_date, to_date)`
- `finance.run_scenario(session, org_id, request)`
- `finance.list_source_rows(session, org_id, ref)`
- `finance.explain_change(session, org_id, metric, from_date, to_date)`

### 2. `RealCfoSnapshotService` (`services/api/app/cfo/services/snapshot_service.py`)
Matches `FakeCfoSnapshotService` signatures 1:1:
- `CfoSnapshotService.get(session, org_id)` $\rightarrow$ returns `{cash, burn, revenue, receivables, payroll, baseline_run_id, as_of_date, currency}` in `ToolResultEnvelope`.

---

## 4. Database Ownership & Migration Boundaries

### Core Tables Owned by Sharjeel (`0001_core` — FROZEN)
1. `organizations`
2. `users`
3. `memberships`
4. `audit_logs` (append-only trigger protected)
5. `decision_runs`
6. `claims`
7. `evidence_links`

### CFO Tables Owned by Sharjeel (`0100_cfo_tables.py`)
1. `finance_settings`
2. `import_batches`
3. `source_rows`
4. `financial_records`
5. `invoices`
6. `payroll_items`
7. `finance_assumptions`
8. `scenarios`
9. `scenario_changes`
10. `forecast_runs`
11. `forecast_points`
12. `anomaly_flags`

> **Note:** Aleena creates tables in migration range `0200-0299` (Moonshot); Aroon creates tables in migration range `0300-0399` (Chatbot). No module creates tables outside its allocated range.

---

## 5. Registered Evidence Target Types

In `app/core/evidence.py`, NeuralCFO has registered resolvers for:
- `source_row`
- `financial_record`
- `forecast_run`
- `forecast_point`
- `finance_assumption`

Moonshot and Chatbot can link claims to any of these targets using `create_claim_with_evidence()`.

---

## 6. Environment Variables (`.env`)

```ini
ENV=dev
DATABASE_URL=sqlite+aiosqlite:///./neuralcfo.db
# In production / Docker Compose:
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/neuralcfo
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=demo-secret-key-change-in-production-never-commit-actual-secrets-32bytes
JWT_ALGORITHM=HS256
DEFAULT_BASE_CURRENCY=USD
DEFAULT_CASH_FLOOR_WEEKS=12
ENGINE_VERSION=0.1.0

# Sponsor Technology (Zetaris)
ZETARIS_ENABLED=false
ZETARIS_ENDPOINT=
ZETARIS_API_KEY=
ZETARIS_DATABASE=
```

---

## 7. Known Gaps & Sponsor Status

### Zetaris Integration Requirements from Organizers
`ZetarisAdapter` currently runs in **labeled mock fallback mode**, passing all smoke tests (`GET /v1/finance/zetaris/smoke-test`). To switch to 100% live execution, the following are needed from hackathon organizers:
1. `ZETARIS_ENDPOINT`: Cluster connection URL / REST API endpoint.
2. `ZETARIS_API_KEY`: Authentication bearer token or API key.
3. `ZETARIS_DATABASE`: Target catalog / database name containing live invoices and transaction tables.
