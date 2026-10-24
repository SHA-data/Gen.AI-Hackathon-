import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.core.auth import create_access_token
from services.api.app.core.database import async_session_factory, Base, engine
from services.api.app.core.models import Membership, Organization, User

SEED_ORGS = [
    {
        "id": UUID("00000000-0000-0000-0000-000000000001"),
        "name": "Acme Digital Agency",
        "base_currency": "USD",
        "users": [
            {"id": UUID("10000000-0000-0000-0000-000000000001"), "email": "alice.owner@acme.test", "display_name": "Alice Owner", "role": "owner"},
            {"id": UUID("10000000-0000-0000-0000-000000000002"), "email": "bob.admin@acme.test", "display_name": "Bob Admin", "role": "admin"},
            {"id": UUID("10000000-0000-0000-0000-000000000003"), "email": "charlie.member@acme.test", "display_name": "Charlie Member", "role": "member"},
            {"id": UUID("10000000-0000-0000-0000-000000000004"), "email": "dana.viewer@acme.test", "display_name": "Dana Viewer", "role": "viewer"},
        ],
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000002"),
        "name": "Globex Marketing",
        "base_currency": "USD",
        "users": [
            {"id": UUID("20000000-0000-0000-0000-000000000001"), "email": "eve.owner@globex.test", "display_name": "Eve Owner", "role": "owner"},
            {"id": UUID("20000000-0000-0000-0000-000000000002"), "email": "frank.admin@globex.test", "display_name": "Frank Admin", "role": "admin"},
            {"id": UUID("20000000-0000-0000-0000-000000000003"), "email": "grace.member@globex.test", "display_name": "Grace Member", "role": "member"},
            {"id": UUID("20000000-0000-0000-0000-000000000004"), "email": "heidi.viewer@globex.test", "display_name": "Heidi Viewer", "role": "viewer"},
        ],
    },
]


async def seed():
    # Ensure tables exist in target database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    tokens_catalog = {}

    async with async_session_factory() as session:
        for org_data in SEED_ORGS:
            org_id = org_data["id"]
            # Check or create org
            existing_org = await session.get(Organization, org_id)
            if not existing_org:
                org = Organization(
                    id=org_id,
                    name=org_data["name"],
                    base_currency=org_data["base_currency"],
                )
                session.add(org)
                await session.flush()
            else:
                org = existing_org

            tokens_catalog[str(org_id)] = {
                "name": org_data["name"],
                "users": {},
            }

            for u_data in org_data["users"]:
                user_id = u_data["id"]
                existing_user = await session.get(User, user_id)
                if not existing_user:
                    user = User(
                        id=user_id,
                        email=u_data["email"],
                        display_name=u_data["display_name"],
                    )
                    session.add(user)
                    await session.flush()
                else:
                    user = existing_user

                # Membership
                stmt = select(Membership).where(
                    Membership.org_id == org_id,
                    Membership.user_id == user_id,
                )
                res = await session.execute(stmt)
                membership = res.scalar_one_or_none()
                if not membership:
                    membership = Membership(
                        org_id=org_id,
                        user_id=user_id,
                        role=u_data["role"],
                    )
                    session.add(membership)
                    await session.flush()

                # Generate Bearer JWT
                token = create_access_token(
                    user_id=user_id,
                    org_id=org_id,
                    role=u_data["role"],
                )
                tokens_catalog[str(org_id)]["users"][u_data["role"]] = {
                    "user_id": str(user_id),
                    "email": u_data["email"],
                    "role": u_data["role"],
                    "jwt": token,
                }

        await session.commit()

    # Save tokens to a seed output file for tests & tools
    out_dir = Path("services/api/seed")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "seeded_tokens.json"
    with open(out_file, "w") as f:
        json.dump(tokens_catalog, f, indent=2)

    print(f"Database seeded successfully. Tokens saved to {out_file}")
    return tokens_catalog


if __name__ == "__main__":
    asyncio.run(seed())
