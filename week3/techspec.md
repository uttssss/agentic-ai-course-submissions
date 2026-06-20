# Technical Specification — Build-in-Public Content Agent

## 1. Overview

An agentic content pipeline that turns a week's course materials, personal notes, and project repo into approved, source-grounded LinkedIn and Substack posts. It replaces the 2–3 hours spent re-reading slides and writing from scratch each week.

The agent's core move is pairing **what I learned** (a concept from the course) with **what I built** (the project feature that applied it), anchored by my own notes so the output carries my synthesis rather than a lecture summary. Drafts are grounded via RAG, reviewed by a critic agent, and only published on explicit human approval — the system would rather hold a post than publish a weak or ungrounded one.

---

## 2. System Architecture

```
User (Streamlit)
      │
      ▼
LangGraph StateGraph (ContentAgentState)
      │
      ├─► ingest ──────────────────────────► Pinecone (3 namespaces)
      │         └── LlamaParse / GitHub API
      │
      ├─► planner ─────────────────────────► openai/gpt-oss-120b via Nebius + post_log memory
      │
      ├─► retriever ───────────────────────► Pinecone dense + BM25 sparse
      │
      ├─► generator ───────────────────────► openai/gpt-oss-120b via Nebius (LinkedIn + Substack)
      │
      ├─► critic ──────────────────────────► openai/gpt-oss-120b via Nebius (score 0–5)
      │      └── (fail) ──► bump_revision ──► generator  (max 2 retries)
      │
      ├─► human_gate ──────────────────────► interrupt() — Streamlit review UI
      │      ├── approve ──► publisher
      │      ├── regenerate ──► bump_revision ──► generator
      │      └── reject ──► END
      │
      └─► publisher ───────────────────────► GitHub Contents API + post_log
```

All data flows through a single typed `ContentAgentState` dict. Nodes are pure functions that return partial state updates.

---

## 3. Source Corpora

Three source types, each ingested into a separate Pinecone namespace per week (`content-{type}-w{week}`):

| Source | Content | Namespace |
|---|---|---|
| Course materials | Lecture slides (PDF), docs, transcripts | `content-course-w{N}` |
| Personal notes | My notes, reactions, questions for the week | `content-notes-w{N}` |
| Project repo | GitHub README + code fetched via Contents API | `content-project-w{N}` |

The planner connects all three: concept from slides → framed through notes → paired with project evidence.

---

## 4. Ingest Pipeline (`ingest_node`)

```
materials_paths / notes_paths / github_repo
        │
        ├─► LlamaParse (PDF layout mode) or direct read (.md)
        ├─► chunk_document (ATX-header-aware, 512 tok / 50 tok overlap)
        ├─► Nebius embed (Qwen/Qwen3-Embedding-8B, 4096-dim)
        └─► Pinecone upsert (namespace per source type)

github_repo ──► GitHub Contents API ──► README text ──► same pipeline
```

Failures are caught per-file: a parse failure skips that file, appends to `error_log`, and continues.

---

## 5. LangGraph Pipeline

Seven nodes + one pass-through counter node, compiled once with a `MemorySaver` checkpointer.

### 5.1 ingest
Parses all three source types and upserts chunks into Pinecone. Returns `ingest_namespaces` (mapping of source type → namespace name) and `github_readme`.

### 5.2 planner
LLM call (Nebius, temperature 0.3, JSON mode) that extracts 2–3 **Themes** — each a `{concept, note_angle, build_evidence}` triple. Injects:
- Top-5 chunks from course and notes namespaces as grounding context
- `past_themes_summary()` from `memory/post_log.py` to avoid repeating prior angles

### 5.3 retriever
Hybrid retrieval per theme:
1. **Dense** — Pinecone ANN across all three namespaces, top-`retrieve_top_k` (default 15)
2. **Sparse** — BM25 query over a per-week pickle index, filtered by `week`
3. Merge, deduplicate, cap at `retrieve_top_k`

Returns `retrieved_context`: dict mapping `theme.concept → [chunk_text, ...]`.

### 5.4 generator
Two LLM calls (Nebius, temperature 0.7) — one per platform:
- **LinkedIn**: 150–300 words, hook-driven, first-person, concept + build pairing, ends with a question
- **Substack**: 500–900 words, sectioned (Hook → Learned → Built → Insight → Next), conversational

Prior critic feedback is injected into the user prompt on revision rounds.

### 5.5 critic
Two LLM calls (Nebius, temperature 0.0, JSON mode) — one per draft. Scores each on four axes (0–5 each):

| Axis | What it checks |
|---|---|
| `tone_fit` | Platform-appropriate style (length, hook, structure) |
| `grounding` | Every factual claim traceable to retrieved context |
| `concept_build_pairing` | Concept explicitly linked to build evidence |
| `non_repetition` | Fresh angle vs. past published posts |

`overall` = mean of the four scores. If `overall < critic_pass_threshold` (default 3.5) **and** `critic_revision_count < max_critic_revisions` (default 2), routes to `bump_revision → generator`. Otherwise forwards to `human_gate`.

### 5.6 bump_revision
Single-line pass-through node that increments `critic_revision_count`. Keeps the counter side-effect out of both the critic and the generator.

### 5.7 human_gate
Calls `langgraph.types.interrupt()` — pauses graph execution and surfaces the current drafts, themes, and critic scores to the Streamlit UI. No write action fires before this clears.

Resumption payload: `{"decision": "approve" | "regenerate" | "reject", "edited_drafts": [...] | None}`

### 5.8 publisher
On approval:
1. Selects the Substack draft (falls back to first draft)
2. Builds a Jekyll front-matter header (`title`, `date`, `layout: post`)
3. Commits to `GITHUB_PAGES_REPO` at `GITHUB_PAGES_POSTS_DIR/YYYY-MM-DD-week{N}-{slug}.md` via GitHub Contents API
4. Logs `{week, concept, angle, url, published_at}` to `data/post_log.json`
5. Returns the rendered GitHub Pages URL

Publish failure is caught and surfaced as a warning — the draft is preserved in state.

---

## 6. State Schema (`agent/state.py`)

```python
class Theme(TypedDict):
    concept: str        # e.g. "confidence gating in RAG"
    note_angle: str     # author's own synthesis
    build_evidence: str # project feature that applied the concept

class Draft(TypedDict):
    platform: str       # "linkedin" | "substack"
    content: str
    critic_score: float
    critic_feedback: str
    revision_count: int

class ContentAgentState(TypedDict, total=False):
    week: int
    materials_paths: list[str]
    notes_paths: list[str]
    github_repo: str
    github_readme: str
    ingest_namespaces: dict        # {source_type: namespace}
    themes: list[Theme]
    retrieved_context: dict        # {concept: [chunk_text]}
    drafts: list[Draft]
    critic_revision_count: int
    human_decision: str            # "approve" | "regenerate" | "reject"
    edited_drafts: list[Draft] | None
    approved_drafts: list[Draft]
    published_url: str | None
    error_log: list[str]
```

---

## 7. Tools

| Tool | File | Type | What it does |
|---|---|---|---|
| `parse_document` | `ingest/parse.py` | READ | LlamaParse layout mode for PDF; direct read for .md |
| `chunk_document` | `ingest/chunk.py` | READ | ATX-header-aware section split → sliding window |
| `embed_texts` | `ingest/embed.py` | READ | Qwen3-Embedding-8B via Nebius OpenAI-compatible endpoint |
| `PineconeStore.query` | `stores/pinecone_client.py` | READ | Dense ANN retrieval across namespaces |
| `BM25 query` | `agent/nodes/retriever.py` | READ | Sparse keyword retrieval from pickle index |
| `fetch_github_readme` | `tools/fetch_github.py` | READ | GitHub Contents API — fetch project README |
| `publish_post` | `tools/publish_github.py` | WRITE | GitHub Contents API — commit post to Pages repo |

---

## 8. Memory (`memory/post_log.py`)

Flat JSON log at `data/post_log.json`. Each entry: `{week, concept, angle, url, published_at}`.

- **Read**: `past_themes_summary()` injects the last 10 entries into the planner prompt to block angle repetition
- **Write**: `log_post()` appends on successful publish

The same Pinecone index is reused for semantic memory (future: vector search over past posts to detect near-duplicate angles at retrieval time).

---

## 9. Configuration (`config/settings.py`)

| Key | Default | Purpose |
|---|---|---|
| `embedding_model` | `Qwen/Qwen3-Embedding-8B` | Alibaba Qwen3 embedding model hosted on Nebius (4096-dim) |
| `generation_model` | `openai/gpt-oss-120b` | 120B open-source model hosted on Nebius Token Factory; used for planner, generator, and critic |
| `pinecone_index` | `realestate-copilot` | Shared Pinecone index (separate namespaces) |
| `embedding_dim` | 4096 | Vector dimension |
| `chunk_size_tokens` | 512 | Max tokens per chunk |
| `chunk_overlap_tokens` | 50 | Sliding window overlap |
| `retrieve_top_k` | 15 | Candidates per retrieval pass |
| `dense_weight` | 0.6 | Hybrid blend (sparse = 1 − dense_weight) |
| `critic_pass_threshold` | 3.5 | Minimum overall critic score to pass |
| `max_critic_revisions` | 2 | Max generator retries before surfacing anyway |
| `github_pages_posts_dir` | `_posts` | Target folder in Pages repo |

---

## 10. Web UI (`app/content_agent_app.py`)

Five-phase Streamlit state machine:

| Phase | What happens |
|---|---|
| `input` | User enters week, GitHub repo, uploads materials + notes PDFs |
| `running` | `app.invoke(initial_state)` runs the graph; spinner blocks until interrupt |
| `review` | Drafts, themes, and critic scores surfaced; user edits inline if needed |
| `publishing` | `app.invoke(Command(resume=payload))` resumes the graph |
| `done` | Published URL displayed; LinkedIn draft surfaced for manual posting |

The `MemorySaver` checkpointer is stored in `st.session_state` so the graph thread persists across Streamlit rerenders. Each session gets a unique `thread_id`.

---

## 11. Key Design Decisions

**Why `interrupt()` instead of a separate approval step?**
LangGraph's `interrupt()` pauses the graph mid-execution and preserves full state in the checkpointer. Resuming with `Command(resume=...)` replays from the exact pause point. This means the publisher node only ever runs after the human gate clears — there's no way to accidentally skip it.

**Why a bounded critic loop rather than an agent loop?**
An unbounded "keep revising until perfect" loop would spin indefinitely on weak source material. Capping at `max_critic_revisions=2` means the agent surfaces the best draft it can produce in at most three passes, then hands off. The human gate is the final quality check — not the critic.

**Why separate Pinecone namespaces per source type and week?**
Retrieval across all three sources for a single theme query would drown notes (sparse, personal) in course slides (dense, verbose). Querying all three namespaces simultaneously lets the retriever pull proportionally from each. Week-scoped namespaces prevent Week 2 material from contaminating Week 3 themes.

**Why log past posts in JSON rather than vector search?**
For 10–20 posts, exact-match injection into the planner prompt is faster, cheaper, and more predictable than a semantic similarity search. The vector approach becomes worthwhile once the archive grows large enough that the prompt injection exceeds context limits.

**Why commit the Substack draft to Pages and surface LinkedIn for manual posting?**
Publishing to GitHub Pages is the autonomous write action that demonstrates the human-in-the-loop boundary — it's real and irreversible (modulo a git revert), which is why it requires explicit approval. LinkedIn's API requires OAuth app review for posting; manual copy-paste keeps the demo self-contained without an approval-gated API integration.
