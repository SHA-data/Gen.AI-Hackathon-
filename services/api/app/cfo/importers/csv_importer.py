import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import io
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.cfo.importers.column_mapper import ColumnMapper
from services.api.app.cfo.models import (
    AnomalyFlag,
    FinancialRecord,
    ImportBatch,
    Invoice,
    PayrollItem,
    SourceRow,
)
from services.api.app.core.errors import AppError, ConflictError, ValidationError


class CsvImporter:
    """Enterprise CSV ingestion engine with quality reporting and anomaly flagging."""

    @classmethod
    def compute_hash(cls, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @classmethod
    async def import_csv(
        cls,
        session: AsyncSession,
        org_id: UUID,
        filename: str,
        content: bytes,
        file_type: str = "invoices",
        override_mapping: Optional[Dict[str, str]] = None,
        idempotency_key: Optional[str] = None,
    ) -> ImportBatch:
        content_hash = cls.compute_hash(content)

        # Idempotency check: return existing completed batch if identical content
        stmt = select(ImportBatch).where(
            ImportBatch.org_id == org_id,
            ImportBatch.content_hash == content_hash,
        )
        existing_batch = (await session.execute(stmt)).scalar_one_or_none()
        if existing_batch:
            return existing_batch

        # Parse CSV text safely
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        stream = io.StringIO(text)
        reader = csv.reader(stream)
        try:
            headers = next(reader)
        except StopIteration:
            raise ValidationError("CSV file is completely empty")

        # Column mapping and ambiguity check
        auto_mapping, ambiguities = ColumnMapper.analyze_headers(headers, file_type=file_type)
        effective_mapping = override_mapping or auto_mapping

        batch = ImportBatch(
            id=uuid4(),
            org_id=org_id,
            filename=filename,
            content_hash=content_hash,
            status="processing",
            column_mapping=effective_mapping,
            quality_report={},
        )
        session.add(batch)
        await session.flush()

        # If unresolved ambiguities exist and no override was supplied
        if ambiguities and not override_mapping:
            batch.status = "needs_mapping"
            batch.quality_report = {
                "status": "needs_mapping",
                "ambiguities": ambiguities,
                "suggested_mapping": auto_mapping,
            }
            await session.commit()
            return batch

        # Ingest rows verbatim into source_rows
        stream.seek(0)
        dict_reader = csv.DictReader(stream)
        source_rows: List[SourceRow] = []
        raw_rows_data: List[Tuple[int, Dict[str, str]]] = []

        row_index = 1
        for row in dict_reader:
            s_row = SourceRow(
                id=uuid4(),
                org_id=org_id,
                batch_id=batch.id,
                row_number=row_index,
                raw_payload=row,
            )
            source_rows.append(s_row)
            raw_rows_data.append((row_index, row))
            row_index += 1

        session.add_all(source_rows)
        await session.flush()

        # Process each row into canonical tables while generating Quality Report
        accepted_count = 0
        rejected_rows: List[Dict[str, Any]] = []
        flagged_anomalies: List[Dict[str, Any]] = []

        for (idx, raw_payload), s_row in zip(raw_rows_data, source_rows):
            try:
                if file_type == "invoices":
                    await cls._process_invoice_row(
                        session, org_id, s_row, raw_payload, effective_mapping, flagged_anomalies
                    )
                elif file_type == "payroll":
                    await cls._process_payroll_row(
                        session, org_id, s_row, raw_payload, effective_mapping
                    )
                elif file_type == "transactions":
                    await cls._process_transaction_row(
                        session, org_id, s_row, raw_payload, effective_mapping
                    )
                else:
                    raise ValidationError(f"Unsupported file type: {file_type}")
                accepted_count += 1
            except (ValueError, KeyError, InvalidOperation) as err:
                rejected_rows.append({
                    "row_number": idx,
                    "reason": str(err),
                    "raw_data": raw_payload,
                })

        batch.total_rows = len(source_rows)
        batch.accepted_rows = accepted_count
        batch.rejected_rows = len(rejected_rows)
        batch.flagged_rows = len(flagged_anomalies)
        batch.status = "completed"
        batch.quality_report = {
            "status": "completed",
            "total_rows": batch.total_rows,
            "accepted_rows": accepted_count,
            "rejected_rows_count": len(rejected_rows),
            "rejected_rows": rejected_rows,
            "flagged_rows_count": len(flagged_anomalies),
            "flagged_anomalies": flagged_anomalies,
        }

        await session.commit()
        return batch

    @classmethod
    async def _process_invoice_row(
        cls,
        session: AsyncSession,
        org_id: UUID,
        s_row: SourceRow,
        raw: Dict[str, str],
        mapping: Dict[str, str],
        flagged_anomalies: List[Dict[str, Any]],
    ):
        inv_col = mapping.get("invoice_number", "invoice_number")
        client_col = mapping.get("client_or_vendor", "client")
        amount_col = mapping.get("amount", "amount")
        issue_col = mapping.get("issue_date", "issue_date")
        due_col = mapping.get("due_date", "due_date")
        expected_col = mapping.get("expected_payment_date", "expected_payment_date")

        inv_num = raw.get(inv_col)
        client = raw.get(client_col)
        raw_amount = raw.get(amount_col)

        if not inv_num or not client or not raw_amount:
            raise ValueError(f"Missing required fields (invoice_number, client, or amount)")

        try:
            amount = Decimal(raw_amount)
        except InvalidOperation:
            raise ValueError(f"Invalid monetary amount: {raw_amount}")

        issue_date = date.fromisoformat(raw.get(issue_col, str(date.today())))
        due_date = date.fromisoformat(raw.get(due_col, str(date.today())))
        expected_date = date.fromisoformat(raw.get(expected_col, str(due_date)))
        is_uncertain = raw.get("is_uncertain", "false").lower() == "true"

        # Check for existing duplicate invoice number
        stmt = select(Invoice).where(
            Invoice.org_id == org_id,
            Invoice.invoice_number == inv_num,
        )
        existing_inv = (await session.execute(stmt)).scalar_one_or_none()
        if existing_inv:
            # FLAGGED NOT DELETED
            flag = AnomalyFlag(
                id=uuid4(),
                org_id=org_id,
                source_row_id=s_row.id,
                entity_type="invoice",
                entity_id=existing_inv.id,
                anomaly_type="duplicate_invoice",
                severity="warning",
                details={
                    "invoice_number": inv_num,
                    "existing_amount": str(existing_inv.amount),
                    "incoming_amount": str(amount),
                    "action": "preserved_in_source_rows_and_flagged",
                },
                status="flagged",
            )
            session.add(flag)
            flagged_anomalies.append({
                "row_number": s_row.row_number,
                "anomaly": "duplicate_invoice",
                "invoice_number": inv_num,
            })
            return

        inv = Invoice(
            id=uuid4(),
            org_id=org_id,
            source_row_id=s_row.id,
            invoice_number=inv_num,
            kind="receivable",
            client_or_vendor=client,
            amount=amount,
            currency=raw.get("currency", "USD"),
            issue_date=issue_date,
            due_date=due_date,
            expected_payment_date=expected_date,
            status=raw.get("status", "issued"),
            is_uncertain=is_uncertain,
        )
        session.add(inv)

    @classmethod
    async def _process_payroll_row(
        cls,
        session: AsyncSession,
        org_id: UUID,
        s_row: SourceRow,
        raw: Dict[str, str],
        mapping: Dict[str, str],
    ):
        emp_id = raw.get(mapping.get("employee_identifier", "employee_identifier"))
        role = raw.get(mapping.get("role_title", "role_title"))
        gross = raw.get(mapping.get("monthly_gross", "monthly_gross"))
        start_d = raw.get(mapping.get("start_date", "start_date"))

        if not emp_id or not role or not gross or not start_d:
            raise ValueError("Missing required payroll fields")

        item = PayrollItem(
            id=uuid4(),
            org_id=org_id,
            source_row_id=s_row.id,
            employee_identifier=emp_id,
            role_title=role,
            monthly_gross=Decimal(gross),
            benefits_and_taxes=Decimal(raw.get("benefits_and_taxes", "0.00")),
            currency=raw.get("currency", "USD"),
            pay_frequency=raw.get("pay_frequency", "monthly"),
            start_date=date.fromisoformat(start_d),
        )
        session.add(item)

    @classmethod
    async def _process_transaction_row(
        cls,
        session: AsyncSession,
        org_id: UUID,
        s_row: SourceRow,
        raw: Dict[str, str],
        mapping: Dict[str, str],
    ):
        tx_d = raw.get(mapping.get("transaction_date", "transaction_date"))
        amount = raw.get(mapping.get("amount", "amount"))
        category = raw.get(mapping.get("category", "category"))

        if not tx_d or not amount or not category:
            raise ValueError("Missing required transaction fields")

        rec = FinancialRecord(
            id=uuid4(),
            org_id=org_id,
            source_row_id=s_row.id,
            transaction_date=date.fromisoformat(tx_d),
            amount=Decimal(amount),
            currency=raw.get("currency", "USD"),
            category=category,
            client_or_vendor=raw.get("client_or_vendor"),
            is_actual=raw.get("is_actual", "true").lower() == "true",
        )
        session.add(rec)
