import asyncio
import csv
import hashlib
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

DEMO_ORG_ID = SEED_ORGS[0]["id"]  # Acme Digital Agency
DATA_DIR = Path(__file__).parent / "data"


def compute_file_hash(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


async def seed_demo_agency():
    async with async_session_factory() as session:
        # 1. Ensure FinanceSettings exists
        stmt = select(FinanceSettings).where(FinanceSettings.org_id == DEMO_ORG_ID)
        res = await session.execute(stmt)
        settings = res.scalar_one_or_none()
        if not settings:
            settings = FinanceSettings(
                id=uuid4(),
                org_id=DEMO_ORG_ID,
                reserve_amount=Decimal("50000.00"),
                cash_floor_weeks=12,
                worst_case_delay_days=14,
                worst_case_rev_pct_delta=Decimal("-10.00"),
                best_case_advance_days=7,
                best_case_rev_pct_delta=Decimal("5.00"),
                currency="USD",
            )
            session.add(settings)
            await session.flush()

        # 2. Ingest Invoices
        invoices_file = DATA_DIR / "invoices.csv"
        inv_hash = compute_file_hash(invoices_file)
        stmt = select(ImportBatch).where(
            ImportBatch.org_id == DEMO_ORG_ID,
            ImportBatch.content_hash == inv_hash,
        )
        batch = (await session.execute(stmt)).scalar_one_or_none()
        if not batch:
            batch = ImportBatch(
                id=uuid4(),
                org_id=DEMO_ORG_ID,
                filename="invoices.csv",
                content_hash=inv_hash,
                status="completed",
                column_mapping={"invoice_number": "invoice_number", "client": "client_or_vendor", "amount": "amount"},
                quality_report={"status": "clean", "rejected_count": 0, "duplicate_count": 0},
            )
            session.add(batch)
            await session.flush()

            with open(invoices_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                row_num = 1
                for r in reader:
                    source_row = SourceRow(
                        id=uuid4(),
                        org_id=DEMO_ORG_ID,
                        batch_id=batch.id,
                        row_number=row_num,
                        raw_payload=r,
                    )
                    session.add(source_row)
                    await session.flush()

                    inv = Invoice(
                        id=uuid4(),
                        org_id=DEMO_ORG_ID,
                        source_row_id=source_row.id,
                        invoice_number=r["invoice_number"],
                        kind="receivable",
                        client_or_vendor=r["client"],
                        amount=Decimal(r["amount"]),
                        currency=r.get("currency", "USD"),
                        issue_date=date.fromisoformat(r["issue_date"]),
                        due_date=date.fromisoformat(r["due_date"]),
                        expected_payment_date=date.fromisoformat(r["expected_payment_date"]),
                        status=r["status"],
                        is_uncertain=r.get("is_uncertain", "false").lower() == "true",
                    )
                    session.add(inv)
                    row_num += 1

                batch.total_rows = row_num - 1
                batch.accepted_rows = row_num - 1

        # 3. Ingest Payroll
        payroll_file = DATA_DIR / "payroll.csv"
        pay_hash = compute_file_hash(payroll_file)
        stmt = select(ImportBatch).where(
            ImportBatch.org_id == DEMO_ORG_ID,
            ImportBatch.content_hash == pay_hash,
        )
        pay_batch = (await session.execute(stmt)).scalar_one_or_none()
        if not pay_batch:
            pay_batch = ImportBatch(
                id=uuid4(),
                org_id=DEMO_ORG_ID,
                filename="payroll.csv",
                content_hash=pay_hash,
                status="completed",
                column_mapping={"employee_identifier": "employee_identifier", "monthly_gross": "monthly_gross"},
                quality_report={"status": "clean", "rejected_count": 0, "duplicate_count": 0},
            )
            session.add(pay_batch)
            await session.flush()

            with open(payroll_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                row_num = 1
                for r in reader:
                    source_row = SourceRow(
                        id=uuid4(),
                        org_id=DEMO_ORG_ID,
                        batch_id=pay_batch.id,
                        row_number=row_num,
                        raw_payload=r,
                    )
                    session.add(source_row)
                    await session.flush()

                    item = PayrollItem(
                        id=uuid4(),
                        org_id=DEMO_ORG_ID,
                        source_row_id=source_row.id,
                        employee_identifier=r["employee_identifier"],
                        role_title=r["role_title"],
                        monthly_gross=Decimal(r["monthly_gross"]),
                        benefits_and_taxes=Decimal(r.get("benefits_and_taxes", "0.00")),
                        currency=r.get("currency", "USD"),
                        pay_frequency=r.get("pay_frequency", "monthly"),
                        start_date=date.fromisoformat(r["start_date"]),
                    )
                    session.add(item)
                    row_num += 1

                pay_batch.total_rows = row_num - 1
                pay_batch.accepted_rows = row_num - 1

        # 4. Ingest Historical Transactions
        tx_file = DATA_DIR / "transactions.csv"
        tx_hash = compute_file_hash(tx_file)
        stmt = select(ImportBatch).where(
            ImportBatch.org_id == DEMO_ORG_ID,
            ImportBatch.content_hash == tx_hash,
        )
        tx_batch = (await session.execute(stmt)).scalar_one_or_none()
        if not tx_batch:
            tx_batch = ImportBatch(
                id=uuid4(),
                org_id=DEMO_ORG_ID,
                filename="transactions.csv",
                content_hash=tx_hash,
                status="completed",
                column_mapping={"transaction_date": "transaction_date", "amount": "amount"},
                quality_report={"status": "clean", "rejected_count": 0, "duplicate_count": 0},
            )
            session.add(tx_batch)
            await session.flush()

            with open(tx_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                row_num = 1
                for r in reader:
                    source_row = SourceRow(
                        id=uuid4(),
                        org_id=DEMO_ORG_ID,
                        batch_id=tx_batch.id,
                        row_number=row_num,
                        raw_payload=r,
                    )
                    session.add(source_row)
                    await session.flush()

                    rec = FinancialRecord(
                        id=uuid4(),
                        org_id=DEMO_ORG_ID,
                        source_row_id=source_row.id,
                        transaction_date=date.fromisoformat(r["transaction_date"]),
                        amount=Decimal(r["amount"]),
                        currency=r.get("currency", "USD"),
                        category=r["category"],
                        client_or_vendor=r.get("client_or_vendor"),
                        is_actual=r.get("is_actual", "true").lower() == "true",
                    )
                    session.add(rec)
                    row_num += 1

                tx_batch.total_rows = row_num - 1
                tx_batch.accepted_rows = row_num - 1

        # 5. Finance Assumptions
        assumptions_file = DATA_DIR / "assumptions.json"
        with open(assumptions_file, "r", encoding="utf-8") as f:
            assumptions_list = json.load(f)

        for a in assumptions_list:
            stmt = select(FinanceAssumption).where(
                FinanceAssumption.org_id == DEMO_ORG_ID,
                FinanceAssumption.key == a["key"],
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if not existing:
                fa = FinanceAssumption(
                    id=uuid4(),
                    org_id=DEMO_ORG_ID,
                    category=a["category"],
                    key=a["key"],
                    value=a["value"],
                    valid_from=date.fromisoformat(a["valid_from"]),
                )
                session.add(fa)

        await session.commit()
    print("Demo agency seeded with complete source-row lineage.")


if __name__ == "__main__":
    asyncio.run(seed_demo_agency())
