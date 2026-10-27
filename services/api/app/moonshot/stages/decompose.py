"""Stage 2: Assumption Tree Decomposition (Card 2).

Breaks the founder's bold goal into a tree of testable assumptions
what would have to be true for the goal to succeed.
Enforces hard requirement: demand-side assumptions are ALWAYS critical.
"""
from __future__ import annotations

import uuid
from typing import List
from pydantic import BaseModel, Field
from packages.contracts.llm import LLMProvider
from packages.contracts.moonshot import FixedConstraints, GoalAssumption
from services.api.app.moonshot.logger import log_agent_event


class DecomposedAssumptionItem(BaseModel):
    text: str
    importance: float = Field(ge=0.0, le=100.0)
    is_critical: bool = False
    category: str = "demand"


class DecomposedTreePayload(BaseModel):
    assumptions: List[DecomposedAssumptionItem] = Field(default_factory=list)


def decompose_goal(
    trace_id: str,
    goal_statement: str,
    constraints: FixedConstraints,
    llm: LLMProvider,
) -> List[GoalAssumption]:
    """Decompose goal into assumptions using LLM and enforce critical demand assumptions."""
    prompt = f"""You are a senior strategy consultant. Decompose the following bold business goal into testable assumptions.
Goal: "{goal_statement}"
Horizon: {constraints.horizon_weeks} weeks
Budget Cap: ${constraints.budget_cap:,.2f}
Team Size: {constraints.team_size}

Break the goal into 3 to 5 critical and execution assumptions across categories: demand, execution, financial, market.
Note: Assumptions concerning customer willingness to pay, adoption, or sales conversion MUST be categorized as 'demand'.
"""

    payload = llm.generate_structured(
        prompt=prompt,
        schema=DecomposedTreePayload,
        system_prompt="Decompose business goals into precise, testable assumptions.",
    )

    results: List[GoalAssumption] = []
    for item in payload.assumptions:
        cat = item.category.lower() if item.category else "demand"
        if cat not in ["demand", "execution", "financial", "market"]:
            cat = "demand"
        
        # Hard Rule: demand-side assumptions are always critical
        is_crit = True if cat == "demand" else item.is_critical

        results.append(
            GoalAssumption(
                id=uuid.uuid4(),
                text=item.text,
                importance=item.importance,
                is_critical=is_crit,
                category=cat,
            )
        )

    log_agent_event(
        trace_id=trace_id,
        agent_name="DecompositionAgent",
        action="decompose_assumptions",
        input_summary=f"Goal: {goal_statement[:60]}...",
        output_summary=f"Generated {len(results)} assumptions ({sum(1 for a in results if a.is_critical)} critical)",
        target_agent="RetrievalAgent",
        model=llm.get_model_name(),
        status="success",
    )

    return results
