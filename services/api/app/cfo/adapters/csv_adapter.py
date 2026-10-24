from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.cfo.adapters.base import FinanceDataSource
from services.api.app.cfo.models import FinancialRecord, Invoice


class CsvAdapter(FinanceDataSource):
    """Standard database/CSV finance data source adapter."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def connect(self) -> bool:
        return True

    async def query_transactions(
        self,
        org_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        stmt = select(FinancialRecord).where(FinancialRecord.org_id == org_id)
        if from_date:
            stmt = stmt.where(FinancialRecord.transaction_date >= from_date)
        if to_date:
            stmt = stmt.where(FinancialRecord.transaction_date <= to_date)
        records = (await self.session.execute(stmt)).scalars().all()
        return [
            {
                "id": str(r.id),
                "transaction_date": r.transaction_date.isoformat(),
                "amount": f"{r.amount:.2f}",
                "currency": r.currency,
                "category": r.category,
                "client_or_vendor": r.client_or_vendor,
                "source_row_id": str(r.source_row_id) if r.source_row_id else None,
            }
            for r in records
        ]

    async def query_invoices(self, org_id: UUID) -> List[Dict[str, Any]]:
        stmt = select(Invoice).where(Invoice.org_id == org_id)
        invoices = (await self.session.execute(stmt)).scalars().all()
        return [
            {
                "id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "client": inv.client_or_vendor,
                "amount": f"{inv.amount:.2f}",
                "currency": inv.currency,
                "issue_date": inv.issue_date.isoformat(),
                "due_date": inv.due_date.isoformat(),
                "expected_payment_date": inv.expected_payment_date.isoformat(),
                "status": inv.status,
                "is_uncertain": inv.is_uncertain,
                "source_row_id": str(inv.source_row_id) if inv.source_row_id else None,
            }
            for inv in invoices
        ]

    async def health_check(self) -> Dict[str, Any]:
        return {"status": "ok", "adapter": "CsvAdapter"}
