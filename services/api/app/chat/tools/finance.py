"""Finance tool wrappers registered in Chatbot (Part A5, Part A6)."""
from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from packages.contracts.envelope import ToolResultEnvelope
from packages.contracts.finance import (
    FakeFinanceService,
    FinanceService,
    MetricRequest,
    MetricResponseData,
    ScenarioChange,
    ScenarioDefinition,
    ScenarioRunRequest,
    ScenarioRunResponseData,
    SourceRowData,
    ExplainChangeData,
)
from services.api.app.core.auth import AuthContext
from services.api.app.core.config import settings

# Global or swappable finance service instance
_finance_service: FinanceService = FakeFinanceService()

def set_finance_service(service: FinanceService):
    global _finance_service
    _finance_service = service

def get_finance_service() -> FinanceService:
    return _finance_service

# --- Input Schemas ---

class GetMetricArgs(BaseModel):
    metric_name: str
    period_start: Optional[date] = None
    period_end: Optional[date] = None

class ScenarioChangeArg(BaseModel):
    lever: str
    op: str = "add"
    value: Any
    start_date: Optional[date] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    is_assumption: bool = False

class RunScenarioArgs(BaseModel):
    name: str
    horizon_weeks: int = 26
    changes: List[ScenarioChangeArg] = Field(default_factory=list)
    baseline_run_id: Optional[UUID] = None

class ListSourceRowsArgs(BaseModel):
    row_ids: List[UUID]

class ExplainChangeArgs(BaseModel):
    metric_name: str
    period_start: Optional[date] = None
    period_end: Optional[date] = None

# --- Handler Functions ---

async def handle_get_metric(auth: AuthContext, metric_name: str, period_start: Optional[date] = None, period_end: Optional[date] = None) -> ToolResultEnvelope[MetricResponseData]:
    req = MetricRequest(metric_name=metric_name, period_start=period_start, period_end=period_end)
    return await _finance_service.get_metric(auth.org_id, req)

async def handle_run_scenario(auth: AuthContext, name: str, horizon_weeks: int = 26, changes: List[Any] = None, baseline_run_id: Optional[UUID] = None) -> ToolResultEnvelope[ScenarioRunResponseData]:
    def _val(c, field, default=None):
        return getattr(c, field, None) if hasattr(c, field) else c.get(field, default)

    changes_list = changes or []
    for c in changes_list:
        lever = _val(c, "lever")
        val = _val(c, "value")
        if lever == "hire" and (not val or val == 0):
            return ToolResultEnvelope(
                status="warning",
                data={},
                sources=[],
                warnings=["needs_input: Please specify the number of developers to hire and expected monthly cost."],
                run_id=None,
            )

    definition = ScenarioDefinition(
        name=name,
        origin="user",
        changes=[
            ScenarioChange(
                lever=_val(c, "lever"),
                op=_val(c, "op", "add"),
                value=_val(c, "value"),
                start_date=_val(c, "start_date"),
                params=_val(c, "params", {}),
                is_assumption=_val(c, "is_assumption", False),
            )
            for c in changes_list
        ],
    )
    req = ScenarioRunRequest(
        baseline_run_id=baseline_run_id or uuid4(),
        horizon_weeks=horizon_weeks,
        scenario=definition,
    )
    return await _finance_service.run_scenario(auth.org_id, req)

async def handle_list_source_rows(auth: AuthContext, row_ids: List[UUID]) -> ToolResultEnvelope[List[SourceRowData]]:
    return await _finance_service.list_source_rows(auth.org_id, row_ids)

async def handle_explain_change(auth: AuthContext, metric_name: str, period_start: Optional[date] = None, period_end: Optional[date] = None) -> ToolResultEnvelope[ExplainChangeData]:
    start = period_start or date(2026, 9, 1)
    end = period_end or date(2026, 9, 30)
    return await _finance_service.explain_change(auth.org_id, metric_name, start, end)
