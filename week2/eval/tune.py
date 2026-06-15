"""Hyperparameter tuning for retrieval blend + confidence gate.

Empirically re-tunes two knobs against the eval set:
  - dense_weight        — hybrid blend (dense vs BM25), by retrieval recall/MRR
  - confidence_threshold — the gate, so answerable cases pass with margin while
                           low-confidence retrievals still escalate

Requires the live stack (Pinecone + embeddings + reranker) and an ingested
corpus. Run after `make ingest`:

    python -m copilot.eval.tune

The pure metric helpers (recall_at_k, mrr, recommend_threshold) are unit-tested
offline; the sweep functions need API keys.
"""
from __future__ import annotations

import json
from pathlib import Path

from .dataset import EVAL_USER_GEO, answerable_cases
from ..config.settings import settings

DENSE_WEIGHT_GRID = [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0]
THRESHOLD_MARGIN = 0.05
_RESULTS_PATH = Path(__file__).resolve().parent / "tuning_results.json"


# ---------------------------------------------------------------- pure helpers
def recall_at_k(retrieved_sources: list[str], expected: tuple[str, ...]) -> float:
    """Fraction of expected source docs present in the retrieved set."""
    if not expected:
        return 1.0
    got = set(retrieved_sources)
    return sum(1 for e in expected if e in got) / len(expected)


def mrr(ranked_sources: list[str], expected: tuple[str, ...]) -> float:
    """Reciprocal rank of the first expected source in the ranked list."""
    for i, src in enumerate(ranked_sources, start=1):
        if src in expected:
            return 1.0 / i
    return 0.0


def recommend_threshold(answerable_scores: list[float], margin: float = THRESHOLD_MARGIN) -> float:
    """Largest threshold that still admits every answerable case, minus a margin.

    Keeps the gate as strict as possible (good for refusal accuracy) without
    wrongly escalating a question the corpus can actually answer.
    """
    if not answerable_scores:
        return settings.confidence_threshold
    floor = min(answerable_scores)
    return round(max(0.0, min(1.0, floor - margin)), 3)


# ----------------------------------------------------------------- live sweeps
def _sources_of(chunks: list[dict]) -> list[str]:
    return [c["metadata"].get("source_document", "?") for c in chunks]


def sweep_dense_weight(grid: list[float] | None = None) -> dict:
    """For each weight, average recall@k over answerable cases. Best = max recall,
    MRR (after rerank) as tiebreak."""
    from ..graph.nodes.retriever import retrieve_candidates
    from ..graph.nodes.reranker import _model, _sigmoid

    grid = grid or DENSE_WEIGHT_GRID
    cases = answerable_cases()
    rows = []
    for w in grid:
        recalls, mrrs = [], []
        for c in cases:
            cands = retrieve_candidates(c.question, EVAL_USER_GEO["state"],
                                        session_id="eval", dense_weight=w)
            recalls.append(recall_at_k(_sources_of(cands), c.expected_sources))
            # rerank to get the post-rerank ordering for MRR
            scores = [_sigmoid(float(s)) for s in
                      _model().predict([(c.question, x["text"]) for x in cands])]
            ranked = [x for x, _ in sorted(zip(cands, scores), key=lambda t: t[1], reverse=True)]
            mrrs.append(mrr(_sources_of(ranked), c.expected_sources))
        rows.append({"dense_weight": w,
                     "recall": round(sum(recalls) / len(recalls), 4),
                     "mrr": round(sum(mrrs) / len(mrrs), 4)})
    best = max(rows, key=lambda r: (r["recall"], r["mrr"]))
    return {"grid": rows, "best_dense_weight": best["dense_weight"]}


def collect_answerable_top_scores(dense_weight: float) -> list[float]:
    """Full retrieve+rerank top_score for each answerable case at the chosen weight."""
    from ..graph.nodes.retriever import retrieve_candidates
    from ..graph.nodes.reranker import _model, _sigmoid

    scores = []
    for c in answerable_cases():
        cands = retrieve_candidates(c.question, EVAL_USER_GEO["state"],
                                    session_id="eval", dense_weight=dense_weight)
        if not cands:
            scores.append(0.0)
            continue
        s = [_sigmoid(float(x)) for x in
             _model().predict([(c.question, x["text"]) for x in cands])]
        scores.append(max(s))
    return scores


def main() -> None:
    print("Sweeping dense_weight…")
    dw = sweep_dense_weight()
    for row in dw["grid"]:
        print(f"  w={row['dense_weight']:>3}  recall={row['recall']:.3f}  mrr={row['mrr']:.3f}")
    best_w = dw["best_dense_weight"]
    print(f"-> best dense_weight = {best_w}")

    print("\nCollecting confidence scores at best weight…")
    top_scores = collect_answerable_top_scores(best_w)
    rec_threshold = recommend_threshold(top_scores)
    print(f"  answerable top_scores: min={min(top_scores):.3f} "
          f"max={max(top_scores):.3f}")
    print(f"-> recommended confidence_threshold = {rec_threshold}")

    result = {
        "current": {"dense_weight": settings.dense_weight,
                    "confidence_threshold": settings.confidence_threshold},
        "recommended": {"dense_weight": best_w,
                        "confidence_threshold": rec_threshold},
        "dense_weight_sweep": dw["grid"],
        "answerable_top_scores": [round(s, 4) for s in top_scores],
    }
    _RESULTS_PATH.write_text(json.dumps(result, indent=2))
    print(f"\nWrote {_RESULTS_PATH.name}. Update config/settings.py with the "
          f"recommended values if they beat the current ones.")


if __name__ == "__main__":
    main()
