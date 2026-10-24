from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field, field_serializer, ConfigDict

from packages.contracts.envelope import ResultStatus, ToolResultEnvelope, ToolStatus


class LeverOp(str, Enum):
    SET = "set"
    ADD = "add"
    MULTIPLY = "multiply"


class ScenarioOrigin(str, Enum):
    USER = "user"
    MOONSHOT_CARD = "moonshot_card"


class ScenarioChange(BaseModel):
    lever: str = Field(..., description="Lever name from registry (e.g. hire, payment_delay)")
    op: LeverOp = Field(default=LeverOp.SET, description="Operation to apply: set, add, multiply")
    value: Union[Decimal, int, str] = Field(..., description="Value to apply")
    start_date: Optional[date] = Field(default=None, description="Effective start date")
    params: Dict[str, Any] = Field(default_factory=dict, description="Additional lever parameters")
    is_assumption: bool = Field(default=True, description="Whether this change represents an assumption")


class ScenarioPayload(BaseModel):
    name: str = Field(..., description="Scenario identifier or descriptive name")
    origin: ScenarioOrigin = Field(default=ScenarioOrigin.USER, description="user or moonshot_card")
    source_card_id: Optional[UUID] = Field(default=None, description="Optional card UUID if from Moonshot")
    changes: List[ScenarioChange] = Field(default_factory=list, description="List of explicit lever changes")


class ScenarioRunRequest(BaseModel):
    baseline_run_id: UUID = Field(..., description="Reference baseline run UUID")
    horizon_weeks: int = Field(default=26, ge=1, le=104, description="Forecast horizon in weeks (default 26, max 104)")
    scenario: ScenarioPayload = Field(..., description="Scenario definition with explicit changes")


class WeeklyCashPoint(BaseModel):
    week_start: date
    cash: Decimal

    @field_serializer("cash")
    def serialize_cash(self, val: Decimal, _info) -> str:
        return f"{val:.2f}"


class CaseResult(BaseModel):
    weekly_cash: List[WeeklyCashPoint] = Field(default_factory=list)
    min_cash: Decimal
    min_cash_date: date
    end_cash: Decimal
    runway_weeks: Optional[int] = Field(default=None, description="Weeks until projected cash < 0, or null")
    reserve_breach: bool = Field(default=False, description="True if projected cash falls below reserve amount")
    cash_floor_breach: bool = Field(default=False, description="True if projected cash falls below weeks-converted floor")

    @field_serializer("min_cash", "end_cash")
    def serialize_decimals(self, val: Decimal, _info) -> str:
        return f"{val:.2f}"


class ScenarioCases(BaseModel):
    expected: CaseResult
    best: CaseResult
    worst: CaseResult


class ScenarioRunData(BaseModel):
    run_id: UUID
    status: ResultStatus
    engine_version: str
    currency: str = Field(..., max_length=3, min_length=3)
    cases: ScenarioCases
    assumptions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    source_row_refs: List[UUID] = Field(default_factory=list)
    evidence_refs: List[UUID] = Field(default_factory=list)


class CfoSnapshotData(BaseModel):
    cash: Decimal
    burn: Decimal
    revenue: Decimal
    receivables: Decimal
    payroll: Decimal
    baseline_run_id: UUID
    as_of_date: date
    currency: str = Field(default="USD", max_length=3, min_length=3)

    @field_serializer("cash", "burn", "revenue", "receivables", "payroll")
    def serialize_decimals(self, val: Decimal, _info) -> str:
        return f"{val:.2f}"


class MetricQueryRequest(BaseModel):
    metric: str
    from_date: Optional[date] = None
    to_date: Optional[date] = None


class MetricResultData(BaseModel):
    metric: str
    value: Decimal
    currency: str
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    source_row_refs: List[UUID] = Field(default_factory=list)

    @field_serializer("value")
    def serialize_value(self, val: Decimal, _info) -> str:
        return f"{val:.2f}"
