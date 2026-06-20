"""Publisher node — commits approved post to GitHub Pages and logs it."""
from __future__ import annotations

from datetime import datetime

from ...memory.post_log import log_post
from ...tools.publish_github import publish_post
from ..state import ContentAgentState


def publisher(state: ContentAgentState) -> dict:
    approved = state.get("approved_drafts", [])
    themes = state.get("themes", [])
    week = state.get("week", 0)
    errors = list(state.get("error_log", []))

    if not approved:
        errors.append("Publisher: no approved drafts to publish.")
        return {"published_url": None, "error_log": errors}

    # Publish the Substack draft to GitHub Pages; keep LinkedIn draft for manual posting
    substack_drafts = [d for d in approved if d.get("platform") == "substack"]
    target = substack_drafts[0] if substack_drafts else approved[0]

    concept = themes[0].get("concept", "post") if themes else "post"
    safe_slug = concept.lower().replace(" ", "-").replace("/", "-")[:50]
    date_prefix = datetime.utcnow().strftime("%Y-%m-%d")

    from ...config.settings import settings
    posts_dir = (settings.github_pages_posts_dir or "week3/githubpages").rstrip("/")
    filepath = f"{posts_dir}/{date_prefix}-week{week}-{safe_slug}.md"

    note_angle = themes[0].get("note_angle", "") if themes else ""
    front_matter = (
        f"---\ntitle: \"Week {week}: {concept}\"\n"
        f"date: {date_prefix}\n"
        f"layout: post\n---\n\n"
    )
    full_content = front_matter + target["content"]

    published_url: str | None = None
    try:
        published_url = publish_post(
            content=full_content,
            filepath=filepath,
            commit_message=f"Week {week} build-in-public post: {concept}",
        )
        log_post(week=week, concept=concept, angle=note_angle, url=published_url)
    except Exception as exc:
        errors.append(f"Publish failed (draft preserved): {exc}")

    return {"published_url": published_url, "error_log": errors}
