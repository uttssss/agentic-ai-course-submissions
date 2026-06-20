# Build-in-Public Content Agent — dev tasks.
# Run from the week3/ directory: `make help`

ROOT := $(abspath ..)

UV := $(shell command -v uv 2>/dev/null)
ifeq ($(UV),)
  PY := PYTHONPATH="$(ROOT)" python3
else
  PY := PYTHONPATH="$(ROOT)" uv run --no-sync python3
endif

.DEFAULT_GOAL := help
.PHONY: help install env run-agent compile clean

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install:  ## Install deps — uv sync if uv is present, else pip
	@if command -v uv >/dev/null 2>&1; then \
		echo "Using uv sync…"; uv sync; \
	else \
		echo "uv not found — using pip…"; pip install -r requirements.txt; \
	fi

env:  ## Create .env from the example (edit it afterwards)
	@test -f .env || cp .env.example .env && echo "Wrote .env — fill in your keys."

run-agent:  ## Launch the Build-in-Public Content Agent
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH="$(ROOT)" uv run --no-sync streamlit run app/content_agent_app.py; \
	else \
		PYTHONPATH="$(ROOT)" streamlit run app/content_agent_app.py; \
	fi

compile:  ## Byte-compile every module (fast sanity check)
	$(PY) -m compileall -q . && echo "compile OK"

clean:  ## Remove caches and build artifacts
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
