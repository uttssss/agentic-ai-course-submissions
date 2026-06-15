"""Debug harness: run each answerable eval case and print answer + top retrieved chunks."""
from __future__ import annotations

from .dataset import EVAL_USER_GEO, answerable_cases
from ..graph.build import build_graph


def main() -> None:
    app = build_graph()
    for case in answerable_cases():
        final = app.invoke({
            "query": case.question,
            "user_geo": EVAL_USER_GEO,
            "session_id": "eval",
        })
        print(f"\n{'='*70}")
        print(f"{case.id}: {case.question}")
        print(f"\nANSWER:\n{final.get('answer', '')}")
        chunks = final.get("reranked_chunks", [])[:3]
        if chunks:
            print("\nTOP CHUNKS:")
            for i, (chunk, score) in enumerate(chunks, 1):
                src = chunk["metadata"].get("source_document", "?")
                print(f"  [{i}] {src}  score={score:.3f}")
                print(f"      {chunk['text'][:300]}")


if __name__ == "__main__":
    main()
