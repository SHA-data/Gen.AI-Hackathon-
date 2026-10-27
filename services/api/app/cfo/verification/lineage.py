from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.cfo.models import (
    FinanceAssumption,
    FinancialRecord,
    ForecastPoint,
    ForecastRun,
    Invoice,
    PayrollItem,
    SourceRow,
)
from services.api.app.core.errors import NotFoundError
from services.api.app.core.evidence import EvidenceRegistry


class LineageResolver:
    """Resolves end-to-end lineage from forecast points to calculation math, assumptions, and raw source rows."""

    @classmethod
    async def get_point_lineage(
        cls, session: AsyncSession, org_id: UUID, point_id: UUID
    ) -> Dict[str, Any]:
        point = await session.get(ForecastPoint, point_id)
        if not point or point.org_id != org_id:
            raise NotFoundError(f"Forecast point {point_id} not found in organization")

        run = await session.get(ForecastRun, point.run_id)

        # 1. Fetch Contributing Invoices / Records
        contributing_inflow_ids = [UUID(ref) for ref in (point.contributing_inflow_refs or []) if ref != str(UUID(int=0))]
        contributing_outflow_ids = [UUID(ref) for ref in (point.contributing_outflow_refs or []) if ref != str(UUID(int=0))]

        # Fetch invoices
        invoices: List[Invoice] = []
        if contributing_inflow_ids:
            stmt = select(Invoice).where(Invoice.id.in_(contributing_inflow_ids))
            invoices = list((await session.execute(stmt)).scalars().all())

        # Fetch payroll items
        payrolls: List[PayrollItem] = []
        if contributing_outflow_ids:
            stmt = select(PayrollItem).where(PayrollItem.id.in_(contributing_outflow_ids))
            payrolls = list((await session.execute(stmt)).scalars().all())

        # 2. Trace back to raw source_rows
        source_row_ids = [inv.source_row_id for inv in invoices if inv.source_row_id]
        source_row_ids += [pay.source_row_id for pay in payrolls if pay.source_row_id]

        raw_source_rows: List[Dict[str, Any]] = []
        if source_row_ids:
            stmt = select(SourceRow).where(SourceRow.id.in_(source_row_ids))
            s_rows = (await session.execute(stmt)).scalars().all()
            for s in s_rows:
                raw_source_rows.append({
                    "id": str(s.id),
                    "batch_id": str(s.batch_id),
                    "row_number": s.row_number,
                    "payload": s.raw_payload,
                })

        # 3. Active Assumptions
        stmt = select(FinanceAssumption).where(FinanceAssumption.org_id == org_id)
        assumptions = (await session.execute(stmt)).scalars().all()
        assumptions_data = [
            {
                "id": str(a.id),
                "category": a.category,
                "key": a.key,
                "value": a.value,
                "valid_from": a.valid_from.isoformat(),
            }
            for a in assumptions
        ]

        return {
            "point_id": str(point.id),
            "run_id": str(run.id),
            "week_number": point.week_number,
            "week_start": point.week_start.isoformat(),
            "formula": "closing_cash = opening_cash + projected_inflows - projected_outflows",
            "calculation": {
                "opening_cash": f"{point.opening_cash:.2f}",
                "projected_inflows": f"{point.projected_inflows:.2f}",
                "projected_outflows": f"{point.projected_outflows:.2f}",
                "net_cash_flow": f"{point.net_cash_flow:.2f}",
                "closing_cash": f"{point.closing_cash:.2f}",
            },
            "contributing_events": {
                "invoices": [
                    {
                        "invoice_number": inv.invoice_number,
                        "client": inv.client_or_vendor,
                        "amount": f"{inv.amount:.2f}",
                        "expected_payment_date": inv.expected_payment_date.isoformat(),
                    }
                    for inv in invoices
                ],
                "payroll_count": len(payrolls),
            },
            "source_rows": raw_source_rows,
            "active_assumptions": assumptions_data,
        }


# Register CFO evidence target resolvers into Core EvidenceRegistry
async def resolve_source_row(session: AsyncSession, org_id: UUID, target_id: UUID) -> Optional[Dict[str, Any]]:
    s_row = await session.get(SourceRow, target_id)
    if not s_row or s_row.org_id != org_id:
        return None
    return {"id": str(s_row.id), "type": "source_row", "payload": s_row.raw_payload}


async def resolve_financial_record(session: AsyncSession, org_id: UUID, target_id: UUID) -> Optional[Dict[str, Any]]:
    rec = await session.get(FinancialRecord, target_id)
    if not rec or rec.org_id != org_id:
        return None
    return {"id": str(rec.id), "type": "financial_record", "amount": str(rec.amount), "category": rec.category}


async def resolve_forecast_run(session: AsyncSession, org_id: UUID, target_id: UUID) -> Optional[Dict[str, Any]]:
    run = await session.get(ForecastRun, target_id)
    if not run or run.org_id != org_id:
        return None
    return {"id": str(run.id), "type": "forecast_run", "case_type": run.case_type, "min_cash": str(run.min_cash)}


async def resolve_forecast_point(session: AsyncSession, org_id: UUID, target_id: UUID) -> Optional[Dict[str, Any]]:
    pt = await session.get(ForecastPoint, target_id)
    if not pt or pt.org_id != org_id:
        return None
    return {"id": str(pt.id), "type": "forecast_point", "week_start": pt.week_start.isoformat(), "closing_cash": str(pt.closing_cash)}


async def resolve_finance_assumption(session: AsyncSession, org_id: UUID, target_id: UUID) -> Optional[Dict[str, Any]]:
    fa = await session.get(FinanceAssumption, target_id)
    if not fa or fa.org_id != org_id:
        return None
    return {"id": str(fa.id), "type": "finance_assumption", "key": fa.key, "value": fa.value}


def register_cfo_evidence_resolvers():
    EvidenceRegistry.register_resolver("source_row", resolve_source_row)
    EvidenceRegistry.register_resolver("financial_record", resolve_financial_record)
    EvidenceRegistry.register_resolver("forecast_run", resolve_forecast_run)
    EvidenceRegistry.register_resolver("forecast_point", resolve_forecast_point)
    EvidenceRegistry.register_resolver("finance_assumption", resolve_finance_assumption)


# Auto-register upon import
register_cfo_evidence_resolvers()
