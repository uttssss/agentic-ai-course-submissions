"""confidence_gate node (PRD §5.2).

Pure routing function on the rerank top score. No side effects, no model calls.
"""
from __future__ import annotations

from ...config.settings import settings
from ..state import RAGState


def confidence_gate(state: RAGState) -> RAGState:
    if state.get("top_score", 0.0) >= settings.confidence_threshold:
        state["route"] = "generate"
    else:
        state["route"] = "escalate"
        state["escalation_reason"] = "low_confidence"
    return state


def gate_decision(state: RAGState) -> str:
    """Conditional-edge selector used by the graph builder."""
    return state["route"]
