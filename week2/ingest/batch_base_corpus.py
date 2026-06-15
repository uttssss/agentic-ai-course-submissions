"""Offline batch job: ingest the base corpus (PRD §2 — annual refresh).

Reads every file under data/base_corpus/, parses -> cleans -> chunks -> embeds ->
tags metadata -> upserts to Pinecone (namespace base-{state}) and builds the BM25
index. A sidecar JSON per document supplies its {state, county, document_type}.

Usage:
    python -m copilot.ingest.batch_base_corpus
"""
from __future__ import annotations

import json
from pathlib import Path

from .chunk import chunk_document
from .embed import embed_texts
from .metadata import build_metadata, make_chunk_id
from .parse import parse_document
from ..stores.bm25_index import BM25Index
from ..stores.pinecone_client import PineconeStore

CORPUS_DIR = Path(__file__).resolve().parent.parent / "data" / "base_corpus"


def _load_sidecar(doc_path: Path) -> dict:
    """Each document foo.md has foo.meta.json: {state, county, document_type}."""
    meta_path = doc_path.with_suffix(".meta.json")
    if not meta_path.exists():
        raise FileNotFoundError(f"missing sidecar metadata: {meta_path.name}")
    return json.loads(meta_path.read_text())


def ingest_file(doc_path: Path, store: PineconeStore) -> list[dict]:
    sidecar = _load_sidecar(doc_path)
    markdown = parse_document(doc_path)
    chunks = chunk_document(markdown)

    texts = [c["text"] for c in chunks]
    vectors_raw = embed_texts(texts)

    records, upserts = [], []
    for idx, (chunk, vec) in enumerate(zip(chunks, vectors_raw)):
        cid = make_chunk_id(sidecar["state"], doc_path.name, chunk["section_header"], idx)
        md = build_metadata(
            state=sidecar["state"], county=sidecar["county"],
            document_type=sidecar["document_type"], source_document=doc_path.name,
            section_header=chunk["section_header"], page=None,
            is_date_bearing=chunk["is_date_bearing"], session_id=None,
            text=chunk["text"],
        )
        records.append({"chunk_id": cid, "text": chunk["text"], "metadata": md})
        upserts.append({"id": cid, "values": vec, "metadata": md})

    store.upsert(upserts, namespace=f"base-{sidecar['state']}")
    return records


def main() -> None:
    store = PineconeStore()
    all_records: list[dict] = []
    files = sorted(p for p in CORPUS_DIR.glob("*") if p.suffix in {".md", ".pdf"})
    for path in files:
        recs = ingest_file(path, store)
        all_records.extend(recs)
        print(f"ingested {path.name}: {len(recs)} chunks")
    BM25Index().build(all_records)
    print(f"done: {len(all_records)} chunks across {len(files)} documents")


if __name__ == "__main__":
    main()
