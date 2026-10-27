from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.contracts.envelope import ToolResultEnvelope, ToolStatus
from packages.contracts.finance import CfoSnapshotData
from services.api.app.cfo.models import (
    FinanceAssumption,
    FinanceSettings,
    FinancialRecord,
    ForecastRun,
    Invoice,
    PayrollItem,
)
from services.api.app.cfo.services.baseline_service import BaselineService
from services.api.app.core.errors import NotFoundError


class RealCfoSnapshotService:
    """Live implementation of CfoSnapshotService providing read-only financial posture for Moonshot intake."""

    @classmethod
    async def get(cls, session: AsyncSession, org_id: UUID) -> ToolResultEnvelope:
        # 1. Opening Cash
        stmt = select(FinanceAssumption).where(
            FinanceAssumption.org_id == org_id,
            FinanceAssumption.category == "opening_cash",
        ).order_by(desc(FinanceAssumption.valid_from))
        cash_assumption = (await session.execute(stmt)).scalars().first()
        current_cash = Decimal(str(cash_assumption.value.get("amount", "0.00"))) if cash_assumption else Decimal("0.00")
        as_of_date = cash_assumption.valid_from if cash_assumption else date.today()

        # 2. Monthly Payroll
        stmt = select(PayrollItem).where(PayrollItem.org_id == org_id)
        payroll_items = (await session.execute(stmt)).scalars().all()
        monthly_payroll = sum(p.monthly_gross + p.benefits_and_taxes for p in payroll_items)

        # 3. Monthly Overhead Burn
        stmt = select(FinanceAssumption).where(
            FinanceAssumption.org_id == org_id,
            FinanceAssumption.category == "recurring_overhead",
        )
        overheads = (await session.execute(stmt)).scalars().all()
        overhead_burn = sum(Decimal(str(ov.value.get("amount", "0.00"))) for ov in overheads)
        total_monthly_burn = monthly_payroll + overhead_burn

        # 4. Receivables (Issued & Unpaid Invoices)
        stmt = select(func.sum(Invoice.amount)).where(
            Invoice.org_id == org_id,
            Invoice.kind == "receivable",
            Invoice.status.in_(["issued", "late"]),
        )
        total_receivables = (await session.execute(stmt)).scalar() or Decimal("0.00")

        # 5. Average Monthly Revenue (from forward active invoices)
        stmt = select(func.sum(Invoice.amount)).where(
            Invoice.org_id == org_id,
            Invoice.kind == "receivable",
            Invoice.status.in_(["issued", "late", "paid"]),
        )
        total_rev = (await session.execute(stmt)).scalar() or Decimal("0.00")
        # Approximate 6-month monthly run rate
        monthly_revenue = total_rev / Decimal("6.00") if total_rev > Decimal("0.00") else Decimal("0.00")

        # 6. Baseline Run ID
        baseline_res = await BaselineService.get_latest_baseline(session, org_id)
        if not baseline_res:
            baseline_run, _ = await BaselineService.run_baseline(session, org_id)
        else:
            baseline_run, _ = baseline_res

        # 7. Base Currency
        stmt = select(FinanceSettings).where(FinanceSettings.org_id == org_id)
        settings = (await session.execute(stmt)).scalar_one_or_none()
        currency = settings.currency if settings else "USD"

        snapshot = CfoSnapshotData(
            cash=current_cash,
            burn=total_monthly_burn,
            revenue=monthly_revenue,
            receivables=total_receivables,
            payroll=monthly_payroll,
            baseline_run_id=baseline_run.id,
            as_of_date=as_of_date,
            currency=currency,
        )

        sources = [str(baseline_run.id)]
        if cash_assumption:
            sources.append(str(cash_assumption.id))

        return ToolResultEnvelope(
            status=ToolStatus.OK,
            data=snapshot.model_dump(mode="json"),
            sources=sources,
            warnings=[],
            run_id=str(baseline_run.id),
        )
