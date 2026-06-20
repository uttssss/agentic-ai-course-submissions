"""Text cleaning (PRD §2).

Strips raw markdown noise while EXPLICITLY preserving date keys and section
headers, and flags date-bearing text.
"""
from __future__ import annotations

import re

# Matches "June 1, 2026", "06/01/2026", "10 days", "within 10 days", etc.
_DATE_RE = re.compile(
    r"\b("
    r"\d{1,2}/\d{1,2}/\d{2,4}"
    r"|(?:january|february|march|april|may|june|july|august|september|october|november|december)"
    r"\s+\d{1,2},?\s+\d{4}"
    r"|\d+\s+(?:calendar\s+)?days?"
    r")\b",
    re.IGNORECASE,
)


def clean_text(text: str) -> str:
    # Drop image tags and stray table pipes, collapse whitespace — but keep words.
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)      # markdown images
    text = re.sub(r"^\s*\|\s*[-:]+\s*\|.*$", "", text, flags=re.MULTILINE)  # md table rules
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_date_bearing(text: str) -> bool:
    return bool(_DATE_RE.search(text))


def extract_section_headers(markdown: str) -> list[tuple[str, int]]:
    """Return [(header_text, char_offset), ...] for markdown ATX headers."""
    out = []
    for m in re.finditer(r"^#{1,6}\s+(.+)$", markdown, flags=re.MULTILINE):
        out.append((m.group(1).strip(), m.start()))
    return out
