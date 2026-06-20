"""escalation node (PRD §5.2 / §5.5).

Returns the configured refusal copy, flags the message for human-agent review,
and NEVER calls the LLM.
"""
from __future__ import annotations

from ...config.settings import ESCALATION_TEMPLATE
from ..state import RAGState

# Map an internal router topic to a user-facing phrase for {topic}.
_TOPIC_PHRASES = {
    "legal_advice": "potential legal action",
    "advice": "what you should do",
    "tax_advice": "tax implications",
    "wrong_geography": "real estate rules in another state",
    None: "this matter",
}


def _topic_phrase(state: RAGState) -> str:
    if state.get("escalation_reason") == "low_confidence":
        # Fall back to the raw query topic when we lack a classification.
        return state.get("query", "this matter").rstrip("?")
    return _TOPIC_PHRASES.get(state.get("_router_topic"), "this matter")


def escalation(state: RAGState) -> RAGState:
    state["answer"] = ESCALATION_TEMPLATE.format(topic=_topic_phrase(state))
    state["escalated"] = True
    state["source_citations"] = []
    state.setdefault("escalation_reason", "out_of_scope")
    _flag_for_agent_review(state)
    return state


def _flag_for_agent_review(state: RAGState) -> None:
    """Hook: push to the agent review queue (ticket, Slack, CRM, etc.).

    Left as a no-op stub for the scaffold; wire to your queue in production.
    """
    return None
