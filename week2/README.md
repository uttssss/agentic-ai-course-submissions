# Localized Real Estate Transaction & Contract Copilot

RAG copilot that answers a first-time homebuyer's contract-deadline
and contingency questions, grounded strictly in official state/county/HOA guidelines
plus the buyer's executed purchase agreement — with a confidence gate that escalates
low-confidence and out-of-scope queries to a human agent. See the tech spec for full
design.

## Layout

```
copilot/
├── app/streamlit_app.py      # web chat + PDF upload
├── graph/                    # LangGraph state + 6 nodes + wiring
├── ingest/                   # parse → clean → chunk → embed → metadata
├── stores/                   # Pinecone (dense) + BM25 (sparse)
├── eval/                     # 15-question dataset + RAGAS + refusal harness
├── data/
│   ├── base_corpus/          # state/county/HOA guidelines (+ .meta.json sidecars)
│   └── user_contracts/       # sample executed agreement
├── config/settings.py        # thresholds, models, keys
├── pyproject.toml            # deps (uv) + pytest config
├── Makefile                  # install / ingest / run / test / eval / tune
└── requirements.txt          # pip fallback
```

## Setup

Dependencies are declared in `pyproject.toml` (with `requirements.txt` kept as a
pip fallback). The recommended path is [uv](https://docs.astral.sh/uv/):

```bash
make install                  # uv sync --extra dev if uv is present, else pip
make env                      # writes .env from the example — then fill in keys
```

Under the hood `make install` runs `uv sync --extra dev`, which creates a `.venv`
matching the lockfile (including pytest). The other `make` targets then run
through `uv run --no-sync`, so they reuse that venv without re-resolving. Run
`make install` again after changing dependencies.

Manual equivalents if you prefer not to use Make:

```bash
uv sync --extra dev                       # or: pip install -r requirements.txt && pip install pytest
cp .env.example .env                       # Nebius / Pinecone / LlamaParse keys
```

## Create the vector index

```bash
# One-time, idempotent. Creates the Pinecone serverless index (dim 1536, cosine).
make create-index        # or: python -m copilot.stores.create_index
```

## Ingest

```bash
# Base corpus (offline, annual). Reads data/base_corpus/*.md + .meta.json sidecars,
# upserts to Pinecone namespace base-{state}, and builds the BM25 index.
make ingest              # or: python -m copilot.ingest.batch_base_corpus
```

A user's contract is ingested on upload via `ingest.ingest_user_contract`
(namespace `session-{id}`), wired into the Streamlit upload widget.

## Run

```bash
streamlit run copilot/app/streamlit_app.py
```

## Evaluate (PRD §6 targets)

```bash
python -m copilot.eval.refusal_eval   # refusal accuracy (target 100%)
python -m copilot.eval.ragas_eval     # faithfulness ≥ 98%, relevance ≥ 95%
```

## Tune (after ingest)

```bash
# Sweeps dense_weight (hybrid blend) by retrieval recall/MRR and recommends a
# confidence_threshold that admits answerable cases with margin. Writes
# eval/tuning_results.json; apply the recommended values to config/settings.py.
make tune
```

The shipped defaults (`dense_weight=0.6`, `confidence_threshold=0.75`) are the
PRD starting points. Re-run `make tune` once the corpus is ingested to set them
empirically — the score-normalization fixes changed the scale they operate on.

> **Limitation — small tuning set.** Tuning runs against only the 15 eval
> questions over a 4-document sample corpus. The recommended `dense_weight` and
> `confidence_threshold` are directionally useful but **not statistically
> robust** — they can overfit this tiny set. Treat them as a starting point.
> For production, build a larger labeled retrieval set (50+ queries with
> ground-truth source docs) and re-run `make tune` before trusting the values.

## Sample data → eval mapping

The included Georgia/Fulton sample corpus + executed agreement (Binding Date
June 1 2026, 10-day due diligence, closing July 15 2026, financing deadline
July 8 2026) are calibrated so the 15 eval questions exercise every path:
date calculation, multi-document stitching, edge cases, and refusals.

## Notes

- Markdown corpus files are read directly so the pipeline runs without LlamaParse
  during development; real PDFs route through LlamaParse layout mode.
- Geographic isolation is enforced at the DB layer via Pinecone metadata filters
  and a state allow-list on the BM25 path.

## Resources
- [week2/eval/tuning_progress.md](https://github.com/uttssss/agentic-ai-course-submissions/blob/main/week2/eval/tuning_progress.md) : Refer for findings during tuning process
- https://github.com/uttssss/agentic-ai-course-submissions/blob/main/week2/eval/debug_eval_results.md: Refer for exact responses
