import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from packages.contracts.envelope import ResultStatus, ToolResultEnvelope, ToolStatus
from packages.contracts.finance import (
    CaseResult,
    CfoSnapshotData,
    MetricResultData,
    ScenarioCases,
    ScenarioRunData,
    ScenarioRunRequest,
    WeeklyCashPoint,
)

# Standard Canned UUIDs for Demo Integration
DEMO_ORG_A_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_BASELINE_RUN_ID = UUID("11111111-1111-1111-1111-111111111111")
DEMO_SOURCE_ROW_IDS = [
    UUID("22222222-2222-2222-2222-222222222201"),
    UUID("22222222-2222-2222-2222-222222222202"),
    UUID("22222222-2222-2222-2222-222222222203"),
]


class FakeCfoSnapshotService:
    """Read-only CFO snapshot service for Moonshot intake."""

    @classmethod
    def get(cls, org_id: UUID) -> ToolResultEnvelope:
        snapshot = CfoSnapshotData(
            cash=Decimal("185000.00"),
            burn=Decimal("42000.00"),
            revenue=Decimal("65000.00"),
            receivables=Decimal("98000.00"),
            payroll=Decimal("36000.00"),
            baseline_run_id=DEMO_BASELINE_RUN_ID,
            as_of_date=date(2026, 10, 22),
            currency="USD",
        )
        return ToolResultEnvelope(
            status=ToolStatus.OK,
            data=snapshot.model_dump(mode="json"),
            sources=[str(ref) for ref in DEMO_SOURCE_ROW_IDS],
            warnings=[],
            run_id=str(DEMO_BASELINE_RUN_ID),
        )


class FakeFinanceService:
    """Deterministic canned finance service for cross-module integration."""

    @classmethod
    def get_metric(
        cls,
        org_id: UUID,
        metric: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> ToolResultEnvelope:
        metric_normalized = metric.lower().strip()
        metric_values = {
            "cash": Decimal("185000.00"),
            "burn": Decimal("42000.00"),
            "revenue": Decimal("65000.00"),
            "receivables": Decimal("98000.00"),
            "payroll": Decimal("36000.00"),
            "runway": Decimal("18.00"),
        }
        val = metric_values.get(metric_normalized, Decimal("100000.00"))
        data = MetricResultData(
            metric=metric_normalized,
            value=val,
            currency="USD",
            from_date=from_date or date(2026, 10, 1),
            to_date=to_date or date(2026, 10, 31),
            source_row_refs=DEMO_SOURCE_ROW_IDS,
        )
        return ToolResultEnvelope(
            status=ToolStatus.OK,
            data=data.model_dump(mode="json"),
            sources=[str(ref) for ref in DEMO_SOURCE_ROW_IDS],
            warnings=[],
            run_id=str(DEMO_BASELINE_RUN_ID),
        )

    @classmethod
    def run_scenario(cls, org_id: UUID, request: ScenarioRunRequest) -> ToolResultEnvelope:
        start_monday = date(2026, 10, 26)
        expected_points: List[WeeklyCashPoint] = []
        best_points: List[WeeklyCashPoint] = []
        worst_points: List[WeeklyCashPoint] = []

        curr_exp = Decimal("185000.00")
        curr_best = Decimal("185000.00")
        curr_worst = Decimal("185000.00")

        # Canned 26-week simulation for demo story (hiring 2 devs + 30-day payment delay)
        # Expected: min cash 18400.00 in Feb 2027
        for w in range(request.horizon_weeks):
            week_date = start_monday + timedelta(weeks=w)
            # Simulated weekly burn and receipts
            if w == 4:  # late payment hit
                curr_exp -= Decimal("45000.00")
                curr_worst -= Decimal("55000.00")
                curr_best -= Decimal("30000.00")
            elif w > 2:  # salary impact of two hires (-$14,000/mo = -$3,500/wk)
                curr_exp -= Decimal("1500.00")
                curr_worst -= Decimal("2500.00")
                curr_best += Decimal("500.00")
            else:
                curr_exp += Decimal("1000.00")
                curr_worst -= Decimal("500.00")
                curr_best += Decimal("2000.00")

            expected_points.append(WeeklyCashPoint(week_start=week_date, cash=curr_exp))
            best_points.append(WeeklyCashPoint(week_start=week_date, cash=curr_best))
            worst_points.append(WeeklyCashPoint(week_start=week_date, cash=curr_worst))

        cases = ScenarioCases(
            expected=CaseResult(
                weekly_cash=expected_points,
                min_cash=Decimal("18400.00"),
                min_cash_date=date(2027, 2, 1),
                end_cash=Decimal("30100.00"),
                runway_weeks=None,
                reserve_breach=False,
                cash_floor_breach=False,
            ),
            best=CaseResult(
                weekly_cash=best_points,
                min_cash=Decimal("52000.00"),
                min_cash_date=date(2026, 11, 30),
                end_cash=Decimal("85000.00"),
                runway_weeks=None,
                reserve_breach=False,
                cash_floor_breach=False,
            ),
            worst=CaseResult(
                weekly_cash=worst_points,
                min_cash=Decimal("-4200.00"),
                min_cash_date=date(2027, 1, 18),
                end_cash=Decimal("-8900.00"),
                runway_weeks=12,
                reserve_breach=True,
                cash_floor_breach=True,
            ),
        )

        scenario_run_id = uuid.uuid4()
        run_data = ScenarioRunData(
            run_id=scenario_run_id,
            status=ResultStatus.VERIFIED,
            engine_version="0.1.0",
            currency="USD",
            cases=cases,
            assumptions=[
                "Two software engineers hired starting 2026-11-01 at $7,000/month each",
                "Client Apex payment delayed by 30 days (due 2026-11-15, expected 2026-12-15)",
            ],
            warnings=[
                "Worst-case scenario projects cash floor breach at week 12 ($ -4,200.00)",
            ],
            source_row_refs=DEMO_SOURCE_ROW_IDS,
            evidence_refs=[uuid.uuid4(), uuid.uuid4()],
        )

        return ToolResultEnvelope(
            status=ToolStatus.OK,
            data=run_data.model_dump(mode="json"),
            sources=[str(ref) for ref in DEMO_SOURCE_ROW_IDS],
            warnings=run_data.warnings,
            run_id=str(scenario_run_id),
        )

    @classmethod
    def list_source_rows(cls, org_id: UUID, ref: Optional[str] = None) -> ToolResultEnvelope:
        rows = [
            {
                "id": str(DEMO_SOURCE_ROW_IDS[0]),
                "row_number": 1,
                "data": {"client": "Apex Corp", "amount": "45000.00", "due_date": "2026-11-15", "type": "invoice"},
            },
            {
                "id": str(DEMO_SOURCE_ROW_IDS[1]),
                "row_number": 2,
                "data": {"client": "Beacon Media", "amount": "20000.00", "due_date": "2026-11-20", "type": "invoice"},
            },
            {
                "id": str(DEMO_SOURCE_ROW_IDS[2]),
                "row_number": 3,
                "data": {"category": "Payroll", "amount": "36000.00", "due_date": "2026-10-31", "type": "payroll"},
            },
        ]
        return ToolResultEnvelope(
            status=ToolStatus.OK,
            data={"rows": rows, "count": len(rows)},
            sources=[str(r["id"]) for r in rows],
            warnings=[],
            run_id=None,
        )

    @classmethod
    def explain_change(
        cls, org_id: UUID, metric: str, from_date: date, to_date: date
    ) -> ToolResultEnvelope:
        return ToolResultEnvelope(
            status=ToolStatus.OK,
            data={
                "metric": metric,
                "change_amount": "-22000.00",
                "drivers": [
                    {
                        "category": "Payroll Increase",
                        "impact": "-14000.00",
                        "description": "Two engineering hires onboarded",
                        "source_row_refs": [str(DEMO_SOURCE_ROW_IDS[2])],
                    },
                    {
                        "category": "Client Payment Delay",
                        "impact": "-45000.00",
                        "description": "Apex Corp receivable shifted +30 days",
                        "source_row_refs": [str(DEMO_SOURCE_ROW_IDS[0])],
                    },
                ],
            },
            sources=[str(ref) for ref in DEMO_SOURCE_ROW_IDS],
            warnings=[],
            run_id=None,
        )
