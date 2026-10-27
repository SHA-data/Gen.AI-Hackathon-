# Moonshot Mode Strategy Module
**Owner:** Aleena (`leena-77`)  
**Location:** `/services/api/app/moonshot`  
**Migrations Allocated:** `0200-0299`  
**Tables Owned:**
- `moonshot_requests`, `goals`, `constraints`, `clarification_questions`, `goal_assumptions`, `candidate_strategies`, `scenario_requests`, `constraint_checks`, `stress_test_items`, `experiment_plans`, `reports`, `criteria`, `scoring_profiles`, `scoring_weights`, `strategy_scores`, `strategy_rankings`, `sensitivity_checks`, `kb_*` tables, `evidence_tiers`.

---

## How to Integrate Seamlessly Without Conflicts:
1. **Contract Interface:** Implement the `MoonshotWorkflow` protocol defined in `/packages/contracts/moonshot.py`:
   - `run(org_id, user_id, goal, constraints, answers) -> Union[NeedsInputResult, MoonshotReport]`
   - `stream_stages(org_id, goal) -> AsyncGenerator[StageEvent, None]`
2. **Connecting to Gateway:**
   - In `services/api/app/chat/tools/moonshot.py`, call `set_moonshot_workflow(your_real_workflow)` or toggle `MOONSHOT_BACKEND=real`.
3. **Database Migrations:** Put all Moonshot Alembic migrations in `/services/api/migrations/versions/` numbered between `0200_` and `0299_`.
4. **Web UI Pages:** Place your strategy explorer and report views under `/apps/web/src/app/moonshot/`.
5. **Testing:** Write your strategy gating and scoring tests under `/tests/moonshot/`.
