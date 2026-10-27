"""Meterless Memory Smoke Test & Cross-Session Recall (Part B2.10, Demo Step 8)."""
import pytest
from uuid import uuid4
from services.api.app.chat.adapters.memory.meterless import MeterlessMemoryStore

@pytest.mark.asyncio
async def test_meterless_smoke_write_read_trace():
    store = MeterlessMemoryStore()
    org_id = uuid4()
    user_id = uuid4()

    # 1. Write (Propose) memory
    item = await store.propose(
        org_id=org_id,
        user_id=user_id,
        category="payroll_schedule",
        key="pay_day",
        value="Payroll occurs on the 28th of every month.",
    )
    assert item.status == "proposed"
    assert item.key == "pay_day"

    # 2. Confirm memory
    confirmed = await store.confirm(org_id, item.id)
    assert confirmed.status == "confirmed"

    # 3. Read back confirmed memory
    items = await store.read(org_id, user_id, category="payroll_schedule")
    assert len(items) == 1
    assert items[0].value == "Payroll occurs on the 28th of every month."

    # 4. Trace the memory lineage
    trace = await store.trace(org_id, item.id)
    assert trace.memory_id == item.id
    assert len(trace.history) >= 2
    assert "meterless" in trace.backend

@pytest.mark.asyncio
async def test_meterless_cross_session_recall():
    """Demo Step 8: Prove that stored assumptions carry over into a second session."""
    store = MeterlessMemoryStore()
    org_id = uuid4()
    user_id = uuid4()

    # Session 1: User says "Remember that payroll is on the 28th"
    session1_item = await store.propose(
        org_id=org_id,
        user_id=user_id,
        category="assumptions",
        key="payroll_date",
        value="28th of the month",
    )
    await store.confirm(org_id, session1_item.id)

    # Session 2: User starts a new conversation in a fresh session
    # System reads existing confirmed memories for (org_id, user_id)
    session2_memories = await store.read(org_id=org_id, user_id=user_id, status="confirmed")
    assert len(session2_memories) == 1
    assert session2_memories[0].key == "payroll_date"
    assert session2_memories[0].value == "28th of the month"
