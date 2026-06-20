# Build-in-Public Content Agent

Agentic pipeline that turns a week's course materials, personal notes, and project repo into approved, source-grounded LinkedIn and Substack posts — replacing the 2–3 hours spent re-reading slides and writing from scratch.

The agent pairs what I learned with what I built, anchors every post on my own notes (not a lecture summary), runs a critic loop before surfacing drafts, and only publishes to GitHub Pages on explicit human approval.

## Layout

```
week3/
├── app/content_agent_app.py   # Streamlit UI — inputs, review gate, publish
├── agent/                     # LangGraph state machine (7 nodes)
│   ├── state.py               # ContentAgentState typed dict
│   ├── build.py               # graph wiring + MemorySaver checkpointer
│   └── nodes/
│       ├── ingest_node.py     # parse + embed course materials, notes, GitHub README
│       ├── planner.py         # LLM extracts 2–3 concept-to-build themes
│       ├── retriever.py       # hybrid Pinecone dense + BM25 sparse per theme
│       ├── generator.py       # LLM drafts LinkedIn + Substack posts
│       ├── critic.py          # LLM scores drafts; loops back up to 2x if failing
│       ├── human_gate.py      # LangGraph interrupt — nothing publishes before this
│       └── publisher.py       # commits approved post to GitHub Pages + logs it
├── tools/
│   ├── fetch_github.py        # GitHub Contents API — read project README
│   └── publish_github.py      # GitHub Contents API — commit post to Pages repo
├── memory/
│   └── post_log.py            # JSON log of past posts; prevents repeating angles
├── ingest/                    # parse → clean → chunk → embed (shared pipeline)
├── stores/                    # Pinecone (dense) + BM25 (sparse)
├── config/settings.py         # models, thresholds, API keys
├── pyproject.toml             # deps (uv) + pytest config
├── Makefile                   # install / run-agent / test
└── .env.example               # required environment variables
```

## How it works

```
START
└─► ingest ─► planner ─► retriever ─► generator ─► critic
                                                       │
                              ┌────────────────────────┤
                              │ pass (score ≥ 3.5)     │ fail (up to 2 retries)
                              ▼                        ▼
                         human_gate          bump_revision ─► generator
                              │
                   ┌──────────┼──────────┐
                 approve   regenerate  reject
                   │
                publisher ─► GitHub Pages + post log ─► END
```

Each theme is a **concept-to-build pairing**: a specific idea from the course, filtered through my own notes, linked to the project evidence that applied it.

## Setup

```bash
make install      # uv sync --extra dev  (or: pip install -r requirements.txt)
cp .env.example .env   # fill in keys
```

Required keys in `.env`:

| Variable | Purpose |
|---|---|
| `NEBIUS_API_KEY` | Embeddings + LLM generation (Nebius Token Factory) |
| `PINECONE_API_KEY` | Vector store |
| `LLAMA_CLOUD_API_KEY` | PDF parsing (LlamaParse) |
| `GITHUB_TOKEN` | Read project repo + commit to Pages (Contents: read/write) |
| `GITHUB_PAGES_REPO` | Target repo for publishing, e.g. `uttssss/agentic-ai-course-submissions` |
| `GITHUB_PAGES_POSTS_DIR` | Folder for posts, e.g. `_posts` |

## Run

```bash
make run-agent
# or: PYTHONPATH=.. streamlit run app/content_agent_app.py
```

## Usage

1. Enter the week number and your project's GitHub repo (`owner/repo`)
2. Upload course material PDFs/Markdown and your personal notes
3. Click **Run content agent →**
4. Review the planned themes and generated drafts (LinkedIn + Substack)
5. Edit inline if needed, then **Approve & publish** — commits the post to GitHub Pages and surfaces the LinkedIn draft for manual posting
