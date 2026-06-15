"""On-upload ingestion of a user's executed purchase agreement (PRD §2, spec §7.2).

Parses instantly, writes to namespace session-{session_id}, and triggers an
immediate vector-space refresh for that transaction session only. Blocks
contract-specific answers until ingestion is confirmed complete.
"""
from __future__ import annotations

from pathlib import Path

from .chunk import chunk_document
from .embed import embed_texts
from .metadata import build_metadata, make_chunk_id
from .parse import parse_document
from ..stores.pinecone_client import PineconeStore


def ingest_user_contract(file_path: str | Path, session_id: str, user_geo: dict) -> dict:
    """Return IngestResult: {chunks_indexed, failed, session_id}."""
    file_path = Path(file_path)
    markdown = parse_document(file_path)
    chunks = chunk_document(markdown)

    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts)

    upserts, failed = [], []
    for idx, (chunk, vec) in enumerate(zip(chunks, vectors)):
        try:
            md = build_metadata(
                state=user_geo["state"], county=user_geo["county"],
                document_type="user_agreement", source_document=file_path.name,
                section_header=chunk["section_header"], page=None,
                is_date_bearing=chunk["is_date_bearing"], session_id=session_id,
                text=chunk["text"],
            )
        except Exception as e:  # metadata validation failure
            failed.append({"idx": idx, "error": str(e)})
            continue
        cid = make_chunk_id(user_geo["state"], file_path.name, chunk["section_header"], idx)
        upserts.append({"id": cid, "values": vec, "metadata": md})

    PineconeStore().upsert(upserts, namespace=f"session-{session_id}")
    return {"chunks_indexed": len(upserts), "failed": failed, "session_id": session_id}
