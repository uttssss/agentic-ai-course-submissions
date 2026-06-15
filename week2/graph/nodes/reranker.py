"""reranker node (PRD §5.3).

Cross-encoder (bge-reranker-large) scores each of the 15 candidates against the
query. Emits (chunk, relevancy_score) tuples sorted descending and writes the
top score to state.top_score — the sole input to the confidence gate.
"""
from __future__ import annotations

import math
from functools import lru_cache

from ...config.settings import settings
from ..state import RAGState


@lru_cache(maxsize=1)
def _model():
    # Lazy import keeps the graph importable without heavy deps installed.
    from sentence_transformers import CrossEncoder
    return CrossEncoder(settings.reranker_model)


def _sigmoid(x: float) -> float:
    """Map a cross-encoder logit to a 0-1 relevance probability.

    bge-reranker-large emits raw logits, not probabilities. The confidence gate
    compares against a 0-1 threshold (0.75), so scores MUST be sigmoid-normalized
    or the gate — and refusal accuracy — is meaningless (review fix #1).
    """
    # Numerically stable for large-magnitude logits.
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def reranker(state: RAGState) -> RAGState:
    candidates = state.get("retrieved_chunks", [])
    if not candidates:
        state["reranked_chunks"] = []
        state["top_score"] = 0.0
        return state

    pairs = [(state["query"], c["text"]) for c in candidates]
    logits = _model().predict(pairs)  # raw cross-encoder logits
    scores = [_sigmoid(float(s)) for s in logits]  # -> 0-1 probabilities

    ranked = sorted(zip(candidates, scores), key=lambda t: t[1], reverse=True)
    state["reranked_chunks"] = ranked
    state["top_score"] = ranked[0][1]
    return state
