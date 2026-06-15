"""query_router node (PRD §5.6).

Classifies scope and extracts geographic context. Out-of-scope queries are
short-circuited to escalation BEFORE any retrieval runs. Wrong-state queries are
caught here so the geographic isolation filter blocks them pre-retrieval (Q15).
"""
from __future__ import annotations

import re

from ..state import RAGState

# Lightweight keyword signals. In production, replace with an LLM classifier
# (still cheap) or a fine-tuned intent model.
_OUT_OF_SCOPE = {
    "legal_advice": [r"\bsue\b", r"\blawsuit\b", r"\bcan i sue\b"],
    # Advice-SEEKING only. "should i <decision verb>" avoids false-positives on
    # benign timing questions like "when should I expect the appraisal?" (fix #7).
    "advice": [
        r"\bshould i\s+(?:waive|accept|offer|sign|agree|back\s+out|skip|drop|remove|counter|reject)\b",
        r"\bdo you recommend\b", r"\bwhat would you do\b",
        r"\bis it a good idea\b", r"\bwhat do you (?:think|suggest)\b",
    ],
    "tax_advice": [r"\btax\b", r"\btaxes\b", r"\bdeduction\b", r"\bwrite[- ]off\b"],
}

# US state names / abbreviations we may detect in a query.
_STATE_TOKENS = {
    "california": "CA", "ca": "CA", "georgia": "GA", "ga": "GA",
    "florida": "FL", "fl": "FL", "texas": "TX", "tx": "TX",
}


def _detect_query_state(query: str) -> str | None:
    q = query.lower()
    for token, abbr in _STATE_TOKENS.items():
        if re.search(rf"\b{re.escape(token)}\b", q):
            return abbr
    return None


def query_router(state: RAGState) -> RAGState:
    query = state["query"]
    user_state = state.get("user_geo", {}).get("state")

    # 1. Topical out-of-scope (legal / advice / tax).
    for reason, patterns in _OUT_OF_SCOPE.items():
        if any(re.search(p, query.lower()) for p in patterns):
            state["route"] = "escalate"
            state["escalation_reason"] = "out_of_scope"
            state["_router_topic"] = reason
            return state

    # 2. Geographic mismatch — wrong state asked about (Q15).
    mentioned = _detect_query_state(query)
    if mentioned and user_state and mentioned != user_state:
        state["route"] = "escalate"
        state["escalation_reason"] = "out_of_scope"
        state["_router_topic"] = "wrong_geography"
        return state

    # 3. In scope -> retrieval path.
    state["route"] = "retrieve"
    return state
