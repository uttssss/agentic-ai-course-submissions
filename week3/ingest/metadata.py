"""Metadata schema + validation (PRD §4.1, §5.3).

Geographic isolation is enforced at the DB layer, so every chunk MUST carry
complete metadata. Documents missing state / county / document_type fail
ingestion loudly — no silent defaults.
"""
from __future__ import annotations

import datetime as dt
import re

REQUIRED = ("state", "county", "document_type")
VALID_DOC_TYPES = {
    "state_contract_template", "county_zoning", "hoa_bylaws", "user_agreement",
}


class MetadataError(ValueError):
    pass


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def make_chunk_id(state: str, source_document: str, section_header: str, idx: int) -> str:
    return f"{state.lower()}_{_slug(source_document)}_{_slug(section_header)}_{idx:03d}"


def build_metadata(*, state: str, county: str, document_type: str,
                   source_document: str, section_header: str, page: int | None,
                   is_date_bearing: bool, session_id: str | None,
                   text: str) -> dict:
    md = {
        "state": state,
        "county": county,
        "document_type": document_type,
        "source_document": source_document,
        "section_header": section_header,
        "page": page,
        "is_date_bearing": is_date_bearing,
        "session_id": session_id,
        "ingested_at": dt.datetime.utcnow().isoformat() + "Z",
        "text": text,   # stored for retrieval display + BM25
    }
    validate(md)
    return {k: v for k, v in md.items() if v is not None}


def validate(md: dict) -> None:
    missing = [k for k in REQUIRED if not md.get(k)]
    if missing:
        raise MetadataError(f"chunk missing required metadata: {missing}")
    if md["document_type"] not in VALID_DOC_TYPES:
        raise MetadataError(f"invalid document_type: {md['document_type']!r}")
