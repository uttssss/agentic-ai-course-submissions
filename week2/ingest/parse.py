"""Layout-aware PDF parsing via LlamaParse (PRD §2).

Preserves multi-column financial grids, transaction dates, and reading order.
Markdown files (sample corpus) are read directly so the pipeline is runnable
without API keys during development.
"""
from __future__ import annotations

from pathlib import Path

from ..config.settings import settings


def parse_document(path: str | Path) -> str:
    """Return markdown-with-structure for a PDF or .md file."""
    path = Path(path)
    if path.suffix.lower() == ".md":
        return path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".pdf":
        return _parse_pdf(path)
    raise ValueError(f"Unsupported file type: {path.suffix}")


def _parse_pdf(path: Path) -> str:
    from llama_parse import LlamaParse
    parser = LlamaParse(
        api_key=settings.llamaparse_api_key,
        result_type="markdown",
        # layout mode keeps grids/dates ordered (PRD §2 ingestion)
        parsing_instruction=(
            "Preserve tables, multi-column financial grids, all dates, and section "
            "headers. Do not reorder content."
        ),
    )
    docs = parser.load_data(str(path))
    return "\n\n".join(d.text for d in docs)
