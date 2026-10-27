from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.cfo.engine.calculator import ForecastCalculationResult, ForecastEngine
from services.api.app.cfo.models import (
    FinanceAssumption,
    FinanceSettings,
    ForecastPoint,
    ForecastRun,
    Invoice,
    PayrollItem,
)
from services.api.app.core.errors import NotFoundError, ValidationError


class BaselineService:
    """Orchestrates baseline forecast generation from canonical records and assumptions."""

    @classmethod
    async def run_baseline(
        cls,
        session: AsyncSession,
        org_id: UUID,
        horizon_weeks: int = 26,
    ) -> Tuple[ForecastRun, List[ForecastPoint]]:
        # 1. Fetch settings
        stmt = select(FinanceSettings).where(FinanceSettings.org_id == org_id)
        settings = (await session.execute(stmt)).scalar_one_or_none()
        reserve_amt = settings.reserve_amount if settings else Decimal("50000.00")
        floor_weeks = settings.cash_floor_weeks if settings else 12

        # 2. Fetch Opening Cash Assumption
        stmt = select(FinanceAssumption).where(
            FinanceAssumption.org_id == org_id,
            FinanceAssumption.category == "opening_cash",
        ).order_by(desc(FinanceAssumption.valid_from))
        cash_assumption = (await session.execute(stmt)).scalars().first()
        if not cash_assumption:
            raise ValidationError("Organization lacks an opening cash assumption; please set opening cash first.")

        opening_cash = Decimal(str(cash_assumption.value.get("amount", "0.00")))
        as_of_date = cash_assumption.valid_from

        # 3. Assemble Inflow Events from Invoices
        stmt = select(Invoice).where(
            Invoice.org_id == org_id,
            Invoice.status.in_(["issued", "late", "draft"]),
            Invoice.expected_payment_date >= as_of_date,
        )
        invoices = (await session.execute(stmt)).scalars().all()
        inflow_events: List[Tuple[date, Decimal, UUID]] = [
            (inv.expected_payment_date, inv.amount, inv.id) for inv in invoices
        ]

        # 4. Assemble Outflow Events from Payroll and Recurring Overheads
        outflow_events: List[Tuple[date, Decimal, UUID]] = []

        stmt = select(PayrollItem).where(PayrollItem.org_id == org_id)
        payroll_items = (await session.execute(stmt)).scalars().all()
        monthly_payroll_sum = sum(p.monthly_gross + p.benefits_and_taxes for p in payroll_items)

        # Distribute monthly payroll on the 28th of every forward month across horizon
        horizon_days = horizon_weeks * 7
        end_date = as_of_date + timedelta(days=horizon_days)

        curr = as_of_date.replace(day=1)
        while curr <= end_date:
            pay_date = date(curr.year, curr.month, 28)
            if pay_date >= as_of_date:
                # Use first payroll item id as representative source ref if available
                ref_id = payroll_items[0].id if payroll_items else uuid4()
                outflow_events.append((pay_date, monthly_payroll_sum, ref_id))
            # Move to next month
            if curr.month == 12:
                curr = date(curr.year + 1, 1, 1)
            else:
                curr = date(curr.year, curr.month + 1, 1)

        # Overhead assumptions (rent on 1st, software on 15th)
        stmt = select(FinanceAssumption).where(
            FinanceAssumption.org_id == org_id,
            FinanceAssumption.category == "recurring_overhead",
        )
        overheads = (await session.execute(stmt)).scalars().all()
        for ov in overheads:
            day_of_month = int(ov.value.get("day_of_month", 1))
            amt = Decimal(str(ov.value.get("amount", "0.00")))
            curr = as_of_date.replace(day=1)
            while curr <= end_date:
                try:
                    ov_date = date(curr.year, curr.month, day_of_month)
                except ValueError:
                    ov_date = date(curr.year, curr.month, 28)
                if ov_date >= as_of_date:
                    outflow_events.append((ov_date, amt, ov.id))
                if curr.month == 12:
                    curr = date(curr.year + 1, 1, 1)
                else:
                    curr = date(curr.year, curr.month + 1, 1)

        # 5. Run Pure Deterministic Engine
        calc_result: ForecastCalculationResult = ForecastEngine.calculate_forecast(
            opening_cash=opening_cash,
            opening_cash_date=as_of_date,
            inflow_events=inflow_events,
            outflow_events=outflow_events,
            horizon_weeks=horizon_weeks,
            reserve_amount=reserve_amt,
            cash_floor_weeks=floor_weeks,
            value_label="calculated",
        )

        # 6. Persist Baseline Run & Forecast Points
        run = ForecastRun(
            id=uuid4(),
            org_id=org_id,
            scenario_id=None,
            case_type="baseline",
            engine_version="0.1.0",
            horizon_weeks=horizon_weeks,
            start_date=as_of_date,
            end_date=end_date,
            min_cash=calc_result.min_cash,
            min_cash_date=calc_result.min_cash_date,
            end_cash=calc_result.end_cash,
            runway_weeks=calc_result.runway_weeks,
            reserve_breach=calc_result.reserve_breach,
            cash_floor_breach=calc_result.cash_floor_breach,
            status="verified",
            baseline_hash=calc_result.schedule_hash,
        )
        session.add(run)
        await session.flush()

        points: List[ForecastPoint] = []
        for p in calc_result.points:
            pt = ForecastPoint(
                id=uuid4(),
                org_id=org_id,
                run_id=run.id,
                week_number=p.week_number,
                week_start=p.week_start,
                opening_cash=p.opening_cash,
                projected_inflows=p.projected_inflows,
                projected_outflows=p.projected_outflows,
                net_cash_flow=p.net_cash_flow,
                closing_cash=p.closing_cash,
                value_label=p.value_label,
                contributing_inflow_refs=[str(r) for r in p.inflow_refs],
                contributing_outflow_refs=[str(r) for r in p.outflow_refs],
            )
            points.append(pt)

        session.add_all(points)
        await session.commit()
        return run, points

    @classmethod
    async def get_latest_baseline(
        cls, session: AsyncSession, org_id: UUID
    ) -> Optional[Tuple[ForecastRun, List[ForecastPoint]]]:
        stmt = (
            select(ForecastRun)
            .where(ForecastRun.org_id == org_id, ForecastRun.case_type == "baseline")
            .order_by(desc(ForecastRun.created_at))
        )
        run = (await session.execute(stmt)).scalars().first()
        if not run:
            return None

        stmt_pts = (
            select(ForecastPoint)
            .where(ForecastPoint.run_id == run.id)
            .order_by(ForecastPoint.week_number)
        )
        points = (await session.execute(stmt_pts)).scalars().all()
        return run, list(points)
