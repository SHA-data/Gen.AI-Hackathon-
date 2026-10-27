"""Intent Router (Part B2.4, PDF §7.2).
Classifies user intent, selects active agent (neuralcfo | moonshot), and restricts allowed tools.
Rule-based routing first; LLM classification as fallback.
"""
import re
from typing import List, Literal, NamedTuple
from pydantic import BaseModel

class RouteDecision(NamedTuple):
    agent_key: Literal["neuralcfo", "moonshot"]
    allowed_tools: List[str]
    intent_category: str
    is_destructive: bool = False

# Rule-based pattern matching table per PDF §7.2
ROUTING_RULES = [
    # 1. Safety violations & destructive requests
    (
        r"\b(delete|drop|wipe|destroy|clear)\s+(all\s+)?(my\s+)?(transactions|records|data|database)\b",
        RouteDecision("neuralcfo", [], "destructive_refused", is_destructive=True),
    ),
    (
        r"\b(ignore\s+(your\s+)?instructions|give\s+me\s+investment\s+advice|legal\s+advice)\b",
        RouteDecision("neuralcfo", [], "refused", is_destructive=True),
    ),
    # 2. Moonshot Mode (bold move, strategy, bold goal, radical idea, double revenue)
    (
        r"\b(bold\s+move|bold\s+strategy|moonshot|radical\s+idea|strategic\s+option|fix\s+this\s+instead)\b",
        RouteDecision("moonshot", ["moonshot.run", "web.search"], "moonshot_run"),
    ),
    # 3. Document & Policy queries (contracts, policies, terms)
    (
        r"\b(policy|according\s+to\s+our\s+contracts?|handbook|clause|what\s+does\s+our\s+policy\s+say)\b",
        RouteDecision("neuralcfo", ["rag.search"], "document_rag"),
    ),
    # 4. Scenarios & Projections (runway if, hire, late payment, revenue drops)
    (
        r"\b(hire|hiring|developers|headcount|pay\s+late|late\s+payment|delay|scenario|projected\s+cash\s+runway|if\s+revenue\s+drops)\b",
        RouteDecision("neuralcfo", ["finance.run_scenario", "finance.get_metric", "finance.list_source_rows"], "finance_scenario"),
    ),
    # 5. Why did cash change (Driver explanation)
    (
        r"\b(why\s+did\s+cash\s+drop|why\s+did\s+revenue|explain\s+change|cash\s+change)\b",
        RouteDecision("neuralcfo", ["finance.explain_change", "finance.list_source_rows", "finance.get_metric"], "finance_explain"),
    ),
    # 6. Web research & market trends
    (
        r"\b(market\s+trends?|industry\s+benchmarks?|latest\s+trends?)\b",
        RouteDecision("neuralcfo", ["web.search"], "web_research"),
    ),
    # 7. Metric queries (spend, cash, revenue, burn, receivables)
    (
        r"\b(what\s+did\s+we\s+spend|how\s+much\s+cash|what\s+is\s+our\s+burn|revenue|receivables|balance|payroll\s+last\s+period)\b",
        RouteDecision("neuralcfo", ["finance.get_metric", "finance.list_source_rows"], "finance_metric"),
    ),
    # 8. Dashboard changes
    (
        r"\b(add\s+(a\s+)?chart|add\s+(a\s+)?kpi|reorder|dashboard|chart)\b",
        RouteDecision("neuralcfo", ["dashboard.propose_action"], "dashboard_action"),
    ),
    # 9. Memory & persistent facts
    (
        r"\b(remember\s+that|note\s+that|keep\s+in\s+mind|store\s+this|save\s+assumption)\b",
        RouteDecision("neuralcfo", ["memory.write", "memory.read"], "memory_action"),
    ),
]

class IntentRouter:
    """Deterministic, rule-first intent router."""

    def route(self, user_message: str, forced_agent: str = None) -> RouteDecision:
        msg_clean = user_message.strip()

        # Check for destructive request first
        for pattern, decision in ROUTING_RULES:
            if re.search(pattern, msg_clean, re.IGNORECASE):
                if decision.is_destructive:
                    return decision
                # If an agent was explicitly chosen by the user in UI, respect it unless mismatched
                if forced_agent in ("neuralcfo", "moonshot"):
                    return RouteDecision(forced_agent, decision.allowed_tools, decision.intent_category)
                return decision

        # Default fallback
        if forced_agent == "moonshot":
            return RouteDecision("moonshot", ["moonshot.run", "web.search"], "moonshot_default")

        return RouteDecision(
            "neuralcfo",
            [
                "finance.get_metric",
                "finance.run_scenario",
                "finance.list_source_rows",
                "finance.explain_change",
                "rag.search",
                "dashboard.propose_action",
                "memory.write",
                "memory.read",
            ],
            "general_cfo_query",
        )

intent_router = IntentRouter()
