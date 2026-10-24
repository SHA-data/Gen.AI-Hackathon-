import json
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from packages.contracts.envelope import ToolResultEnvelope, ToolStatus
from services.api.app.cfo.importers.csv_importer import CsvImporter
from services.api.app.cfo.models import ImportBatch
from services.api.app.core.audit import create_audit_log
from services.api.app.core.auth import AuthContext, RoleChecker, get_auth_context
from services.api.app.core.database import get_db
from services.api.app.core.errors import ForbiddenError, NotFoundError, ValidationError

router = APIRouter(prefix="/v1/finance", tags=["Finance"])


@router.post("/imports")
async def import_financial_file(
    file: UploadFile = File(...),
    file_type: str = Form(default="invoices"),
    column_mapping: Optional[str] = Form(default=None),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Multipart CSV ingestion endpoint. Admin/owner only.

    Idempotent by file hash or Idempotency-Key.
    Duplicates are FLAGGED, never silently deleted.
    Ambiguities are surfaced in the Quality Report.
    """
    RoleChecker("admin")(auth)

    content = await file.read()
    if not content:
        raise ValidationError("Uploaded file is empty")

    override_map = None
    if column_mapping:
        try:
            override_map = json.loads(column_mapping)
        except Exception:
            raise ValidationError("Invalid JSON format for column_mapping")

    batch = await CsvImporter.import_csv(
        session=db,
        org_id=auth.org_id,
        filename=file.filename or "uploaded.csv",
        content=content,
        file_type=file_type,
        override_mapping=override_map,
        idempotency_key=idempotency_key,
    )

    await create_audit_log(
        session=db,
        org_id=auth.org_id,
        actor_user_id=auth.user_id,
        action="IMPORT_BATCH",
        entity_type="import_batch",
        entity_id=batch.id,
        decision="accepted" if batch.status == "completed" else batch.status,
        metadata={"filename": batch.filename, "content_hash": batch.content_hash, "status": batch.status},
    )

    return {
        "batch_id": str(batch.id),
        "status": batch.status,
        "filename": batch.filename,
        "total_rows": batch.total_rows,
        "accepted_rows": batch.accepted_rows,
        "rejected_rows": batch.rejected_rows,
        "flagged_rows": batch.flagged_rows,
        "quality_report": batch.quality_report,
    }


@router.get("/imports/{batch_id}")
async def get_import_quality_report(
    batch_id: UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full quality report for an import batch."""
    batch = await db.get(ImportBatch, batch_id)
    if not batch or batch.org_id != auth.org_id:
        raise NotFoundError(f"Import batch {batch_id} not found")

    return {
        "batch_id": str(batch.id),
        "status": batch.status,
        "filename": batch.filename,
        "total_rows": batch.total_rows,
        "accepted_rows": batch.accepted_rows,
        "rejected_rows": batch.rejected_rows,
        "flagged_rows": batch.flagged_rows,
        "column_mapping": batch.column_mapping,
        "quality_report": batch.quality_report,
        "created_at": batch.created_at.isoformat(),
    }
