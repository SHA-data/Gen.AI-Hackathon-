"""Unit & Golden Tests for Multi-Criteria Scoring & Sensitivity Engine."""
import uuid
import pytest
from packages.contracts.moonshot import GoalAssumption
from services.api.app.moonshot.scoring import (
    EVIDENCE_MULTIPLIERS,
    SCORING_PROFILES,
    compute_cash_impact,
    compute_fit_score,
    compute_reversibility,
    compute_time_to_signal,
    score_and_rank,
    score_candidate,
    validate_profile_weights,
)


def test_profile_weights_integrity():
    """HR-11 / DB View `bad_weight_profiles`: ensures all profile weights sum to 1.0."""
    invalid = validate_profile_weights()
    assert len(invalid) == 0, f"Profiles failed 1.0 sum check: {invalid}"


def test_fit_score_with_critical_assumptions():
    """Fit formula gives double weight to critical assumptions."""
    a1 = GoalAssumption(text="Demand validated", importance=80.0, is_critical=True)
    a2 = GoalAssumption(text="Team can deliver", importance=40.0, is_critical=False)
    # Total weight = 80*2 + 40*1 = 160 + 40 = 200

    # If only critical assumption a1 is addressed: 160 / 200 = 80%
    score_a1 = compute_fit_score([a1.id], [a1, a2])
    assert score_a1 == 80.0

    # If both addressed: 200 / 200 = 100%
    score_both = compute_fit_score([a1.id, a2.id], [a1, a2])
    assert score_both == 100.0

    # If neither addressed: 0%
    score_none = compute_fit_score([], [a1, a2])
    assert score_none == 0.0


def test_cash_impact_normalization_and_single_survivor():
    c1 = uuid.uuid4()
    c2 = uuid.uuid4()
    c3 = uuid.uuid4()

    # Three candidates: c1 is max, c3 is min
    cash_data = [
        (c1, 50000.0, 40000.0),  # highest
        (c2, 25000.0, 20000.0),  # mid
        (c3, 0.0, 0.0),          # lowest
    ]
    scores = compute_cash_impact(cash_data)
    assert scores[c1] == 100.0
    assert scores[c3] == 0.0
    assert scores[c2] == 50.0

    # Single survivor edge case -> must receive 100.0
    single_score = compute_cash_impact([(c1, 10000.0, 5000.0)])
    assert single_score[c1] == 100.0


def test_time_to_signal_bands():
    assert compute_time_to_signal(10) == 100.0  # <= 14d
    assert compute_time_to_signal(21) == 80.0   # 15-30d
    assert compute_time_to_signal(45) == 60.0   # 31-60d
    assert compute_time_to_signal(75) == 40.0   # 61-90d
    assert compute_time_to_signal(120) == 20.0  # 91-180d
    assert compute_time_to_signal(200) == 0.0   # > 180d


def test_reversibility_bands():
    cap = 50000.0
    assert compute_reversibility(2500.0, cap) == 100.0  # 5% <= 10%
    assert compute_reversibility(10000.0, cap) == 75.0  # 20% in 11-25%
    assert compute_reversibility(20000.0, cap) == 50.0  # 40% in 26-50%
    assert compute_reversibility(40000.0, cap) == 25.0  # 80% in 51-100%
    assert compute_reversibility(60000.0, cap) == 0.0   # 120% > 100%


def test_pdf_worked_example_golden_test():
    """Golden Test (PDF §8 / §9.3 & Aleena Prompt B2.8):

    Strategy A = 60.4 (ROC) / 60.0 (Rank-Sum) / 60.0 (Equal)
    Strategy B = 67.2 (ROC) / 64.5 (Rank-Sum) / 56.3 (Equal)
    """
    strat_a_id = uuid.uuid4()
    strat_b_id = uuid.uuid4()

    # Exact criteria values for Strategy A and Strategy B
    crit_a = {"fit": 63.1, "cash": 53.8, "signal": 63.1, "reversibility": 60.0}
    crit_b = {"fit": 71.7, "cash": 76.2, "signal": 52.3, "reversibility": 25.0}

    # Strategy A: Tier A (mult = 1.0)
    score_a_roc = score_candidate(crit_a, "roc_default", "A")[2]
    score_a_ranksum = score_candidate(crit_a, "rank_sum", "A")[2]
    score_a_equal = score_candidate(crit_a, "equal", "A")[2]

    assert score_a_roc == 60.4, f"Strategy A ROC expected 60.4, got {score_a_roc}"
    assert score_a_ranksum == 60.0, f"Strategy A Rank-sum expected 60.0, got {score_a_ranksum}"
    assert score_a_equal == 60.0, f"Strategy A Equal expected 60.0, got {score_a_equal}"

    # Strategy B: Tier A (mult = 1.0)
    score_b_roc = score_candidate(crit_b, "roc_default", "A")[2]
    score_b_ranksum = score_candidate(crit_b, "rank_sum", "A")[2]
    score_b_equal = score_candidate(crit_b, "equal", "A")[2]

    assert score_b_roc == 67.2, f"Strategy B ROC expected 67.2, got {score_b_roc}"
    assert score_b_ranksum == 64.5, f"Strategy B Rank-sum expected 64.5, got {score_b_ranksum}"
    assert score_b_equal == 56.3, f"Strategy B Equal expected 56.3, got {score_b_equal}"

    # Test sensitivity analysis across both candidates
    data = {
        strat_a_id: (crit_a, "A"),
        strat_b_id: (crit_b, "A"),
    }
    rankings, sensitivity = score_and_rank(data, profiles=["roc_default", "rank_sum", "equal"])
    
    # Under ROC and Rank-Sum, B is #1 (67.2 > 60.4 and 64.5 > 60.0). Under Equal, A is #1 (60.0 > 56.3).
    # Therefore, ranking shifts between profiles -> must be tagged sensitive!
    assert not sensitivity.is_robust
    assert "sensitive to how criteria are weighted" in sensitivity.summary
