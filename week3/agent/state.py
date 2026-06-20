"""Typed state for the Build-in-Public Content Agent (Week 3)."""
from __future__ import annotations

from typing import TypedDict


class Theme(TypedDict):
    concept: str          # e.g. "confidence gating in RAG"
    note_angle: str       # author's own synthesis / point of view
    build_evidence: str   # project feature that applied the concept


class Draft(TypedDict):
    platform: str         # "linkedin" | "substack"
    content: str
    critic_score: float   # 0–5
    critic_feedback: str
    revision_count: int


class ContentAgentState(TypedDict, total=False):
    # --- Inputs ---
    week: int
    materials_paths: list[str]   # local paths to course material files (PDF/md)
    notes_paths: list[str]       # local paths to personal note files
    github_repo: str             # "owner/repo" of the week's project
    github_readme: str           # fetched README text

    # --- Ingestion ---
    ingest_namespaces: dict      # {source_type: pinecone_namespace}

    # --- Planning ---
    themes: list[Theme]          # 2–3 concept-to-build pairings

    # --- Retrieval ---
    retrieved_context: dict      # {theme_concept: [chunk_text, ...]}

    # --- Generation / critic ---
    drafts: list[Draft]
    critic_revision_count: int

    # --- Human gate ---
    human_decision: str          # "approve" | "regenerate" | "reject"
    edited_drafts: list[Draft] | None

    # --- Publishing ---
    approved_drafts: list[Draft]
    published_url: str | None

    # --- Diagnostics ---
    error_log: list[str]
