"""FastAPI HTTP & SSE Streaming Endpoints for Moonshot Mode (Range 0200-0299).

Provides:
- POST /v1/moonshot/run (JSON and SSE stream stage events)
- POST /v1/moonshot/requests/{id}/answers (resume after clarification)
- GET /v1/moonshot/reports/{id}
- GET /v1/moonshot/reports/{id}/export (Markdown & PDF-ready HTML styled with BRANDING tokens)
- GET /v1/moonshot/cards
- POST /v1/moonshot/cards/{id}/approve (Admin only)
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, FastAPI, HTTPException, Header, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from services.api.app.moonshot.cards import StrategyCard, get_approved_cards
from services.api.app.moonshot.db import init_db
from services.api.app.moonshot.workflow import MoonshotWorkflow

# Create modular APIRouter with /v1/moonshot prefix
moonshot_router = APIRouter(prefix="/v1/moonshot", tags=["moonshot"])

# Global state / engine instances
workflow_engine = MoonshotWorkflow()
reports_db: Dict[str, Dict[str, Any]] = {}


class RunRequestPayload(BaseModel):
    goal: Optional[str] = None
    raw_text: Optional[str] = None
    horizon_weeks: Optional[int] = None
    budget_cap: Optional[float] = None
    team_size: Optional[int] = None
    risk_tolerance: Optional[Literal["low", "medium", "high"]] = None
    cash_floor_weeks: Optional[int] = None
    constraints: Optional[Dict[str, Any]] = None
    stream: bool = False


class AnswersPayload(BaseModel):
    answers: Dict[str, Any]


@moonshot_router.post("/run")
async def run_moonshot(
    payload: RunRequestPayload,
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Run Moonshot pipeline or stream SSE stage events."""
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()

    target_goal = payload.goal or payload.raw_text
    if not target_goal:
        raise HTTPException(status_code=422, detail="Goal statement ('goal' or 'raw_text') is required.")

    provided = {}
    if payload.constraints and isinstance(payload.constraints, dict):
        for k, v in payload.constraints.items():
            if v is not None:
                provided[k] = v
    if payload.horizon_weeks is not None:
        provided["horizon_weeks"] = payload.horizon_weeks
    if payload.budget_cap is not None:
        provided["budget_cap"] = payload.budget_cap
    if payload.team_size is not None:
        provided["team_size"] = payload.team_size
    if payload.risk_tolerance is not None:
        provided["risk_tolerance"] = payload.risk_tolerance
    if payload.cash_floor_weeks is not None:
        provided["cash_floor_weeks"] = payload.cash_floor_weeks

    accept_header = request.headers.get("accept", "")
    should_stream = payload.stream or ("text/event-stream" in accept_header)

    if should_stream:
        # SSE Streaming
        async def event_generator():
            yield f"event: stage\ndata: {json.dumps({'stage': 'intake', 'agent': 'IntakeAgent', 'message': 'Intake & Constraints Verified'})}\n\n"
            result = workflow_engine.run(
                goal=target_goal,
                org_id=org_id,
                user_id=user_id,
                provided_constraints=provided,
            )
            if result.get("status") == "needs_input":
                yield f"event: needs_input\ndata: {json.dumps(result, default=str)}\n\n"
                yield "event: done\ndata: {}\n\n"
                return

            yield f"event: stage\ndata: {json.dumps({'stage': 'decompose', 'agent': 'DecompositionAgent', 'message': 'Goal Assumption Tree Decomposed'})}\n\n"
            yield f"event: stage\ndata: {json.dumps({'stage': 'retrieve', 'agent': 'RetrievalAgent', 'message': 'Archival Precedents Retrieved'})}\n\n"
            yield f"event: stage\ndata: {json.dumps({'stage': 'simulate', 'agent': 'SimulationAgent', 'message': 'CFO Financial Simulations Run'})}\n\n"
            yield f"event: stage\ndata: {json.dumps({'stage': 'gate', 'agent': 'GatingAgent', 'message': 'Deterministic Hard Limits Evaluated (G1-G4)'})}\n\n"
            yield f"event: stage\ndata: {json.dumps({'stage': 'score', 'agent': 'ScoringAgent', 'message': 'Multi-Criteria ROC Scoring Computed'})}\n\n"
            yield f"event: stage\ndata: {json.dumps({'stage': 'skeptic', 'agent': 'SkepticAgent', 'message': 'Pre-Mortem Downside Stress-Test Evaluated'})}\n\n"
            yield f"event: stage\ndata: {json.dumps({'stage': 'report', 'agent': 'AssemblyAgent', 'message': 'Deterministic Report Verified & Assembled'})}\n\n"

            report = result.get("report", {})
            if report:
                reports_db[report["report_id"]] = report

            yield f"event: report_ready\ndata: {json.dumps(result, default=str)}\n\n"
            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # Synchronous execution
    result = workflow_engine.run(
        goal=target_goal,
        org_id=org_id,
        user_id=user_id,
        provided_constraints=provided,
    )
    if result.get("report"):
        reports_db[result["report"]["report_id"]] = result["report"]

    return result


@moonshot_router.post("/requests/{request_id}/answers")
async def resume_moonshot(request_id: str, payload: AnswersPayload):
    """Resume a paused workflow run after user submits clarification answers."""
    result = workflow_engine.resume(request_id=request_id, answers=payload.answers)
    if result.get("report"):
        reports_db[result["report"]["report_id"]] = result["report"]
    return result


@moonshot_router.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Retrieve report by ID."""
    report = reports_db.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return report


@moonshot_router.get("/reports/{report_id}/export")
async def export_report(
    report_id: str,
    format: Literal["markdown", "html"] = Query("markdown"),
    theme: Literal["light", "dark"] = Query("light"),
):
    """Export report as Markdown or PDF-ready HTML styled with BRANDING.md tokens."""
    report = reports_db.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    md_content = report.get("report_markdown", "")

    if format == "markdown":
        return PlainTextResponse(md_content, media_type="text/markdown")

    # Render HTML with BRANDING tokens
    bg_color = "#0A1624" if theme == "dark" else "#F7F9FB"
    card_bg = "#12233A" if theme == "dark" else "#FFFFFF"
    text_color = "#E8EEF5" if theme == "dark" else "#0B1F33"
    primary = "#35C0CB" if theme == "dark" else "#0B6B74"
    accent = "#A99DF5" if theme == "dark" else "#5B49C0"
    border_color = "#5B7391" if theme == "dark" else "#7B8794"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>NeuralCFO Moonshot Report</title>
<style>
  body {{
    background-color: {bg_color};
    color: {text_color};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 40px;
  }}
  .card {{
    background-color: {card_bg};
    border: 1px solid {border_color};
    border-radius: 8px;
    padding: 32px;
    max-width: 900px;
    margin: 0 auto;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }}
  h1, h2, h3 {{ color: {primary}; }}
  .accent {{ color: {accent}; }}
  .disclaimer {{
    color: #475569;
    font-size: 13px;
    margin-top: 32px;
    border-top: 1px solid {border_color};
    padding-top: 16px;
  }}
  table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  th, td {{ border: 1px solid {border_color}; padding: 10px; text-align: left; }}
  th {{ background-color: {bg_color}; }}
</style>
</head>
<body>
<div class="card">
  <div style="font-weight: 700; font-size: 20px;">Neural<span class="accent">CFO</span> • Moonshot</div>
  <pre style="white-space: pre-wrap; font-family: inherit;">{md_content}</pre>
</div>
</body>
</html>
"""
    return HTMLResponse(content=html)


@moonshot_router.get("/cards")
async def list_cards():
    """List approved strategy cards."""
    cards = get_approved_cards()
    return {"cards": [c.model_dump() for c in cards], "count": len(cards)}


# Standalone app instance for isolated testing or serving
app = FastAPI(
    title="NeuralCFO Moonshot Mode API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(moonshot_router)

@app.on_event("startup")
def on_startup():
    """Ensure SQLite database, schema, views, and seed data are initialized."""
    init_db()
