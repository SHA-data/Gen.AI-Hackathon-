from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient

from packages.contracts.envelope import (
    ErrorDetail,
    ErrorEnvelope,
    ResultStatus,
    ToolResultEnvelope,
    ToolStatus,
)
from services.api.app.main import app


def test_envelope_models():
    # Error envelope shape
    err = ErrorEnvelope(
        error=ErrorDetail(
            code="UNAUTHORIZED",
            message="Token required",
            details={"field": "Authorization"},
            request_id=str(uuid4()),
        )
    )
    d = err.model_dump()
    assert "error" in d
    assert d["error"]["code"] == "UNAUTHORIZED"
    assert "request_id" in d["error"]

    # Tool result envelope shape
    tool_env = ToolResultEnvelope(
        status=ToolStatus.OK,
        data={"metric": "cash", "value": "185000.00"},
        sources=[str(uuid4())],
        warnings=[],
        run_id=str(uuid4()),
    )
    t = tool_env.model_dump()
    assert t["status"] == "ok"
    assert "data" in t
    assert "sources" in t
    assert "warnings" in t
    assert "run_id" in t

    # ResultStatus enum values
    assert ResultStatus.VERIFIED == "verified"
    assert ResultStatus.WARNING == "warning"
    assert ResultStatus.UNVERIFIED == "unverified"
    assert ResultStatus.FAILED == "failed"


@pytest.mark.asyncio
async def test_api_error_envelope_response():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Calling /v1/me without token produces ErrorEnvelope with 401
        resp = await client.get("/v1/me")
        assert resp.status_code == 401
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "UNAUTHORIZED"
        assert "request_id" in data["error"]
        assert resp.headers.get("X-Request-ID") == data["error"]["request_id"]
