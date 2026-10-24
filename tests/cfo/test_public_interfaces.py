from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient

from packages.contracts.envelope import ToolStatus
from services.api.app.cfo.services.finance_service import RealFinanceService
from services.api.app.cfo.services.snapshot_service import RealCfoSnapshotService
from services.api.app.core.auth import create_access_token
from services.api.app.core.database import async_session_factory
from services.api.app.main import app
from services.api.seed.seed_data import SEED_ORGS

DEMO_ORG_ID = SEED_ORGS[0]["id"]


@pytest.mark.asyncio
async def test_python_finance_and_snapshot_services():
    async with async_session_factory() as session:
        # 1. Snapshot Service
        snapshot_env = await RealCfoSnapshotService.get(session, DEMO_ORG_ID)
        assert snapshot_env.status == ToolStatus.OK
        assert "cash" in snapshot_env.data
        assert "baseline_run_id" in snapshot_env.data
        assert snapshot_env.data["currency"] == "USD"

        # 2. Finance Service Metrics
        cash_env = await RealFinanceService.get_metric(session, DEMO_ORG_ID, "cash")
        assert cash_env.status == ToolStatus.OK
        assert cash_env.data["metric"] == "cash"
        assert cash_env.data["value"] == "185000.00"

        rec_env = await RealFinanceService.get_metric(session, DEMO_ORG_ID, "receivables")
        assert rec_env.status == ToolStatus.OK
        assert rec_env.data["metric"] == "receivables"

        pay_env = await RealFinanceService.get_metric(session, DEMO_ORG_ID, "payroll")
        assert pay_env.status == ToolStatus.OK
        assert pay_env.data["value"] == "60000.00"

        # 3. Source Rows Listing
        rows_env = await RealFinanceService.list_source_rows(session, DEMO_ORG_ID)
        assert rows_env.status == ToolStatus.OK
        assert rows_env.data["count"] > 0

        # 4. Explain Change
        explain_env = await RealFinanceService.explain_change(
            session, DEMO_ORG_ID, "cash", from_date=None, to_date=None
        )
        assert explain_env.status == ToolStatus.OK
        assert "drivers" in explain_env.data


@pytest.mark.asyncio
async def test_http_public_endpoints():
    member_token = create_access_token(user_id=uuid4(), org_id=DEMO_ORG_ID, role="member")
    admin_token = create_access_token(user_id=uuid4(), org_id=DEMO_ORG_ID, role="admin")
    viewer_token = create_access_token(user_id=uuid4(), org_id=DEMO_ORG_ID, role="viewer")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET /v1/finance/metrics
        resp = await client.get(
            "/v1/finance/metrics?metric=cash",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["data"]["metric"] == "cash"

        # GET /v1/finance/snapshot
        resp = await client.get(
            "/v1/finance/snapshot",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert "baseline_run_id" in resp.json()["data"]

        # GET /v1/finance/source-rows
        resp = await client.get(
            "/v1/finance/source-rows",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["data"]["count"] > 0

        # GET /v1/finance/settings
        resp = await client.get(
            "/v1/finance/settings",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert resp.status_code == 200
        assert "reserve_amount" in resp.json()

        # PATCH /v1/finance/settings - viewer fails
        resp_v = await client.patch(
            "/v1/finance/settings",
            json={"reserve_amount": "65000.00"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp_v.status_code == 403

        # PATCH /v1/finance/settings - admin succeeds
        resp_a = await client.patch(
            "/v1/finance/settings",
            json={"reserve_amount": "65000.00"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp_a.status_code == 200
        assert resp_a.json()["status"] == "ok"
