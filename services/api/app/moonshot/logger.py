"""Structured JSONL Audit & Trace Logger for Moonshot Mode.

Adheres to Vibe Coding Starter Guide §11:
Logs agent interactions, actions, handoffs, confidence, and models used
to prove agents did real work for hackathon judges.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "agent_traces.jsonl"


def get_log_dir() -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def log_agent_event(
    trace_id: str,
    agent_name: str,
    action: str,
    input_summary: str,
    output_summary: str,
    target_agent: Optional[str] = None,
    model: str = "sample-mode",
    confidence: float = 1.0,
    status: str = "success",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Emit a structured event to stdout and append to logs/agent_traces.jsonl."""
    get_log_dir()
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "agent_name": agent_name,
        "action": action,
        "input_summary": input_summary,
        "output_summary": output_summary,
        "target_agent": target_agent,
        "model": model,
        "confidence": round(confidence, 2),
        "status": status,
        "metadata": metadata or {},
    }

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        pass  # Never crash business logic on logging failure

    return event
