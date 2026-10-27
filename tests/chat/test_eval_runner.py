"""Tests for 20-Question Evaluation Runner (Part B2.14, PDF §15.2)."""
import pytest
from services.api.app.chat.eval.runner import eval_runner

@pytest.mark.asyncio
async def test_evaluation_runner_20_questions():
    summary = await eval_runner.run_evaluation()
    assert summary.total_cases == 20
    assert summary.pass_rate_pct >= 90.0  # At least 90% pass rate
    assert summary.avg_latency_ms < 50.0  # Fast routing

    # Verify key canonical categories
    categories = {r.category for r in summary.results}
    assert "finance" in categories
    assert "dashboard" in categories
    assert "documents" in categories
    assert "strategy" in categories
    assert "safety" in categories
