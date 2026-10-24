from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from services.api.app.core.database import async_session_factory
from services.api.app.core.models import (
    Claim,
    DecisionRun,
    Membership,
    Organization,
    User,
)


@pytest.mark.asyncio
async def test_org_tenant_data_isolation():
    async with async_session_factory() as session:
        # Create two distinct organizations
        org_a = Organization(id=uuid4(), name="Tenant A Alpha", base_currency="USD")
        org_b = Organization(id=uuid4(), name="Tenant B Beta", base_currency="EUR")
        session.add_all([org_a, org_b])
        await session.flush()

        # Create decision runs in each org
        run_a = DecisionRun(id=uuid4(), org_id=org_a.id, kind="cfo", status="verified")
        run_b = DecisionRun(id=uuid4(), org_id=org_b.id, kind="cfo", status="verified")
        session.add_all([run_a, run_b])
        await session.flush()

        # Create claims in each org
        claim_a = Claim(
            id=uuid4(),
            org_id=org_a.id,
            decision_run_id=run_a.id,
            text="Org A Cash Runway: 24 weeks",
            tag="computed",
            status="verified",
        )
        claim_b = Claim(
            id=uuid4(),
            org_id=org_b.id,
            decision_run_id=run_b.id,
            text="Org B Cash Runway: 12 weeks",
            tag="computed",
            status="verified",
        )
        session.add_all([claim_a, claim_b])
        await session.commit()

        # Verify querying for Org A returns only Org A's claims
        stmt_a = select(Claim).where(Claim.org_id == org_a.id)
        res_a = await session.execute(stmt_a)
        claims_a = res_a.scalars().all()
        assert len(claims_a) == 1
        assert claims_a[0].id == claim_a.id
        assert claims_a[0].text == "Org A Cash Runway: 24 weeks"

        # Verify querying for Org B returns only Org B's claims
        stmt_b = select(Claim).where(Claim.org_id == org_b.id)
        res_b = await session.execute(stmt_b)
        claims_b = res_b.scalars().all()
        assert len(claims_b) == 1
        assert claims_b[0].id == claim_b.id
        assert claims_b[0].text == "Org B Cash Runway: 12 weeks"


@pytest.mark.asyncio
async def test_duplicate_membership_in_same_org_fails():
    async with async_session_factory() as session:
        org = Organization(id=uuid4(), name="Isolated Org", base_currency="USD")
        user = User(id=uuid4(), email=f"user_{uuid4().hex[:8]}@test.com", display_name="Test User")
        session.add_all([org, user])
        await session.flush()

        mem1 = Membership(id=uuid4(), org_id=org.id, user_id=user.id, role="member")
        session.add(mem1)
        await session.commit()

        # Second membership for same user in same org must violate unique constraint
        mem2 = Membership(id=uuid4(), org_id=org.id, user_id=user.id, role="admin")
        session.add(mem2)
        with pytest.raises(IntegrityError):
            await session.commit()
