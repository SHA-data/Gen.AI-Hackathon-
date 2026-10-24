from datetime import date
from decimal import Decimal
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from packages.contracts.envelope import ResultStatus, ToolStatus
from packages.contracts.finance import (
    ScenarioChange,
    ScenarioPayload,
    ScenarioRunRequest,
)
from services.api.app.cfo.models import ForecastRun, Invoice
from services.api.app.cfo.services.baseline_service import BaselineService
from services.api.app.cfo.services.scenario_service import ScenarioService
from services.api.app.core.auth import create_access_token
from services.api.app.core.database import async_session_factory
from services.api.app.main import app
from services.api.seed.seed_data import SEED_ORGS

DEMO_ORG_ID = SEED_ORGS[0]["id"]


@pytest.mark.asyncio
async def test_run_scenario_three_cases_and_baseline_immutability():
    async with async_session_factory() as session:
        # 1. Ensure baseline exists
        baseline_run, _ = await BaselineService.run_baseline(session, DEMO_ORG_ID, horizon_weeks=26)
        initial_hash = baseline_run.baseline_hash
        assert initial_hash is not None

        # 2. Run Hire 2 Devs + Apex 30-Day Delay scenario
        req = ScenarioRunRequest(
            baseline_run_id=baseline_run.id,
            horizon_weeks=26,
            scenario=ScenarioPayload(
                name="hire_two_devs_with_apex_delay",
                origin="user",
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
                        params={"client": "Apex Corp", "days": 30},
                    ),
                ],
            ),
        )

        envelope = await ScenarioService.run_scenario(session, DEMO_ORG_ID, req)
        assert envelope.status == ToolStatus.OK
        assert envelope.run_id is not None
        data = envelope.data

        # Check 3 cases present
        assert "cases" in data
        assert "expected" in data["cases"]
        assert "best" in data["cases"]
        assert "worst" in data["cases"]

        expected_case = data["cases"]["expected"]
        worst_case = data["cases"]["worst"]
        best_case = data["cases"]["best"]

        # Expected case should show the cash dip
        assert len(expected_case["weekly_cash"]) == 26
        # Worst case cash is lower than expected
        assert Decimal(worst_case["min_cash"]) <= Decimal(expected_case["min_cash"])
        # Best case cash is higher than expected
        assert Decimal(best_case["min_cash"]) >= Decimal(expected_case["min_cash"])

        # 3. Assert baseline hash remains strictly immutable
        refreshed_baseline = await session.get(ForecastRun, baseline_run.id)
        assert refreshed_baseline.baseline_hash == initial_hash


@pytest.mark.asyncio
async def test_payment_delay_does_not_modify_invoices_table():
    async with async_session_factory() as session:
        # Check original expected date of Apex invoice in DB
        stmt = select(Invoice).where(
            Invoice.org_id == DEMO_ORG_ID,
            Invoice.client_or_vendor == "Apex Corp",
        ).order_by(Invoice.issue_date)
        apex_inv = (await session.execute(stmt)).scalars().first()
        orig_expected_date = apex_inv.expected_payment_date

        # Run scenario with 45-day delay on Apex
        baseline_res = await BaselineService.get_latest_baseline(session, DEMO_ORG_ID)
        baseline_run, _ = baseline_res

        req = ScenarioRunRequest(
            baseline_run_id=baseline_run.id,
            horizon_weeks=26,
            scenario=ScenarioPayload(
                name="apex_45d_delay",
                changes=[
                    ScenarioChange(
                        lever="payment_delay",
                        op="set",
                        value=45,
                        params={"client": "Apex Corp", "days": 45},
                    )
                ],
            ),
        )
        await ScenarioService.run_scenario(session, DEMO_ORG_ID, req)

        # Check that DB invoice expected_payment_date is completely UNTOUCHED
        refreshed_inv = await session.get(Invoice, apex_inv.id)
        assert refreshed_inv.expected_payment_date == orig_expected_date


@pytest.mark.asyncio
async def test_http_scenario_run_and_compare_api():
    token = create_access_token(user_id=uuid4(), org_id=DEMO_ORG_ID, role="member")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Fetch baseline
        b_resp = await client.get("/v1/finance/baseline", headers={"Authorization": f"Bearer {token}"})
        assert b_resp.status_code == 200
        baseline_id = b_resp.json()["run_id"]

        # Run Scenario via Contract v1
        payload = {
            "baseline_run_id": baseline_id,
            "horizon_weeks": 26,
            "scenario": {
                "name": "api_test_scenario",
                "origin": "user",
                "changes": [
                    {
                        "lever": "revenue_change_pct",
                        "op": "set",
                        "value": 15,
                        "params": {},
                        "is_assumption": True,
                    }
                ],
            },
        }

        resp = await client.post(
            "/v1/finance/scenarios/run",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        res = resp.json()
        assert res["status"] == "ok"
        assert res["data"]["engine_version"] == "0.1.0"
        assert "expected" in res["data"]["cases"]
