"""Unit tests for Claim & Quote Verification Engine."""
import uuid
import pytest
from services.api.app.moonshot.verifier import (
    audit_claim,
    compute_sha256,
    verify_disclaimer_presence,
    verify_quote,
)
from packages.contracts.finance import (
    CaseResult,
    ScenarioCases,
    ScenarioRunResponse,
    WeeklyCashPoint,
)
from datetime import date


def test_claim_tag_validation():
    # Valid tags
    for tag in ["cited", "computed", "inferred", "commentary"]:
        res = audit_claim("Sample claim text", tag=tag)
        assert res["status"] in ["verified", "unverified"]

    # Invalid tag fails immediately
    bad_res = audit_claim("Sample claim text", tag="invented_tag")
    assert bad_res["status"] == "failed"
    assert "Invalid claim tag" in bad_res["reason"]


def test_quote_hash_verification_and_tamper_rejection():
    quote = "We stopped billing by the hour and demanded upfront payments for fixed-scope project blocks."
    correct_hash = compute_sha256(quote)

    # Valid quote passes
    valid, err = verify_quote(quote, correct_hash)
    assert valid
    assert err is None

    # Tampered quote fails
    tampered_quote = "We stopped billing by the hour and demanded 50% upfront payments."
    valid_tampered, err_tampered = verify_quote(tampered_quote, correct_hash)
    assert not valid_tampered
    assert "Quote hash mismatch" in err_tampered


def test_quote_length_limit():
    long_quote = "A" * 301
    quote_hash = compute_sha256(long_quote)
    valid, err = verify_quote(long_quote, quote_hash)
    assert not valid
    assert "exceeds maximum allowed 300 characters" in err


def test_computed_cash_amount_audit():
    today = date(2026, 10, 24)
    scenario_res = ScenarioRunResponse(
        run_id=uuid.uuid4(),
        cases=ScenarioCases(
            expected=CaseResult(
                weekly_cash=[WeeklyCashPoint(week_start=today, cash="145000.00")],
                min_cash="110000.00",
                min_cash_date=today,
                end_cash="145000.00",
                runway_weeks=20,
            ),
            best=CaseResult(
                weekly_cash=[WeeklyCashPoint(week_start=today, cash="160000.00")],
                min_cash="120000.00",
                min_cash_date=today,
                end_cash="160000.00",
                runway_weeks=24,
            ),
            worst=CaseResult(
                weekly_cash=[WeeklyCashPoint(week_start=today, cash="95000.00")],
                min_cash="85000.00",
                min_cash_date=today,
                end_cash="95000.00",
                runway_weeks=12,
            ),
        ),
    )

    # Legitimate figure in scenario run (145000.00)
    audit_ok = audit_claim(
        "Expected ending cash reaches $145,000",
        tag="computed",
        scenario_ref=(145000.00, scenario_res),
    )
    assert audit_ok["status"] == "verified"

    # Invented / unfound figure (290000.00)
    audit_bad = audit_claim(
        "Expected ending cash reaches $290,000",
        tag="computed",
        scenario_ref=(290000.00, scenario_res),
    )
    assert audit_bad["status"] == "unverified"
    assert "could not be verified" in audit_bad["reason"]


def test_disclaimer_presence():
    valid_text = "Here is the moonshot report. Decision support, not financial advice. Forecasts depend on assumptions."
    assert verify_disclaimer_presence(valid_text)

    invalid_text = "Here is the moonshot report without any caution."
    assert not verify_disclaimer_presence(invalid_text)
