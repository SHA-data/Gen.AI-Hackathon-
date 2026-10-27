"""End-to-End Workflow Orchestrator & State Machine for Moonshot Mode.

Coordinates the 10-stage pipeline:
Intake -> Constraint Check -> Decomposition -> Retrieval -> Simulation -> Gating & Scoring -> Skeptic -> Report
Emits SSE stage events and supports resumable clarification cycles (needs_input).
Provides FakeMoonshotWorkflow for Aroon's frontend & chat integration.
"""
from __future__ import annotations

import json
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional
from services.api.app.moonshot.gates import evaluate_gates
from services.api.app.moonshot.logger import log_agent_event
from services.api.app.moonshot.scoring import (
    compute_cash_impact,
    compute_fit_score,
    compute_reversibility,
    compute_time_to_signal,
    score_and_rank,
)
from services.api.app.moonshot.stages.decompose import decompose_goal
from services.api.app.moonshot.stages.intake import check_and_clarify_constraints
from services.api.app.moonshot.stages.report import assemble_moonshot_report
from services.api.app.moonshot.stages.retrieve import retrieve_strategies
from services.api.app.moonshot.stages.simulate import translate_and_simulate
from services.api.app.moonshot.stages.stresstest import build_skeptic_section
from packages.contracts.finance import FakeFinanceService
from packages.contracts.llm import FakeLLMProvider, LLMProvider, get_llm_provider
from packages.contracts.moonshot import (
    CandidateStrategy,
    FixedConstraints,
    GoalAssumption,
    SensitivityCheckResult,
    UserHardLimit,
)


class MoonshotWorkflow:
    """Production Moonshot Workflow Orchestrator."""

    def __init__(
        self,
        llm: Optional[LLMProvider] = None,
        finance_service: Optional[FakeFinanceService] = None,
    ):
        self.llm = llm or get_llm_provider()
        self.finance_service = finance_service or FakeFinanceService()
        self.active_runs: Dict[str, Dict[str, Any]] = {}

    def run(
        self,
        goal: str,
        org_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        provided_constraints: Optional[Dict[str, Any]] = None,
        hard_limits: Optional[List[UserHardLimit]] = None,
        request_id: Optional[uuid.UUID] = None,
        round_number: int = 1,
    ) -> Dict[str, Any]:
        """Execute Moonshot pipeline or pause for clarification."""
        req_id = request_id or uuid.uuid4()
        o_id = org_id or uuid.UUID("00000000-0000-0000-0000-000000000001")
        u_id = user_id or uuid.UUID("00000000-0000-0000-0000-000000000002")
        trace_id = f"moonshot-{req_id}"

        # Stage 0 & 1: Intake & Constraints
        constraints, questions = check_and_clarify_constraints(
            trace_id=trace_id,
            raw_goal=goal,
            provided_constraints=provided_constraints,
            round_number=round_number,
        )

        if questions:
            self.active_runs[str(req_id)] = {
                "goal": goal,
                "org_id": o_id,
                "user_id": u_id,
                "provided_constraints": provided_constraints or {},
                "hard_limits": hard_limits or [],
                "round_number": round_number,
            }
            return {
                "status": "needs_input",
                "request_id": str(req_id),
                "questions": [q.model_dump() for q in questions],
                "message": "Clarification required on operating constraints before strategy decomposition.",
            }

        # Stage 2: Assumption Tree
        assumptions = decompose_goal(trace_id, goal, constraints, self.llm)

        # Stage 3: Retrieval
        candidates, found = retrieve_strategies(trace_id, goal, assumptions, self.llm)
        if not found or not candidates:
            return {
                "status": "completed",
                "request_id": str(req_id),
                "precedent_found": False,
                "message": "No documented founder precedent found matching these assumptions. Offering first-principles breakdown only.",
                "assumptions": [a.model_dump() for a in assumptions],
            }

        # Stage 4 & 5: Simulation Seam
        simulations = translate_and_simulate(trace_id, candidates, constraints, self.finance_service, o_id)

        # Stage 6: Gating
        surviving_candidates: List[CandidateStrategy] = []
        flagged_candidates: List[Dict[str, Any]] = []

        h_limits = hard_limits or []
        for cand in candidates:
            sim_res = simulations.get(cand.id)
            gate_res = evaluate_gates(cand, constraints, h_limits, sim_res)
            if gate_res.passed:
                surviving_candidates.append(cand)
            else:
                flagged_candidates.append({
                    "candidate_id": str(cand.id),
                    "title": cand.title,
                    "breached_gates": gate_res.breached_gates,
                    "warnings": gate_res.warnings,
                })

        if not surviving_candidates:
            report = assemble_moonshot_report(
                request_id=req_id,
                org_id=o_id,
                user_id=u_id,
                goal_statement=goal,
                constraints=constraints,
                assumptions=assumptions,
                ranked_candidates=[],
                rankings_by_profile={"roc_default": [], "rank_sum": [], "equal": []},
                flagged_candidates=flagged_candidates,
                simulations=simulations,
                skeptic_section={"pre_mortem_scenarios": [], "experiments": [], "base_rates": []},
                sensitivity=SensitivityCheckResult(
                    top_candidate_id=uuid.uuid4(),
                    is_robust=False,
                    summary="All candidate strategies were gated by budget cap, cash floor, or planning horizon.",
                    profile_top_picks={},
                ),
            )
            return {
                "status": "completed",
                "request_id": str(req_id),
                "report_id": report["report_id"],
                "report": report,
            }

        # Stage 6: Criteria Scoring & Normalization
        cash_deltas = []
        for cand in surviving_candidates:
            sim = simulations[cand.id]
            d_end = float(sim.cases.expected.end_cash) - self.finance_service.baseline_cash
            d_min = float(sim.cases.expected.min_cash) - self.finance_service.baseline_cash
            cash_deltas.append((cand.id, d_end, d_min))

        cash_scores = compute_cash_impact(cash_deltas)

        candidates_criteria = {}
        for cand in surviving_candidates:
            fit_val = compute_fit_score(cand.assumptions_addressed, assumptions)
            cash_val = cash_scores.get(cand.id, 50.0)
            sig_val = compute_time_to_signal(cand.time_to_signal_days)
            rev_val = compute_reversibility(cand.cost_to_undo, constraints.budget_cap)

            criteria_dict = {
                "fit": fit_val,
                "cash": cash_val,
                "signal": sig_val,
                "reversibility": rev_val,
            }
            candidates_criteria[cand.id] = (criteria_dict, cand.evidence_tier)

        rankings_by_profile, sensitivity = score_and_rank(candidates_criteria)

        # Re-order surviving candidates by default ROC ranking
        roc_ranked_ids = [r.candidate_id for r in rankings_by_profile["roc_default"]]
        cand_map = {c.id: c for c in surviving_candidates}
        ordered_candidates = [cand_map[cid] for cid in roc_ranked_ids if cid in cand_map]

        # Stage 7: Skeptic Stress-Test
        top_candidate = ordered_candidates[0]
        skeptic_section = build_skeptic_section(trace_id, top_candidate, assumptions, self.llm)

        # Stage 8: Report Assembly & Verification
        report = assemble_moonshot_report(
            request_id=req_id,
            org_id=o_id,
            user_id=u_id,
            goal_statement=goal,
            constraints=constraints,
            assumptions=assumptions,
            ranked_candidates=ordered_candidates,
            rankings_by_profile=rankings_by_profile,
            flagged_candidates=flagged_candidates,
            simulations=simulations,
            skeptic_section=skeptic_section,
            sensitivity=sensitivity,
            candidates_criteria=candidates_criteria,
        )

        return {
            "status": "completed",
            "request_id": str(req_id),
            "report_id": report["report_id"],
            "report": report,
        }

    def resume(self, request_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Resume paused run after clarification."""
        run_data = self.active_runs.get(request_id)
        if not run_data:
            return {"status": "failed", "error": f"Request ID {request_id} not found in active memory"}

        provided = run_data["provided_constraints"]
        provided.update(answers)
        round_num = run_data["round_number"] + 1

        return self.run(
            goal=run_data["goal"],
            org_id=run_data["org_id"],
            user_id=run_data["user_id"],
            provided_constraints=provided,
            hard_limits=run_data["hard_limits"],
            request_id=uuid.UUID(request_id),
            round_number=round_num,
        )


class FakeMoonshotWorkflow:
    """Deterministic canned workflow for Aroon's chat and UI integration (PDF B2.11)."""

    def __init__(self):
        self.default_report_id = "r0000000-0000-0000-0000-000000000001"

    def run(self, goal: str, **kwargs) -> Dict[str, Any]:
        req_id = kwargs.get("request_id") or uuid.uuid4()
        return {
            "status": "completed",
            "request_id": str(req_id),
            "report_id": self.default_report_id,
            "report": {
                "report_id": self.default_report_id,
                "goal_statement": goal,
                "disclaimer": "Decision support, not financial advice. Forecasts depend on the assumptions shown and are not guaranteed predictions.",
                "disclaimer_verified": True,
                "top_strategies_count": 3,
                "sensitivity": {
                    "is_robust": True,
                    "summary": "Recommendation is robust: top pick is unchanged across all weight profiles.",
                },
                "report_markdown": f"# NeuralCFO • Moonshot Strategy Report\n\n**Goal**: {goal}\n\nTop Pick: Annual Upfront Retainers\n\n> Decision support, not financial advice.",
            },
        }
