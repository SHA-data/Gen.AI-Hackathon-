"""Verifier Engine (Part B2.6, PDF §12.2).
Executes deterministic checks V1-V9 on candidate answers.
"""
from typing import Any, Dict, List, Literal, NamedTuple, Optional
from uuid import UUID

from services.api.app.chat.verifier.checks import (
    CheckResult,
    check_v1_numbers,
    check_v2_quotes,
    check_v3_citations,
    check_v5_units,
    check_v6_gates,
    check_v8_disclaimer,
)

class VerificationSummary(NamedTuple):
    overall_status: Literal["verified", "warning", "unverified", "failed"]
    checks: List[CheckResult]
    should_regenerate: bool
    caveat_message: Optional[str] = None

class VerifierEngine:
    """Orchestrates deterministic verifier checks post-turn."""

    def verify_turn(
        self,
        answer_text: str,
        current_turn_tool_results: List[Any],
        caller_org_id: UUID,
        cited_sources: Optional[List[Dict[str, Any]]] = None,
        is_report_turn: bool = False,
        top_strategies: Optional[List[Dict[str, Any]]] = None,
        failed_gates: Optional[List[Dict[str, Any]]] = None,
    ) -> VerificationSummary:
        results: List[CheckResult] = []

        # 1. V1 Numbers
        results.append(check_v1_numbers(answer_text, current_turn_tool_results))

        # 2. V2 Quotes
        results.append(check_v2_quotes(answer_text))

        # 3. V3 Citations
        if cited_sources:
            results.append(check_v3_citations(cited_sources, caller_org_id))
        else:
            results.append(CheckResult("V3_citations", "passed", {"info": "no_citations"}))

        # 4. V5 Units
        results.append(check_v5_units(answer_text))

        # 5. V6 Gates (if strategy evaluation)
        if top_strategies and failed_gates:
            results.append(check_v6_gates(top_strategies, failed_gates))
        else:
            results.append(CheckResult("V6_gates", "passed", {"info": "no_strategy_gates"}))

        # 6. V8 Disclaimer (if scenario / report turn)
        results.append(check_v8_disclaimer(answer_text, is_report_turn))

        # Determine overall status and whether V9 regeneration is triggered
        has_failed = any(c.status == "failed" for c in results)
        has_warning = any(c.status == "warning" for c in results)

        if has_failed:
            return VerificationSummary(
                overall_status="failed",
                checks=results,
                should_regenerate=True,
                caveat_message="Verification check failed. Review tool-source lineage.",
            )
        elif has_warning:
            return VerificationSummary(
                overall_status="warning",
                checks=results,
                should_regenerate=False,
                caveat_message="Caution: Some numeric figures could not be directly matched to tool outputs.",
            )

        return VerificationSummary(
            overall_status="verified",
            checks=results,
            should_regenerate=False,
            caveat_message=None,
        )

verifier_engine = VerifierEngine()
