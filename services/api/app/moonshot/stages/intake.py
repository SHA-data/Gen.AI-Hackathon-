"""Stage 0 & 1: Goal Intake & 5 Fixed Constraints Checker (Card 1).

Enforces Hard Rule HR-05:
- Must establish the 5 fixed constraints before decomposition.
- Generates clarification questions with tappable options for missing constraints (max 2 rounds).
- If declined or exhausted, applies documented defaults flagged as 'assumed_default'.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple
from packages.contracts.moonshot import ClarificationQuestion, FixedConstraints
from services.api.app.moonshot.logger import log_agent_event


def check_and_clarify_constraints(
    trace_id: str,
    raw_goal: str,
    provided_constraints: Optional[Dict[str, Any]] = None,
    round_number: int = 1,
) -> Tuple[Optional[FixedConstraints], List[ClarificationQuestion]]:
    """Inspect provided constraints and return (constraints, questions).

    If any fixed constraint is missing and round_number <= 2, returns clarification questions.
    If round_number > 2, fills defaults with status 'assumed_default'.
    """
    provided = provided_constraints or {}
    questions: List[ClarificationQuestion] = []

    # 1. Horizon weeks
    horizon = provided.get("horizon_weeks")
    if horizon is None and round_number <= 2:
        questions.append(
            ClarificationQuestion(
                field_name="horizon_weeks",
                question="What is your target planning horizon for this bold move?",
                tappable_options=["12 weeks (3 months)", "26 weeks (6 months)", "52 weeks (1 year)"],
                round_number=round_number,
            )
        )

    # 2. Budget cap
    budget = provided.get("budget_cap")
    if budget is None and round_number <= 2:
        questions.append(
            ClarificationQuestion(
                field_name="budget_cap",
                question="What is the maximum upfront budget cap allocated?",
                tappable_options=["$10,000", "$25,000", "$50,000", "$100,000"],
                round_number=round_number,
            )
        )

    # 3. Team size
    team = provided.get("team_size")
    if team is None and round_number <= 2:
        questions.append(
            ClarificationQuestion(
                field_name="team_size",
                question="How many team members can work on executing this strategy?",
                tappable_options=["1–2 people", "3–5 people", "6–10 people"],
                round_number=round_number,
            )
        )

    # 4. Risk tolerance
    risk = provided.get("risk_tolerance")
    if risk is None and round_number <= 2:
        questions.append(
            ClarificationQuestion(
                field_name="risk_tolerance",
                question="What is your risk tolerance for cash runway preservation?",
                tappable_options=["Low (preserve cash floor)", "Medium (balanced)", "High (aggressive)"],
                round_number=round_number,
            )
        )

    # If questions exist and rounds not exceeded, trigger needs_input
    if questions and round_number <= 2:
        log_agent_event(
            trace_id=trace_id,
            agent_name="IntakeAgent",
            action="request_clarification",
            input_summary=f"Goal: {raw_goal[:60]}...",
            output_summary=f"Emitted {len(questions)} clarification questions (round {round_number})",
            target_agent="User",
            status="needs_input",
        )
        return None, questions

    # Otherwise, finalize constraints with defaults for any missing items
    status = "assumed_default" if (round_number > 2 or any(k not in provided for k in ["horizon_weeks", "budget_cap", "team_size", "risk_tolerance"])) else "confirmed"

    final_constraints = FixedConstraints(
        horizon_weeks=int(provided.get("horizon_weeks", 26)),
        budget_cap=float(provided.get("budget_cap", 50000.0)),
        team_size=int(provided.get("team_size", 4)),
        risk_tolerance=provided.get("risk_tolerance", "medium"),
        cash_floor_weeks=int(provided.get("cash_floor_weeks", 12)),
        status=status,
    )

    log_agent_event(
        trace_id=trace_id,
        agent_name="IntakeAgent",
        action="constraints_confirmed",
        input_summary=f"Goal: {raw_goal[:60]}...",
        output_summary=f"Constraints locked ({status}): horizon={final_constraints.horizon_weeks}w, budget=${final_constraints.budget_cap:,.0f}",
        target_agent="DecompositionAgent",
        status="success",
    )

    return final_constraints, []
