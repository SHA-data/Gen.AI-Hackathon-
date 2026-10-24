from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
import hashlib
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from packages.contracts.envelope import ResultStatus


@dataclass
class WeeklyScheduleItem:
    week_number: int
    week_start: date
    week_end: date
    opening_cash: Decimal
    projected_inflows: Decimal
    projected_outflows: Decimal
    net_cash_flow: Decimal
    closing_cash: Decimal
    value_label: str
    inflow_refs: List[UUID] = field(default_factory=list)
    outflow_refs: List[UUID] = field(default_factory=list)


@dataclass
class ForecastCalculationResult:
    points: List[WeeklyScheduleItem]
    min_cash: Decimal
    min_cash_date: date
    end_cash: Decimal
    runway_weeks: Optional[int]
    reserve_breach: bool
    cash_floor_breach: bool
    cash_risk: bool
    converted_cash_floor: Decimal
    schedule_hash: str


class ForecastEngine:
    """Pure, deterministic finance calculation engine.

    No LLM, no network, decimal-safe arithmetic, explicit week schedule scanning.
    """

    @classmethod
    def get_monday_of_week(cls, d: date) -> date:
        # ISO weekday: Monday is 1, Sunday is 7
        return d - timedelta(days=d.isoweekday() - 1)

    @classmethod
    def calculate_forecast(
        cls,
        opening_cash: Decimal,
        opening_cash_date: date,
        inflow_events: List[Tuple[date, Decimal, UUID]],
        outflow_events: List[Tuple[date, Decimal, UUID]],
        horizon_weeks: int = 26,
        reserve_amount: Decimal = Decimal("50000.00"),
        cash_floor_weeks: int = 12,
        value_label: str = "calculated",
    ) -> ForecastCalculationResult:
        if horizon_weeks < 1 or horizon_weeks > 104:
            raise ValueError(f"horizon_weeks must be between 1 and 104; got {horizon_weeks}")

        start_monday = cls.get_monday_of_week(opening_cash_date)
        points: List[WeeklyScheduleItem] = []
        current_cash = opening_cash

        # Map inflow and outflow events into calendar day buckets
        inflows_by_day: Dict[date, List[Tuple[Decimal, UUID]]] = {}
        for d, amt, ref in inflow_events:
            inflows_by_day.setdefault(d, []).append((amt, ref))

        outflows_by_day: Dict[date, List[Tuple[Decimal, UUID]]] = {}
        for d, amt, ref in outflow_events:
            outflows_by_day.setdefault(d, []).append((amt, ref))

        total_committed_outflow = Decimal("0.00")

        for w in range(1, horizon_weeks + 1):
            w_start = start_monday + timedelta(weeks=w - 1)
            w_end = w_start + timedelta(days=6)

            week_inflows = Decimal("0.00")
            week_inflow_refs: List[UUID] = []

            week_outflows = Decimal("0.00")
            week_outflow_refs: List[UUID] = []

            # Aggregate events falling into [w_start, w_end]
            curr_day = w_start
            while curr_day <= w_end:
                if curr_day in inflows_by_day:
                    for amt, ref in inflows_by_day[curr_day]:
                        week_inflows += amt
                        week_inflow_refs.append(ref)
                if curr_day in outflows_by_day:
                    for amt, ref in outflows_by_day[curr_day]:
                        week_outflows += amt
                        week_outflow_refs.append(ref)
                curr_day += timedelta(days=1)

            net_flow = week_inflows - week_outflows
            closing_cash = current_cash + net_flow
            total_committed_outflow += week_outflows

            item = WeeklyScheduleItem(
                week_number=w,
                week_start=w_start,
                week_end=w_end,
                opening_cash=current_cash,
                projected_inflows=week_inflows,
                projected_outflows=week_outflows,
                net_cash_flow=net_flow,
                closing_cash=closing_cash,
                value_label=value_label,
                inflow_refs=week_inflow_refs,
                outflow_refs=week_outflow_refs,
            )
            points.append(item)
            current_cash = closing_cash

        # Derive Metrics
        min_point = min(points, key=lambda p: p.closing_cash)
        min_cash = min_point.closing_cash
        min_cash_date = min_point.week_start
        end_cash = points[-1].closing_cash

        # Runway Scanner: first week where closing_cash < 0
        runway_weeks: Optional[int] = None
        for p in points:
            if p.closing_cash < Decimal("0.00"):
                runway_weeks = p.week_number
                break

        # Dual Cash Floor Evaluation
        avg_weekly_outflow = total_committed_outflow / Decimal(str(horizon_weeks))
        converted_floor = Decimal(str(cash_floor_weeks)) * avg_weekly_outflow

        reserve_breach = any(p.closing_cash < reserve_amount for p in points)
        cash_floor_breach = any(p.closing_cash < converted_floor for p in points)
        cash_risk = reserve_breach or cash_floor_breach or (runway_weeks is not None and runway_weeks < 26)

        # Compute cryptographic hash of the point sequence to enforce immutability
        hasher = hashlib.sha256()
        for p in points:
            hasher.update(f"{p.week_number}:{p.week_start}:{p.closing_cash:.2f};".encode("utf-8"))
        schedule_hash = hasher.hexdigest()

        return ForecastCalculationResult(
            points=points,
            min_cash=min_cash,
            min_cash_date=min_cash_date,
            end_cash=end_cash,
            runway_weeks=runway_weeks,
            reserve_breach=reserve_breach,
            cash_floor_breach=cash_floor_breach,
            cash_risk=cash_risk,
            converted_cash_floor=converted_floor,
            schedule_hash=schedule_hash,
        )
