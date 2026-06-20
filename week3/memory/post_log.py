"""Persistent log of published posts — prevents week-over-week angle repetition."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

_LOG_PATH = Path(__file__).resolve().parents[1] / "data" / "post_log.json"


def _load() -> list[dict]:
    if _LOG_PATH.exists():
        try:
            return json.loads(_LOG_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save(entries: list[dict]) -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _LOG_PATH.write_text(json.dumps(entries, indent=2))


def get_past_themes() -> list[dict]:
    """Return all logged {week, concept, angle, url, published_at} entries."""
    return _load()


def log_post(week: int, concept: str, angle: str, url: str | None) -> None:
    """Append a published-post record to the log."""
    entries = _load()
    entries.append({
        "week": week,
        "concept": concept,
        "angle": angle,
        "url": url,
        "published_at": datetime.utcnow().isoformat(),
    })
    _save(entries)


def past_themes_summary() -> str:
    """Return a compact summary string for injection into planner prompts."""
    entries = _load()
    if not entries:
        return "None yet."
    lines = [
        f"Week {e['week']}: concept='{e['concept']}', angle='{e['angle']}'"
        for e in entries[-10:]  # last 10 posts
    ]
    return "\n".join(lines)
