"""Central configuration. Values come from environment variables (see .env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


def _env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


@dataclass(frozen=True)
class Settings:
    # --- Model providers (Nebius Token Factory) ---
    nebius_api_key: str | None = field(default_factory=lambda: _env("NEBIUS_API_KEY"))
    nebius_base_url: str = field(default_factory=lambda: _env("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1"))
    nebius_embedding_base_url: str = field(default_factory=lambda: _env("NEBIUS_EMBEDDING_BASE_URL", "https://api.tokenfactory.nebius.com/v1"))
    embedding_model: str = "Qwen/Qwen3-Embedding-8B"
    generation_model: str = "openai/gpt-oss-120b"

    # --- Vector store ---
    pinecone_api_key: str | None = field(default_factory=lambda: _env("PINECONE_API_KEY"))
    pinecone_index: str = field(default_factory=lambda: _env("PINECONE_INDEX", "realestate-copilot"))
    embedding_dim: int = 4096

    # --- Reranker ---
    reranker_model: str = "BAAI/bge-reranker-large"

    # --- Retrieval / chunking ---
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 50
    retrieve_top_k: int = 15          # candidates before rerank
    dense_weight: float = 0.6         # hybrid score blend; sparse = 1 - dense_weight

    # --- Confidence gate (PRD §5.2) ---
    confidence_threshold: float = 0.45  # tuned: max reranker score on this corpus is ~0.73

    # --- PDF parsing ---
    llamaparse_api_key: str | None = field(default_factory=lambda: _env("LLAMA_CLOUD_API_KEY"))

    # --- Eval targets (PRD §6) ---
    target_faithfulness: float = 0.98
    target_relevance: float = 0.95
    target_refusal_accuracy: float = 1.0
    target_latency_p95_s: float = 4.0

    # --- Week 3: Build-in-Public Content Agent ---
    github_token: str | None = field(default_factory=lambda: _env("GITHUB_TOKEN"))
    github_pages_repo: str | None = field(default_factory=lambda: _env("GITHUB_PAGES_REPO"))
    # Folder inside github_pages_repo where posts land (e.g. "week3/githubpages" or "_posts")
    github_pages_posts_dir: str = field(default_factory=lambda: _env("GITHUB_PAGES_POSTS_DIR", "_posts"))
    critic_pass_threshold: float = 3.5   # minimum critic score (0–5) to pass
    max_critic_revisions: int = 2         # max generator retries before surfacing anyway


settings = Settings()

ESCALATION_TEMPLATE = (
    "I see you are asking about {topic}. Because this requires specific legal "
    "interpretation, I have flagged this message and forwarded it to your agent "
    "to review."
)
