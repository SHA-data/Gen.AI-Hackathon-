"""Contract & Seed Dataset Integrity Tests."""
import uuid
import pytest
from packages.contracts.finance import FakeFinanceService, ScenarioChange, ScenarioPayload, ScenarioRunRequest
from packages.contracts.llm import FakeLLMProvider
from packages.contracts.moonshot import FixedConstraints, GoalAssumption
from services.api.app.moonshot.cards import SEED_APPROVED_CARDS, get_approved_cards, make_quote_hash


def test_fake_finance_service_contract_conformance():
    fake_cfo = FakeFinanceService(baseline_cash=100000.0, monthly_burn=25000.0)
    org_id = uuid.uuid4()

    # 1. Snapshot test
    snapshot = fake_cfo.get_snapshot(org_id)
    assert snapshot.org_id == org_id
    assert snapshot.currency == "USD"
    assert float(snapshot.cash) == 100000.0
    assert snapshot.runway_weeks > 0

    # 2. Scenario Run test
    req = ScenarioRunRequest(
        baseline_run_id=snapshot.baseline_run_id,
        horizon_weeks=26,
        scenario=ScenarioPayload(
            name="Test Price Hike",
            origin="moonshot_card",
            changes=[
                ScenarioChange(lever="price_change_pct", op="add", value=20, is_assumption=True)
            ],
        ),
    )
    res = fake_cfo.run_scenario(req, org_id)
    assert res.status == "verified"
    assert res.engine_version == "1.0.0"
    assert len(res.cases.expected.weekly_cash) > 0
    assert float(res.cases.expected.end_cash) > 0.0
    assert float(res.cases.best.end_cash) >= float(res.cases.expected.end_cash)
    assert float(res.cases.expected.end_cash) >= float(res.cases.worst.end_cash)


def test_seed_cards_integrity_and_hr_rules():
    """Validates that all 12 approved seed cards comply with HR-03, HR-04, HR-09, HR-10, HR-12."""
    cards = get_approved_cards()
    assert len(cards) == 12, f"Expected 12 approved cards, got {len(cards)}"

    for card in cards:
        # HR-10: reviewer, review date, documented citation
        assert card.status == "approved"
        assert card.reviewer != ""
        assert card.review_date is not None
        assert len(card.source_citation) > 0

        # HR-04: excerpt length <= 300 chars & exact hash match
        assert len(card.source_excerpt) <= 300, f"Card '{card.title}' excerpt exceeds 300 chars"
        expected_hash = make_quote_hash(card.source_excerpt)
        assert card.source_excerpt_hash == expected_hash, f"Card '{card.title}' hash mismatch"

        # Levers and parameters
        assert "lever" in card.parameter_template
        assert card.time_to_signal_days > 0
        assert card.evidence_tier in ["A", "B", "C"]
