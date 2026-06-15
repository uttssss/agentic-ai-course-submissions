"""Embeddings via text-embedding-3-small on Nebius (PRD §3)."""
from __future__ import annotations

from functools import lru_cache

from ..config.settings import settings


@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI
    return OpenAI(api_key=settings.nebius_api_key, base_url=settings.nebius_base_url)


def embed_texts(texts: list[str]) -> list[list[float]]:
    resp = _client().embeddings.create(model=settings.embedding_model, input=texts)
    return [d.embedding for d in resp.data]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
