"""Stage 4 & 5: Scenario Translation & Simulation Seam (Card 3).

Enforces Hard Rules HR-02, HR-07:
- Maps card parameter templates to Contract A5 levers (editable, flagged is_assumption).
- Invokes CFO Scenario Engine (FakeFinanceService or live CFO service).
- Never performs financial arithmetic in prose; every cash figure carries a run_id.
"""
from __future__ import annotations

import uuid
from typing import Dict, List, Tuple
from packages.contracts.finance import (
    FakeFinanceService,
    ScenarioChange,
    ScenarioPayload,
    ScenarioRunRequest,
    ScenarioRunResponse,
)
from packages.contracts.moonshot import CandidateStrategy, FixedConstraints
from services.api.app.moonshot.logger import log_agent_event


def translate_and_simulate(
    trace_id: str,
    candidates: List[CandidateStrategy],
    constraints: FixedConstraints,
    finance_service: FakeFinanceService,
    org_id: uuid.UUID,
) -> Dict[uuid.UUID, ScenarioRunResponse]:
    """Translate each card's parameter template into an A5 scenario run and execute simulation."""
    snapshot = finance_service.get_snapshot(org_id)
    simulation_results: Dict[uuid.UUID, ScenarioRunResponse] = {}

    for candidate in candidates:
        template = candidate.parameter_template
        lever_change = ScenarioChange(
            lever=template.get("lever", candidate.lever_type),
            op=template.get("op", "set"),
            value=template.get("value", 0),
            is_assumption=True,
        )

        scenario_req = ScenarioRunRequest(
            baseline_run_id=snapshot.baseline_run_id,
            horizon_weeks=constraints.horizon_weeks,
            scenario=ScenarioPayload(
                name=f"Moonshot Simulation: {candidate.title}",
                origin="moonshot_card",
                source_card_id=candidate.card_id,
                changes=[lever_change],
            ),
        )

        response = finance_service.run_scenario(scenario_req, org_id)
        simulation_results[candidate.id] = response

        log_agent_event(
            trace_id=trace_id,
            agent_name="SimulationAgent",
            action="simulate_cfo_scenario",
            input_summary=f"Candidate: {candidate.title} (lever: {lever_change.lever}={lever_change.value})",
            output_summary=f"CFO Run {response.run_id}: Expected End Cash=${float(response.cases.expected.end_cash):,.0f}, Min=${float(response.cases.expected.min_cash):,.0f}, Runway={response.cases.expected.runway_weeks}w",
            target_agent="GatingAndScoringAgent",
            status="success",
        )

    return simulation_results
