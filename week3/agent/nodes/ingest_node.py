"""Ingest node — parses course materials, notes, and GitHub project into Pinecone."""
from __future__ import annotations

from pathlib import Path

from ...ingest.chunk import chunk_document
from ...ingest.embed import embed_texts
from ...ingest.parse import parse_document
from ...stores.pinecone_client import PineconeStore
from ...tools.fetch_github import fetch_github_readme
from ..state import ContentAgentState


def ingest_node(state: ContentAgentState) -> dict:
    week = state.get("week", 0)
    errors = list(state.get("error_log", []))
    namespaces: dict[str, str] = {}
    store = PineconeStore()

    def _ingest_files(paths: list[str], source_type: str) -> None:
        if not paths:
            return
        ns = f"content-{source_type}-w{week}"
        namespaces[source_type] = ns
        vectors = []
        for path in paths:
            try:
                text = parse_document(path)
                chunks = chunk_document(text)
                texts = [c["text"] for c in chunks]
                embeddings = embed_texts(texts)
                stem = Path(path).stem
                for i, (chunk, vec) in enumerate(zip(chunks, embeddings)):
                    vectors.append({
                        "id": f"{stem}-{source_type}-w{week}-{i}",
                        "values": vec,
                        "metadata": {
                            "text": chunk["text"],
                            "week": week,
                            "source_type": source_type,
                            "source": Path(path).name,
                        },
                    })
            except Exception as exc:
                errors.append(f"Parse failed for {path}: {exc}")
        if vectors:
            store.upsert(vectors, namespace=ns)

    _ingest_files(state.get("materials_paths", []), "course")
    _ingest_files(state.get("notes_paths", []), "notes")

    # Fetch and ingest GitHub README as project evidence
    readme = ""
    repo = state.get("github_repo", "")
    if repo:
        try:
            readme = fetch_github_readme(repo)
            if readme:
                chunks = chunk_document(readme)
                texts = [c["text"] for c in chunks]
                embeddings = embed_texts(texts)
                ns = f"content-project-w{week}"
                namespaces["project"] = ns
                vectors = [
                    {
                        "id": f"readme-w{week}-{i}",
                        "values": vec,
                        "metadata": {
                            "text": c["text"],
                            "week": week,
                            "source_type": "project",
                            "source": f"{repo}/README",
                        },
                    }
                    for i, (c, vec) in enumerate(zip(chunks, embeddings))
                ]
                store.upsert(vectors, namespace=ns)
        except Exception as exc:
            errors.append(f"GitHub fetch failed for {repo} (retrying not possible): {exc}")

    return {
        "ingest_namespaces": namespaces,
        "github_readme": readme,
        "error_log": errors,
    }
