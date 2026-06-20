"""Retriever node — hybrid dense+sparse retrieval per theme."""
from __future__ import annotations

from ...config.settings import settings
from ...stores.pinecone_client import PineconeStore
from ..state import ContentAgentState


def retriever(state: ContentAgentState) -> dict:
    themes = state.get("themes", [])
    namespaces = state.get("ingest_namespaces", {})
    errors = list(state.get("error_log", []))

    store = PineconeStore()
    all_namespaces = list(namespaces.values())
    retrieved: dict[str, list[str]] = {}

    for theme in themes:
        concept = theme.get("concept", "")
        build = theme.get("build_evidence", "")
        angle = theme.get("note_angle", "")
        query = f"{concept} {angle} {build}"

        chunks: list[str] = []

        if all_namespaces:
            try:
                hits = store.query(query, all_namespaces, {}, settings.retrieve_top_k)
                chunks = [h["text"] for h in hits if h["text"].strip()]
            except Exception as exc:
                errors.append(f"Dense retrieval failed for '{concept}': {exc}")

        # Sparse BM25 pass — supplement dense hits with keyword-matched chunks
        bm25_texts = _bm25_query(query, namespaces, state.get("week", 0))
        seen = set(chunks)
        for t in bm25_texts:
            if t not in seen:
                chunks.append(t)
                seen.add(t)

        retrieved[concept] = chunks[:settings.retrieve_top_k]

    return {"retrieved_context": retrieved, "error_log": errors}


def _bm25_query(query: str, namespaces: dict, week: int) -> list[str]:
    """Best-effort BM25 retrieval; returns [] on any failure."""
    try:
        import re
        import pickle
        from pathlib import Path

        index_path = Path(__file__).resolve().parents[3] / "data" / "content_bm25.pkl"
        if not index_path.exists():
            return []
        with open(index_path, "rb") as f:
            data = pickle.load(f)

        model = data.get("model")
        records = data.get("records", [])
        if model is None:
            return []

        tokens = re.findall(r"[a-z0-9]+", query.lower())
        scores = model.get_scores(tokens)
        ranked = sorted(zip(records, scores), key=lambda t: t[1], reverse=True)
        out = []
        for rec, score in ranked:
            if rec.get("week") == week and score > 0:
                out.append(rec["text"])
            if len(out) >= 10:
                break
        return out
    except Exception:
        return []
