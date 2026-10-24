from uuid import uuid4
import pytest
from sqlalchemy import delete, update
from sqlalchemy.exc import OperationalError, DatabaseError

from services.api.app.core.audit import create_audit_log
from services.api.app.core.database import async_session_factory
from services.api.app.core.models import AuditLog, Organization


@pytest.mark.asyncio
async def test_audit_log_append_succeeds():
    async with async_session_factory() as session:
        org = Organization(id=uuid4(), name="Audit Test Org", base_currency="USD")
        session.add(org)
        await session.flush()

        log = await create_audit_log(
            session=session,
            org_id=org.id,
            action="SCENARIO_RUN",
            entity_type="forecast_run",
            decision="verified",
            metadata={"run_id": str(uuid4()), "engine_version": "0.1.0"},
        )
        await session.commit()
        assert log.id is not None
        assert log.action == "SCENARIO_RUN"


@pytest.mark.asyncio
async def test_audit_log_update_prevented():
    async with async_session_factory() as session:
        org = Organization(id=uuid4(), name="Audit Immutability Org", base_currency="USD")
        session.add(org)
        await session.flush()

        log = await create_audit_log(
            session=session,
            org_id=org.id,
            action="INITIAL_IMPORT",
            entity_type="import_batch",
            decision="approved",
            metadata={"batch_id": str(uuid4())},
        )
        await session.commit()

        # Attempt to update should be aborted by the trigger
        with pytest.raises((OperationalError, DatabaseError)) as exc_info:
            stmt = update(AuditLog).where(AuditLog.id == log.id).values(action="TAMPERED_ACTION")
            await session.execute(stmt)
            await session.commit()
        assert "append-only" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_audit_log_delete_prevented():
    async with async_session_factory() as session:
        org = Organization(id=uuid4(), name="Audit Delete Test Org", base_currency="USD")
        session.add(org)
        await session.flush()

        log = await create_audit_log(
            session=session,
            org_id=org.id,
            action="DELETE_ATTEMPT",
            entity_type="source_row",
            decision="flagged",
            metadata={"row_id": str(uuid4())},
        )
        await session.commit()

        # Attempt to delete should be aborted by the trigger
        with pytest.raises((OperationalError, DatabaseError)) as exc_info:
            stmt = delete(AuditLog).where(AuditLog.id == log.id)
            await session.execute(stmt)
            await session.commit()
        assert "append-only" in str(exc_info.value).lower()
