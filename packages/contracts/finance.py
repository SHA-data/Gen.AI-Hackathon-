"""Shared Finance Engine Contract v1 (Part A5).
Canonical contract between NeuralCFO (Sharjeel), Moonshot (Aleena), and Chatbot (Aroon).
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional, Protocol
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

class ScenarioRunResponseData(BaseModel):
    run_id: UUID
    status: Literal["verified", "warning", "unverified", "failed"]
    engine_version: str = "1.0.0"
    currency: str = "USD"
    cases: Dict[Literal["expected", "best", "worst"], CaseResult]
    assumptions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    source_row_refs: List[UUID] = Field(default_factory=list)
    evidence_refs: List[UUID] = Field(default_factory=list)

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

class FakeFinanceService:
    """Runnable fake for standalone Chatbot testing and decoupled development."""
    def __init__(self):
        self.default_baseline_run_id = uuid4()

    async def run_scenario(self, org_id: UUID, request: ScenarioRunRequest) -> ToolResultEnvelope[ScenarioRunResponseData]:
        today = date.today()
        run_id = uuid4()
        weekly_series: List[WeeklyCashPoint] = []
        base_cash = Decimal("120000.00")
        min_cash = base_cash
        min_cash_date = today

        # Check for hire or delay lever
        is_hire = any(c.lever == "hire" for c in request.scenario.changes)
        is_delay = any(c.lever == "payment_delay" for c in request.scenario.changes)

        weekly_burn = Decimal("5000.00")
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
            runway_weeks=runway,
            reserve_breach=(min_cash < Decimal("30000.00")),
            cash_floor_breach=(min_cash < Decimal("15000.00")),
        )
        case_best = CaseResult(
            weekly_cash=weekly_series,
            min_cash=f"{min_cash + Decimal('20000.00'):.2f}",
            min_cash_date=min_cash_date,
            end_cash=f"{Decimal(weekly_series[-1].cash) + Decimal('25000.00'):.2f}",
            runway_weeks=None,
            reserve_breach=False,
            cash_floor_breach=False,
        )
        case_worst = CaseResult(
            weekly_cash=weekly_series,
            min_cash=f"{min_cash - Decimal('30000.00'):.2f}",
            min_cash_date=min_cash_date,
            end_cash=f"{Decimal(weekly_series[-1].cash) - Decimal('40000.00'):.2f}",
            runway_weeks=max(4, runway - 4) if runway else 12,
            reserve_breach=True,
            cash_floor_breach=True,
        )

        row_ref = uuid4()
        evidence_ref = uuid4()
        return ToolResultEnvelope(
            status="ok",
            data=ScenarioRunResponseData(
                run_id=run_id,
                status="verified",
                engine_version="1.0.0-fake",
                currency="USD",
                cases={"expected": case_expected, "best": case_best, "worst": case_worst},
                assumptions=[f"Scenario applied: {request.scenario.name}", "Weekly series canonical from forecast schedule"],
                warnings=["Uncertain payments delayed 14d in worst case"] if is_delay else [],
                source_row_refs=[row_ref],
                evidence_refs=[evidence_ref],
            ),
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
