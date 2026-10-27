"""Moonshot Integration & Integrity Test Suite M1-M10 (PDF §15.2)."""
import pytest
from uuid import uuid4

from packages.contracts.moonshot import FakeMoonshotWorkflow, NeedsInputResult, MoonshotReport
from services.api.app.chat.verifier.engine import verifier_engine
from services.api.app.core.auth import DEMO_ORG_A, DEMO_ORG_B, DEMO_USER_A_MEMBER, DEMO_USER_B_MEMBER, create_access_token
from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_m1_missing_constraints_two_rounds():
    workflow = FakeMoonshotWorkflow()
    org_id = uuid4()
    user_id = uuid4()

    # Round 1: Returns needs_input with max 2 questions
    r1 = await workflow.run(org_id, user_id, goal="Grow revenue 100%")
    assert isinstance(r1, NeedsInputResult)
    assert r1.round_number == 1
    assert len(r1.questions) <= 2

    # Round 2: With answers, completes to full report
    r2 = await workflow.run(
        org_id,
        user_id,
        goal="Grow revenue 100%",
        answers={"risk_tolerance": "moderate", "budget_cap": "cap_50k"},
    )
    assert isinstance(r2, MoonshotReport)

@pytest.mark.asyncio
async def test_m2_strategy_below_cash_floor_flagged():
    workflow = FakeMoonshotWorkflow()
    report = await workflow.run(uuid4(), uuid4(), goal="Headcount expansion", answers={"risk_tolerance": "low"})
    # Must have failed gate for cash floor breach
    assert len(report.failed_gates) >= 1
    failed = report.failed_gates[0]
    assert "Cash Floor" in failed.failed_gate or "Cash" in failed.reason

    # Ensure failed strategy does NOT appear in ranked strategies (V6 check)
    v6_res = verifier_engine.verify_turn(
        answer_text="Sample report",
        current_turn_tool_results=[],
        caller_org_id=uuid4(),
        top_strategies=[s.model_dump() for s in report.top_strategies],
        failed_gates=[f.model_dump() for f in report.failed_gates],
    )
    assert any(c.check_name == "V6_gates" and c.status == "passed" for c in v6_res.checks)

def test_m3_m4_verifier_quotes_and_numbers():
    org_id = uuid4()
    # M3: Altered long quote fails V2
    bad_quote = '"' + ("Fake Quote " * 40) + '"'
    res_m3 = verifier_engine.verify_turn(
        answer_text=f"Quote: {bad_quote}",
        current_turn_tool_results=[],
        caller_org_id=org_id,
    )
    assert res_m3.overall_status == "failed"

    # M4: Unmatched figure marked unverified
    res_m4 = verifier_engine.verify_turn(
        answer_text="Our cash balance is $999,999.00.",
        current_turn_tool_results=[{"amount": "120000.00"}],
        caller_org_id=org_id,
    )
    assert res_m4.overall_status == "warning"

def test_m9_m10_isolation_and_disclaimer():
    # M9: Cross-tenant isolation
    token_a = create_access_token(DEMO_USER_A_MEMBER, DEMO_ORG_A, "member")
    token_b = create_access_token(DEMO_USER_B_MEMBER, DEMO_ORG_B, "member")

    res = client.post(
        "/v1/conversations",
        json={"title": "Private Org A"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    conv_id = res.json()["id"]

    # Org B reading Org A conversation -> 404
    get_res = client.get(f"/v1/conversations/{conv_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_res.status_code == 404

    # M10: Report without disclaimer fails V8
    v8_res = verifier_engine.verify_turn(
        answer_text="Strategic plan with top ranked moves and zero legal caveats",
        current_turn_tool_results=[],
        caller_org_id=DEMO_ORG_A,
        is_report_turn=True,
    )
    assert any(c.check_name == "V8_disclaimer" and c.status == "failed" for c in v8_res.checks)
