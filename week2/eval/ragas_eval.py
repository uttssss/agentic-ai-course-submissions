"""RAGAS faithfulness + relevance evaluation (PRD §6.1).

Scores answerable cases (Q1-Q11) via RAGAS over graph runs. Targets:
faithfulness >= 0.98, answer_relevancy >= 0.95. Also checks that
expects_calculated_date cases contain a concrete calendar date.
"""
from __future__ import annotations

import re

from .dataset import EVAL_USER_GEO, answerable_cases
from ..config.settings import settings
from ..graph.build import build_graph

_DATE_RE = re.compile(
    r"\b(?:january|february|march|april|may|june|july|august|september|october|"
    r"november|december)\s+\d{1,2},?\s+\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    re.IGNORECASE,
)


def _collect_runs() -> list[dict]:
    """Execute each answerable case, capturing answer + retrieved contexts."""
    app = build_graph()
    runs = []
    for case in answerable_cases():
        state = {"query": case.question, "user_geo": EVAL_USER_GEO, "session_id": "eval"}
        final = app.invoke(state)
        contexts = [d["text"] for d, _ in final.get("reranked_chunks", [])]
        runs.append({
            "id": case.id,
            "question": case.question,
            "answer": final.get("answer", ""),
            "contexts": contexts,
            "expects_date": case.expects_calculated_date,
        })
    return runs


def _score_with_ragas(runs: list[dict]) -> dict:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, faithfulness

    ds = Dataset.from_dict({
        "question": [r["question"] for r in runs],
        "answer": [r["answer"] for r in runs],
        "contexts": [r["contexts"] for r in runs],
    })
    result = evaluate(ds, metrics=[faithfulness, answer_relevancy])
    return {k: float(v) for k, v in result.items()}


def run() -> dict:
    runs = _collect_runs()

    date_checks = [
        {"id": r["id"], "has_date": bool(_DATE_RE.search(r["answer"]))}
        for r in runs if r["expects_date"]
    ]
    date_pass = all(d["has_date"] for d in date_checks)

    try:
        scores = _score_with_ragas(runs)
    except Exception as e:   # RAGAS deps / keys missing in dev
        scores = {"error": str(e)}

    return {
        "scores": scores,
        "targets": {"faithfulness": settings.target_faithfulness,
                    "answer_relevancy": settings.target_relevance},
        "calculated_date_check": {"all_pass": date_pass, "details": date_checks},
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
