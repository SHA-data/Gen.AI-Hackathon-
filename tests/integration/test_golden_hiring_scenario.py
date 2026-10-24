from datetime import date
from decimal import Decimal
import json
from pathlib import Path
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient

from packages.contracts.envelope import ResultStatus, ToolStatus
from packages.contracts.finance import ScenarioChange, ScenarioPayload, ScenarioRunRequest
from services.api.app.cfo.services.baseline_service import BaselineService
from services.api.app.cfo.services.scenario_service import ScenarioService
from services.api.app.cfo.verification.lineage import LineageResolver
from services.api.app.core.auth import create_access_token
from services.api.app.core.database import async_session_factory
from services.api.app.main import app
from services.api.seed.seed_data import SEED_ORGS

DEMO_ORG_ID = SEED_ORGS[0]["id"]


@pytest.mark.asyncio
async def test_golden_demo_hiring_and_delay_scenarios():
    golden_path = Path("tests/cfo/golden_demo_values.json")
    with open(golden_path, "r") as f:
        golden = json.load(f)

    async with async_session_factory() as session:
        # Step 1: Baseline cash position & forecast
        baseline_run, points = await BaselineService.run_baseline(session, DEMO_ORG_ID, horizon_weeks=26)
        assert baseline_run.status in ("verified", "warning")
        # System flags a cash risk per canonical story (cash floor breach on baseline)
        assert baseline_run.cash_floor_breach is True

        # Step 2: Individual Hire Scenario (2 Devs @ $7,000/mo)
        req_hire = ScenarioRunRequest(
            baseline_run_id=baseline_run.id,
            horizon_weeks=26,
            scenario=ScenarioPayload(
                name="hire_two_developers",
                changes=[
                    ScenarioChange(
                        lever="hire",
                        op="set",
                        value=2,
                        params={"count": 2, "monthly_cost": "7000.00"},
                        start_date=date(2026, 11, 1),
                    )
                ],
            ),
        )
        hire_env = await ScenarioService.run_scenario(session, DEMO_ORG_ID, req_hire)
        assert hire_env.status == ToolStatus.OK
        hire_data = hire_env.data
        assert Decimal(hire_data["cases"]["expected"]["end_cash"]) < baseline_run.end_cash

        # Step 3: Individual Delay Scenario (Apex Corp pays 30 days late)
        req_delay = ScenarioRunRequest(
            baseline_run_id=baseline_run.id,
            horizon_weeks=26,
            scenario=ScenarioPayload(
                name="apex_30d_delay",
                changes=[
                    ScenarioChange(
                        lever="payment_delay",
                        op="set",
                        value=30,
                        params={"client": golden["concentrated_client"]["name"], "days": 30},
                    )
                ],
            ),
        )
        delay_env = await ScenarioService.run_scenario(session, DEMO_ORG_ID, req_delay)
        assert delay_env.status == ToolStatus.OK

        # Step 4: Combined Scenario (Hire 2 devs AND Apex pays 30 days late)
        req_combined = ScenarioRunRequest(
            baseline_run_id=baseline_run.id,
            horizon_weeks=26,
            scenario=ScenarioPayload(
                name=golden["demo_scenario"]["name"],
                changes=[
                    ScenarioChange(
                        lever="hire",
                        op="set",
                        value=2,
                        params={"count": 2, "monthly_cost": "7000.00"},
                        start_date=date(2026, 11, 1),
                    ),
                    ScenarioChange(
                        lever="payment_delay",
                        op="set",
                        value=30,
                        params={"client": golden["concentrated_client"]["name"], "days": 30},
                    ),
                ],
            ),
        )
        combined_env = await ScenarioService.run_scenario(session, DEMO_ORG_ID, req_combined)
        assert combined_env.status == ToolStatus.OK
        combined_data = combined_env.data

        expected_case = combined_data["cases"]["expected"]
        worst_case = combined_data["cases"]["worst"]
        best_case = combined_data["cases"]["best"]

        # Expected case checks: cash floor breach
        assert expected_case["reserve_breach"] is False
        assert expected_case["cash_floor_breach"] is True
        assert expected_case["min_cash"] == golden["demo_scenario"]["cases"]["expected"]["min_cash"]

        # Worst case checks: reserve & cash floor breach
        assert worst_case["reserve_breach"] is True
        assert worst_case["cash_floor_breach"] is True
        assert worst_case["min_cash"] == golden["demo_scenario"]["cases"]["worst"]["min_cash"]

        # Best case checks: safe
        assert best_case["reserve_breach"] is False
        assert best_case["min_cash"] == golden["demo_scenario"]["cases"]["best"]["min_cash"]

        # Step 5: Open evidence drawer on a forecast point with contributing transactions
        point_with_events = next(p for p in points if p.contributing_inflow_refs or p.contributing_outflow_refs)
        lineage_res = await LineageResolver.get_point_lineage(session, DEMO_ORG_ID, point_with_events.id)
        assert "formula" in lineage_res
        assert len(lineage_res["source_rows"]) > 0
