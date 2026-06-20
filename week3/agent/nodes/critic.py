"""Critic node — scores drafts and routes back to generator if they fail."""
from __future__ import annotations

import json
from functools import lru_cache

from ...config.settings import settings
from ..state import ContentAgentState, Draft


@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI
    return OpenAI(api_key=settings.nebius_api_key, base_url=settings.nebius_base_url)


_CRITIC_SYSTEM = """You are a strict content editor. Score a draft post on four criteria (each 0–5):
1. tone_fit: Does it match the platform's style? (LinkedIn: punchy/short; Substack: narrative/sectioned)
2. grounding: Are all factual claims supported by the provided context? No invented stats or vague claims.
3. concept_build_pairing: Does it clearly link one specific concept to one concrete build example?
4. non_repetition: Does it bring a fresh angle (given the past-posts list)?

Return JSON: {"scores": {"tone_fit": N, "grounding": N, "concept_build_pairing": N, "non_repetition": N}, "overall": N, "feedback": "one sentence of the most important thing to fix, or 'Approved' if score >= 3.5"}
Overall = mean of the four scores, rounded to 1 decimal."""


def critic(state: ContentAgentState) -> dict:
    drafts = state.get("drafts", [])
    retrieved = state.get("retrieved_context", {})
    themes = state.get("themes", [])
    errors = list(state.get("error_log", []))
    revision_count = state.get("critic_revision_count", 0)

    if not drafts:
        errors.append("Critic: no drafts to review.")
        return {"drafts": [], "critic_revision_count": revision_count, "error_log": errors}

    context_text = ""
    if themes:
        concept = themes[0].get("concept", "")
        chunks = retrieved.get(concept, [])
        context_text = "\n---\n".join(chunks[:5])

    from ...memory.post_log import past_themes_summary
    past = past_themes_summary()

    reviewed: list[Draft] = []
    for draft in drafts:
        platform = draft.get("platform", "")
        content = draft.get("content", "")
        rev = draft.get("revision_count", 0)

        try:
            resp = _client().chat.completions.create(
                model=settings.generation_model,
                messages=[
                    {"role": "system", "content": _CRITIC_SYSTEM},
                    {"role": "user", "content": (
                        f"Platform: {platform}\n\n"
                        f"Draft:\n{content}\n\n"
                        f"Grounding context:\n{context_text or '(none)'}\n\n"
                        f"Past published angles:\n{past}"
                    )},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            result = json.loads(resp.choices[0].message.content)
            score = float(result.get("overall", 0))
            feedback = result.get("feedback", "")
        except Exception as exc:
            errors.append(f"Critic LLM call failed ({platform}): {exc}")
            score = 5.0   # don't block on critic failure
            feedback = "Critic unavailable — passing through."

        reviewed.append(Draft(
            platform=platform,
            content=content,
            critic_score=score,
            critic_feedback=feedback,
            revision_count=rev,
        ))

    return {
        "drafts": reviewed,
        "critic_revision_count": revision_count,
        "error_log": errors,
    }


def critic_decision(state: ContentAgentState) -> str:
    """Conditional edge: route to generator for revision or forward to human_gate."""
    drafts = state.get("drafts", [])
    revision_count = state.get("critic_revision_count", 0)

    all_pass = all(
        d.get("critic_score", 0) >= settings.critic_pass_threshold
        for d in drafts
    )
    if all_pass or revision_count >= settings.max_critic_revisions:
        return "human_gate"
    return "revise"
