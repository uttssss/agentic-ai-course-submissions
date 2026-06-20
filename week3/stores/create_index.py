"""Create the Pinecone serverless index if it doesn't already exist.

Idempotent: safe to run repeatedly. Reads name/dim from config.settings and
cloud/region from env (defaults: aws / us-east-1).

Usage:
    python -m copilot.stores.create_index
"""
from __future__ import annotations

import os
import time

from ..config.settings import settings


def create_index() -> None:
    from pinecone import Pinecone, ServerlessSpec

    if not settings.pinecone_api_key:
        raise SystemExit("PINECONE_API_KEY is not set — add it to your .env first.")

    pc = Pinecone(api_key=settings.pinecone_api_key)
    name = settings.pinecone_index

    existing = {ix["name"] for ix in pc.list_indexes()}
    if name in existing:
        print(f"Index '{name}' already exists — nothing to do.")
        return

    cloud = os.environ.get("PINECONE_CLOUD", "aws")
    region = os.environ.get("PINECONE_REGION", "us-east-1")

    print(f"Creating serverless index '{name}' "
          f"(dim={settings.embedding_dim}, metric=cosine, {cloud}/{region})…")
    pc.create_index(
        name=name,
        dimension=settings.embedding_dim,   # 1536 for text-embedding-3-small
        metric="cosine",
        spec=ServerlessSpec(cloud=cloud, region=region),
    )

    # Wait until the index reports ready.
    while not pc.describe_index(name).status.get("ready", False):
        time.sleep(1)
    print(f"Index '{name}' is ready.")


if __name__ == "__main__":
    create_index()
