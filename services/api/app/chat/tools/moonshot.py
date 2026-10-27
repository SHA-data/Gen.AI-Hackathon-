"""Moonshot tool wrapper (Part A6, Part B2.7)."""
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from packages.contracts.envelope import ToolResultEnvelope
from packages.contracts.moonshot import (
    FakeMoonshotWorkflow,
    MoonshotReport,
    MoonshotWorkflow,
    NeedsInputResult,
)
from services.api.app.core.auth import AuthContext
from services.api.app.core.config import settings


def _resolve_default_workflow() -> MoonshotWorkflow:
    if getattr(settings, "MOONSHOT_BACKEND", "fake") == "real":
        try:
            from services.api.app.moonshot.adapter import RealMoonshotWorkflowAdapter
            return RealMoonshotWorkflowAdapter()
        except Exception:
            return FakeMoonshotWorkflow()
    return FakeMoonshotWorkflow()


_moonshot_workflow: MoonshotWorkflow = _resolve_default_workflow()


def set_moonshot_workflow(workflow: MoonshotWorkflow):
    global _moonshot_workflow
    _moonshot_workflow = workflow


def get_moonshot_workflow() -> MoonshotWorkflow:
    return _moonshot_workflow


class MoonshotRunArgs(BaseModel):
    goal: str
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)
    answers: Optional[Dict[str, str]] = None


async def handle_moonshot_run(
    auth: AuthContext,
    goal: str,
    constraints: Optional[Dict[str, Any]] = None,
    answers: Optional[Dict[str, str]] = None,
) -> ToolResultEnvelope[Any]:
    result = await _moonshot_workflow.run(
        org_id=auth.org_id,
        user_id=auth.user_id,
        goal=goal,
        constraints=constraints,
        answers=answers,
    )

    if isinstance(result, NeedsInputResult):
        return ToolResultEnvelope(
            status="warning",
            data={
                "kind": "needs_input",
                "request_id": str(result.request_id),
                "round_number": result.round_number,
                "questions": [q.model_dump() for q in result.questions],
            },
            sources=[],
            warnings=["Clarification required before running full Moonshot strategy synthesis."],
            run_id=result.request_id,
        )

    # MoonshotReport
    sources = [str(s.strategy_id) for s in result.top_strategies] + [str(s.cfo_run_id) for s in result.top_strategies]
    return ToolResultEnvelope(
        status="ok",
        data=result.model_dump(),
        sources=sources,
        warnings=[],
        run_id=result.report_id,
    )
