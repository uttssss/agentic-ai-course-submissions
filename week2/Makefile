# Real Estate Contract Copilot — dev tasks.
# Run from the copilot/ directory: `make help`

ROOT := $(abspath ..)

# Prefer uv when available: `uv run` executes inside the project venv created by
# `uv sync`. Falls back to plain python3 otherwise. Either way PYTHONPATH points
# at the parent so `import copilot...` resolves.
# Prefer uv when available. `--no-sync` means run targets use the venv built by
# `make install` (uv sync) without re-resolving/downloading on every call — run
# `make install` first. Falls back to plain python3 when uv isn't installed.
UV := $(shell command -v uv 2>/dev/null)
ifeq ($(UV),)
  PY := PYTHONPATH="$(ROOT)" python3
else
  PY := PYTHONPATH="$(ROOT)" uv run --no-sync python3
endif

.DEFAULT_GOAL := help
.PHONY: help install env create-index ingest ingest-contract run test test-unit eval eval-refusal eval-ragas tune compile clean

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install:  ## Install deps — uv sync if uv is present, else pip
	@if command -v uv >/dev/null 2>&1; then \
		echo "Using uv sync…"; uv sync --extra dev; \
	else \
		echo "uv not found — using pip…"; pip install -r requirements.txt && pip install pytest; \
	fi

env:  ## Create .env from the example (edit it afterwards)
	@test -f .env || cp .env.example .env && echo "Wrote .env — fill in your keys."

create-index:  ## Create the Pinecone serverless index (dim 1536, cosine) — idempotent
	$(PY) -m copilot.stores.create_index

ingest:  ## Ingest the base corpus into Pinecone + build BM25 index
	$(PY) -m copilot.ingest.batch_base_corpus

ingest-contract:  ## Ingest the sample executed agreement (session=demo-session)
	$(PY) -c "from copilot.ingest.ingest_user_contract import ingest_user_contract; \
		print(ingest_user_contract('data/user_contracts/Sample_Executed_Purchase_Agreement.md', \
		'demo-session', {'state':'GA','county':'Fulton'}))"

run:  ## Launch the Streamlit chat app
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH="$(ROOT)" uv run --no-sync streamlit run app/streamlit_app.py; \
	else \
		PYTHONPATH="$(ROOT)" streamlit run app/streamlit_app.py; \
	fi

test: test-unit  ## Alias for the unit suite

test-unit:  ## Run the pytest unit suite (no external keys needed)
	$(PY) -m pytest -q

debug-eval:  ## Print each Q1-Q11 answer + top-3 retrieved chunks with scores
	$(PY) -m copilot.eval.debug_eval

eval: eval-refusal eval-ragas  ## Run both eval harnesses (needs API keys)

eval-refusal:  ## Refusal-accuracy eval (PRD target 100%)
	$(PY) -m copilot.eval.refusal_eval

eval-ragas:  ## RAGAS faithfulness + relevance eval (Q1-Q11)
	$(PY) -m copilot.eval.ragas_eval

tune:  ## Sweep dense_weight + confidence_threshold against the eval set (needs ingest)
	$(PY) -m copilot.eval.tune

compile:  ## Byte-compile every module (fast sanity check)
	$(PY) -m compileall -q . && echo "compile OK"

clean:  ## Remove caches and build artifacts
	find . -type d -name __pycache__ -prune -exec rm -rf {} + ; \
	rm -rf .pytest_cache copilot/data/bm25_index.pkl
