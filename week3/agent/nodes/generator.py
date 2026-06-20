"""Generator node — drafts platform-specific posts grounded in retrieved context."""
from __future__ import annotations

from functools import lru_cache

from ...config.settings import settings
from ..state import ContentAgentState, Draft


@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI
    return OpenAI(api_key=settings.nebius_api_key, base_url=settings.nebius_base_url)


_LINKEDIN_SYSTEM = """You are a ghostwriter for a PM building in public. Write a LinkedIn post that:
- Opens with a punchy, specific hook (no "I" as first word, no emoji walls)
- Tells a tight first-person story: what I learned → what I built → why it matters
- Pairs exactly one concept with one concrete build example (the "concept + build" structure)
- Cites specific details from the provided context; never invent facts or statistics
- Ends with a genuine question or observation to invite discussion
- Stays between 150 and 300 words
- Uses short paragraphs (1–3 sentences each)
- Avoids corporate jargon, hustle-culture clichés, and empty superlatives"""

_SUBSTACK_SYSTEM = """You are a ghostwriter for a PM building in public. Write a Substack post that:
- Has a clear H2 section structure: Hook → What I learned → What I built → The key insight → What's next
- Pairs the concept with the specific build evidence in the "What I built" section
- Cites every factual claim to the provided context; no invented statistics
- Reads as genuine synthesis (author's own take), not a lecture summary
- Stays between 500 and 900 words
- Uses approachable, conversational prose — not a listicle"""


def generator(state: ContentAgentState) -> dict:
    themes = state.get("themes", [])
    retrieved = state.get("retrieved_context", {})
    prior_drafts = state.get("drafts", [])
    errors = list(state.get("error_log", []))

    if not themes:
        errors.append("Generator: no themes to write about.")
        return {"drafts": [], "error_log": errors}

    # Use the top theme; if regenerating, critic feedback is in prior_drafts
    theme = themes[0]
    concept = theme.get("concept", "")
    note_angle = theme.get("note_angle", "")
    build_evidence = theme.get("build_evidence", "")
    context_chunks = retrieved.get(concept, [])
    context_text = "\n---\n".join(context_chunks[:8]) if context_chunks else "(no grounding context available)"

    # Gather prior critic feedback for this round
    feedback_note = ""
    for d in prior_drafts:
        if d.get("critic_feedback"):
            feedback_note += f"\nPrior critic feedback ({d['platform']}): {d['critic_feedback']}"

    user_prompt = f"""Week concept: {concept}
My angle (from my notes): {note_angle}
Build evidence (what I shipped): {build_evidence}

Grounding context (cite from this, do not invent):
{context_text}
{feedback_note}

Write the post now. Do not add any preamble or meta-commentary."""

    drafts: list[Draft] = []
    revision_count = state.get("critic_revision_count", 0)

    for platform, system in [("linkedin", _LINKEDIN_SYSTEM), ("substack", _SUBSTACK_SYSTEM)]:
        try:
            resp = _client().chat.completions.create(
                model=settings.generation_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
            )
            content = resp.choices[0].message.content.strip()
        except Exception as exc:
            errors.append(f"Generator LLM call failed ({platform}): {exc}")
            content = f"[Draft generation failed: {exc}]"

        drafts.append(Draft(
            platform=platform,
            content=content,
            critic_score=0.0,
            critic_feedback="",
            revision_count=revision_count,
        ))

    return {"drafts": drafts, "error_log": errors}
