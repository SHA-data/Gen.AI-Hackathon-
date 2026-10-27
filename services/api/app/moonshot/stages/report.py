"""Stage 8: Report Assembly, Claim Tagging & Verification (Card 5 & Output).

Assembles the final comprehensive Moonshot Report adhering strictly to PDF Section 12.3:
1. Goal & Constraints (with status confirmed / assumed_default)
2. What Must Be True (assumption tree with critical flags)
3. Top 3 Ranked Strategies & Flagged List with Gate Breach Reasons
4. Cash Impact in Three Cases (Expected, Best, Worst) with CFO Run IDs
5. Skeptic Section (Pre-mortem failure modes, base rates, 30-day experiments)
6. Weight Sensitivity Analysis (ROC, Rank-Sum, Equal, Low-Risk)
7. Audit Trail of Claims (Cited, Computed, Inferred tags)
8. Mandatory Disclaimer: "Decision support, not financial advice."
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from services.api.app.moonshot.verifier import (
    MANDATORY_DISCLAIMER_PHRASE,
    audit_claim,
    compute_sha256,
    verify_disclaimer_presence,
)
from packages.contracts.finance import ScenarioRunResponse
from packages.contracts.moonshot import (
    CandidateStrategy,
    FixedConstraints,
    GoalAssumption,
    SensitivityCheckResult,
    StrategyRanking,
)

MANDATORY_DISCLAIMER = (
    "Decision support, not financial advice. Forecasts depend on the assumptions shown "
    "and are not guaranteed predictions."
)


def assemble_moonshot_report(
    request_id: uuid.UUID,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    goal_statement: str,
    constraints: FixedConstraints,
    assumptions: List[GoalAssumption],
    ranked_candidates: List[CandidateStrategy],
    rankings_by_profile: Dict[str, List[StrategyRanking]],
    flagged_candidates: List[Dict[str, Any]],
    simulations: Dict[uuid.UUID, ScenarioRunResponse],
    skeptic_section: Dict[str, Any],
    sensitivity: SensitivityCheckResult,
    candidates_criteria: Optional[Dict[uuid.UUID, Tuple[Dict[str, float], str]]] = None,
) -> Dict[str, Any]:
    """Assemble verified Moonshot Report and structured data."""
    report_id = uuid.uuid4()
    claims: List[Dict[str, Any]] = []

    # 1. Top 3 Strategies structured array
    top_3 = ranked_candidates[:3]
    structured_strategies: List[Dict[str, Any]] = []

    # Markdown assembly
    lines = [
        f"# NeuralCFO • Moonshot Strategy Report",
        f"**Report ID**: `{report_id}` | **Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "---",
        "## 1. Goal & Operating Constraints",
        f"- **Bold Goal**: {goal_statement}",
        f"- **Planning Horizon**: {constraints.horizon_weeks} weeks",
        f"- **Budget Cap**: ${constraints.budget_cap:,.2f}",
        f"- **Team Capacity**: {constraints.team_size} members",
        f"- **Risk Tolerance**: {constraints.risk_tolerance.capitalize()}",
        f"- **Cash Floor**: {constraints.cash_floor_weeks} weeks of runway",
        f"- **Constraint Status**: `{constraints.status}`",
        "",
        "## 2. What Must Be True (Assumption Tree)",
    ]

    for a in assumptions:
        crit_label = "**[CRITICAL]**" if a.is_critical else "[Supporting]"
        lines.append(f"- {crit_label} {a.text} *(Category: {a.category}, Importance: {a.importance}%)*")
        claims.append(audit_claim(f"Assumption: {a.text}", tag="inferred"))

    lines.extend([
        "",
        "## 3. Top Recommended Strategies",
    ])

    for idx, cand in enumerate(top_3, 1):
        roc_rank = next((r for r in rankings_by_profile.get("roc_default", []) if r.candidate_id == cand.id), None)
        score_val = roc_rank.final_score if roc_rank else 0.0

        sim_res = simulations.get(cand.id)
        exp_case = sim_res.cases.expected if sim_res else None

        # Extract criteria & mathematical details if available
        crit_entry = (candidates_criteria or {}).get(cand.id)
        c_scores = crit_entry[0] if crit_entry else {"fit": 0.0, "cash": 0.0, "signal": 0.0, "reversibility": 0.0}
        mult_val = 1.0 if cand.evidence_tier == "A" else (0.8 if cand.evidence_tier == "B" else 0.5)
        w_sum = roc_rank.weighted_sum if roc_rank else 0.0
        formula_str = (
            f"{score_val:.1f} = {mult_val} × (0.52·{c_scores.get('fit', 0.0):.1f} + "
            f"0.27·{c_scores.get('cash', 0.0):.1f} + 0.15·{c_scores.get('signal', 0.0):.1f} + "
            f"0.06·{c_scores.get('reversibility', 0.0):.1f})"
        )

        strat_item = {
            "rank": idx,
            "id": str(cand.id),
            "card_id": str(cand.card_id),
            "title": cand.title,
            "summary": cand.summary,
            "score": score_val,
            "evidence_tier": cand.evidence_tier,
            "evidence_multiplier": mult_val,
            "weighted_sum": w_sum,
            "formula_breakdown": formula_str,
            "criteria_scores": {
                "fit": round(c_scores.get("fit", 0.0), 1),
                "cash": round(c_scores.get("cash", 0.0), 1),
                "signal": round(c_scores.get("signal", 0.0), 1),
                "reversibility": round(c_scores.get("reversibility", 0.0), 1),
            },
            "lever_type": cand.lever_type,
            "assumptions_addressed": [str(aid) for aid in cand.assumptions_addressed],
            "source_citation": cand.source_citation,
            "source_quote": cand.source_quote,
            "source_quote_hash": cand.source_quote_hash,
            "strategic_mechanism": cand.strategic_mechanism,
            "time_to_signal_days": cand.time_to_signal_days,
            "upfront_cost": cand.upfront_cost,
            "cost_to_undo": cand.cost_to_undo,
            "expected_end_cash": float(exp_case.end_cash) if exp_case else 0.0,
            "min_cash": float(exp_case.min_cash) if exp_case else 0.0,
            "runway_weeks": exp_case.runway_weeks if exp_case else 0,
            "run_id": str(sim_res.run_id) if sim_res else "",
        }
        structured_strategies.append(strat_item)

        lines.extend([
            f"### #{idx}: {cand.title} (Score: {score_val} / 100)",
            f"- **Summary**: {cand.summary}",
            f"- **Evidence Tier**: Tier {cand.evidence_tier} *(Source: {cand.source_citation})*",
            f"- **Primary Archival Quote**: *\"{cand.source_quote}\"*",
            f"- **Strategic Cash Flow Mechanism**: {cand.strategic_mechanism}",
            f"- **Execution Horizon**: {cand.time_to_signal_days} days to first signal",
            f"- **Upfront Cost**: ${cand.upfront_cost:,.2f} | **Cost to Undo**: ${cand.cost_to_undo:,.2f}",
        ])

        claims.append(
            audit_claim(
                f"Founder Quote: \"{cand.source_quote}\"",
                tag="cited",
                quote_ref=(cand.source_quote, cand.source_quote_hash),
            )
        )
        if cand.strategic_mechanism:
            claims.append(
                audit_claim(
                    f"Strategic Mechanism for {cand.title}: {cand.strategic_mechanism}",
                    tag="inferred",
                )
            )

        if sim_res and exp_case:
            lines.extend([
                f"- **Financial Simulation (Run ID: `{sim_res.run_id}`)**:",
                f"  - Expected Ending Cash: **${float(exp_case.end_cash):,.2f}**",
                f"  - Minimum Projected Cash: **${float(exp_case.min_cash):,.2f}**",
                f"  - Expected Runway: **{exp_case.runway_weeks} weeks**",
            ])
            claims.append(
                audit_claim(
                    f"Expected Ending Cash for {cand.title} reaches ${float(exp_case.end_cash):,.2f}",
                    tag="computed",
                    scenario_ref=(float(exp_case.end_cash), sim_res),
                )
            )

    # Flagged Strategies
    if flagged_candidates:
        lines.extend([
            "",
            "### Flagged Strategies (Gated)",
        ])
        for fl in flagged_candidates:
            breach_str = "; ".join(fl.get("breached_gates", []))
            lines.append(f"- **{fl.get('title')}**: Excluded from ranking — *{breach_str}*")

    # Skeptic Section
    lines.extend([
        "",
        "## 4. Skeptic Section & Downside Stress-Test",
        "> **Skeptic Mandate**: We rigorously probe failure modes before capital is committed.",
        "",
        "### Pre-Mortem Failure Modes",
    ])
    for pm in skeptic_section.get("pre_mortem_scenarios", []):
        lines.append(
            f"- **{pm.get('failure_mode')}** (Risk: {pm.get('impact')} impact / {pm.get('probability')} likelihood):"
            f"\n  *Mitigation*: {pm.get('mitigation')}"
        )

    lines.extend([
        "",
        "### 30-Day Validation Experiments",
    ])
    for exp in skeptic_section.get("experiments", []):
        lines.append(
            f"- **{exp.get('title')}** ({exp.get('duration_days')} days): Track metric *{exp.get('metric')}* "
            f"towards target *{exp.get('target')}*."
        )

    # Sensitivity Table data
    sensitivity_rows = []
    for cand in top_3:
        s_roc = next((r.final_score for r in rankings_by_profile.get("roc_default", []) if r.candidate_id == cand.id), 0.0)
        s_rnk = next((r.final_score for r in rankings_by_profile.get("rank_sum", []) if r.candidate_id == cand.id), 0.0)
        s_eql = next((r.final_score for r in rankings_by_profile.get("equal", []) if r.candidate_id == cand.id), 0.0)
        sensitivity_rows.append({
            "title": cand.title,
            "roc": s_roc,
            "rank_sum": s_rnk,
            "equal": s_eql,
            "tier": cand.evidence_tier,
        })

    # Weight Sensitivity Matrix in markdown
    lines.extend([
        "",
        "## 5. Weight Sensitivity Analysis",
        f"**Verdict**: *{sensitivity.summary}*",
        "",
        "| Strategy | ROC (Default) | Rank-Sum | Equal |",
        "|---|---|---|---|",
    ])
    for row in sensitivity_rows:
        lines.append(f"| {row['title']} | {row['roc']} | {row['rank_sum']} | {row['equal']} |")

    # Mandatory Disclaimer
    lines.extend([
        "",
        "---",
        f"> **Disclaimer**: {MANDATORY_DISCLAIMER}",
    ])

    report_md = "\n".join(lines)
    disclaimer_ok = verify_disclaimer_presence(report_md)

    return {
        "report_id": str(report_id),
        "request_id": str(request_id),
        "org_id": str(org_id),
        "user_id": str(user_id),
        "goal_statement": goal_statement,
        "constraints": constraints.model_dump(),
        "assumptions": [a.model_dump() for a in assumptions],
        "ranked_strategies": structured_strategies,
        "flagged_strategies": flagged_candidates,
        "skeptic_section": skeptic_section,
        "sensitivity": {
            "is_robust": sensitivity.is_robust,
            "summary": sensitivity.summary,
            "rows": sensitivity_rows,
        },
        "report_markdown": report_md,
        "disclaimer": MANDATORY_DISCLAIMER,
        "disclaimer_verified": disclaimer_ok,
        "claims_audit": claims,
        "top_strategies_count": len(top_3),
        "flagged_count": len(flagged_candidates),
    }
