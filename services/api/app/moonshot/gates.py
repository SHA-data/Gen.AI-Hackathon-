"""Gating Engine (PDF Section 9.1 & 9.3; Card 4 Stage 6).

Gates run strictly before scoring. Gated strategies leave the ranking
and appear in a flagged list with the diagnostic reason. They are NEVER silently hidden.
"""
from __future__ import annotations

from typing import List, Optional
from packages.contracts.moonshot import CandidateStrategy, FixedConstraints, GateResult, UserHardLimit
from packages.contracts.finance import ScenarioRunResponse


def evaluate_gates(
    candidate: CandidateStrategy,
    constraints: FixedConstraints,
    hard_limits: List[UserHardLimit],
    scenario_result: Optional[ScenarioRunResponse] = None,
) -> GateResult:
    """Evaluate candidate strategy against Gates G1 to G4."""
    breached_gates: List[str] = []
    warnings: List[str] = []

    # G1: Budget Gate - upfront cost exceeds budget cap
    if candidate.upfront_cost > constraints.budget_cap:
        breached_gates.append(
            f"G1 Budget: Upfront cost ${candidate.upfront_cost:,.2f} exceeds budget cap of ${constraints.budget_cap:,.2f}"
        )

    # G2: Cash Floor Gate - runway below cash floor
    if scenario_result is not None:
        expected_case = scenario_result.cases.expected
        worst_case = scenario_result.cases.worst

        if constraints.risk_tolerance == "low":
            # Low risk evaluates on worst case
            if worst_case.cash_floor_breach or (
                worst_case.runway_weeks is not None and worst_case.runway_weeks < constraints.cash_floor_weeks
            ):
                breached_gates.append(
                    f"G2 Cash Floor: Worst-case runway ({worst_case.runway_weeks} weeks) falls below cash floor ({constraints.cash_floor_weeks} weeks)"
                )
        else:
            # Medium / High evaluates on expected case
            if expected_case.cash_floor_breach or (
                expected_case.runway_weeks is not None and expected_case.runway_weeks < constraints.cash_floor_weeks
            ):
                breached_gates.append(
                    f"G2 Cash Floor: Expected runway ({expected_case.runway_weeks} weeks) falls below cash floor ({constraints.cash_floor_weeks} weeks)"
                )
            elif worst_case.cash_floor_breach or (
                worst_case.runway_weeks is not None and worst_case.runway_weeks < constraints.cash_floor_weeks
            ):
                warnings.append(
                    f"Warning: Expected case passes, but worst-case runway breaches cash floor ({worst_case.runway_weeks} weeks vs {constraints.cash_floor_weeks} weeks)"
                )

    # G3: Hard Limits Gate
    for limit in hard_limits:
        # Check against limit rules (e.g. no price increase, no debt)
        if limit.limit_type == "no_price_hike" and "price" in candidate.lever_type.lower():
            breached_gates.append(f"G3 Hard Limit: Violates rule '{limit.description}'")
        elif limit.limit_type == "no_headcount_increase" and "hire" in candidate.lever_type.lower():
            breached_gates.append(f"G3 Hard Limit: Violates rule '{limit.description}'")

    # G4: Horizon Gate - time to signal exceeds horizon
    horizon_days = constraints.horizon_weeks * 7
    if candidate.time_to_signal_days > horizon_days:
        breached_gates.append(
            f"G4 Horizon: Days to first signal ({candidate.time_to_signal_days}d) exceeds planning horizon ({horizon_days}d)"
        )

    passed = len(breached_gates) == 0
    return GateResult(
        candidate_id=candidate.id,
        passed=passed,
        breached_gates=breached_gates,
        warnings=warnings,
    )
