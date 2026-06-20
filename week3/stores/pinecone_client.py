"""Pinecone serverless wrapper (PRD §3, §4.3).

- Namespace-per-state for the base corpus (base-GA, base-FL, ...).
- Namespace-per-session for uploaded user contracts (session-{id}).
- Metadata filter applied BEFORE vector math at the DB layer (geo isolation §5.3).
"""
from __future__ import annotations

from functools import lru_cache

from ..config.settings import settings
from ..ingest.embed import embed_query


@lru_cache(maxsize=1)
def _index():
    from pinecone import Pinecone
    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index)


class PineconeStore:
    def upsert(self, vectors: list[dict], namespace: str) -> None:
        """vectors: [{id, values, metadata}, ...]"""
        _index().upsert(vectors=vectors, namespace=namespace)

    def query(self, query: str, namespaces: list[str], metadata_filter: dict,
              top_k: int) -> list[dict]:
        vec = embed_query(query)
        hits: list[dict] = []
        for ns in namespaces:
            res = _index().query(
                vector=vec, top_k=top_k, namespace=ns,
                filter=metadata_filter, include_metadata=True,
            )
            # QueryResponse supports __getitem__ across client versions; .get may
            # not exist on it (review fix #6).
            for m in (res["matches"] or []):
                hits.append({
                    "chunk_id": m["id"],
                    "score": float(m["score"]),
                    "text": m["metadata"].get("text", ""),
                    "metadata": m["metadata"],
                })
        return hits

    def delete_session(self, session_id: str) -> None:
        _index().delete(delete_all=True, namespace=f"session-{session_id}")
