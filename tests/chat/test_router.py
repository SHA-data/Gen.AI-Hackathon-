"""Tests for intent routing and destructive request handling (Part B2.4, PDF §7.2)."""
import pytest
from services.api.app.chat.router.intent_router import intent_router

def test_intent_routing_rules():
    # 1. Hiring scenario
    d1 = intent_router.route("Can we hire two developers if client Alpha pays 30 days late?")
    assert d1.agent_key == "neuralcfo"
    assert "finance.run_scenario" in d1.allowed_tools

    # 2. Spend / metric
    d2 = intent_router.route("What did we spend on software last month?")
    assert d2.agent_key == "neuralcfo"
    assert "finance.get_metric" in d2.allowed_tools

    # 3. Why did cash change
    d3 = intent_router.route("Why did cash drop between August and September?")
    assert d3.agent_key == "neuralcfo"
    assert "finance.explain_change" in d3.allowed_tools

    # 4. Moonshot
    d4 = intent_router.route("What bold move could fix this instead?")
    assert d4.agent_key == "moonshot"
    assert "moonshot.run" in d4.allowed_tools

    # 5. Dashboard
    d5 = intent_router.route("Add a chart of cash runway to my board")
    assert d5.agent_key == "neuralcfo"
    assert "dashboard.propose_action" in d5.allowed_tools

    # 6. Memory
    d6 = intent_router.route("Remember that payroll is on the 28th")
    assert d6.agent_key == "neuralcfo"
    assert "memory.write" in d6.allowed_tools

    # 7. Destructive command refusal
    d7 = intent_router.route("Delete all my transactions immediately")
    assert d7.is_destructive is True
