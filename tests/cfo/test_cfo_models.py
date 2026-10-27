from datetime import date
from decimal import Decimal
from uuid import uuid4
import pytest
from sqlalchemy.exc import IntegrityError

from services.api.app.cfo.models import (
    FinanceAssumption,
    FinanceSettings,
    FinancialRecord,
    ForecastPoint,
    ForecastRun,
    Invoice,
    PayrollItem,
)
from services.api.app.core.database import async_session_factory
from services.api.app.core.models import Organization


@pytest.mark.asyncio
async def test_canonical_model_check_constraints():
    async with async_session_factory() as session:
        org = Organization(id=uuid4(), name="Model Test Org", base_currency="USD")
        session.add(org)
        await session.flush()

        # 1. Invalid invoice kind check constraint
        inv_bad_kind = Invoice(
            id=uuid4(),
            org_id=org.id,
            invoice_number="INV-BAD-KIND",
            kind="invalid_kind",  # Must be 'receivable' or 'payable'
            client_or_vendor="Vendor Corp",
            amount=Decimal("1000.00"),
            issue_date=date(2026, 11, 1),
            due_date=date(2026, 12, 1),
            expected_payment_date=date(2026, 12, 1),
            status="issued",
        )
        session.add(inv_bad_kind)
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()

        # 2. Invalid invoice status check constraint
        inv_bad_status = Invoice(
            id=uuid4(),
            org_id=org.id,
            invoice_number="INV-BAD-STATUS",
            kind="receivable",
            client_or_vendor="Client Corp",
            amount=Decimal("1000.00"),
            issue_date=date(2026, 11, 1),
            due_date=date(2026, 12, 1),
            expected_payment_date=date(2026, 12, 1),
            status="unknown_status",  # Must be draft|issued|paid|late|disputed|written_off
        )
        session.add(inv_bad_status)
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()

        # 3. Invalid payroll frequency check constraint
        payroll_bad_freq = PayrollItem(
            id=uuid4(),
            org_id=org.id,
            employee_identifier="EMP-BAD",
            role_title="Developer",
            monthly_gross=Decimal("5000.00"),
            pay_frequency="daily",  # Must be weekly|biweekly|monthly
            start_date=date(2026, 1, 1),
        )
        session.add(payroll_bad_freq)
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()


@pytest.mark.asyncio
async def test_separation_of_actual_expected_and_hypothetical():
    async with async_session_factory() as session:
        org = Organization(id=uuid4(), name="Separation Org", base_currency="USD")
        session.add(org)
        await session.flush()

        # Actual: historical transaction
        actual_rec = FinancialRecord(
            id=uuid4(),
            org_id=org.id,
            transaction_date=date(2026, 9, 15),
            amount=Decimal("45000.00"),
            currency="USD",
            category="revenue",
            is_actual=True,
        )
        session.add(actual_rec)

        # Expected: receivable invoice
        expected_inv = Invoice(
            id=uuid4(),
            org_id=org.id,
            invoice_number="INV-SEP-01",
            kind="receivable",
            client_or_vendor="Apex Corp",
            amount=Decimal("45000.00"),
            issue_date=date(2026, 10, 15),
            due_date=date(2026, 11, 15),
            expected_payment_date=date(2026, 11, 15),
            status="issued",
        )
        session.add(expected_inv)

        # Hypothetical: forecast run and point
        run = ForecastRun(
            id=uuid4(),
            org_id=org.id,
            case_type="expected",
            engine_version="0.1.0",
            horizon_weeks=26,
            start_date=date(2026, 10, 26),
            end_date=date(2027, 4, 26),
            min_cash=Decimal("18400.00"),
            min_cash_date=date(2027, 2, 1),
            end_cash=Decimal("30100.00"),
            status="verified",
        )
        session.add(run)
        await session.flush()

        point = ForecastPoint(
            id=uuid4(),
            org_id=org.id,
            run_id=run.id,
            week_number=1,
            week_start=date(2026, 10, 26),
            opening_cash=Decimal("185000.00"),
            projected_inflows=Decimal("10000.00"),
            projected_outflows=Decimal("5000.00"),
            net_cash_flow=Decimal("5000.00"),
            closing_cash=Decimal("190000.00"),
            value_label="hypothetical",
        )
        session.add(point)
        await session.commit()

        # Assert clean separation
        assert actual_rec.is_actual is True
        assert expected_inv.status == "issued"
        assert point.value_label == "hypothetical"
