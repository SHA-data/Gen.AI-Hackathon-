"""End-to-End Tests for Moonshot Workflow & Fake Parity."""
import uuid
import pytest
from services.api.app.moonshot.workflow import FakeMoonshotWorkflow, MoonshotWorkflow
from packages.contracts.finance import FakeFinanceService
from packages.contracts.llm import FakeLLMProvider


def test_moonshot_workflow_end_to_end_with_clarification():
    workflow = MoonshotWorkflow(
        llm=FakeLLMProvider(),
        finance_service=FakeFinanceService(baseline_cash=120000.0),
    )
    goal = "Transition our web development agency from billing hourly to $15k monthly upfront retainers"

    # Step 1: Run with missing constraints -> triggers needs_input
    res_input = workflow.run(goal=goal, provided_constraints={})
    assert res_input["status"] == "needs_input"
    assert "questions" in res_input
    assert len(res_input["questions"]) > 0
    request_id = res_input["request_id"]

    # Step 2: Resume with user answers
    answers = {
        "horizon_weeks": 26,
        "budget_cap": 50000.0,
        "team_size": 4,
        "risk_tolerance": "medium",
        "cash_floor_weeks": 12,
    }
    res_complete = workflow.resume(request_id=request_id, answers=answers)
    assert res_complete["status"] == "completed"
    assert "report" in res_complete

    report = res_complete["report"]
    assert report["disclaimer_verified"]
    assert "Decision support, not financial advice" in report["disclaimer"]
    assert report["top_strategies_count"] > 0
    assert "sensitivity" in report
    assert "report_markdown" in report
    assert len(report["claims_audit"]) > 0


def test_fake_moonshot_workflow_parity():
    fake = FakeMoonshotWorkflow()
    goal = "Triple our MRR in 6 months"
    res = fake.run(goal=goal)
    assert res["status"] == "completed"
    assert "report" in res
    assert res["report"]["disclaimer_verified"]
    assert "top_pick" in res["report"]["report_markdown"].lower() or "retainer" in res["report"]["report_markdown"].lower()
