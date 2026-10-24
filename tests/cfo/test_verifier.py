from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4
import pytest

from packages.contracts.envelope import ResultStatus
from services.api.app.cfo.models import ForecastPoint, ForecastRun
from services.api.app.cfo.services.baseline_service import BaselineService
from services.api.app.cfo.verification.verifier import FinanceVerifier
from services.api.app.core.database import async_session_factory
from services.api.seed.seed_data import SEED_ORGS

DEMO_ORG_ID = SEED_ORGS[0]["id"]


@pytest.mark.asyncio
async def test_v1_and_v5_clean_verification():
    async with async_session_factory() as session:
        run, points = await BaselineService.get_latest_baseline(session, DEMO_ORG_ID)
        status, warnings = FinanceVerifier.verify_run(run, points)
        # Baseline flags cash floor risk per canonical demo story -> status is WARNING with reasons
        assert status in (ResultStatus.VERIFIED, ResultStatus.WARNING)
        if run.cash_floor_breach or run.reserve_breach:
            assert status == ResultStatus.WARNING
            assert len(warnings) > 0
        else:
            assert status == ResultStatus.VERIFIED


def test_v1_failure_on_tampered_arithmetic():
    run = ForecastRun(
        id=uuid4(),
        org_id=uuid4(),
        case_type="baseline",
        engine_version="0.1.0",
        horizon_weeks=2,
        start_date=date(2026, 11, 2),
        end_date=date(2026, 11, 16),
        min_cash=Decimal("110000.00"),
        min_cash_date=date(2026, 11, 2),
        end_cash=Decimal("120000.00"),
    )

    p1 = ForecastPoint(
        id=uuid4(),
        org_id=run.org_id,
        run_id=run.id,
        week_number=1,
        week_start=date(2026, 11, 2),
        opening_cash=Decimal("100000.00"),
        projected_inflows=Decimal("10000.00"),
        projected_outflows=Decimal("0.00"),
        net_cash_flow=Decimal("10000.00"),
        closing_cash=Decimal("110000.00"),
    )

    # Corrupt p2 arithmetic: closing_cash says 150000 instead of 120000
    p2 = ForecastPoint(
        id=uuid4(),
        org_id=run.org_id,
        run_id=run.id,
        week_number=2,
        week_start=date(2026, 11, 9),
        opening_cash=Decimal("110000.00"),
        projected_inflows=Decimal("10000.00"),
        projected_outflows=Decimal("0.00"),
        net_cash_flow=Decimal("10000.00"),
        closing_cash=Decimal("150000.00"),  # TAMPERED
    )

    status, errs = FinanceVerifier.verify_run(run, [p1, p2])
    assert status == ResultStatus.FAILED
    assert any("V1 Failed" in e for e in errs)


def test_v5_failure_on_date_gap():
    run = ForecastRun(
        id=uuid4(),
        org_id=uuid4(),
        case_type="baseline",
        engine_version="0.1.0",
        horizon_weeks=2,
        start_date=date(2026, 11, 2),
        end_date=date(2026, 11, 23),
        min_cash=Decimal("100000.00"),
        min_cash_date=date(2026, 11, 2),
        end_cash=Decimal("100000.00"),
    )

    p1 = ForecastPoint(
        id=uuid4(),
        org_id=run.org_id,
        run_id=run.id,
        week_number=1,
        week_start=date(2026, 11, 2),
        opening_cash=Decimal("100000.00"),
        projected_inflows=Decimal("0.00"),
        projected_outflows=Decimal("0.00"),
        net_cash_flow=Decimal("0.00"),
        closing_cash=Decimal("100000.00"),
    )

    # 14 days later instead of 7 days
    p2 = ForecastPoint(
        id=uuid4(),
        org_id=run.org_id,
        run_id=run.id,
        week_number=2,
        week_start=date(2026, 11, 16),
        opening_cash=Decimal("100000.00"),
        projected_inflows=Decimal("0.00"),
        projected_outflows=Decimal("0.00"),
        net_cash_flow=Decimal("0.00"),
        closing_cash=Decimal("100000.00"),
    )

    status, errs = FinanceVerifier.verify_run(run, [p1, p2])
    assert status == ResultStatus.FAILED
    assert any("V5 Failed" in e for e in errs)


def test_v4_failure_on_tampered_baseline_hash():
    baseline = ForecastRun(
        id=uuid4(),
        org_id=uuid4(),
        case_type="baseline",
        baseline_hash="hash_alpha_123",
    )
    scenario_run = ForecastRun(
        id=uuid4(),
        org_id=baseline.org_id,
        case_type="expected",
        min_cash=Decimal("50000.00"),
        end_cash=Decimal("50000.00"),
        baseline_hash="hash_MODIFIED_456",  # Diverged!
    )
    pt = ForecastPoint(
        id=uuid4(),
        org_id=baseline.org_id,
        run_id=scenario_run.id,
        week_number=1,
        week_start=date(2026, 11, 2),
        opening_cash=Decimal("50000.00"),
        projected_inflows=Decimal("0.00"),
        projected_outflows=Decimal("0.00"),
        net_cash_flow=Decimal("0.00"),
        closing_cash=Decimal("50000.00"),
    )

    status, errs = FinanceVerifier.verify_run(scenario_run, [pt], baseline_run=baseline)
    assert status == ResultStatus.FAILED
    assert any("V4 Failed" in e for e in errs)
