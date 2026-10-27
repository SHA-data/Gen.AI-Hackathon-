"""FastAPI Endpoint & SSE Integration Tests for Integrated Monolith."""
import pytest
from starlette.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)


def test_api_list_cards():
    resp = client.get("/v1/moonshot/cards")
    assert resp.status_code == 200
    data = resp.json()
    assert "cards" in data
    assert data["count"] == 12


def test_api_run_json_and_export():
    payload = {
        "goal": "Launch annual prepay tier for our design platform",
        "horizon_weeks": 26,
        "budget_cap": 50000.0,
        "team_size": 4,
        "risk_tolerance": "medium",
        "cash_floor_weeks": 12,
        "stream": False,
    }
    resp = client.post("/v1/moonshot/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert "report" in data

    report_id = data["report"]["report_id"]

    # 1. Fetch report by ID
    get_resp = client.get(f"/v1/moonshot/reports/{report_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["report_id"] == report_id

    # 2. Export Markdown
    export_md = client.get(f"/v1/moonshot/reports/{report_id}/export?format=markdown")
    assert export_md.status_code == 200
    assert "Decision support, not financial advice" in export_md.text

    # 3. Export HTML with BRANDING tokens
    export_html = client.get(f"/v1/moonshot/reports/{report_id}/export?format=html&theme=dark")
    assert export_html.status_code == 200
    assert "#0A1624" in export_html.text  # Dark page token
    assert "#35C0CB" in export_html.text  # Primary dark token
    assert "Decision support, not financial advice" in export_html.text


def test_api_run_sse_stream():
    payload = {
        "goal": "Shift client contracts to upfront blocks",
        "horizon_weeks": 26,
        "budget_cap": 50000.0,
        "team_size": 4,
        "risk_tolerance": "medium",
        "cash_floor_weeks": 12,
        "stream": True,
    }
    resp = client.post("/v1/moonshot/run", json=payload)
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    text = resp.text
    assert "event: stage" in text
    assert "event: report_ready" in text
    assert "event: done" in text
