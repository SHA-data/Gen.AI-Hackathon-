"""Shared Finance Engine Contract v1 (Part A5 & Moonshot Mode Part 2).
Canonical contract between NeuralCFO (Sharjeel), Moonshot (Aleena), and Chatbot (Aroon).
"""
from __future__ import annotations

import asyncio
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional, Protocol, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from packages.contracts.envelope import ToolResultEnvelope

LEVER_REGISTRY = {
    "hire": ["count", "monthly_cost", "start_date"],
    "payment_delay": ["client", "invoice", "days"],
    "payment_terms_days": ["days", "start_date"],
    "deposit_pct": ["percent", "start_date"],
    "revenue_change_pct": ["percent", "start_date"],
    "lost_client": ["client", "date"],
    "price_change_pct": ["percent", "start_date", "scope"],
    "expense_change": ["amount", "cadence", "start_date"],
}

class ScenarioChange(BaseModel):
    lever: str
    op: Literal["set", "add", "multiply"]
    value: Any
    start_date: Optional[date] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    is_assumption: bool = False

class ScenarioDefinition(BaseModel):
    name: str
    origin: Literal["user", "moonshot_card"] = "user"
    source_card_id: Optional[UUID] = None
    changes: List[ScenarioChange] = Field(default_factory=list)

# Backward-compatibility alias
ScenarioPayload = ScenarioDefinition

class ScenarioRunRequest(BaseModel):
    baseline_run_id: UUID
    horizon_weeks: int = Field(default=26, ge=1, le=104)
    scenario: ScenarioDefinition

class WeeklyCashPoint(BaseModel):
    week_start: date
    cash: str  # Decimal string per Part A5

class CaseResult(BaseModel):
    weekly_cash: List[WeeklyCashPoint]
    min_cash: str
    min_cash_date: date
    end_cash: str
    runway_weeks: Optional[int] = None
    reserve_breach: bool = False
    cash_floor_breach: bool = False

class ScenarioCases(BaseModel):
    """Scenario Cases model supporting both attribute access and dict-style items()."""
    expected: CaseResult
    best: CaseResult
    worst: CaseResult

    def items(self):
        return [("expected", self.expected), ("best", self.best), ("worst", self.worst)]

    def __getitem__(self, item: str) -> CaseResult:
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def __contains__(self, item: object) -> bool:
        return item in ("expected", "best", "worst")

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

class ScenarioRunResponse(BaseModel):
    run_id: UUID
    status: Literal["verified", "warning", "unverified", "failed"] = "verified"
    engine_version: str = "1.0.0"
    currency: str = "USD"
    cases: ScenarioCases
    assumptions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    source_row_refs: List[UUID] = Field(default_factory=list)
    evidence_refs: List[UUID] = Field(default_factory=list)

    def __await__(self):
        async def _identity():
            return self
        return _identity().__await__()

# Backward-compatibility alias
ScenarioRunResponseData = ScenarioRunResponse

class CfoSnapshot(BaseModel):
    org_id: UUID
    currency: str = "USD"
    cash: str
    burn: str = "25000.00"
    revenue: str = "45000.00"
    receivables: str = "18500.00"
    payroll: str = "24000.00"
    baseline_run_id: UUID
    as_of_date: Optional[date] = None
    runway_weeks: int = 16
    cash_floor_weeks: int = 12

class MetricRequest(BaseModel):
    metric_name: str
    period_start: Optional[date] = None
    period_end: Optional[date] = None

class MetricResponseData(BaseModel):
    metric_name: str
    amount: str
    currency: str = "USD"
    period_start: date
    period_end: date
    source_row_ids: List[UUID] = Field(default_factory=list)

class SourceRowData(BaseModel):
    id: UUID
    transaction_date: date
    description: str
    amount: str
    category: str
    currency: str = "USD"

class ExplainChangeData(BaseModel):
    metric_name: str
    period_start: date
    period_end: date
    change_amount: str
    percentage_change: str
    primary_drivers: List[Dict[str, Any]] = Field(default_factory=list)
    source_row_ids: List[UUID] = Field(default_factory=list)

class FinanceService(Protocol):
    """Service interface published by Sharjeel (NeuralCFO)."""
    async def run_scenario(self, org_id: UUID, request: ScenarioRunRequest) -> ToolResultEnvelope[ScenarioRunResponseData]:
        ...

    async def get_metric(self, org_id: UUID, request: MetricRequest) -> ToolResultEnvelope[MetricResponseData]:
        ...

    async def list_source_rows(self, org_id: UUID, row_ids: List[UUID]) -> ToolResultEnvelope[List[SourceRowData]]:
        ...

    async def explain_change(self, org_id: UUID, metric_name: str, period_start: date, period_end: date) -> ToolResultEnvelope[ExplainChangeData]:
        ...


class AwaitableEnvelope(ToolResultEnvelope):
    def __await__(self):
        async def _identity():
            return self
        return _identity().__await__()


class FakeFinanceService:
    """Runnable fake supporting both Chatbot async ToolResultEnvelope and Moonshot ScenarioRunResponse."""
    def __init__(self, baseline_cash: float = 120_000.0, monthly_burn: float = 25_000.0):
        self.baseline_cash = float(baseline_cash)
        self.monthly_burn = float(monthly_burn)
        self.default_baseline_run_id = uuid4()
        self.baseline_run_id = uuid4()

    def get_snapshot(self, org_id: UUID) -> CfoSnapshot:
        return CfoSnapshot(
            org_id=org_id,
            currency="USD",
            cash=f"{self.baseline_cash:.2f}",
            burn=f"{self.monthly_burn:.2f}",
            revenue="45000.00",
            receivables="18500.00",
            payroll="24000.00",
            baseline_run_id=self.baseline_run_id,
            as_of_date=date.today(),
            runway_weeks=max(4, int(self.baseline_cash / max(1.0, (self.monthly_burn / 4.33)))),
            cash_floor_weeks=12,
        )

    def run_scenario(self, arg1: Any, arg2: Any = None) -> Any:
        today = date.today()
        run_id = uuid4()

        if isinstance(arg1, ScenarioRunRequest):
            # Moonshot call: (request, org_id)
            request = arg1
            org_id = arg2 or uuid4()
            
            net_cash_delta = 0.0
            upfront_impact = 0.0

            for change in request.scenario.changes:
                val = float(change.value) if isinstance(change.value, (int, float, str)) and str(change.value).replace(".", "", 1).isdigit() else 0.0
                if change.lever == "price_change_pct":
                    net_cash_delta += val * 1200.0
                elif change.lever == "deposit_pct":
                    net_cash_delta += val * 450.0
                elif change.lever == "hire":
                    upfront_impact -= val * 6000.0
                elif change.lever == "expense_change":
                    net_cash_delta -= val

            expected_end = self.baseline_cash + net_cash_delta + upfront_impact
            expected_min = min(self.baseline_cash, expected_end)
            
            best_end = expected_end + 15_000.0
            best_min = expected_min + 5_000.0
            
            worst_end = expected_end - 22_000.0
            worst_min = expected_min - 18_000.0
            
            worst_runway = max(2, int((worst_min / max(1.0, (self.monthly_burn / 4.33)))))
            expected_runway = max(4, int((expected_min / max(1.0, (self.monthly_burn / 4.33)))))
            best_runway = max(6, int((best_min / max(1.0, (self.monthly_burn / 4.33)))))

            reserve_threshold = (self.monthly_burn / 4.33) * 12
            expected_floor_breach = expected_min < reserve_threshold
            worst_floor_breach = worst_min < reserve_threshold

            def make_moonshot_case(end_c: float, min_c: float, runway: int, floor_b: bool) -> CaseResult:
                pts = [
                    WeeklyCashPoint(week_start=today, cash=f"{self.baseline_cash:.2f}"),
                    WeeklyCashPoint(week_start=today + timedelta(weeks=request.horizon_weeks), cash=f"{end_c:.2f}"),
                ]
                return CaseResult(
                    weekly_cash=pts,
                    min_cash=f"{min_c:.2f}",
                    min_cash_date=today,
                    end_cash=f"{end_c:.2f}",
                    runway_weeks=runway,
                    reserve_breach=floor_b,
                    cash_floor_breach=floor_b,
                )

            return ScenarioRunResponse(
                run_id=run_id,
                status="verified",
                engine_version="1.0.0",
                currency="USD",
                cases=ScenarioCases(
                    expected=make_moonshot_case(expected_end, expected_min, expected_runway, expected_floor_breach),
                    best=make_moonshot_case(best_end, best_min, best_runway, False),
                    worst=make_moonshot_case(worst_end, worst_min, worst_runway, worst_floor_breach),
                ),
                assumptions=[f"Scenario applied: {request.scenario.name}"],
                warnings=[],
                source_row_refs=[],
                evidence_refs=[],
            )

        # Chatbot call: (org_id, request)
        org_id = arg1
        request = arg2

        weekly_series: List[WeeklyCashPoint] = []
        base_cash = Decimal(f"{self.baseline_cash:.2f}")
        min_cash = base_cash
        min_cash_date = today

        is_hire = any(c.lever == "hire" for c in request.scenario.changes)
        is_delay = any(c.lever == "payment_delay" for c in request.scenario.changes)

        weekly_burn = Decimal(f"{self.monthly_burn / 4.33:.2f}")
        if is_hire:
            weekly_burn += Decimal("3000.00")
        delay_impact = Decimal("40000.00") if is_delay else Decimal("0.00")

        current = base_cash - delay_impact
        for i in range(request.horizon_weeks):
            week_date = today + timedelta(weeks=i)
            current -= weekly_burn
            if current < min_cash:
                min_cash = current
                min_cash_date = week_date
            weekly_series.append(WeeklyCashPoint(week_start=week_date, cash=f"{current:.2f}"))

        runway = None
        for idx, pt in enumerate(weekly_series):
            if Decimal(pt.cash) < 0:
                runway = idx
                break

        case_expected = CaseResult(
            weekly_cash=weekly_series,
            min_cash=f"{min_cash:.2f}",
            min_cash_date=min_cash_date,
            end_cash=weekly_series[-1].cash,
            runway_weeks=runway or 24,
            reserve_breach=(min_cash < Decimal("30000.00")),
            cash_floor_breach=(min_cash < Decimal("15000.00")),
        )
        case_best = CaseResult(
            weekly_cash=weekly_series,
            min_cash=f"{min_cash + Decimal('20000.00'):.2f}",
            min_cash_date=min_cash_date,
            end_cash=f"{Decimal(weekly_series[-1].cash) + Decimal('25000.00'):.2f}",
            runway_weeks=32,
            reserve_breach=False,
            cash_floor_breach=False,
        )
        case_worst = CaseResult(
            weekly_cash=weekly_series,
            min_cash=f"{min_cash - Decimal('30000.00'):.2f}",
            min_cash_date=min_cash_date,
            end_cash=f"{Decimal(weekly_series[-1].cash) - Decimal('40000.00'):.2f}",
            runway_weeks=max(4, (runway or 16) - 4),
            reserve_breach=True,
            cash_floor_breach=True,
        )

        cases_obj = ScenarioCases(expected=case_expected, best=case_best, worst=case_worst)

        response_data = ScenarioRunResponse(
            run_id=run_id,
            status="verified",
            engine_version="1.0.0",
            currency="USD",
            cases=cases_obj,
            assumptions=[f"Scenario applied: {request.scenario.name}", "Weekly series canonical from forecast schedule"],
            warnings=["Uncertain payments delayed 14d in worst case"] if is_delay else [],
            source_row_refs=[uuid4()],
            evidence_refs=[uuid4()],
        )

        row_ref = response_data.source_row_refs[0]
        evidence_ref = response_data.evidence_refs[0]
        return AwaitableEnvelope(
            status="ok",
            data=response_data,
            sources=[row_ref, evidence_ref],
            warnings=[],
            run_id=run_id,
        )

    async def get_metric(self, org_id: UUID, request: MetricRequest) -> ToolResultEnvelope[MetricResponseData]:
        today = date.today()
        ref = uuid4()
        amounts = {
            "cash": "120000.00",
            "burn": "22000.00",
            "revenue": "85000.00",
            "receivables": "45000.00",
            "payroll": "32000.00",
            "spend": "38500.00",
        }
        amount = amounts.get(request.metric_name.lower(), "50000.00")
        return ToolResultEnvelope(
            status="ok",
            data=MetricResponseData(
                metric_name=request.metric_name,
                amount=amount,
                currency="USD",
                period_start=request.period_start or (today - timedelta(days=30)),
                period_end=request.period_end or today,
                source_row_ids=[ref],
            ),
            sources=[ref],
            warnings=[],
            run_id=uuid4(),
        )

    async def list_source_rows(self, org_id: UUID, row_ids: List[UUID]) -> ToolResultEnvelope[List[SourceRowData]]:
        today = date.today()
        rows = [
            SourceRowData(
                id=rid,
                transaction_date=today - timedelta(days=7),
                description=f"Synthetic Transaction for Ref {str(rid)[:8]}",
                amount="15000.00",
                category="Accounts Receivable",
                currency="USD",
            )
            for rid in row_ids
        ]
        return ToolResultEnvelope(status="ok", data=rows, sources=row_ids, warnings=[], run_id=uuid4())

    async def explain_change(self, org_id: UUID, metric_name: str, period_start: date, period_end: date) -> ToolResultEnvelope[ExplainChangeData]:
        ref = uuid4()
        return ToolResultEnvelope(
            status="ok",
            data=ExplainChangeData(
                metric_name=metric_name,
                period_start=period_start,
                period_end=period_end,
                change_amount="-18000.00",
                percentage_change="-15.0%",
                primary_drivers=[
                    {"factor": "Delayed invoice from Client Alpha", "impact": "-25000.00"},
                    {"factor": "Annual software renewal", "impact": "-7000.00"},
                    {"factor": "New project deposit", "impact": "+14000.00"},
                ],
                source_row_ids=[ref],
            ),
            sources=[ref],
            warnings=[],
            run_id=uuid4(),
        )
