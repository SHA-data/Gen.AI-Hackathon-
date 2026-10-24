# 00. Requirements Analysis & Traceability (NeuralCFO)
**Open Agent Hackathon 2026 · Master Specification v0.1 Analysis**  
**Role:** Senior Backend Engineer (Sharjeel)  
**Module:** NeuralCFO (Finance Engine) + Shared Foundation Kit (Part A, Phase 0)  
**Status:** STEP 0 COMPLETE — PENDING REVIEW BEFORE PART A PHASE 0 EXECUTION

---

## 1. Executive Summary & Bound Principles

As the senior backend engineer responsible for **NeuralCFO** and the **Foundation Kit (Part A, Phase 0)**, this analysis extracts and verifies all binding requirements from the master specification (*NeuralCFO + Moonshot Mode: Unified Project Documentation v0.1*).

### The Inviolable Core Principles
1. **The Model Never Calculates:** The LLM never performs financial arithmetic, balances cash, or derives runway. Calculations are 100% deterministic, executed by pure Python code in the finance engine.
2. **The Baseline is Immutable:** The baseline forecast represents validated reality and agreed operating parameters. No scenario run, what-if lever, or client simulation mutates baseline records.
3. **Decimal-Safe Financial Arithmetic:** All currency values are strictly `NUMERIC(18, 2)` accompanied by an explicit ISO-4217 `CHAR(3)` currency code. Floating-point arithmetic is strictly prohibited across the entire stack.
4. **Complete Source-Row Lineage:** Every financial record, baseline forecast point, and scenario deviation must deterministically link back to its originating `source_rows` or explicit `finance_assumptions`.
5. **Zero Trust Tenant Isolation (`org_id`):** Every tenant table enforces `org_id UUID NOT NULL REFERENCES organizations(id)`. The `org_id` is extracted strictly from the verified JWT claims via `get_auth_context()`. It is never accepted from HTTP request bodies, route params, or tool arguments.
6. **No Silent Drops or Overwrites:** CSV ingestion preserves raw data in `source_rows`. Ambiguities are flagged for user resolution; duplicate rows are flagged rather than deleted; bad rows produce explicit rejection reasons in the import quality report.
7. **Fail Safe with Explicit Envelopes:** If engine calculation fails or data is insufficient, return status `failed` with diagnostic warnings and **no partial numbers**.

---

## 2. Requirements Inventory Touching NeuralCFO

| Req ID | Section Ref | Category | Exact Master Specification Requirement |
| :--- | :--- | :--- | :--- |
| **REQ-CFO-01** | PDF §1, §7.3 | Ingestion | Support CSV ingestion for financial records, invoices, and payroll with raw row storage in `source_rows` (JSONB raw payload, row index, content hash). |
| **REQ-CFO-02** | PDF §1, §7.3 | Quality Report | Generate a comprehensive Import Quality Report upon upload: total rows, accepted count, rejected count with explicit reasons, and duplicate detection (flagged, never silently deleted). |
| **REQ-CFO-03** | PDF §1 | Ambiguity | Detect and surface at least one column-mapping ambiguity (e.g., `Date` vs `Due Date` vs `Invoice Date`) requiring user/admin resolution. |
| **REQ-CFO-04** | PDF §1, §7.3, §11.2 | Data Model | Canonical representation separating `financial_records` (actuals), `invoices` (receivables/payables with status, due date, expected payment date), and `payroll_items`. |
| **REQ-CFO-05** | PDF §8.1 | Engine Model | Method: `Projected cash(t) = projected cash(t-1) + inflows(t) - outflows(t)`. Opening cash is bound to a stated valid date from `finance_assumptions`. |
| **REQ-CFO-06** | PDF §8.1, §8.5 | Granularity | Weekly forecast buckets are canonical (`forecast_points` with `week_start`). Monthly views are strictly derived rollups of canonical weekly points. |
| **REQ-CFO-07** | PDF §8.1 | Date Semantics | Late-payment scenarios shift `expected_payment_date`. They must never rewrite historical transactions, actual receipts, or invoice issue dates. |
| **REQ-CFO-08** | PDF §8.1, §8.2 | Immutability | Baseline forecast is cryptographically or structurally immutable. Scenarios are modeled purely as delta transformations (`scenarios`, `scenario_changes`). |
| **REQ-CFO-09** | PDF §8.1 | Data Labeling | Every displayed financial value is strictly categorized with an explicit label: `observed`, `calculated`, `estimated`, or `hypothetical`. |
| **REQ-CFO-10** | PDF §8.1, §8.5 | Runway Rule | `runway_weeks` is calculated as the exact number of weeks until projected cash first drops below zero from the forecast schedule, or `null` if cash never drops below zero within horizon. Never extrapolate via burn rate. |
| **REQ-CFO-11** | PDF §8.1 | Versioning | Every forecast run records `engine_version` (e.g. `0.1.0`) to guarantee deterministic reproducibility. |
| **REQ-CFO-12** | PDF §8.2, §8.5 | 3-Case Projection | Every scenario run must produce three discrete cases: `expected`, `best`, and `worst`. |
| **REQ-CFO-13** | PDF §8.3, §8.4 | Contract v1 | Expose scenario runner accepting `baseline_run_id`, `horizon_weeks` (default 26, max 104), and `changes` with full lever registry support. |
| **REQ-CFO-14** | PDF §8.4 | Lever Registry | Implement MVP levers: `hire`, `payment_delay`, `payment_terms_days`, `deposit_pct`, `revenue_change_pct`, `lost_client`, `price_change_pct`, `expense_change`. |
| **REQ-CFO-15** | PDF §8.5 | Cash Floor | Store both `reserve_amount` (currency) and `cash_floor_weeks` (default 12). Engine converts weeks to currency as `weeks * average weekly committed outflow` and returns `reserve_breach` and `cash_floor_breach`. |
| **REQ-CFO-16** | PDF §8.5, §12.2 | Failure Safety | On engine calculation failure or invalid inputs, return `status: "failed"` with descriptive reason and warnings, returning NO partial or guessed numbers. |
| **REQ-CFO-17** | PDF §7.5, Part A7 | Cross-Module | Expose `CfoSnapshotService.get(org_id)` returning `{cash, burn, revenue, receivables, payroll, baseline_run_id, as_of_date, currency}` for Moonshot Mode intake. |
| **REQ-CFO-18** | PDF §10.2, §7.2 | Tool Functions | Implement four typed tools in Python: `finance.get_metric`, `finance.run_scenario`, `finance.list_source_rows`, `finance.explain_change`. |
| **REQ-CFO-19** | PDF §11.1, §13 | Multi-Tenancy | Strict tenant isolation via `org_id` on all tables, indexes prefixing `org_id`, composite foreign keys/triggers preventing cross-tenant references. |
| **REQ-CFO-20** | PDF §11.2 | CFO Tables | Sharjeel owns 12 CFO tables: `finance_settings`, `import_batches`, `source_rows`, `financial_records`, `invoices`, `payroll_items`, `finance_assumptions`, `scenarios`, `scenario_changes`, `forecast_runs`, `forecast_points`, `anomaly_flags`. |
| **REQ-CFO-21** | PDF §12.1, §12.2 | Verification | Verifier checks: V1 Numbers (traceable to tool results), V4 Scenarios (same baseline, declared levers only), V5 Units (currency, sign, date consistency). Result status: `verified`, `warning`, `unverified`, `failed`. |
| **REQ-CFO-22** | PDF §12.1 | Evidence Link | Lineage endpoint `GET /v1/finance/forecast-points/{id}/lineage` returning exact math formula, active assumptions, and referenced `source_rows`. |
| **REQ-CFO-23** | PDF §14 | Sponsor Adapter | Implement `FinanceDataSource` interface with `CsvAdapter` and `ZetarisAdapter` (+ fake fallback), ensuring a real or mocked query can feed transactions/invoices. |
| **REQ-CFO-24** | PDF §15.1, §15.2 | Test Suite | Golden test reproducing the hero demo story: 6-10 agency clients, client concentration, 30-day late payment, hiring 2 developers; baseline vs hire vs delay vs combined. |
| **REQ-CFO-25** | Part A, Phase 0 | Foundation Kit | Sharjeel builds and freezes Core migration `0001_core` (7 tables), Auth/JWT, Error/Tool Envelopes, Evidence Registry skeleton, and `FakeFinanceService`. |

---

## 3. Requirement Traceability Matrix

| Requirement | Planned Component | Implementation Path | Planned Verification / Test |
| :--- | :--- | :--- | :--- |
| **REQ-CFO-01** (CSV Ingest) | `CsvImporter`, `app/cfo/importers/csv_importer.py` | Stream CSV, compute content hash, batch insert `source_rows` with raw JSONB | `tests/cfo/test_csv_importer.py::test_idempotent_import_stores_raw_rows` |
| **REQ-CFO-02** (Quality Report) | `ImportQualityService`, `app/cfo/services/import_service.py` | Validate data types, detect duplicate invoice numbers, assemble validation metrics | `tests/cfo/test_csv_importer.py::test_import_quality_report_flags_duplicates` |
| **REQ-CFO-03** (Ambiguity) | `ColumnMapper`, `app/cfo/importers/column_mapper.py` | Heuristic ambiguity check (e.g. both `Transaction Date` and `Effective Date` present) | `tests/cfo/test_csv_importer.py::test_detects_column_mapping_ambiguity` |
| **REQ-CFO-04** (Canonical Model) | CFO DB Models, `app/cfo/models/` | SQLAlchemy models with explicit status check constraints & date columns | `tests/cfo/test_cfo_models.py::test_status_checks_and_foreign_keys` |
| **REQ-CFO-05** (Engine Math) | `FinanceEngine`, `app/cfo/engine/calculator.py` | Pure deterministic cash flow accumulator: $C_t = C_{t-1} + I_t - O_t$ | `tests/cfo/test_engine.py::test_cash_arithmetic_matches_penny` |
| **REQ-CFO-06** (Weekly Buckets) | `CalendarBucketer`, `app/cfo/engine/bucketer.py` | ISO Monday week-start bucketing, rollup queries for monthly reporting | `tests/cfo/test_engine.py::test_weekly_bucketing_and_monthly_rollup` |
| **REQ-CFO-07** (Date Shifts) | `ScenarioApplier`, `app/cfo/engine/scenario_applier.py` | Modifies expected cash in schedule; source invoices unmodified | `tests/cfo/test_engine.py::test_payment_delay_shifts_expected_without_mutating_source` |
| **REQ-CFO-08** (Baseline Immutability) | `BaselineService`, `app/cfo/services/baseline_service.py` | Compute SHA-256 hash of baseline points before and after scenario runs | `tests/cfo/test_engine.py::test_baseline_immutable_after_scenarios` |
| **REQ-CFO-09** (Value Labeling) | `ForecastPointModel`, `app/cfo/schemas/` | Typed schema enum: `observed`, `calculated`, `estimated`, `hypothetical` | `tests/cfo/test_schemas.py::test_value_labels_serialized_properly` |
| **REQ-CFO-10** (Runway Rule) | `RunwayCalculator`, `app/cfo/engine/runway.py` | Scan weekly cash series for index where $C_t < 0$; return null if $C_t \ge 0 \forall t$ | `tests/cfo/test_engine.py::test_runway_weeks_schedule_scan` |
| **REQ-CFO-11** (Versioning) | `EngineConfig`, `app/cfo/engine/__init__.py` | Fixed semantic version string (`0.1.0`) embedded in every run artifact | `tests/contract/test_contract.py::test_engine_version_present` |
| **REQ-CFO-12** (3 Cases) | `CaseGenerator`, `app/cfo/engine/cases.py` | Apply worst-case (+14d payment, -10% rev) & best-case (-7d payment, +5% rev) deltas | `tests/cfo/test_engine.py::test_three_cases_generation` |
| **REQ-CFO-13** (Contract v1) | `POST /v1/finance/scenarios/run` | FastAPI router mounting shared Pydantic request/response schemas | `tests/contract/test_finance_contract.py::test_scenario_run_envelope` |
| **REQ-CFO-14** (Lever Registry) | `LeverHandlerRegistry`, `app/cfo/engine/levers.py` | Strategy pattern dispatching operations for all 8 MVP levers | `tests/cfo/test_levers.py::test_all_mvp_levers` |
| **REQ-CFO-15** (Cash Floor) | `ReserveEvaluator`, `app/cfo/engine/reserve.py` | Average committed outflow calculation over horizon; breach boolean flags | `tests/cfo/test_engine.py::test_cash_floor_and_reserve_breaches` |
| **REQ-CFO-16** (Failure Envelope) | `GlobalExceptionHandler`, `app/core/errors.py` | Catch validation & arithmetic errors; return empty data + diagnostics | `tests/cfo/test_engine.py::test_missing_params_yields_failed_status_no_numbers` |
| **REQ-CFO-17** (CFO Snapshot) | `CfoSnapshotService`, `app/cfo/services/snapshot.py` | Aggregate cash, runway, ARR/MRR, payroll, baseline run id into tool envelope | `tests/cfo/test_snapshot.py::test_cfo_snapshot_service_output` |
| **REQ-CFO-18** (Finance Tools) | `FinanceService`, `app/cfo/services/finance_service.py` | Implement `get_metric`, `run_scenario`, `list_source_rows`, `explain_change` | `tests/contract/test_finance_service.py::test_matches_fake_finance_service` |
| **REQ-CFO-19** (Isolation) | `get_auth_context`, `app/core/auth.py` | Dependency injection injecting `TenantContext(org_id, user_id, role)` | `tests/core/test_auth_isolation.py::test_cross_org_access_returns_404` |
| **REQ-CFO-20** (CFO Migrations) | Alembic migrations `0100_cfo_tables.py` | Strict schema generation for 12 CFO tables with constraints and indexes | `tests/core/test_migrations.py::test_alembic_cfo_tables_exist` |
| **REQ-CFO-21** (Verifier Checks) | `FinanceVerifier`, `app/cfo/verification/verifier.py` | Check V1, V4, V5 rules before returning responses | `tests/cfo/test_verifier.py::test_v1_v4_v5_verification_rules` |
| **REQ-CFO-22** (Lineage & Claims) | `EvidenceRegistry`, `app/core/evidence.py` | Lineage resolver linking `forecast_point -> calculation -> source_rows` | `tests/cfo/test_lineage.py::test_forecast_point_lineage_resolution` |
| **REQ-CFO-23** (Zetaris Adapter) | `FinanceDataSource`, `app/cfo/adapters/` | Interface + `CsvAdapter` + `ZetarisAdapter` with mock fallback & smoke test | `tests/cfo/test_zetaris_adapter.py::test_zetaris_smoke_and_mock_fallback` |
| **REQ-CFO-24** (Golden Demo) | `SeedScript`, `services/api/seed/seed_data.py` | Seed synthetic agency, 8 clients, 1 concentrated client, run baseline & scenarios | `tests/integration/test_golden_hiring_scenario.py::test_golden_numbers` |
| **REQ-CFO-25** (Foundation Kit) | Repo Skeleton, `app/core/`, Contracts | Docker Compose, Makefile, Core tables migration `0001_core`, contracts package | `tests/core/test_foundation.py::test_foundation_kit_complete` |

---

## 4. Master Specification Conflict Resolution (F1 – F16)

The master specification highlights 16 conflicts and gaps (F1–F16). Below is the explicit analysis of every finding affecting the finance engine and how Part A / Phase 0 resolves it:

| Conflict ID | Severity | Finding Summary in PDF | How Part A & Sharjeel's Module Resolves It |
| :--- | :--- | :--- | :--- |
| **F1** | High | Rules & tooling unresolved (Cursor vs Antigravity, models, pre-window work). | **Resolved in Part A:** Standard modular monolith (FastAPI + Next.js + PostgreSQL 16) runnable via standard CLI, Makefile, and Docker. Agnostic to editor; code enforces all constraints directly. |
| **F2** | High | Three incompatible CFO engine contracts (BP company_id vs CH2 weekly vs MP monthly). | **Resolved in Part A5:** Strictly adopt the single **Contract v1** in Section 8. Standardized to `baseline_run_id`, `horizon_weeks` (canonical weekly series), `cases` (`expected`, `best`, `worst`), and standard lever schema. Frozen at end of Day 1. |
| **F3** | High | Overlapping data models, inconsistent tenant keys (`company_id` vs `org_id`), and mixed DBs. | **Resolved in Part A3:** Single PostgreSQL schema, UUID primary keys, and `org_id` on every tenant table. Strict migration ranges: `0001-0099` (Core, frozen), `0100-0199` (CFO), `0200-0299` (Moonshot), `0300-0399` (Chat). Zero table overlap. |
| **F5** | High | Scope exceeds hackathon time (60+ tables, 12 phases, heavy integrations). | **Resolved in Part A/B2:** Strict prioritization. Slices 1–9 (Must) are built first in vertical slices. "Could" items (voice, autonomous actions) are explicitly deferred or cut. |
| **F8** | Med | Sponsor roles inconsistent & unverified (Zetaris & Meterless). | **Resolved in Part A1 & B2.9:** Build clean adapter `FinanceDataSource` with `CsvAdapter` and `ZetarisAdapter`. Include a clearly marked deterministic fake + smoke test. State exact missing organizer specs in docs. |
| **F9** | Med | Scenario vs Case semantic ambiguity (BP 1 series vs MP/CH2 3 cases). | **Resolved in Part A5 & B2.5:** Scenario = set of explicit lever changes applied to baseline. Case = projection outcome (`expected`, `best`, `worst`) generated for that scenario. Engine always computes all three cases per scenario run. |
| **F10** | Med | Granularity & cash floor discrepancy (weekly vs monthly; runway weeks vs currency reserve). | **Resolved in Part A5:** Weekly is canonical. Finance settings stores both `reserve_amount` (currency) and `cash_floor_weeks` (default 12). Engine computes average weekly committed outflow and checks both conditions. Runway is derived from the schedule, never burn extrapolation. |
| **F11** | Med | Evidence modeled three ways (`EvidenceReference`, `message_citations`, `claim` + `evidence_link`). | **Resolved in Part A3 & A7:** Core migration `0001_core` implements single `claims` and `evidence_links` model (one row = exactly one target). Target existence validated by registry in `app/core/evidence.py`. |
| **F12** | Med | Ownership gaps across team members. | **Resolved in Part A:** Fixed ownership: Sharjeel owns Core Foundation (`0001_core`) and NeuralCFO (`0100-0199`); Aleena owns Moonshot (`0200-0299`); Aroon owns Chat & UI Shell (`0300-0399`). |
| **F13** | Low | Naming clash: `assumption` (Moonshot) vs `BusinessAssumption` (Finance). | **Resolved in Part A3:** Renamed to `goal_assumptions` (Moonshot) and `finance_assumptions` (CFO). |
| **F16** | Info | Strengths to keep: 12 hard rules, database-level constraints, claim tags. | **Confirmed:** Retained and reinforced in Core Foundation and CFO engine verification pipeline. |

---

## 5. Architectural Assumptions & Decision Tags

Following the specification's tagging convention (`[DECIDED]`, `[PROPOSED]`, `[OPEN]`, `[VERIFY]`):

### [DECIDED] Invariants (Binding)
1. **[DECIDED: PDF §6, §8.1]** The model never performs arithmetic; engine is deterministic; baseline is immutable.
2. **[DECIDED: PDF §11.1]** Monetary values are `NUMERIC(18,2)` with ISO 4217 `CHAR(3)` currency codes. No floating-point types in DB or calculations.
3. **[DECIDED: PDF §11.1, §13]** `org_id` is supplied exclusively by the authenticated JWT context, never accepted from request body or query parameters.
4. **[DECIDED: PDF §8.5]** The canonical forecast resolution is weekly (starting on Monday). Monthly summaries are strictly derived rollups.
5. **[DECIDED: PDF §8.5]** `runway_weeks` is the index of the first projected week where ending cash $< 0$, or `null` if cash stays $\ge 0$ throughout the forecast horizon.
6. **[DECIDED: PDF §11.2, Part A3]** Core migration `0001_core` defines the 7 shared tables (`organizations`, `users`, `memberships`, `audit_logs`, `decision_runs`, `claims`, `evidence_links`) with audit log immutability enforced by a database trigger.
7. **[DECIDED: PDF §12.1]** Evidence links point to exactly one target type and target ID; validated via `app/core/evidence.py`.
8. **[DECIDED: PDF §7.3, B2.2]** CSV ingestion stores raw payloads in `source_rows` (JSONB) with row numbers and file content hash; duplicates are flagged in `anomaly_flags`, never deleted.

### [PROPOSED] Architecture & Engineering Choices (Adopted in Part A)
1. **[PROPOSED: Part A5] Best/Worst Case Bounds:**
   - `expected`: Exactly matches the scenario's stated parameters.
   - `worst`: Uncertain client receivables are delayed by $+14$ days; revenue adjustments are degraded by $-10$ percentage points relative.
   - `best`: Receivables accelerate by $-7$ days; revenue adjustments increase by $+5$ percentage points relative.
   *(All defaults stored in `finance_settings` and exposed transparently to the user as assumptions).*
2. **[PROPOSED: Part A5] Cash Floor Currency Conversion:**
   $$\text{Converted Floor} = \text{cash\_floor\_weeks} \times \left(\frac{1}{H} \sum_{w=1}^{H} \text{committed\_outflows}_w\right)$$
   Where committed outflows include recurring payroll and known payables across horizon $H$.
3. **[PROPOSED: Part B2.2] CSV Ambiguity Resolution:**
   The CSV importer automatically identifies header collisions (e.g., both `Due Date` and `Expected Payment Date` present, or generic `Date`). If ambiguous, the import batch enters status `needs_mapping` with a suggested default mapping, requiring user confirmation.
4. **[PROPOSED: Part A1] Repository Layout:**
   Clean modular monolith layout in `c:\Users\n tech\Desktop\Neural CFO`:
   - `/apps/web` (Next.js frontend)
   - `/services/api/app/core` (Foundation Kit)
   - `/services/api/app/cfo` (NeuralCFO module)
   - `/services/api/migrations` (Alembic)
   - `/packages/contracts` (Pydantic models, JSON schemas, OpenAPI specs)
   - `/docs/cfo` (Documentation, reports, progress logs)
   - `/tests/` (Unit, integration, contract, security tests)

### [OPEN] Items Requiring Confirmation
1. **[OPEN: PDF §8.2] Identification of "Uncertain" Invoices:**
   Which invoices undergo the $+14\text{d} / -7\text{d}$ case shift?
   *Proposed Resolution:* Invoices without an explicit signed contract term or with a client history of late payments ($\ge 14$ days past due) receive the `uncertain` flag.
2. **[OPEN: PDF §4, D9] Hackathon Track Positioning:**
   Track 2 (Evidence-backed explanations) vs Track 3. Will be confirmed with team leads; building `finance.explain_change` makes NeuralCFO a prime candidate for Track 2.

### [VERIFY] External Dependencies & Sponsor Specifics
1. **[VERIFY: PDF §14, §18] Zetaris Connectivity & API:**
   Primary connection parameters (REST endpoint, JDBC/ODBC, or Python SDK) and auth mechanisms are not yet provided in the repo.
   *Resolution Strategy:* Implement `FinanceDataSource` abstract base class with a fully functional `CsvAdapter` and a mock/fake `ZetarisAdapter` containing realistic queries. Provide a standalone smoke test script `tests/cfo/test_zetaris_smoke.py` and document exact connection parameters required from hackathon organizers in `docs/cfo/INTEGRATION.md`.

---

## 6. Next Steps Workflow
Upon review and acknowledgment of this requirements analysis:
1. Initialize the repository structure according to Part A1.
2. Build the **Foundation Kit (Part A, Phase 0)**:
   - Config, async DB session, Alembic migrations `0001_core`
   - JWT authentication & role-based access control (`get_auth_context`)
   - Development token endpoint (`POST /v1/dev/token`)
   - Standardized error and tool envelopes
   - `EvidenceRegistry` skeleton
   - `/packages/contracts` with `FakeFinanceService` and shared Pydantic models
   - Seed data for two tenant organizations
   - Core test suite (auth, org isolation, audit trigger immutability, contract checks)
3. Tag commit `foundation-v1` and unblock Aleena and Aroon.
4. Submit `docs/cfo/01_architecture.md` for approval before writing CFO domain code.
