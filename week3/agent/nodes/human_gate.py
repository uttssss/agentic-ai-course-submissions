"""Human-gate node — LangGraph interrupt; no write action fires before this clears."""
from __future__ import annotations

from langgraph.types import interrupt

from ..state import ContentAgentState


def human_gate(state: ContentAgentState) -> dict:
    """Pause execution and surface drafts for human review.

    The interrupt payload is what the Streamlit UI reads to show the user.
    Resumption expects: {"decision": "approve"|"regenerate"|"reject", "edited_drafts": [...] | None}
    """
    decision: dict = interrupt({
        "drafts": state.get("drafts", []),
        "themes": state.get("themes", []),
        "critic_revision_count": state.get("critic_revision_count", 0),
        "error_log": state.get("error_log", []),
    })

    human_decision = decision.get("decision", "reject")
    edited = decision.get("edited_drafts")

    updates: dict = {
        "human_decision": human_decision,
        "edited_drafts": edited,
    }

    if human_decision == "approve":
        approved = edited if edited else state.get("drafts", [])
        updates["approved_drafts"] = approved

    return updates


def gate_decision(state: ContentAgentState) -> str:
    """Conditional edge after human_gate."""
    decision = state.get("human_decision", "reject")
    if decision == "approve":
        return "publish"
    if decision == "regenerate":
        return "regenerate"
    return "end"
