"""Stage 3: Strategy Card Retrieval & Re-ranking (Card 2).

Enforces Hard Rules HR-03, HR-09, HR-10, HR-12:
- Retrieves exclusively from `approved_cards`. Unapproved cards are NEVER returned.
- Keyword and tag filtering followed by LLM re-ranking.
- Maps candidate strategies directly to the goal assumptions they address.
- Handles empty retrieval by flagging 'no documented precedent found'.
"""
from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Tuple
from services.api.app.moonshot.cards import StrategyCard, get_approved_cards
from packages.contracts.llm import LLMProvider
from packages.contracts.moonshot import CandidateStrategy, GoalAssumption
from services.api.app.moonshot.logger import log_agent_event

STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "is", "are", "was", "were", "be", "been", "that", "this", "our", "we",
    "can", "will", "all", "as", "from", "into", "align", "when", "how", "what"
}


def tokenize(text: str) -> set[str]:
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return {w for w in words if w not in STOP_WORDS}


def retrieve_strategies(
    trace_id: str,
    goal_statement: str,
    assumptions: List[GoalAssumption],
    llm: LLMProvider,
    top_k: int = 4,
) -> Tuple[List[CandidateStrategy], bool]:
    """Retrieve top approved strategy cards matching the goal and assumptions.

    Returns (candidates, precedent_found_flag).
    """
    approved_pool: List[StrategyCard] = get_approved_cards()

    if not approved_pool:
        log_agent_event(
            trace_id=trace_id,
            agent_name="RetrievalAgent",
            action="retrieve_cards",
            input_summary=f"Goal: {goal_statement[:50]}...",
            output_summary="Zero approved cards in database",
            status="no_precedent",
        )
        return [], False

    goal_tokens = tokenize(goal_statement)
    scored_pool: List[Tuple[StrategyCard, List[uuid.UUID], int]] = []

    for card in approved_pool:
        addressed_ids: List[uuid.UUID] = []
        match_score = 0

        # Tokenize card content
        card_content = card.title + " " + card.summary + " " + " ".join(card.tags)
        card_tokens = tokenize(card_content)

        # Check goal keyword overlap
        overlap = len(goal_tokens.intersection(card_tokens))
        match_score += overlap * 4

        # Check assumptions overlap
        for assumption in assumptions:
            assump_tokens = tokenize(assumption.text)
            common = assump_tokens.intersection(card_tokens)
            if len(common) >= 2 or (len(common) >= 1 and overlap >= 1):
                addressed_ids.append(assumption.id)
                match_score += 5 if assumption.is_critical else 2

        # Candidate must have meaningful match score (>= 4) and goal overlap
        if match_score >= 4 and overlap >= 1:
            scored_pool.append((card, addressed_ids, match_score))

    # If no matches above threshold, enforce HR-03 (never invent precedents)
    if not scored_pool:
        log_agent_event(
            trace_id=trace_id,
            agent_name="RetrievalAgent",
            action="retrieve_cards",
            input_summary=f"Goal: {goal_statement[:50]}...",
            output_summary="No documented precedent found matching assumptions",
            status="no_precedent",
        )
        return [], False

    # Sort descending by match score
    scored_pool.sort(key=lambda item: item[2], reverse=True)
    candidate_dicts = [
        {
            "card_id": str(c.id),
            "title": c.title,
            "summary": c.summary,
            "evidence_tier": c.evidence_tier,
            "time_to_signal_days": c.time_to_signal_days,
            "cost_to_undo": c.cost_to_undo,
            "upfront_cost": c.upfront_cost,
        }
        for c, _, _ in scored_pool[:8]
    ]

    # LLM Re-rank
    reranked = llm.rerank(query=goal_statement, candidates=candidate_dicts, top_k=top_k)
    reranked_ids = {uuid.UUID(c["card_id"]) for c in reranked}

    candidates: List[CandidateStrategy] = []
    card_map = {c.id: (c, a_ids) for c, a_ids, _ in scored_pool}

    for cid in reranked_ids:
        if cid in card_map:
            card_obj, addressed = card_map[cid]
            candidates.append(
                CandidateStrategy(
                    id=uuid.uuid4(),
                    card_id=card_obj.id,
                    title=card_obj.title,
                    summary=card_obj.summary,
                    lever_type=card_obj.lever_type,
                    time_to_signal_days=card_obj.time_to_signal_days,
                    cost_to_undo=card_obj.cost_to_undo,
                    upfront_cost=card_obj.upfront_cost,
                    evidence_tier=card_obj.evidence_tier,
                    assumptions_addressed=addressed,
                    parameter_template=card_obj.parameter_template,
                    source_quote=card_obj.source_excerpt,
                    source_quote_hash=card_obj.source_excerpt_hash,
                    source_citation=card_obj.source_citation,
                    strategic_mechanism=card_obj.strategic_mechanism,
                )
            )

    log_agent_event(
        trace_id=trace_id,
        agent_name="RetrievalAgent",
        action="retrieve_cards",
        input_summary=f"Goal: {goal_statement[:50]}...",
        output_summary=f"Retrieved and re-ranked top {len(candidates)} approved strategy cards",
        target_agent="SimulationAgent",
        model=llm.get_model_name(),
        status="success",
    )

    return candidates, True
