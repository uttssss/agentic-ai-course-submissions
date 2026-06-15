"""Typed state passed through every LangGraph node (PRD §4)."""
from __future__ import annotations

from typing import TypedDict


class Document(TypedDict):
    """A retrieved chunk with its metadata (see ingest/metadata.py)."""
    chunk_id: str
    text: str
    metadata: dict


class RAGState(TypedDict, total=False):
    query: str
    user_geo: dict                      # {"state": "GA", "county": "Fulton"}
    session_id: str
    route: str                          # "retrieve" | "escalate"
    retrieved_chunks: list[Document]
    reranked_chunks: list[tuple[Document, float]]
    top_score: float
    answer: str
    escalated: bool
    escalation_reason: str              # "out_of_scope" | "low_confidence"
    source_citations: list[str]
    latency_ms: dict                    # {node_name: milliseconds}
