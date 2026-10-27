"""Tests for Chat SSE event streaming (Part B2.3)."""
import json
import pytest
from uuid import uuid4

from services.api.app.chat.runtime.loop import AgentRuntimeLoop
from services.api.app.core.auth import AuthContext, DEMO_ORG_A, DEMO_USER_A_MEMBER

@pytest.mark.asyncio
async def test_chat_sse_stream_hiring_scenario():
    loop = AgentRuntimeLoop()
    auth = AuthContext(user_id=DEMO_USER_A_MEMBER, org_id=DEMO_ORG_A, role="member")
    conv_id = uuid4()

    events_received = []
    async for frame in loop.execute_turn(
        conversation_id=conv_id,
        user_message="Can we hire two developers if client Alpha pays 30 days late?",
        auth=auth,
        agent_key="neuralcfo",
    ):
        for line in frame.strip().split("\n"):
            if line.startswith("event: "):
                events_received.append(line.replace("event: ", "").strip())

    assert "tool_start" in events_received
    assert "tool_result" in events_received
    assert "chart" in events_received
    assert "token" in events_received
    assert "done" in events_received

@pytest.mark.asyncio
async def test_chat_sse_stream_moonshot():
    loop = AgentRuntimeLoop()
    auth = AuthContext(user_id=DEMO_USER_A_MEMBER, org_id=DEMO_ORG_A, role="member")
    conv_id = uuid4()

    events_received = []
    async for frame in loop.execute_turn(
        conversation_id=conv_id,
        user_message="What bold move could fix this instead?",
        auth=auth,
        agent_key="moonshot",
    ):
        for line in frame.strip().split("\n"):
            if line.startswith("event: "):
                events_received.append(line.replace("event: ", "").strip())

    assert "stage" in events_received
    assert "tool_start" in events_received
    assert "done" in events_received
