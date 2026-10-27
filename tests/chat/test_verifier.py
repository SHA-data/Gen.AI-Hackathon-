"""Tests for deterministic Verifier Engine checks V1-V9 (Part B2.6, PDF §12.2)."""
import pytest
from uuid import uuid4

from services.api.app.chat.verifier.engine import verifier_engine

def test_v1_numbers_matching():
    org_id = uuid4()
    tool_results = [{"cases": {"expected": {"min_cash": "45000.00", "runway_weeks": 18}}}]
    answer_text = "Your projected minimum cash is $45,000.00 with 18 weeks of runway."

    res = verifier_engine.verify_turn(
        answer_text=answer_text,
        current_turn_tool_results=tool_results,
        caller_org_id=org_id,
    )
    assert res.overall_status == "verified"

def test_v1_numbers_unverified_flag():
    org_id = uuid4()
    # Tool output does not contain 95000
    tool_results = [{"cases": {"expected": {"min_cash": "45000.00", "runway_weeks": 18}}}]
    answer_text = "Your projected cash will reach $95,000.00 next month."

    res = verifier_engine.verify_turn(
        answer_text=answer_text,
        current_turn_tool_results=tool_results,
        caller_org_id=org_id,
    )
    assert res.overall_status == "warning"
    assert "$95,000.00" in res.checks[0].details["unverified_numbers"]

def test_v2_quotes_length_and_hash():
    org_id = uuid4()
    # Quote longer than 300 characters should fail
    long_quote = '"' + ("A" * 350) + '"'
    res = verifier_engine.verify_turn(
        answer_text=f"As stated: {long_quote}",
        current_turn_tool_results=[],
        caller_org_id=org_id,
    )
    assert res.overall_status == "failed"
    assert res.checks[1].check_name == "V2_quotes"
    assert res.checks[1].status == "failed"

def test_v8_disclaimer_on_report():
    org_id = uuid4()
    # Report without disclaimer fails V8
    report_without_disclaimer = "Here is your Moonshot strategic report with top ranked moves."
    res = verifier_engine.verify_turn(
        answer_text=report_without_disclaimer,
        current_turn_tool_results=[],
        caller_org_id=org_id,
        is_report_turn=True,
    )
    assert res.overall_status == "failed"
    assert res.checks[5].check_name == "V8_disclaimer"
    assert res.checks[5].status == "failed"

    # With disclaimer passes
    report_with_disclaimer = (
        "Here is your Moonshot report. Disclaimer: NeuralCFO provides decision support, not financial advice."
    )
    res_pass = verifier_engine.verify_turn(
        answer_text=report_with_disclaimer,
        current_turn_tool_results=[],
        caller_org_id=org_id,
        is_report_turn=True,
    )
    assert res_pass.overall_status == "verified"
