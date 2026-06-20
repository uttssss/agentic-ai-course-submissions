"""LangGraph wiring for the Build-in-Public Content Agent (Week 3).

Graph:
  START
  └─► ingest ─► planner ─► retriever ─► generator ─► critic
                                                         │
                               ┌─────────────────────────┤
                               │ (score ≥ threshold       │ (score < threshold
                               │  OR max revisions)       │  AND revisions left)
                               ▼                          ▼
                          human_gate              bump_revision ─► generator (loop)
                               │
                    ┌──────────┼──────────┐
                    │          │          │
                  approve  regenerate  reject
                    │          │          │
                 publisher   bump_revision  END
                    │          └──────────►  generator (loop)
                    ▼
                   END
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes.critic import critic, critic_decision
from .nodes.generator import generator
from .nodes.human_gate import gate_decision, human_gate
from .nodes.ingest_node import ingest_node
from .nodes.planner import planner
from .nodes.publisher import publisher
from .nodes.retriever import retriever
from .state import ContentAgentState


def _bump_revision(state: ContentAgentState) -> dict:
    """Increment the revision counter before looping back to the generator."""
    return {"critic_revision_count": state.get("critic_revision_count", 0) + 1}


def build_content_graph(checkpointer=None):
    """Compile and return the content agent StateGraph app."""
    g = StateGraph(ContentAgentState)

    g.add_node("ingest", ingest_node)
    g.add_node("planner", planner)
    g.add_node("retriever", retriever)
    g.add_node("generator", generator)
    g.add_node("critic", critic)
    g.add_node("bump_revision", _bump_revision)
    g.add_node("human_gate", human_gate)
    g.add_node("publisher", publisher)

    g.add_edge(START, "ingest")
    g.add_edge("ingest", "planner")
    g.add_edge("planner", "retriever")
    g.add_edge("retriever", "generator")
    g.add_edge("generator", "critic")

    # Critic routes: forward to human_gate or loop back via bump_revision
    g.add_conditional_edges(
        "critic",
        critic_decision,
        {"human_gate": "human_gate", "revise": "bump_revision"},
    )
    g.add_edge("bump_revision", "generator")

    # Human gate routes: publish, regenerate (loop), or end
    g.add_conditional_edges(
        "human_gate",
        gate_decision,
        {"publish": "publisher", "regenerate": "bump_revision", "end": END},
    )
    g.add_edge("publisher", END)

    return g.compile(checkpointer=checkpointer or MemorySaver())


@lru_cache(maxsize=1)
def get_content_graph():
    """Singleton for non-Streamlit usage (no per-session checkpointing needed)."""
    return build_content_graph()
