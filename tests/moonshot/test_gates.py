"""Unit tests for Gating Engine (G1 to G4)."""
import uuid
import pytest
from packages.contracts.moonshot import CandidateStrategy, FixedConstraints, UserHardLimit
from packages.contracts.finance import (
    CaseResult,
    ScenarioCases,
    ScenarioRunResponse,
    WeeklyCashPoint,
)
from services.api.app.moonshot.gates import evaluate_gates
from datetime import date


def make_test_scenario(
    expected_runway: int,
    worst_runway: int,
    expected_breach: bool = False,
    worst_breach: bool = False,
) -> ScenarioRunResponse:
    today = date(2026, 10, 24)
    case_exp = CaseResult(
        weekly_cash=[WeeklyCashPoint(week_start=today, cash="100000.00")],
        min_cash="100000.00",
        min_cash_date=today,
        end_cash="120000.00",
        runway_weeks=expected_runway,
        cash_floor_breach=expected_breach,
    )
    case_worst = CaseResult(
        weekly_cash=[WeeklyCashPoint(week_start=today, cash="80000.00")],
        min_cash="80000.00",
        min_cash_date=today,
        end_cash="70000.00",
        runway_weeks=worst_runway,
        cash_floor_breach=worst_breach,
    )
    return ScenarioRunResponse(
        run_id=uuid.uuid4(),
        cases=ScenarioCases(expected=case_exp, best=case_exp, worst=case_worst),
    )


def test_g1_budget_gate_fails_when_over_budget():
    candidate = CandidateStrategy(
        title="Expensive Strategy",
        lever_type="pricing",
        time_to_signal_days=30,
        cost_to_undo=5000.0,
        upfront_cost=75000.0,  # exceeds 50k
    )
    constraints = FixedConstraints(budget_cap=50000.0)
    res = evaluate_gates(candidate, constraints, hard_limits=[])
    assert not res.passed
    assert any("G1 Budget" in b for b in res.breached_gates)


def test_g2_cash_floor_gate_low_risk_evaluates_worst_case():
    candidate = CandidateStrategy(
        title="Risky Cash Strategy",
        lever_type="hire",
        time_to_signal_days=30,
        cost_to_undo=5000.0,
        upfront_cost=10000.0,
    )
    # Expected runway = 16, Worst runway = 8, Floor = 12
    scenario = make_test_scenario(expected_runway=16, worst_runway=8)
    
    # Low risk evaluates worst case -> should breach
    low_risk_constraints = FixedConstraints(risk_tolerance="low", cash_floor_weeks=12)
    res_low = evaluate_gates(candidate, low_risk_constraints, hard_limits=[], scenario_result=scenario)
    assert not res_low.passed
    assert any("G2 Cash Floor" in b for b in res_low.breached_gates)

    # Medium risk evaluates expected case -> passes, but produces warning
    med_risk_constraints = FixedConstraints(risk_tolerance="medium", cash_floor_weeks=12)
    res_med = evaluate_gates(candidate, med_risk_constraints, hard_limits=[], scenario_result=scenario)
    assert res_med.passed
    assert len(res_med.warnings) > 0
    assert any("worst-case runway breaches" in w for w in res_med.warnings)


def test_g3_hard_limit_gate_fails_when_rule_violated():
    candidate = CandidateStrategy(
        title="Price Increase Strategy",
        lever_type="price_change_pct",
        time_to_signal_days=14,
        cost_to_undo=1000.0,
        upfront_cost=2000.0,
    )
    constraints = FixedConstraints()
    hard_limits = [
        UserHardLimit(description="No price hikes for current clients", limit_type="no_price_hike")
    ]
    res = evaluate_gates(candidate, constraints, hard_limits=hard_limits)
    assert not res.passed
    assert any("G3 Hard Limit" in b for b in res.breached_gates)


def test_g4_horizon_gate_fails_when_signal_exceeds_horizon():
    candidate = CandidateStrategy(
        title="Slow Enterprise Move",
        lever_type="enterprise",
        time_to_signal_days=200,  # 200 days > 26 weeks * 7 = 182 days
        cost_to_undo=5000.0,
        upfront_cost=5000.0,
    )
    constraints = FixedConstraints(horizon_weeks=26)
    res = evaluate_gates(candidate, constraints, hard_limits=[])
    assert not res.passed
    assert any("G4 Horizon" in b for b in res.breached_gates)
