"""BM25 sparse index (PRD §3).

Persists a rank_bm25 model + the chunk records alongside the corpus. Supports a
state allow-list so sparse retrieval honors the same geographic isolation as the
dense path.
"""
from __future__ import annotations

import pickle
import re
from pathlib import Path

_INDEX_PATH = Path(__file__).resolve().parent.parent / "data" / "bm25_index.pkl"


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25Index:
    def __init__(self) -> None:
        self._model = None
        self._records: list[dict] = []
        if _INDEX_PATH.exists():
            self._load()

    def build(self, records: list[dict]) -> None:
        """records: [{chunk_id, text, metadata}, ...]"""
        from rank_bm25 import BM25Okapi
        self._records = records
        corpus = [_tokenize(r["text"]) for r in records]
        self._model = BM25Okapi(corpus)
        self._save()

    def query(self, query: str, allowed_states: set[str], top_k: int) -> list[dict]:
        if self._model is None:
            return []
        scores = self._model.get_scores(_tokenize(query))
        ranked = sorted(zip(self._records, scores), key=lambda t: t[1], reverse=True)
        out = []
        for rec, score in ranked:
            if rec["metadata"].get("state") not in allowed_states:
                continue   # honor geographic isolation
            out.append({"chunk_id": rec["chunk_id"], "score": float(score),
                        "text": rec["text"], "metadata": rec["metadata"]})
            if len(out) >= top_k:
                break
        return out

    def _save(self) -> None:
        _INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_INDEX_PATH, "wb") as f:
            pickle.dump({"model": self._model, "records": self._records}, f)

    def _load(self) -> None:
        # SECURITY: pickle.load executes arbitrary code on untrusted input. This
        # file is only ever written by build() in our own process (review fix #8).
        # Never point _INDEX_PATH at a file from an external/untrusted source.
        with open(_INDEX_PATH, "rb") as f:
            data = pickle.load(f)
        self._model, self._records = data["model"], data["records"]
