# Technical Specification — Real Estate Transaction Copilot

## 1. Overview

A production-grade RAG copilot that answers first-time homebuyer questions about
contract deadlines and contingencies. Answers are grounded strictly in official
state/county/HOA guidelines plus the buyer's uploaded purchase agreement.
Queries outside that scope — legal advice, personal recommendations, tax questions,
or wrong-geography questions — are refused and routed to a human agent.

---

## 2. System Architecture

```
User (Streamlit) ──► LangGraph Graph ──► Nebius (GPT-4o / Qwen3-Embedding-8B)
                           │
              ┌────────────┴─────────────┐
              │                          │
         Pinecone                      BM25
      (dense, serverless)           (sparse, local)
```

The runtime path is a compiled LangGraph `StateGraph`. All data flows through a
single typed `RAGState` dict; nodes are pure functions that mutate and return it.

---

## 3. Ingest Pipeline

Documents enter through two paths:

**Base corpus** (`make ingest` / `ingest/batch_base_corpus.py`)
Offline, run annually or when guidelines change.

**User contract** (`ingest/ingest_user_contract.py`)
Triggered on PDF upload in the Streamlit UI; stored in an ephemeral session namespace.

Both paths follow the same five stages:

| Stage | Module | Detail |
|---|---|---|
| Parse | `ingest/parse.py` | LlamaParse layout mode for PDFs; Markdown files read directly |
| Clean | `ingest/clean.py` | Normalises whitespace, strips boilerplate, flags date-bearing sections |
| Chunk | `ingest/chunk.py` | ATX-header-aware section split → sliding window (512 tok / 50 tok overlap) |
| Embed | `ingest/embed.py` | `Qwen/Qwen3-Embedding-8B` via Nebius OpenAI-compatible endpoint; 4096-dim vectors |
| Store | `stores/` | Dense → Pinecone; sparse → BM25 index |

Sidecar `.meta.json` files alongside each base-corpus document carry structured
metadata (state, county, document type, source title) that is written into
Pinecone vector metadata at upsert time.

---

## 4. Storage Layer

### Dense store — Pinecone serverless (`stores/pinecone_client.py`)

- Index: `realestate-copilot`, 4096-dim, cosine similarity.
- **Geographic isolation via namespaces**: base corpus sharded by state
  (`base-GA`, `base-FL`, …); user contracts isolated by session (`session-{id}`).
- Metadata filter `{"state": user_state}` applied **before** vector math at the
  DB layer, preventing cross-jurisdiction leakage.
- Session namespaces are deleted via `delete_session()` after a session ends.

### Sparse store — BM25 (`stores/bm25_index.py`)

- Local index; queried with an `allowed_states` set for geographic isolation.
- Scores are unbounded; normalised before blending (see §5.2).

---

## 5. LangGraph Pipeline

Six nodes, compiled once (`lru_cache`) and reused across requests.

```
START
  └─► query_router
        ├─► (out-of-scope / wrong-geo) ──► escalation ──► END
        └─► (in-scope) ──► retriever ──► reranker ──► confidence_gate
                                                         ├─► (score ≥ 0.75) ──► generator ──► END
                                                         └─► (score < 0.75)  ──► escalation ──► END
```

Per-node wall-clock latency is recorded in `state["latency_ms"]` by a `_timed`
wrapper in `graph/build.py`.

### 5.1 query_router

Keyword + regex classifier (no LLM call). Two checks in order:

1. **Topical scope**: patterns for legal advice (`sue`, `lawsuit`), personal
   recommendations (`should I waive/accept/…`), and tax questions. Positive match
   → `route = "escalate"`, `escalation_reason = "out_of_scope"`.
2. **Geographic mismatch**: detects a US state mentioned in the query; if it
   differs from `user_geo.state` → escalate with `_router_topic = "wrong_geography"`.

In-scope queries set `route = "retrieve"`.

### 5.2 retriever — hybrid retrieval (`graph/nodes/retriever.py`)

Two-stage hybrid:

1. **Dense**: Pinecone ANN over `base-{state}` + (optionally) `session-{id}` namespaces, top-15.
2. **Sparse**: BM25 query over the same geo-scoped corpus, top-15.
3. **Blend**: both score maps are **min-max normalised** independently to `[0, 1]`,
   then combined as `dense_weight × dense + (1 − dense_weight) × sparse`.
   Default `dense_weight = 0.6` (empirically tuned via `make tune`).
4. Top-15 blended candidates passed to reranker.

### 5.3 reranker (`graph/nodes/reranker.py`)

Cross-encoder `BAAI/bge-reranker-large` scores each (query, chunk) pair.
Raw logits are converted to 0–1 relevance probabilities via sigmoid so the
confidence gate threshold operates on a consistent scale.
Output: `reranked_chunks` sorted descending + `top_score` (sigmoid of best logit).

### 5.4 confidence_gate (`graph/nodes/gate.py`)

Pure routing: `top_score >= confidence_threshold` (default 0.75) → `"generate"`,
otherwise → `"escalate"` with `escalation_reason = "low_confidence"`.
No model calls; no side effects.

### 5.5 generator (`graph/nodes/generator.py`)

Calls GPT-4o via Nebius at `temperature=0.0`.

**Deadline pre-computation**: before the LLM call, the generator deterministically
extracts the binding date and named contractual periods (Due Diligence, Counteroffer
Response) from user-contract chunks and computes exact calendar deadlines using
`utils/dates.py`. These are injected into the context as authoritative facts so
the LLM narrates pre-calculated dates rather than doing arithmetic itself.

System prompt hard rules:
- Answer **only** from provided context chunks; never invent facts.
- Cite `[source_document §section_header]` for every factual claim.
- Show deadline arithmetic explicitly when a date is implied.
- Stitch statutory baseline rules with the buyer's personal contract dates.

### 5.6 escalation (`graph/nodes/escalation.py`)

Returns canned refusal copy from `ESCALATION_TEMPLATE` (config). Calls a stub
`_flag_for_agent_review()` hook — wire to your ticketing / CRM queue in production.
Never calls the LLM.

---

## 6. State Schema (`graph/state.py`)

```python
class RAGState(TypedDict, total=False):
    query: str
    user_geo: dict            # {"state": "GA", "county": "Fulton"}
    session_id: str
    route: str                # "retrieve" | "escalate" | "generate"
    retrieved_chunks: list[Document]
    reranked_chunks: list[tuple[Document, float]]
    top_score: float
    answer: str
    escalated: bool
    escalation_reason: str    # "out_of_scope" | "low_confidence"
    source_citations: list[str]
    latency_ms: dict          # {node_name: ms}
```

---

## 7. Configuration (`config/settings.py`)

Frozen dataclass; all secrets via environment variables (`.env`).

| Key | Default | Tunable |
|---|---|---|
| `embedding_model` | `Qwen/Qwen3-Embedding-8B` | No |
| `generation_model` | `gpt-4o` | No |
| `reranker_model` | `BAAI/bge-reranker-large` | No |
| `embedding_dim` | 4096 | No |
| `chunk_size_tokens` | 512 | Yes |
| `chunk_overlap_tokens` | 50 | Yes |
| `retrieve_top_k` | 15 | Yes |
| `dense_weight` | 0.6 | Yes — `make tune` |
| `confidence_threshold` | 0.75 | Yes — `make tune` |

---

## 8. Evaluation & Quality Targets

| Metric | Target | Harness |
|---|---|---|
| Faithfulness | ≥ 98% | `eval/ragas_eval.py` (RAGAS) |
| Answer relevance | ≥ 95% | `eval/ragas_eval.py` (RAGAS) |
| Refusal accuracy | 100% | `eval/refusal_eval.py` |
| Retrieval MRR | ~0.77 (shipped) | `make tune` |
| P95 latency | ≤ 4 s | `state["latency_ms"]` aggregation |

The 15-question evaluation set covers: date calculation, multi-document stitching,
edge cases (expired deadlines, waiver detection), and refusals (legal, advice, tax,
wrong-geography).

`make tune` sweeps `dense_weight` across `[0.0, 0.2, …, 1.0]` and recommends a
`confidence_threshold` with margin. Results written to `eval/tuning_results.json`.

---

## 9. Web UI (`app/streamlit_app.py`)

- PDF upload widget → calls `ingest.ingest_user_contract` on-the-fly, stores in
  `session-{id}` namespace.
- Chat input → `graph.build.run_graph(query, user_profile, session_id)`.
- Renders answer, source citations, and escalation status.

---

## 10. Key Design Decisions

**Why hybrid retrieval?** Keyword (BM25) catches exact clause references ("Section
12B"); dense catches semantic paraphrases. Min-max normalisation before blending
is required because BM25 scores are unbounded while cosine similarity is ~0–1.

**Why a cross-encoder reranker?** Bi-encoder retrieval optimises embedding
similarity, not query–passage relevance. The cross-encoder sees both together and
produces more accurate relevance scores for the confidence gate.

**Why pre-compute deadlines?** LLMs are unreliable at calendar arithmetic. Injecting
pre-calculated dates as authoritative context facts drives the faithfulness score
above the 98% target.

**Why keyword-based routing instead of an LLM classifier?** Adds ~0ms latency,
zero cost, and zero hallucination risk for the scope gate. The patterns are narrow
enough that false-positive rates are low on homebuying queries. Replace with an
LLM or fine-tuned intent model if scope needs to widen.

**Why Pinecone namespaces for isolation?** Metadata filters alone are a soft
guarantee; namespace partitioning is enforced at the infrastructure level, so a
misconfigured filter cannot leak cross-jurisdiction documents.
