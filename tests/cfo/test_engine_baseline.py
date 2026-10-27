from datetime import date
from decimal import Decimal
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient

from services.api.app.cfo.engine.calculator import ForecastEngine
from services.api.app.cfo.services.baseline_service import BaselineService
from services.api.app.core.auth import create_access_token
from services.api.app.core.database import async_session_factory
from services.api.app.main import app
from services.api.seed.seed_data import SEED_ORGS

DEMO_ORG_ID = SEED_ORGS[0]["id"]


def test_cash_arithmetic_matches_exact_cents():
    opening = Decimal("100000.50")
    as_of = date(2026, 11, 2)  # Monday

    inflows = [
        (date(2026, 11, 4), Decimal("25000.25"), uuid4()),
        (date(2026, 11, 12), Decimal("15000.10"), uuid4()),
    ]
    outflows = [
        (date(2026, 11, 6), Decimal("12000.35"), uuid4()),
        (date(2026, 11, 14), Decimal("8000.50"), uuid4()),
    ]

    res = ForecastEngine.calculate_forecast(
        opening_cash=opening,
        opening_cash_date=as_of,
        inflow_events=inflows,
        outflow_events=outflows,
        horizon_weeks=2,
    )

    # Week 1:
    # opening: 100000.50
    # in: 25000.25, out: 12000.35 => net = +12999.90
    # closing: 112999.90 + 0.50 = 113000.40
    assert res.points[0].closing_cash == Decimal("113000.40")

    # Week 2:
    # opening: 113000.40
    # in: 15000.10, out: 8000.50 => net = +6999.60
    # closing: 113000.40 + 6999.60 = 120000.00
    assert res.points[1].closing_cash == Decimal("120000.00")
    assert res.end_cash == Decimal("120000.00")
    assert res.runway_weeks is None


def test_runway_scan_detects_insolvency_week():
    opening = Decimal("20000.00")
    as_of = date(2026, 11, 2)

    # Big outflow in week 3 that pushes cash into negative
    outflows = [
        (date(2026, 11, 4), Decimal("5000.00"), uuid4()),
        (date(2026, 11, 11), Decimal("5000.00"), uuid4()),
        (date(2026, 11, 18), Decimal("25000.00"), uuid4()),  # Cash = 10,000 - 25,000 = -15,000
    ]

    res = ForecastEngine.calculate_forecast(
        opening_cash=opening,
        opening_cash_date=as_of,
        inflow_events=[],
        outflow_events=outflows,
        horizon_weeks=6,
    )

    assert res.runway_weeks == 3
    assert res.min_cash == Decimal("-15000.00")


def test_reserve_and_cash_floor_breaches():
    opening = Decimal("60000.00")
    as_of = date(2026, 11, 2)

    # Outflow of $20,000 in week 1 drops cash to $40,000 (< $50,000 reserve)
    outflows = [(date(2026, 11, 4), Decimal("20000.00"), uuid4())]

    res = ForecastEngine.calculate_forecast(
        opening_cash=opening,
        opening_cash_date=as_of,
        inflow_events=[],
        outflow_events=outflows,
        horizon_weeks=4,
        reserve_amount=Decimal("50000.00"),
        cash_floor_weeks=12,
    )

    assert res.reserve_breach is True
    # Committed outflow average = 20,000 / 4 = 5,000/wk. 12 weeks = 60,000 floor.
    # Closing cash 40,000 is < 60,000 => cash_floor_breach = True
    assert res.cash_floor_breach is True
    assert res.cash_risk is True


@pytest.mark.asyncio
async def test_baseline_service_generates_and_persists_run():
    async with async_session_factory() as session:
        run, points = await BaselineService.run_baseline(session, DEMO_ORG_ID, horizon_weeks=26)
        assert run.id is not None
        assert run.case_type == "baseline"
        assert len(points) == 26
        assert run.baseline_hash is not None
        assert run.status == "verified"
        assert run.min_cash > Decimal("0.00")

    # Test HTTP Baseline API
    member_token = create_access_token(user_id=uuid4(), org_id=DEMO_ORG_ID, role="member")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/v1/finance/baseline", headers={"Authorization": f"Bearer {member_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_type"] == "baseline"
        assert len(data["weekly_cash"]) == 26
        assert "baseline_hash" in data
