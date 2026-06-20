"""retriever node (PRD §5.2).

Two-stage hybrid pipeline. Dense (Pinecone) + sparse (BM25) over the SAME
geo-scoped corpus, blended, top-15 returned. The Pinecone metadata filter is
applied BEFORE vector math at the database layer (geographic isolation, §5.3).
Merges the user's base-{state} namespace with the session-{id} namespace so the
generator can stitch statutory rules with the user's personal contract dates.
"""
from __future__ import annotations

from ...config.settings import settings
from ...stores.bm25_index import BM25Index
from ...stores.pinecone_client import PineconeStore
from ..state import RAGState

_pc = PineconeStore()
_bm25 = BM25Index()


def _normalize(scores: dict[str, float]) -> dict[str, float]:
    """Min-max normalize to [0, 1] so dense (cosine ~0-1) and sparse (BM25,
    unbounded) live on a comparable scale before blending (review fix #2)."""
    if not scores:
        return {}
    lo, hi = min(scores.values()), max(scores.values())
    if hi == lo:
        return {cid: 1.0 for cid in scores}  # all equal -> treat as full match
    span = hi - lo
    return {cid: (s - lo) / span for cid, s in scores.items()}


def _blend(dense: dict[str, float], sparse: dict[str, float], w: float) -> dict[str, float]:
    """Weighted-sum blend of independently normalized dense and sparse scores."""
    dn, sn = _normalize(dense), _normalize(sparse)
    ids = set(dn) | set(sn)
    return {cid: w * dn.get(cid, 0.0) + (1 - w) * sn.get(cid, 0.0) for cid in ids}


def retrieve_candidates(query: str, user_state: str, session_id: str | None = None,
                        dense_weight: float | None = None,
                        top_k: int | None = None) -> list[dict]:
    """Hybrid retrieval returning the blended top-k candidate chunks.

    Exposed (with overridable dense_weight/top_k) so the tuning harness can sweep
    the blend without mutating global settings.
    """
    w = settings.dense_weight if dense_weight is None else dense_weight
    k = settings.retrieve_top_k if top_k is None else top_k

    namespaces = [f"base-{user_state}"]
    if session_id:
        namespaces.append(f"session-{session_id}")
    metadata_filter = {"state": user_state}

    # Dense + sparse, scoped to geography at the DB layer.
    dense_hits = _pc.query(query, namespaces=namespaces,
                           metadata_filter=metadata_filter, top_k=k)
    sparse_hits = _bm25.query(query, allowed_states={user_state}, top_k=k)

    blended = _blend(
        {h["chunk_id"]: h["score"] for h in dense_hits},
        {h["chunk_id"]: h["score"] for h in sparse_hits},
        w,
    )
    docs_by_id = {h["chunk_id"]: h for h in (*dense_hits, *sparse_hits)}
    ranked_ids = sorted(blended, key=blended.get, reverse=True)[:k]
    return [docs_by_id[cid] for cid in ranked_ids]


def retriever(state: RAGState) -> RAGState:
    state["retrieved_chunks"] = retrieve_candidates(
        state["query"], state["user_geo"]["state"], state.get("session_id"),
    )
    return state
