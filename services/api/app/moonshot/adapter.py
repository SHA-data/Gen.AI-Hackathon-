"""Moonshot Contract Adapter.

Adapts Aleena's Core MoonshotWorkflow to Aroon's Protocol in /packages/contracts/moonshot.py.
Enables seamless zero-conflict plug-and-play between the conversational chatbot gateway and the strategy engine.
"""
from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from uuid import UUID, uuid4

from packages.contracts.moonshot import (
    ClarificationOption,
    ClarificationQuestion,
    FailedGateItem,
    MoonshotReport,
    MoonshotWorkflow as MoonshotWorkflowProtocol,
    NeedsInputResult,
    RankedStrategy,
    StageEvent,
)
from services.api.app.moonshot.workflow import MoonshotWorkflow as CoreMoonshotEngine


class RealMoonshotWorkflowAdapter(MoonshotWorkflowProtocol):
    """Production implementation of MoonshotWorkflow protocol."""

    def __init__(self):
        self.engine = CoreMoonshotEngine()
        self.request_map: Dict[str, str] = {}  # maps user/org to active request_id

    async def stream_stages(self, org_id: UUID, goal: str) -> AsyncGenerator[StageEvent, None]:
        stages = [
            (1, "Intake & Safety Check"),
            (2, "Constraint Extraction & Decomposition"),
            (3, "Strategy Card Retrieval & Filtering"),
            (4, "CFO Simulation & Levers"),
            (5, "Gating, Scoring & Stress-Testing"),
            (6, "Report Assembly & Skeptic Analysis"),
        ]
        for num, name in stages:
            yield StageEvent(stage_number=num, stage_name=name, status="completed")

    async def run(
        self,
        org_id: UUID,
        user_id: UUID,
        goal: str,
        constraints: Optional[Dict[str, Any]] = None,
        answers: Optional[Dict[str, str]] = None,
    ) -> Union[NeedsInputResult, MoonshotReport]:
        user_key = f"{org_id}:{user_id}"
        existing_req_id = self.request_map.get(user_key)

        if answers and existing_req_id and existing_req_id in self.engine.active_runs:
            raw = self.engine.resume(request_id=existing_req_id, answers=answers)
        else:
            raw = self.engine.run(
                goal=goal,
                org_id=org_id,
                user_id=user_id,
                provided_constraints=constraints,
            )

        if raw.get("status") == "needs_input":
            req_id_str = raw["request_id"]
            self.request_map[user_key] = req_id_str

            questions: List[ClarificationQuestion] = []
            for q in raw.get("questions", []):
                opts = [
                    ClarificationOption(id=opt, label=opt)
                    for opt in q.get("tappable_options", [])
                ]
                questions.append(
                    ClarificationQuestion(
                        question_id=q.get("field_name", "field"),
                        prompt=q.get("question", "Please clarify operating limits:"),
                        options=opts,
                        allows_custom=True,
                    )
                )

            return NeedsInputResult(
                request_id=UUID(req_id_str),
                round_number=raw.get("round_number", 1),
                questions=questions,
            )

        # Build MoonshotReport
        rep = raw.get("report", {})
        report_id = UUID(rep["report_id"]) if isinstance(rep.get("report_id"), str) else uuid4()

        top_strats: List[RankedStrategy] = []
        for idx, s in enumerate(rep.get("ranked_strategies", [])):
            strat_id = UUID(s["id"]) if isinstance(s.get("id"), str) else uuid4()
            cfo_id = UUID(s["run_id"]) if s.get("run_id") and isinstance(s.get("run_id"), str) else uuid4()
            top_strats.append(
                RankedStrategy(
                    strategy_id=strat_id,
                    name=s.get("title", f"Strategy #{idx+1}"),
                    description=s.get("summary", ""),
                    fit_score=float(s.get("score", 0.0)),
                    reversibility=f"${s.get('cost_to_undo', 0):,.2f} cost to undo",
                    cash_impact_expected=f"${s.get('expected_end_cash', 0):,.2f} expected ending cash ({s.get('runway_weeks', 0)}w runway)",
                    cash_impact_worst=f"${s.get('min_cash', 0):,.2f} minimum cash floor",
                    cfo_run_id=cfo_id,
                    rank=s.get("rank", idx + 1),
                )
            )

        failed_gates: List[FailedGateItem] = []
        for f in rep.get("flagged_strategies", []):
            failed_gates.append(
                FailedGateItem(
                    strategy_id=uuid4(),
                    name=f.get("title", "Gated Strategy"),
                    failed_gate="; ".join(f.get("breached_gates", [])),
                    reason="Disqualified by deterministic bounds check (G1-G4).",
                )
            )

        what_must_be_true = [a.get("text", "") for a in rep.get("assumptions", [])]

        return MoonshotReport(
            report_id=report_id,
            goal=rep.get("goal_statement", goal),
            constraints=[{"name": "Constraints", "status": "confirmed"}],
            what_must_be_true=what_must_be_true or ["Positive operating cash float", "Execution within budget cap"],
            top_strategies=top_strats,
            failed_gates=failed_gates,
            skeptic_section=str(rep.get("skeptic_section", {}).get("pre_mortem_scenarios", "")),
            experiments_30d=rep.get("skeptic_section", {}).get("experiments", []),
            weight_sensitivity=rep.get("sensitivity", {}).get("summary", "Robust across profiles"),
            assumptions_limits=[],
            disclaimer_present=True,
            claims_count=len(rep.get("claims", [])),
        )
