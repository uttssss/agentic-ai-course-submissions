"""Planner node — extracts 2-3 concept-to-build Themes from this week's materials."""
from __future__ import annotations

import json
from functools import lru_cache

from ...config.settings import settings
from ...stores.pinecone_client import PineconeStore
from ...memory.post_log import past_themes_summary
from ..state import ContentAgentState, Theme


@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI
    return OpenAI(api_key=settings.nebius_api_key, base_url=settings.nebius_base_url)


def planner(state: ContentAgentState) -> dict:
    week = state.get("week", 0)
    namespaces = state.get("ingest_namespaces", {})
    errors = list(state.get("error_log", []))

    store = PineconeStore()

    def _pull(query: str, ns_key: str, k: int = 5) -> str:
        ns = namespaces.get(ns_key)
        if not ns:
            return ""
        hits = store.query(query, [ns], {}, k)
        return "\n---\n".join(h["text"] for h in hits)

    course_ctx = _pull("key concepts, frameworks, and techniques taught this week", "course")
    notes_ctx = _pull("my insights, reactions, and what surprised me", "notes")
    project_ctx = state.get("github_readme", "") or _pull("what I built, shipped, and how it works", "project")

    past = past_themes_summary()

    prompt = f"""You are a content strategist for a PM building in public through a weekly AI bootcamp.

Your job: extract 2–3 post-worthy THEMES from this week's materials. Each theme must pair a CONCEPT from the course with the BUILD EVIDENCE (a specific feature or design choice from the project) that applied it, anchored by the author's own NOTE (their synthesis, not just a lecture summary).

The key structure for each theme:
- concept: a specific technical idea or framework from the course (not vague)
- note_angle: the author's own take — what surprised them, what trade-off they saw, what their "aha" moment was
- build_evidence: the specific thing they shipped that applied this concept (name the feature/node/design choice)

COURSE MATERIALS (what was taught):
{course_ctx or "(no course materials ingested)"}

PERSONAL NOTES (author's synthesis):
{notes_ctx or "(no notes ingested)"}

PROJECT README (what was built):
{project_ctx or "(no project content available)"}

PAST PUBLISHED POSTS (avoid repeating these angles):
{past}

Return a JSON object with a single key "themes" whose value is a list of 2–3 objects, each with keys: "concept", "note_angle", "build_evidence".
Example: {{"themes": [{{"concept": "confidence gating in RAG", "note_angle": "I learned that designing the refusal path first makes the happy path cleaner", "build_evidence": "the escalation node in my Week 2 RAG app that routes low-confidence retrievals to a human"}}]}}
"""

    try:
        resp = _client().chat.completions.create(
            model=settings.generation_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
        themes: list[Theme] = data.get("themes", [])[:3]
    except Exception as exc:
        errors.append(f"Planner LLM call failed: {exc}")
        themes = []

    return {"themes": themes, "error_log": errors}
