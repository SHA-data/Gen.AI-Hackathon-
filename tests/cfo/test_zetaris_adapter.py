from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient

from services.api.app.cfo.adapters.csv_adapter import CsvAdapter
from services.api.app.cfo.adapters.zetaris_adapter import ZetarisAdapter
from services.api.app.core.auth import create_access_token
from services.api.app.core.database import async_session_factory
from services.api.app.main import app
from services.api.seed.seed_data import SEED_ORGS

DEMO_ORG_ID = SEED_ORGS[0]["id"]


@pytest.mark.asyncio
async def test_zetaris_smoke_test():
    res = await ZetarisAdapter.smoke_test()
    assert res["connected"] is True
    assert res["smoke_test_status"] == "PASSED"
    assert res["transactions_count"] > 0
    assert res["invoices_count"] > 0
    assert "sample_tx" in res
    assert "source" in res["sample_tx"]


@pytest.mark.asyncio
async def test_csv_adapter_queries():
    async with async_session_factory() as session:
        adapter = CsvAdapter(session)
        assert await adapter.connect() is True

        txs = await adapter.query_transactions(DEMO_ORG_ID)
        assert len(txs) > 0

        invs = await adapter.query_invoices(DEMO_ORG_ID)
        assert len(invs) > 0
        assert any(i["client"] == "Apex Corp" for i in invs)


@pytest.mark.asyncio
async def test_http_zetaris_smoke_test_endpoint():
    token = create_access_token(user_id=uuid4(), org_id=DEMO_ORG_ID, role="member")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/v1/finance/zetaris/smoke-test",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["smoke_test_status"] == "PASSED"
        assert data["health"]["status"] == "healthy"
