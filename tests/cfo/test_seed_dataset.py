import json
from pathlib import Path
import pytest
from sqlalchemy import select

from services.api.app.cfo.models import (
    FinanceAssumption,
    FinanceSettings,
    FinancialRecord,
    ImportBatch,
    Invoice,
    PayrollItem,
    SourceRow,
)
from services.api.app.core.database import async_session_factory
from services.api.seed.seed_data import SEED_ORGS

DEMO_ORG_ID = SEED_ORGS[0]["id"]


@pytest.mark.asyncio
async def test_seed_dataset_integrity():
    golden_path = Path("tests/cfo/golden_demo_values.json")
    with open(golden_path, "r") as f:
        golden = json.load(f)

    async with async_session_factory() as session:
        # Settings
        stmt = select(FinanceSettings).where(FinanceSettings.org_id == DEMO_ORG_ID)
        settings = (await session.execute(stmt)).scalar_one_or_none()
        assert settings is not None
        assert str(settings.reserve_amount) == golden["reserve_amount"]
        assert settings.cash_floor_weeks == golden["cash_floor_weeks"]

        # Invoices
        stmt = select(Invoice).where(Invoice.org_id == DEMO_ORG_ID)
        invoices = (await session.execute(stmt)).scalars().all()
        assert len(invoices) >= 20

        # Every invoice must link to a valid source_row
        for inv in invoices:
            assert inv.source_row_id is not None
            source_row = await session.get(SourceRow, inv.source_row_id)
            assert source_row is not None
            assert source_row.org_id == DEMO_ORG_ID

        # Concentrated client (Apex Corp)
        apex_invoices = [inv for inv in invoices if inv.client_or_vendor == golden["concentrated_client"]["name"]]
        assert len(apex_invoices) >= 5
        assert str(apex_invoices[0].amount) == golden["concentrated_client"]["monthly_retainer"]

        # Payroll
        stmt = select(PayrollItem).where(PayrollItem.org_id == DEMO_ORG_ID)
        payroll_items = (await session.execute(stmt)).scalars().all()
        assert len(payroll_items) == golden["payroll"]["headcount"]
        monthly_payroll_total = sum(item.monthly_gross for item in payroll_items)
        assert str(monthly_payroll_total) == golden["payroll"]["monthly_total"]

        # Assumptions
        stmt = select(FinanceAssumption).where(
            FinanceAssumption.org_id == DEMO_ORG_ID,
            FinanceAssumption.category == "opening_cash",
        )
        opening_cash = (await session.execute(stmt)).scalar_one_or_none()
        assert opening_cash is not None
        assert opening_cash.value["amount"] == golden["opening_cash"]
