"""Dashboard action proposal tool wrapper (Part A6, Part B2.12)."""
from typing import Any, Dict, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from packages.contracts.envelope import ToolResultEnvelope
from services.api.app.core.auth import AuthContext

class ProposeActionArgs(BaseModel):
    action_type: Literal[
        "set_date_range",
        "add_chart",
        "add_kpi",
        "reorder_widget",
        "create_report",
        "update_assumption",
        "import_transactions",
    ]
    payload: Dict[str, Any]
    risk_level: Literal["low", "medium", "high"] = "low"

# Allowed schemas for dashboard actions
ACTION_RISK_MAP = {
    "set_date_range": "low",
    "add_chart": "low",
    "add_kpi": "low",
    "reorder_widget": "low",
    "create_report": "medium",
    "update_assumption": "high",
    "import_transactions": "high",
}

async def handle_propose_action(
    auth: AuthContext,
    action_type: str,
    payload: Dict[str, Any],
    risk_level: str = "low",
) -> ToolResultEnvelope[Dict[str, Any]]:
    # Reject unsupported actions per PDF §10.4
    if action_type.startswith("delete_") or action_type.startswith("share_"):
        return ToolResultEnvelope(
            status="failed",
            data={},
            sources=[],
            warnings=[f"Action '{action_type}' is forbidden by system policy in v1."],
            run_id=None,
        )

    # Force true risk level from system policy, never trust model's claimed risk level!
    enforced_risk = ACTION_RISK_MAP.get(action_type, "high")
    action_id = uuid4()

    return ToolResultEnvelope(
        status="ok",
        data={
            "action_id": str(action_id),
            "action_type": action_type,
            "risk_level": enforced_risk,
            "preview": payload,
            "requires_approval": True,
            "status": "proposed",
        },
        sources=[],
        warnings=[],
        run_id=action_id,
    )
