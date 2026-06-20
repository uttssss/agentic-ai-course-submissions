"""Structure-aware semantic chunking (PRD §2).

Bounded by document section markers; ~512 tokens with 50-token overlap. Section
boundaries take precedence so a single clause is never split mid-rule.
"""
from __future__ import annotations

import re

from ..config.settings import settings
from .clean import clean_text, is_date_bearing

# Cheap token proxy: ~0.75 words/token -> approximate by word count * 1.33.
_WORDS_PER_TOKEN = 0.75


def _approx_tokens(text: str) -> int:
    return int(len(text.split()) / _WORDS_PER_TOKEN)


def _split_sections(markdown: str) -> list[tuple[str, str]]:
    """Split into (section_header, body) pairs on ATX headers."""
    parts = re.split(r"^(#{1,6}\s+.+)$", markdown, flags=re.MULTILINE)
    sections, header = [], "Document"
    # re.split keeps captured headers as separate items.
    buf = parts[0]
    if buf.strip():
        sections.append((header, buf))
    for i in range(1, len(parts), 2):
        header = re.sub(r"^#{1,6}\s+", "", parts[i]).strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        sections.append((header, body))
    return sections


def _window(text: str, size: int, overlap: int) -> list[str]:
    words = text.split()
    step = max(1, int((size - overlap) * _WORDS_PER_TOKEN))
    win = max(1, int(size * _WORDS_PER_TOKEN))
    return [" ".join(words[i:i + win]) for i in range(0, len(words), step)] or [text]


def chunk_document(markdown: str) -> list[dict]:
    """Return [{text, section_header, is_date_bearing}, ...]."""
    chunks = []
    for header, body in _split_sections(markdown):
        body = clean_text(body)
        if not body:
            continue
        pieces = (
            [body] if _approx_tokens(body) <= settings.chunk_size_tokens
            else _window(body, settings.chunk_size_tokens, settings.chunk_overlap_tokens)
        )
        for piece in pieces:
            piece = piece.strip()
            if piece:
                chunks.append({
                    "text": piece,
                    "section_header": header,
                    "is_date_bearing": is_date_bearing(piece),
                })
    return chunks
