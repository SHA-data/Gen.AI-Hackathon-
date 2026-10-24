from datetime import date
from decimal import Decimal
from uuid import uuid4
import pytest

from packages.contracts.envelope import ResultStatus, ToolResultEnvelope, ToolStatus
from packages.contracts.fake_service import (
    DEMO_BASELINE_RUN_ID,
    DEMO_ORG_A_ID,
    FakeCfoSnapshotService,
    FakeFinanceService,
)
from packages.contracts.finance import (
    CfoSnapshotData,
    MetricResultData,
    ScenarioCases,
    ScenarioChange,
    ScenarioPayload,
    ScenarioRunData,
    ScenarioRunRequest,
)


def test_fake_cfo_snapshot_service():
    envelope = FakeCfoSnapshotService.get(DEMO_ORG_A_ID)
    assert envelope.status == ToolStatus.OK
    assert envelope.run_id == str(DEMO_BASELINE_RUN_ID)
    assert len(envelope.sources) > 0

    snapshot = CfoSnapshotData.model_validate(envelope.data)
    assert snapshot.cash == Decimal("185000.00")
    assert snapshot.burn == Decimal("42000.00")
    assert snapshot.revenue == Decimal("65000.00")
    assert snapshot.receivables == Decimal("98000.00")
    assert snapshot.payroll == Decimal("36000.00")
    assert snapshot.currency == "USD"


def test_fake_finance_get_metric():
    envelope = FakeFinanceService.get_metric(DEMO_ORG_A_ID, "cash")
    assert envelope.status == ToolStatus.OK
    metric_data = MetricResultData.model_validate(envelope.data)
    assert metric_data.metric == "cash"
    assert metric_data.value == Decimal("185000.00")
    assert metric_data.currency == "USD"


def test_fake_finance_run_scenario():
    req = ScenarioRunRequest(
        baseline_run_id=DEMO_BASELINE_RUN_ID,
        horizon_weeks=26,
        scenario=ScenarioPayload(
            name="hire_and_delay",
            changes=[
                ScenarioChange(lever="hire", op="set", value=2, params={"monthly_cost": "7000"}),
                ScenarioChange(lever="payment_delay", op="set", value=30, params={"client": "Apex Corp"}),
            ],
        ),
    )

    envelope = FakeFinanceService.run_scenario(DEMO_ORG_A_ID, req)
    assert envelope.status == ToolStatus.OK
    assert envelope.run_id is not None

    run_data = ScenarioRunData.model_validate(envelope.data)
    assert run_data.status == ResultStatus.VERIFIED
    assert run_data.currency == "USD"
    assert len(run_data.cases.expected.weekly_cash) == 26
    assert run_data.cases.expected.min_cash == Decimal("18400.00")
    assert run_data.cases.worst.cash_floor_breach is True
    assert run_data.cases.worst.runway_weeks == 12


def test_fake_finance_list_source_rows():
    envelope = FakeFinanceService.list_source_rows(DEMO_ORG_A_ID)
    assert envelope.status == ToolStatus.OK
    assert envelope.data["count"] == 3
    assert len(envelope.sources) == 3


def test_fake_finance_explain_change():
    envelope = FakeFinanceService.explain_change(
        DEMO_ORG_A_ID, "cash", date(2026, 10, 1), date(2026, 10, 31)
    )
    assert envelope.status == ToolStatus.OK
    assert "drivers" in envelope.data
    assert len(envelope.data["drivers"]) >= 2
