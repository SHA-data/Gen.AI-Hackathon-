"""Tests for shared contracts and fakes in /packages/contracts."""
import asyncio
import pytest
from uuid import uuid4
from datetime import date

from packages.contracts import (
    FakeFinanceService,
    ScenarioRunRequest,
    ScenarioDefinition,
    ScenarioChange,
    MetricRequest,
    FakeMoonshotWorkflow,
    NeedsInputResult,
    MoonshotReport,
    FakeLLMProvider,
    Message,
    FakeMemoryStore,
    FakeEmbeddingProvider,
    FakeSearchProvider,
    FakeSttProvider,
    ToolResultEnvelope,
)

@pytest.mark.asyncio
async def test_fake_finance_service():
    service = FakeFinanceService()
    org_id = uuid4()
    req = ScenarioRunRequest(
        baseline_run_id=uuid4(),
        horizon_weeks=26,
        scenario=ScenarioDefinition(
            name="Hire 2 Devs + 30d Client Delay",
            changes=[
                ScenarioChange(lever="hire", op="add", value=2),
                ScenarioChange(lever="payment_delay", op="set", value=30),
            ],
        ),
    )
    res = await service.run_scenario(org_id, req)
    assert res.status == "ok"
    assert "expected" in res.data.cases
    assert "best" in res.data.cases
    assert "worst" in res.data.cases
    assert len(res.data.cases["expected"].weekly_cash) == 26
    assert res.data.currency == "USD"

    metric_res = await service.get_metric(org_id, MetricRequest(metric_name="cash"))
    assert metric_res.status == "ok"
    assert metric_res.data.amount == "120000.00"

@pytest.mark.asyncio
async def test_fake_moonshot_workflow():
    workflow = FakeMoonshotWorkflow()
    org_id = uuid4()
    user_id = uuid4()

    # Round 1: Returns needs_input
    step1 = await workflow.run(org_id, user_id, goal="Double monthly recurring revenue")
    assert isinstance(step1, NeedsInputResult)
    assert step1.kind == "needs_input"
    assert len(step1.questions) == 2

    # Round 2: With answers, returns full MoonshotReport
    step2 = await workflow.run(
        org_id,
        user_id,
        goal="Double monthly recurring revenue",
        answers={"risk_tolerance": "moderate", "budget_cap": "cap_50k"},
    )
    assert isinstance(step2, MoonshotReport)
    assert step2.disclaimer_present is True
    assert len(step2.top_strategies) == 2
    assert len(step2.failed_gates) == 1

@pytest.mark.asyncio
async def test_fake_llm_provider():
    llm = FakeLLMProvider()
    resp = await llm.chat_with_tools([Message(role="user", content="Can we hire two developers?")])
    assert resp.tool_calls is not None
    assert resp.tool_calls[0].function.name == "finance.run_scenario"

    # Streaming test
    chunks = []
    async for chunk in llm.stream_chat([Message(role="user", content="Hello there")]):
        if chunk.delta_content:
            chunks.append(chunk.delta_content)
    full_text = "".join(chunks)
    assert "NeuralCFO" in full_text

@pytest.mark.asyncio
async def test_fake_memory_store():
    store = FakeMemoryStore()
    org_id = uuid4()
    user_id = uuid4()

    item = await store.propose(org_id, user_id, "payroll", "pay_date", "28th of every month")
    assert item.status == "proposed"

    confirmed = await store.confirm(org_id, item.id)
    assert confirmed.status == "confirmed"

    items = await store.read(org_id, user_id)
    assert len(items) == 1
    assert items[0].value == "28th of every month"

    trace = await store.trace(org_id, item.id)
    assert trace.backend == "fake_memory_store"

@pytest.mark.asyncio
async def test_fake_embedding_search_stt():
    embedder = FakeEmbeddingProvider()
    vec = await embedder.embed_text("test query")
    assert len(vec) == 1536

    searcher = FakeSearchProvider()
    results = await searcher.search("benchmarks")
    assert len(results) == 1
    assert results[0].is_untrusted is True

    stt = FakeSttProvider()
    res = await stt.transcribe(b"dummy", "audio.wav")
    assert "two developers" in res.raw_transcript
