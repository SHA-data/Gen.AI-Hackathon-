"""SSE Stream Formatter (Part A6, Part B2.3).
Events: token, tool_start, tool_result, citation, chart, action_proposal, stage, error, done.
"""
import json
from typing import Any, Dict, Optional
from uuid import UUID

def format_sse(event: str, data: Dict[str, Any]) -> str:
    """Format an SSE frame with event and data."""
    def _sanitize(obj):
        if isinstance(obj, UUID):
            return str(obj)
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(x) for x in obj]
        return obj

    clean_data = _sanitize(data)
    json_str = json.dumps(clean_data, default=str)
    return f"event: {event}\ndata: {json_str}\n\n"

def sse_token(delta: str) -> str:
    return format_sse("token", {"delta": delta})

def sse_tool_start(tool_name: str, arguments: Dict[str, Any], tool_call_id: str) -> str:
    return format_sse("tool_start", {"tool_name": tool_name, "arguments": arguments, "tool_call_id": tool_call_id})

def sse_tool_result(tool_name: str, tool_call_id: str, status: str, kind: str = "normal", warnings: Optional[list] = None, data: Optional[Any] = None) -> str:
    payload = {
        "tool_name": tool_name,
        "tool_call_id": tool_call_id,
        "status": status,
        "kind": kind,
        "warnings": warnings or [],
    }
    if data is not None:
        payload["data"] = data
    return format_sse("tool_result", payload)

def sse_citation(citation_id: UUID, target_type: str, target_id: UUID, label: str, snippet: Optional[str] = None) -> str:
    return format_sse("citation", {
        "id": citation_id,
        "target_type": target_type,
        "target_id": target_id,
        "label": label,
        "snippet": snippet,
    })

def sse_chart(chart_type: str, title: str, cases: Dict[str, Any]) -> str:
    return format_sse("chart", {
        "chart_type": chart_type,
        "title": title,
        "cases": cases,
    })

def sse_action_proposal(action_id: UUID, action_type: str, risk_level: str, preview: Dict[str, Any], requires_approval: bool = True) -> str:
    return format_sse("action_proposal", {
        "action_id": action_id,
        "action_type": action_type,
        "risk_level": risk_level,
        "preview": preview,
        "requires_approval": requires_approval,
    })

def sse_stage(stage_number: int, stage_name: str, status: str) -> str:
    return format_sse("stage", {
        "stage_number": stage_number,
        "stage_name": stage_name,
        "status": status,
    })

def sse_error(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> str:
    return format_sse("error", {
        "code": code,
        "message": message,
        "details": details or {},
    })

def sse_done(message_id: UUID, decision_run_id: UUID, status: str = "verified", claims_count: int = 0) -> str:
    return format_sse("done", {
        "message_id": message_id,
        "decision_run_id": decision_run_id,
        "status": status,
        "claims_count": claims_count,
    })
