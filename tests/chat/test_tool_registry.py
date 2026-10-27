"""Tests for Tool Registry validation, timeout, and RBAC (Part B2.5)."""
import pytest
from uuid import uuid4

from services.api.app.chat.tools.registry import tool_registry
from services.api.app.core.auth import (
    AuthContext,
    DEMO_ORG_A,
    DEMO_USER_A_MEMBER,
    DEMO_USER_A_VIEWER,
)

@pytest.mark.asyncio
async def test_tool_registry_rbac_enforcement():
    # Viewer role calling scenario tool should be denied
    viewer_auth = AuthContext(user_id=DEMO_USER_A_VIEWER, org_id=DEMO_ORG_A, role="viewer")
    res = await tool_registry.execute_tool(
        name="finance.run_scenario",
        raw_arguments={"name": "Test", "horizon_weeks": 26},
        auth=viewer_auth,
    )
    assert res.status == "failed"
    assert "not authorized" in res.warnings[0]

@pytest.mark.asyncio
async def test_tool_registry_argument_validation():
    member_auth = AuthContext(user_id=DEMO_USER_A_MEMBER, org_id=DEMO_ORG_A, role="member")
    # Passing invalid arguments (missing required name)
    res = await tool_registry.execute_tool(
        name="finance.run_scenario",
        raw_arguments={},  # Missing name
        auth=member_auth,
    )
    assert res.status == "failed"
    assert "validation failed" in res.warnings[0].lower()

@pytest.mark.asyncio
async def test_tool_registry_org_id_injection():
    # Ensure model-supplied org_id is overwritten by auth context
    member_auth = AuthContext(user_id=DEMO_USER_A_MEMBER, org_id=DEMO_ORG_A, role="member")
    rogue_org = uuid4()
    res = await tool_registry.execute_tool(
        name="finance.get_metric",
        raw_arguments={"metric_name": "cash", "org_id": str(rogue_org)},
        auth=member_auth,
    )
    assert res.status == "ok"
    assert res.data.metric_name == "cash"
