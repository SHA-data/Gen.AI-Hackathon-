import time
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient, ASGITransport
import jwt

from services.api.app.core.auth import (
    AuthContext,
    RoleChecker,
    create_access_token,
    decode_access_token,
)
from services.api.app.core.config import settings
from services.api.app.core.errors import ForbiddenError, UnauthorizedError
from services.api.app.main import app


@pytest.mark.asyncio
async def test_create_and_decode_valid_token():
    user_id = uuid4()
    org_id = uuid4()
    token = create_access_token(user_id=user_id, org_id=org_id, role="admin")

    ctx = decode_access_token(token)
    assert ctx.user_id == user_id
    assert ctx.org_id == org_id
    assert ctx.role == "admin"


@pytest.mark.asyncio
async def test_expired_token_raises_unauthorized():
    user_id = uuid4()
    org_id = uuid4()
    # Expired token (exp in past)
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "role": "member",
        "iat": now - 3600,
        "exp": now - 1800,
    }
    expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(UnauthorizedError) as exc_info:
        decode_access_token(expired_token)
    assert "expired" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_role_hierarchy_checks():
    viewer = AuthContext(user_id=uuid4(), org_id=uuid4(), role="viewer")
    member = AuthContext(user_id=uuid4(), org_id=uuid4(), role="member")
    admin = AuthContext(user_id=uuid4(), org_id=uuid4(), role="admin")
    owner = AuthContext(user_id=uuid4(), org_id=uuid4(), role="owner")

    # Viewer
    assert viewer.can_perform("viewer") is True
    assert viewer.can_perform("member") is False
    assert viewer.can_perform("admin") is False

    # Member
    assert member.can_perform("viewer") is True
    assert member.can_perform("member") is True
    assert member.can_perform("admin") is False

    # Admin
    assert admin.can_perform("admin") is True
    assert admin.can_perform("owner") is False

    # Owner
    assert owner.can_perform("owner") is True

    # Test RoleChecker class
    admin_checker = RoleChecker("admin")
    assert admin_checker(admin) == admin
    with pytest.raises(ForbiddenError):
        admin_checker(member)


@pytest.mark.asyncio
async def test_dev_token_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        user_id = uuid4()
        org_id = uuid4()
        resp = await client.post(
            "/v1/dev/token",
            json={"user_id": str(user_id), "org_id": str(org_id), "role": "admin"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["role"] == "admin"
        assert data["org_id"] == str(org_id)
        assert data["user_id"] == str(user_id)

        # Use minted token against /v1/me
        token = data["access_token"]
        me_resp = await client.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["user_id"] == str(user_id)
        assert me_data["org_id"] == str(org_id)
        assert me_data["role"] == "admin"
