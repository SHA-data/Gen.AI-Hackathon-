from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from services.api.app.cfo.services.baseline_service import BaselineService
from services.api.app.cfo.verification.lineage import LineageResolver
from services.api.app.core.auth import create_access_token
from services.api.app.core.database import async_session_factory
from services.api.app.core.evidence import EvidenceRegistry, create_claim_with_evidence
from services.api.app.core.models import Claim, DecisionRun, EvidenceLink
from services.api.app.main import app
from services.api.seed.seed_data import SEED_ORGS

DEMO_ORG_ID = SEED_ORGS[0]["id"]


@pytest.mark.asyncio
async def test_forecast_point_lineage_resolution():
    async with async_session_factory() as session:
        run, points = await BaselineService.get_latest_baseline(session, DEMO_ORG_ID)
        # Select week 3 (which has invoice inflows and payroll)
        target_point = points[2]

        lineage = await LineageResolver.get_point_lineage(session, DEMO_ORG_ID, target_point.id)
        assert lineage["point_id"] == str(target_point.id)
        assert lineage["run_id"] == str(run.id)
        assert "formula" in lineage
        assert lineage["calculation"]["closing_cash"] == f"{target_point.closing_cash:.2f}"
        assert len(lineage["source_rows"]) > 0

    # Test HTTP endpoint
    token = create_access_token(user_id=uuid4(), org_id=DEMO_ORG_ID, role="member")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/v1/finance/forecast-points/{target_point.id}/lineage",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["point_id"] == str(target_point.id)
        assert len(data["source_rows"]) > 0


@pytest.mark.asyncio
async def test_evidence_target_resolvers():
    async with async_session_factory() as session:
        run, points = await BaselineService.get_latest_baseline(session, DEMO_ORG_ID)
        target_point = points[0]

        # 1. Resolve forecast_point
        res_pt = await EvidenceRegistry.resolve_target(session, DEMO_ORG_ID, "forecast_point", target_point.id)
        assert res_pt is not None
        assert res_pt["type"] == "forecast_point"
        assert res_pt["closing_cash"] == str(target_point.closing_cash)

        # 2. Resolve forecast_run
        res_run = await EvidenceRegistry.resolve_target(session, DEMO_ORG_ID, "forecast_run", run.id)
        assert res_run is not None
        assert res_run["type"] == "forecast_run"
        assert res_run["case_type"] == "baseline"


@pytest.mark.asyncio
async def test_create_claim_with_computed_evidence():
    async with async_session_factory() as session:
        run, points = await BaselineService.get_latest_baseline(session, DEMO_ORG_ID)
        target_point = points[0]

        decision_run = DecisionRun(
            id=uuid4(),
            org_id=DEMO_ORG_ID,
            kind="cfo",
            status="verified",
        )
        session.add(decision_run)
        await session.flush()

        claim = await create_claim_with_evidence(
            session=session,
            org_id=DEMO_ORG_ID,
            decision_run_id=decision_run.id,
            text=f"Closing cash for week 1 is projected at ${target_point.closing_cash:.2f}",
            tag="computed",
            status="verified",
            target_type="forecast_point",
            target_id=target_point.id,
        )
        await session.commit()

        assert claim.id is not None
        assert claim.tag == "computed"

        # Check evidence link was created
        stmt = select(EvidenceLink).where(EvidenceLink.claim_id == claim.id)
        link = (await session.execute(stmt)).scalar_one_or_none()
        assert link is not None
        assert link.target_type == "forecast_point"
        assert link.target_id == target_point.id
