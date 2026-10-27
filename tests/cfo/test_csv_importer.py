import json
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from services.api.app.cfo.models import AnomalyFlag, ImportBatch, Invoice, SourceRow
from services.api.app.core.auth import create_access_token
from services.api.app.core.database import async_session_factory
from services.api.app.main import app


@pytest.mark.asyncio
async def test_idempotent_import_stores_raw_rows():
    org_id = uuid4()
    admin_id = uuid4()
    admin_token = create_access_token(user_id=admin_id, org_id=org_id, role="admin")

    csv_content = (
        "invoice_number,client,amount,currency,issue_date,due_date,expected_payment_date\n"
        "TEST-INV-001,Alpha Corp,12500.00,USD,2026-11-01,2026-12-01,2026-12-01\n"
        "TEST-INV-002,Beta LLC,8000.00,USD,2026-11-05,2026-12-05,2026-12-05\n"
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First upload
        files = {"file": ("test_invoices.csv", csv_content.encode("utf-8"), "text/csv")}
        data = {"file_type": "invoices"}
        headers = {"Authorization": f"Bearer {admin_token}"}

        resp = await client.post("/v1/finance/imports", files=files, data=data, headers=headers)
        assert resp.status_code == 200
        res = resp.json()
        assert res["status"] == "completed"
        assert res["total_rows"] == 2
        assert res["accepted_rows"] == 2
        assert res["rejected_rows"] == 0
        batch_id = res["batch_id"]

        # Check DB source_rows
        async with async_session_factory() as session:
            stmt = select(SourceRow).where(SourceRow.batch_id == batch_id)
            rows = (await session.execute(stmt)).scalars().all()
            assert len(rows) == 2
            assert rows[0].raw_payload["invoice_number"] == "TEST-INV-001"
            assert rows[1].raw_payload["invoice_number"] == "TEST-INV-002"

        # Idempotent re-upload of identical file
        files2 = {"file": ("test_invoices.csv", csv_content.encode("utf-8"), "text/csv")}
        resp2 = await client.post("/v1/finance/imports", files=files2, data=data, headers=headers)
        assert resp2.status_code == 200
        res2 = resp2.json()
        assert res2["batch_id"] == batch_id  # Same batch returned


@pytest.mark.asyncio
async def test_import_quality_report_flags_duplicates():
    org_id = uuid4()
    admin_id = uuid4()
    admin_token = create_access_token(user_id=admin_id, org_id=org_id, role="admin")

    # Upload first invoice
    csv1 = (
        "invoice_number,client,amount,issue_date,due_date\n"
        "DUP-INV-100,Global Tech,25000.00,2026-11-01,2026-12-01\n"
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp1 = await client.post(
            "/v1/finance/imports",
            files={"file": ("invoices1.csv", csv1.encode("utf-8"), "text/csv")},
            data={"file_type": "invoices"},
            headers=headers,
        )
        assert resp1.status_code == 200

        # Upload duplicate invoice number in second batch
        csv2 = (
            "invoice_number,client,amount,issue_date,due_date\n"
            "DUP-INV-100,Global Tech Conflict,30000.00,2026-11-02,2026-12-02\n"
        )
        resp2 = await client.post(
            "/v1/finance/imports",
            files={"file": ("invoices2.csv", csv2.encode("utf-8"), "text/csv")},
            data={"file_type": "invoices"},
            headers=headers,
        )
        assert resp2.status_code == 200
        res2 = resp2.json()
        assert res2["flagged_rows"] == 1
        assert len(res2["quality_report"]["flagged_anomalies"]) == 1
        assert res2["quality_report"]["flagged_anomalies"][0]["anomaly"] == "duplicate_invoice"

        # Check anomaly_flags table
        async with async_session_factory() as session:
            stmt = select(AnomalyFlag).where(
                AnomalyFlag.org_id == org_id,
                AnomalyFlag.anomaly_type == "duplicate_invoice",
            )
            flag = (await session.execute(stmt)).scalar_one_or_none()
            assert flag is not None
            assert flag.status == "flagged"


@pytest.mark.asyncio
async def test_detects_column_mapping_ambiguity():
    org_id = uuid4()
    admin_id = uuid4()
    admin_token = create_access_token(user_id=admin_id, org_id=org_id, role="admin")

    # Ambiguous headers: both 'amount' and 'total'
    csv_ambiguous = (
        "invoice_number,client,amount,total,date\n"
        "AMB-01,Acme,1000.00,1200.00,2026-11-01\n"
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = await client.post(
            "/v1/finance/imports",
            files={"file": ("ambiguous.csv", csv_ambiguous.encode("utf-8"), "text/csv")},
            data={"file_type": "invoices"},
            headers=headers,
        )
        assert resp.status_code == 200
        res = resp.json()
        assert res["status"] == "needs_mapping"
        assert len(res["quality_report"]["ambiguities"]) > 0


@pytest.mark.asyncio
async def test_invalid_rows_reported_with_reasons():
    org_id = uuid4()
    admin_id = uuid4()
    admin_token = create_access_token(user_id=admin_id, org_id=org_id, role="admin")

    # One good row, one bad amount row, one missing client row
    csv_corrupt = (
        "invoice_number,client,amount,issue_date,due_date\n"
        "VALID-01,Good Client,5000.00,2026-11-01,2026-12-01\n"
        "BAD-01,Client Two,NOT_A_NUMBER,2026-11-01,2026-12-01\n"
        "BAD-02,,7000.00,2026-11-01,2026-12-01\n"
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = await client.post(
            "/v1/finance/imports",
            files={"file": ("corrupt.csv", csv_corrupt.encode("utf-8"), "text/csv")},
            data={"file_type": "invoices"},
            headers=headers,
        )
        assert resp.status_code == 200
        res = resp.json()
        assert res["total_rows"] == 3
        assert res["accepted_rows"] == 1
        assert res["rejected_rows"] == 2
        assert len(res["quality_report"]["rejected_rows"]) == 2


@pytest.mark.asyncio
async def test_viewer_cannot_import_role_check():
    org_id = uuid4()
    viewer_id = uuid4()
    viewer_token = create_access_token(user_id=viewer_id, org_id=org_id, role="viewer")

    csv_data = "invoice_number,client,amount\nINV-1,Test,100\n"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {viewer_token}"}
        resp = await client.post(
            "/v1/finance/imports",
            files={"file": ("test.csv", csv_data.encode("utf-8"), "text/csv")},
            data={"file_type": "invoices"},
            headers=headers,
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data["error"]["code"] == "FORBIDDEN"
