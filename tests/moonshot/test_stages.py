"""Unit and Stage Integration Tests for Part 2 Pipeline Stages."""
import json
import uuid
from pathlib import Path
import pytest
from services.api.app.moonshot.db import get_connection, init_db
from services.api.app.moonshot.logger import LOG_FILE, log_agent_event
from services.api.app.moonshot.stages.decompose import decompose_goal
from services.api.app.moonshot.stages.intake import check_and_clarify_constraints
from services.api.app.moonshot.stages.retrieve import retrieve_strategies
from services.api.app.moonshot.stages.simulate import translate_and_simulate
from services.api.app.moonshot.stages.stresstest import build_skeptic_section
from packages.contracts.finance import FakeFinanceService
from packages.contracts.llm import FakeLLMProvider
from packages.contracts.moonshot import FixedConstraints, GoalAssumption


def test_database_init_and_views(tmp_path: Path):
    db_file = tmp_path / "test_moonshot.db"
    conn = init_db(db_file)
    cur = conn.cursor()

    # 1. Verify bad_weight_profiles view returns zero rows (HR-11 / Test M8)
    cur.execute("SELECT * FROM bad_weight_profiles")
    bad_rows = cur.fetchall()
    assert len(bad_rows) == 0, f"Found invalid weight profiles: {bad_rows}"

    # 2. Verify approved_cards view returns all 12 seeded approved cards (HR-12 / Test M7)
    cur.execute("SELECT COUNT(*) FROM approved_cards")
    count = cur.fetchone()[0]
    assert count == 12

    # 3. Test that inserting an unapproved card excludes it from approved_cards view
    unapproved_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO strategy_cards
        (id, title, summary, lever_type, parameter_template, time_to_signal_days, cost_to_undo, upfront_cost,
         evidence_tier, source_citation, source_excerpt, source_excerpt_hash, status)
        VALUES (?, 'Draft Move', 'Draft', 'price', '{}', 14, 100, 100, 'B', 'Citation', 'Quote', 'hash', 'draft')""",
        (unapproved_id,),
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM approved_cards WHERE id = ?", (unapproved_id,))
    assert cur.fetchone()[0] == 0


def test_card1_intake_clarification_cycle():
    trace_id = "test-intake-trace"
    goal = "Triple our agency revenue in 6 months by switching to productized retainers"

    # Round 1: Missing constraints -> triggers questions with tappable options
    constraints_r1, questions_r1 = check_and_clarify_constraints(
        trace_id=trace_id,
        raw_goal=goal,
        provided_constraints={},
        round_number=1,
    )
    assert constraints_r1 is None
    assert len(questions_r1) > 0
    assert all(len(q.tappable_options) > 0 for q in questions_r1)

    # Round 3: Exhausted / user declines -> fills defaults flagged as assumed_default (HR-05)
    constraints_r3, questions_r3 = check_and_clarify_constraints(
        trace_id=trace_id,
        raw_goal=goal,
        provided_constraints={},
        round_number=3,
    )
    assert constraints_r3 is not None
    assert len(questions_r3) == 0
    assert constraints_r3.status == "assumed_default"
    assert constraints_r3.horizon_weeks == 26
    assert constraints_r3.budget_cap == 50000.0


def test_card2_decomposition_critical_demand():
    trace_id = "test-decompose-trace"
    goal = "Launch self-serve annual prepay"
    constraints = FixedConstraints()
    llm = FakeLLMProvider()

    assumptions = decompose_goal(trace_id, goal, constraints, llm)
    assert len(assumptions) > 0
    # Hard Rule check: demand-side assumptions are always critical
    for a in assumptions:
        if a.category == "demand":
            assert a.is_critical, f"Assumption '{a.text}' in category demand was not flagged critical"


def test_card2_retrieval_and_empty_precedent_handling():
    trace_id = "test-retrieve-trace"
    llm = FakeLLMProvider()
    assumptions = [
        GoalAssumption(text="Clients accept upfront retainers", importance=90.0, is_critical=True, category="demand")
    ]

    # Matching query retrieves candidates
    candidates, found = retrieve_strategies(trace_id, "agency retainer upfront pricing", assumptions, llm)
    assert found
    assert len(candidates) > 0
    assert all(len(c.source_quote) <= 300 for c in candidates)
    assert all(len(c.source_quote_hash) == 64 for c in candidates)

    # Completely alien query with no matching precedent
    no_match_query = "quantum teleportation mining blockchain teleportation"
    alien_assumptions = [GoalAssumption(text="subatomic particles align", importance=50.0, is_critical=False)]
    _, alien_found = retrieve_strategies(trace_id, no_match_query, alien_assumptions, llm)
    # Never invent precedents when none match
    assert not alien_found


def test_card3_simulation_lever_translation():
    trace_id = "test-sim-trace"
    constraints = FixedConstraints(horizon_weeks=26)
    fake_cfo = FakeFinanceService(baseline_cash=120000.0)
    llm = FakeLLMProvider()
    org_id = uuid.uuid4()

    assumptions = [GoalAssumption(text="Prepay acceptance", importance=90.0, is_critical=True)]
    candidates, _ = retrieve_strategies(trace_id, "retainers upfront pricing", assumptions, llm)
    assert len(candidates) > 0

    sim_results = translate_and_simulate(trace_id, candidates[:2], constraints, fake_cfo, org_id)
    assert len(sim_results) == 2
    for cid, resp in sim_results.items():
        assert resp.status == "verified"
        assert resp.cases.expected.runway_weeks is not None
        assert float(resp.cases.expected.end_cash) > 0.0


def test_card5_skeptic_mandatory_section():
    trace_id = "test-skeptic-trace"
    llm = FakeLLMProvider()
    assumptions = [GoalAssumption(text="High customer retention", importance=85.0, is_critical=True)]
    candidates, _ = retrieve_strategies(trace_id, "retainers", assumptions, llm)
    top_candidate = candidates[0]

    skeptic = build_skeptic_section(trace_id, top_candidate, assumptions, llm)
    assert "pre_mortem_scenarios" in skeptic
    assert len(skeptic["pre_mortem_scenarios"]) > 0
    assert "experiments" in skeptic
    assert len(skeptic["experiments"]) > 0
    assert "base_rates" in skeptic


def test_logger_emits_jsonl():
    trace_id = f"trace-{uuid.uuid4()}"
    event = log_agent_event(
        trace_id=trace_id,
        agent_name="TestAgent",
        action="test_action",
        input_summary="Input test",
        output_summary="Output test",
        target_agent="EvaluatorAgent",
        model="test-model",
    )
    assert event["trace_id"] == trace_id
    assert LOG_FILE.exists()
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert any(trace_id in line for line in lines)
