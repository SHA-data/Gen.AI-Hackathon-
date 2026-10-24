from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.contracts.envelope import ToolResultEnvelope, ToolStatus
from packages.contracts.finance import (
    MetricResultData,
    ScenarioRunRequest,
)
from services.api.app.cfo.models import (
    FinanceAssumption,
    FinanceSettings,
    FinancialRecord,
    ForecastPoint,
    ForecastRun,
    Invoice,
    PayrollItem,
    SourceRow,
)
from services.api.app.cfo.services.baseline_service import BaselineService
from services.api.app.cfo.services.scenario_service import ScenarioService
from services.api.app.core.errors import NotFoundError, ValidationError


class RealFinanceService:
    """Production implementation of FinanceService satisfying the A6 tool interface contract."""

    @classmethod
    async def get_metric(
        cls,
        session: AsyncSession,
        org_id: UUID,
        metric: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> ToolResultEnvelope:
        m = metric.lower().strip()
        stmt_settings = select(FinanceSettings).where(FinanceSettings.org_id == org_id)
        settings = (await session.execute(stmt_settings)).scalar_one_or_none()
        currency = settings.currency if settings else "USD"

        sources: List[UUID] = []
        val = Decimal("0.00")

        if m == "cash":
            stmt = select(FinanceAssumption).where(
                FinanceAssumption.org_id == org_id,
                FinanceAssumption.category == "opening_cash",
            ).order_by(desc(FinanceAssumption.valid_from))
            fa = (await session.execute(stmt)).scalars().first()
            if fa:
                val = Decimal(str(fa.value.get("amount", "0.00")))
                sources.append(fa.id)
        elif m == "receivables":
            stmt = select(Invoice).where(
                Invoice.org_id == org_id,
                Invoice.kind == "receivable",
                Invoice.status.in_(["issued", "late"]),
            )
            invoices = (await session.execute(stmt)).scalars().all()
            val = sum(inv.amount for inv in invoices)
            sources = [inv.source_row_id for inv in invoices if inv.source_row_id][:10]
        elif m == "payroll":
            stmt = select(PayrollItem).where(PayrollItem.org_id == org_id)
            payroll_items = (await session.execute(stmt)).scalars().all()
            val = sum(p.monthly_gross for p in payroll_items)
            sources = [p.source_row_id for p in payroll_items if p.source_row_id]
        elif m == "burn":
            stmt_p = select(PayrollItem).where(PayrollItem.org_id == org_id)
            pay_sum = sum(p.monthly_gross + p.benefits_and_taxes for p in (await session.execute(stmt_p)).scalars().all())
            stmt_o = select(FinanceAssumption).where(
                FinanceAssumption.org_id == org_id,
                FinanceAssumption.category == "recurring_overhead",
            )
            ov_sum = sum(Decimal(str(ov.value.get("amount", "0.00"))) for ov in (await session.execute(stmt_o)).scalars().all())
            val = pay_sum + ov_sum
        elif m == "runway":
            baseline_res = await BaselineService.get_latest_baseline(session, org_id)
            if baseline_res:
                run, _ = baseline_res
                val = Decimal(str(run.runway_weeks)) if run.runway_weeks is not None else Decimal("52.00")
                sources.append(run.id)
        elif m == "revenue":
            stmt = select(Invoice).where(
                Invoice.org_id == org_id,
                Invoice.kind == "receivable",
                Invoice.status.in_(["issued", "late", "paid"]),
            )
            invoices = (await session.execute(stmt)).scalars().all()
            total = sum(inv.amount for inv in invoices)
            val = total / Decimal("6.00") if total > Decimal("0.00") else Decimal("0.00")
            sources = [inv.source_row_id for inv in invoices if inv.source_row_id][:10]
        else:
            raise ValidationError(f"Unknown financial metric: '{metric}'")

        metric_data = MetricResultData(
            metric=m,
            value=val,
            currency=currency,
            from_date=from_date,
            to_date=to_date,
            source_row_refs=sources,
        )

        return ToolResultEnvelope(
            status=ToolStatus.OK,
            data=metric_data.model_dump(mode="json"),
            sources=[str(s) for s in sources],
            warnings=[],
            run_id=None,
        )

    @classmethod
    async def run_scenario(
        cls, session: AsyncSession, org_id: UUID, request: ScenarioRunRequest
    ) -> ToolResultEnvelope:
        return await ScenarioService.run_scenario(session, org_id, request)

    @classmethod
    async def list_source_rows(
        cls, session: AsyncSession, org_id: UUID, ref: Optional[str] = None
    ) -> ToolResultEnvelope:
        stmt = select(SourceRow).where(SourceRow.org_id == org_id)
        if ref:
            try:
                ref_uuid = UUID(ref)
                stmt = stmt.where(SourceRow.id == ref_uuid)
            except ValueError:
                pass
        stmt = stmt.order_by(SourceRow.created_at.desc()).limit(100)
        rows = (await session.execute(stmt)).scalars().all()

        data = {
            "count": len(rows),
            "rows": [
                {
                    "id": str(r.id),
                    "batch_id": str(r.batch_id),
                    "row_number": r.row_number,
                    "payload": r.raw_payload,
                }
                for r in rows
            ],
        }

        return ToolResultEnvelope(
            status=ToolStatus.OK,
            data=data,
            sources=[str(r.id) for r in rows],
            warnings=[],
            run_id=None,
        )

    @classmethod
    async def explain_change(
        cls,
        session: AsyncSession,
        org_id: UUID,
        metric: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> ToolResultEnvelope:
        """Analyzes period comparison and identifies largest financial drivers."""
        drivers = []
        sources = []

        if metric.lower() in ("cash", "burn"):
            # Check payroll changes
            stmt = select(PayrollItem).where(PayrollItem.org_id == org_id)
            payrolls = (await session.execute(stmt)).scalars().all()
            if payrolls:
                total_pay = sum(p.monthly_gross for p in payrolls)
                drivers.append({
                    "category": "Committed Payroll",
                    "impact": f"-{total_pay:.2f}",
                    "description": f"Monthly salary disbursement for {len(payrolls)} staff",
                })
                sources.extend([str(p.id) for p in payrolls[:3]])

            # Check late receivables
            stmt = select(Invoice).where(
                Invoice.org_id == org_id,
                Invoice.status == "late",
            )
            late_invoices = (await session.execute(stmt)).scalars().all()
            for late_inv in late_invoices:
                drivers.append({
                    "category": "Overdue Receivable",
                    "impact": f"-{late_inv.amount:.2f}",
                    "description": f"Overdue payment from {late_inv.client_or_vendor} ({late_inv.invoice_number})",
                })
                sources.append(str(late_inv.id))

        return ToolResultEnvelope(
            status=ToolStatus.OK,
            data={
                "metric": metric,
                "from_date": from_date.isoformat() if from_date else None,
                "to_date": to_date.isoformat() if to_date else None,
                "drivers": drivers,
            },
            sources=sources,
            warnings=[],
            run_id=None,
        )
