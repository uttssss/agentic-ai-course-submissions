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

    # --- Retrieval / chunking ---
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 50
    retrieve_top_k: int = 15
    dense_weight: float = 0.6

    # --- PDF parsing ---
    llamaparse_api_key: str | None = field(default_factory=lambda: _env("LLAMA_CLOUD_API_KEY"))

    # --- GitHub (publishing + project ingestion) ---
    github_token: str | None = field(default_factory=lambda: _env("GITHUB_TOKEN"))
    github_pages_repo: str | None = field(default_factory=lambda: _env("GITHUB_PAGES_REPO"))
    github_pages_posts_dir: str = field(default_factory=lambda: _env("GITHUB_PAGES_POSTS_DIR", "_posts"))

    # --- Critic / revision ---
    critic_pass_threshold: float = 3.5
    max_critic_revisions: int = 2


settings = Settings()
