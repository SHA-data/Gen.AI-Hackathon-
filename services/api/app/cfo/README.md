# NeuralCFO Finance Engine Module
**Owner:** Sharjeel  
**Location:** `/services/api/app/cfo`  
**Migrations Allocated:** `0100-0199`  
**Tables Owned:**
- `finance_settings`, `import_batches`, `source_rows`, `financial_records`, `invoices`, `payroll_items`, `finance_assumptions`, `scenarios`, `scenario_changes`, `forecast_runs`, `forecast_points`, `anomaly_flags`.

---

## How to Integrate Seamlessly Without Conflicts:
1. **Contract Interface:** Implement the `FinanceService` protocol defined in `/packages/contracts/finance.py`:
   - `run_scenario(org_id, request: ScenarioRunRequest) -> ToolResultEnvelope[ScenarioRunResponseData]`
   - `get_metric(org_id, request: MetricRequest) -> ToolResultEnvelope[MetricResponseData]`
   - `list_source_rows(org_id, row_ids) -> ToolResultEnvelope[List[SourceRowData]]`
   - `explain_change(org_id, metric, start, end) -> ToolResultEnvelope[ExplainChangeData]`
2. **Connecting to Gateway:**
   - In `services/api/app/chat/tools/finance.py`, call `set_finance_service(your_real_service)` or toggle `FINANCE_BACKEND=real`.
3. **Database Migrations:** Put all CFO Alembic migrations in `/services/api/migrations/versions/` numbered between `0100_` and `0199_`.
4. **Web UI Pages:** Place your full-page scenario dashboard under `/apps/web/src/app/cfo/`.
5. **Testing:** Write your unit and scenario tests under `/tests/cfo/`.
