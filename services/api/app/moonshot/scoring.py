"""Multi-Criteria Scoring & Sensitivity Analysis Engine (PDF Section 9.3; Card 4 Stage 6).

Implements the exact MP scoring model (which wins over MS per F4/D6):
1. Fit: Inferred from assumption tree coverage (critical assumptions double-weighted).
2. Cash Impact: Min-max normalized mean of ending and minimum cash deltas.
3. Time to Signal: Exact bands cited from card.
4. Reversibility: Cost to undo / budget cap bands cited from card.
5. Evidence Multipliers: Tier A = 1.0, Tier B = 0.8, Tier C = 0.5.
6. Sensitivity Analysis across 4 weight profiles: ROC, Rank-Sum, Equal, ROC-Low-Risk.
"""
from __future__ import annotations

import uuid
from typing import Dict, List, Literal, Tuple
from packages.contracts.moonshot import (
    CandidateStrategy,
    CriterionScore,
    GoalAssumption,
    SensitivityCheckResult,
    StrategyRanking,
)

# Standard Profiles per PDF 9.3 & 9.4 (all sum to 1.0)
SCORING_PROFILES: Dict[str, Dict[str, float]] = {
    "roc_default": {
        "fit": 0.52,
        "cash": 0.27,
        "signal": 0.15,
        "reversibility": 0.06,
    },
    "rank_sum": {
        "fit": 0.40,
        "cash": 0.30,
        "signal": 0.20,
        "reversibility": 0.10,
    },
    "equal": {
        "fit": 0.25,
        "cash": 0.25,
        "signal": 0.25,
        "reversibility": 0.25,
    },
    "roc_low_risk": {
        "fit": 0.52,
        "cash": 0.27,
        "reversibility": 0.15,
        "signal": 0.06,
    },
}

EVIDENCE_MULTIPLIERS: Dict[str, float] = {
    "A": 1.0,
    "B": 0.8,
    "C": 0.5,
}


def validate_profile_weights() -> List[str]:
    """Verification check corresponding to DB view `bad_weight_profiles`. Returns empty list if all sum to 1.0."""
    invalid = []
    for name, weights in SCORING_PROFILES.items():
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            invalid.append(f"Profile {name} sum is {total}, expected 1.0")
    return invalid


def compute_fit_score(
    assumptions_addressed: List[uuid.UUID],
    all_assumptions: List[GoalAssumption],
) -> float:
    """Fit = 100 x (importance of addressed assumptions / importance of all assumptions),

    critical assumptions count double.
    """
    if not all_assumptions:
        return 0.0

    total_weight = sum(a.importance * (2.0 if a.is_critical else 1.0) for a in all_assumptions)
    if total_weight <= 0.0:
        return 0.0

    addressed_set = set(assumptions_addressed)
    addressed_weight = sum(
        a.importance * (2.0 if a.is_critical else 1.0) for a in all_assumptions if a.id in addressed_set
    )
    return round(min(100.0, max(0.0, (addressed_weight / total_weight) * 100.0)), 2)


def compute_cash_impact(
    candidates_cash: List[Tuple[uuid.UUID, float, float]],  # list of (id, delta_end_cash, delta_min_cash)
) -> Dict[uuid.UUID, float]:
    """Min-max normalized mean of ending cash and min cash changes vs baseline.

    Edge case: single survivor gets 100.0.
    """
    if not candidates_cash:
        return {}

    if len(candidates_cash) == 1:
        return {candidates_cash[0][0]: 100.0}

    end_deltas = [c[1] for c in candidates_cash]
    min_deltas = [c[2] for c in candidates_cash]

    max_end, min_end = max(end_deltas), min(end_deltas)
    max_min, min_min = max(min_deltas), min(min_deltas)

    scores = {}
    for cid, d_end, d_min in candidates_cash:
        norm_end = 100.0 if max_end == min_end else ((d_end - min_end) / (max_end - min_end)) * 100.0
        norm_min = 100.0 if max_min == min_min else ((d_min - min_min) / (max_min - min_min)) * 100.0
        scores[cid] = round((norm_end + norm_min) / 2.0, 2)

    return scores


def compute_time_to_signal(days: int) -> float:
    """Time to signal bands (PDF §9.3):

    <=14d: 100; 15-30d: 80; 31-60d: 60; 61-90d: 40; 91-180d: 20; >180d: 0.
    """
    if days <= 14:
        return 100.0
    elif days <= 30:
        return 80.0
    elif days <= 60:
        return 60.0
    elif days <= 90:
        return 40.0
    elif days <= 180:
        return 20.0
    else:
        return 0.0


def compute_reversibility(cost_to_undo: float, budget_cap: float) -> float:
    """Reversibility bands (cost_to_undo / budget_cap):

    <=10%: 100; 11-25%: 75; 26-50%: 50; 51-100%: 25; >100%: 0.
    """
    if budget_cap <= 0.0:
        return 0.0
    ratio = cost_to_undo / budget_cap
    if ratio <= 0.10:
        return 100.0
    elif ratio <= 0.25:
        return 75.0
    elif ratio <= 0.50:
        return 50.0
    elif ratio <= 1.00:
        return 25.0
    else:
        return 0.0


def score_candidate(
    criteria_scores: Dict[str, float],
    profile_name: str = "roc_default",
    evidence_tier: Literal["A", "B", "C"] = "B",
) -> Tuple[float, float, float]:
    """Returns (weighted_sum, multiplier, final_score) for a single candidate."""
    weights = SCORING_PROFILES[profile_name]
    multiplier = EVIDENCE_MULTIPLIERS.get(evidence_tier, 0.8)

    weighted_sum = sum(weights[k] * criteria_scores[k] for k in ["fit", "cash", "signal", "reversibility"])
    final_score = round(multiplier * weighted_sum, 1)
    return round(weighted_sum, 2), multiplier, final_score


def score_and_rank(
    candidates_criteria: Dict[uuid.UUID, Tuple[Dict[str, float], Literal["A", "B", "C"]]],
    profiles: List[str] = ["roc_default", "rank_sum", "equal"],
) -> Tuple[Dict[str, List[StrategyRanking]], SensitivityCheckResult]:
    """Score all surviving candidates under all specified profiles and run sensitivity check."""
    rankings_by_profile: Dict[str, List[StrategyRanking]] = {}
    top_pick_by_profile: Dict[str, uuid.UUID] = {}

    for profile in profiles:
        ranked = []
        for cid, (crit, tier) in candidates_criteria.items():
            w_sum, mult, f_score = score_candidate(crit, profile_name=profile, evidence_tier=tier)
            ranked.append(
                StrategyRanking(
                    candidate_id=cid,
                    profile_name=profile,
                    weighted_sum=w_sum,
                    multiplier=mult,
                    final_score=f_score,
                    position=1,  # will assign below
                )
            )

        # Sort descending by final_score
        ranked.sort(key=lambda r: r.final_score, reverse=True)
        for idx, r in enumerate(ranked):
            r.position = idx + 1

        rankings_by_profile[profile] = ranked
        if ranked:
            top_pick_by_profile[profile] = ranked[0].candidate_id

    # Sensitivity check across profiles
    unique_tops = set(top_pick_by_profile.values())
    is_robust = len(unique_tops) == 1 if unique_tops else True
    primary_top = list(unique_tops)[0] if unique_tops else uuid.uuid4()

    summary = (
        "Recommendation is robust: top pick is unchanged across all weight profiles."
        if is_robust
        else "Recommendation is sensitive to how criteria are weighted; ranking shifts between profiles."
    )

    sensitivity = SensitivityCheckResult(
        top_candidate_id=primary_top,
        is_robust=is_robust,
        summary=summary,
        profile_top_picks=top_pick_by_profile,
    )

    return rankings_by_profile, sensitivity
