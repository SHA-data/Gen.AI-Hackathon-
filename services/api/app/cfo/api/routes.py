import json
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from packages.contracts.envelope import ToolResultEnvelope, ToolStatus
from services.api.app.cfo.importers.csv_importer import CsvImporter
from services.api.app.cfo.models import ImportBatch
from services.api.app.cfo.services.baseline_service import BaselineService
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


@router.post("/baseline/run")
async def run_baseline_forecast(
    horizon_weeks: int = 26,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Generates an immutable baseline forecast for the tenant."""
    run, points = await BaselineService.run_baseline(
        session=db,
        org_id=auth.org_id,
        horizon_weeks=horizon_weeks,
    )

    await create_audit_log(
        session=db,
        org_id=auth.org_id,
        actor_user_id=auth.user_id,
        action="RUN_BASELINE",
        entity_type="forecast_run",
        entity_id=run.id,
        decision="verified",
        metadata={
            "run_id": str(run.id),
            "horizon_weeks": horizon_weeks,
            "min_cash": f"{run.min_cash:.2f}",
            "baseline_hash": run.baseline_hash,
        },
    )

    return {
        "run_id": str(run.id),
        "case_type": run.case_type,
        "engine_version": run.engine_version,
        "horizon_weeks": run.horizon_weeks,
        "min_cash": f"{run.min_cash:.2f}",
        "min_cash_date": run.min_cash_date.isoformat(),
        "end_cash": f"{run.end_cash:.2f}",
        "runway_weeks": run.runway_weeks,
        "reserve_breach": run.reserve_breach,
        "cash_floor_breach": run.cash_floor_breach,
        "baseline_hash": run.baseline_hash,
        "weekly_points_count": len(points),
    }


@router.get("/baseline")
async def get_baseline_forecast(
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve latest immutable baseline forecast."""
    result = await BaselineService.get_latest_baseline(db, auth.org_id)
    if not result:
        raise NotFoundError("No baseline forecast found. Please run POST /v1/finance/baseline/run first.")
    run, points = result

    return {
        "run_id": str(run.id),
        "case_type": run.case_type,
        "engine_version": run.engine_version,
        "horizon_weeks": run.horizon_weeks,
        "min_cash": f"{run.min_cash:.2f}",
        "min_cash_date": run.min_cash_date.isoformat(),
        "end_cash": f"{run.end_cash:.2f}",
        "runway_weeks": run.runway_weeks,
        "reserve_breach": run.reserve_breach,
        "cash_floor_breach": run.cash_floor_breach,
        "baseline_hash": run.baseline_hash,
        "weekly_cash": [
            {
                "point_id": str(p.id),
                "week_number": p.week_number,
                "week_start": p.week_start.isoformat(),
                "opening_cash": f"{p.opening_cash:.2f}",
                "projected_inflows": f"{p.projected_inflows:.2f}",
                "projected_outflows": f"{p.projected_outflows:.2f}",
                "closing_cash": f"{p.closing_cash:.2f}",
                "value_label": p.value_label,
            }
            for p in points
        ],
    }

