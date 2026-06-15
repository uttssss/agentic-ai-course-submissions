"""Graph wiring (PRD §4 / §6.2).

START -> query_router
query_router    -> retriever   (route == "retrieve")
query_router    -> escalation  (route == "escalate")
retriever       -> reranker
reranker        -> confidence_gate
confidence_gate -> generator   (top_score >= 0.75)
confidence_gate -> escalation  (top_score <  0.75)
generator       -> END
escalation      -> END
"""
from __future__ import annotations

import time
from functools import lru_cache

from .nodes.escalation import escalation
from .nodes.gate import confidence_gate, gate_decision
from .nodes.generator import generator
from .nodes.reranker import reranker
from .nodes.retriever import retriever
from .nodes.router import query_router
from .state import RAGState


def _timed(name, fn):
    """Wrap a node so per-node latency lands in state.latency_ms (PRD §6.3)."""
    def wrapped(state: RAGState) -> RAGState:
        t0 = time.perf_counter()
        out = fn(state)
        out.setdefault("latency_ms", {})[name] = round((time.perf_counter() - t0) * 1000, 1)
        return out
    return wrapped


def build_graph():
    """Compile and return the LangGraph app."""
    from langgraph.graph import END, START, StateGraph

    g = StateGraph(RAGState)
    g.add_node("query_router", _timed("query_router", query_router))
    g.add_node("retriever", _timed("retriever", retriever))
    g.add_node("reranker", _timed("reranker", reranker))
    g.add_node("confidence_gate", _timed("confidence_gate", confidence_gate))
    g.add_node("generator", _timed("generator", generator))
    g.add_node("escalation", _timed("escalation", escalation))

    g.add_edge(START, "query_router")
    g.add_conditional_edges(
        "query_router", lambda s: s["route"],
        {"retrieve": "retriever", "escalate": "escalation"},
    )
    g.add_edge("retriever", "reranker")
    g.add_edge("reranker", "confidence_gate")
    g.add_conditional_edges(
        "confidence_gate", gate_decision,
        {"generate": "generator", "escalate": "escalation"},
    )
    g.add_edge("generator", END)
    g.add_edge("escalation", END)
    return g.compile()


@lru_cache(maxsize=1)
def get_graph():
    """Compile once and reuse — avoids rebuilding the graph on every query
    (review fix #4)."""
    return build_graph()


def run_graph(query: str, user_profile: dict, session_id: str | None = None) -> dict:
    """Convenience entrypoint returning a RAGResponse-shaped dict (spec §7.1)."""
    app = get_graph()
    state: RAGState = {
        "query": query,
        "user_geo": {"state": user_profile["state"], "county": user_profile.get("county")},
        "session_id": session_id,
    }
    final = app.invoke(state)
    return {
        "answer": final.get("answer", ""),
        "escalated": final.get("escalated", False),
        "escalation_reason": final.get("escalation_reason"),
        "citations": final.get("source_citations", []),
        "top_score": final.get("top_score", 0.0),
        "latency_ms": sum(final.get("latency_ms", {}).values()),
    }
