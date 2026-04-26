# SDD Tech Writer

Automated technical article generator. Given a tool (e.g. *Docker vs Podman*), the pipeline researches the web, extracts structured evidence, analyses it, drafts a long-form article, and iteratively critiques/rewrites it until quality criteria pass.

---

## Problem and solution

Writing a thorough, source-grounded technical article requires hours of research, synthesis, and self-review. SDD automates that loop:

1. **Research** — issues parallel search queries, scrapes content, indexes chunks in Chroma, and produces per-tool research snapshots.
2. **Evidence** — deterministically parses research into a structured `EvidencePack` (items, gaps, retained URLs) with no LLM involved.
3. **Analysis** — LLM synthesises the evidence pack into structured analysis, using only grounded facts.
4. **Writing** — LLM drafts the article from the analysis; `evidence_summary` is injected as volatile context after the cache breakpoint so prompt caching is effective.
5. **Critic** — validates structure, question coverage, and URL groundedness (any URL in the article must appear in the evidence pack); retries or enriches research on failure.

Orchestration is handled by **LangGraph** so the retry/enrichment flow is explicit and testable.

---

## Architecture

```
main.py
└── SDDPipeline (pipeline.py)
    └── LangGraphOrchestrator (orchestration/langgraph_runner.py)
        ├── research      ← ResearcherSkill  (skills/researcher.py)
        ├── evidence      ← EvidenceBuilderSkill (skills/evidence_builder.py)
        ├── analysis      ← AnalystSkill     (skills/analyst.py)
        ├── writer        ← WriterSkill      (skills/writer.py)
        ├── question_coverage  (deterministic check)
        ├── critic        ← CriticSkill      (skills/critic.py)
        ├── after_failure ← retry writer / enrich research+analysis
        └── finalize
```

### Key packages

| Package | Responsibility |
|---|---|
| `skills/` | One class per pipeline role; shared schemas in `skills/schemas.py` |
| `skills/evidence_builder.py` | Deterministic research→EvidencePack; no LLM |
| `pipeline_stages/` | Thin LangGraph node wrappers around each skill |
| `llm/` | Unified LLM client, provider config, circuit breaker, structured output |
| `memory/` | Chroma vector index + episodic memory JSON |
| `tools/` | Search, scraping (Crawl4AI), source ranker |
| `prompts/` | YAML template files loaded by `prompts/manager.py` |
| `validators/` | Spec/schema/template validators (fail-fast at startup) |
| `researcher_modules/` | Researcher internals (queries, scraping, context building) |
| `utils/` | Shared utilities: `logger.py`, observability scripts, text helpers |
| `evals/` | Batch eval runner + fixed dataset |
| `spec/` | `article_spec.yaml` + `schema.json` — runtime contract |

### Output artifacts (`output/`)

| File / dir | Contents |
|---|---|
| `pipeline_events.jsonl` | Structured event stream (one JSON per line) |
| `metrics.json` | Run metrics |
| `evidence_pack.json` | Structured evidence pack for the last run |
| `urls_*.txt` | Discovered URLs per tool |
| `debug_research_<tool>.md` | Raw research snapshot per tool |
| `debug_html_<tool>/` | HTML debug (only if `SDD_HTML_DEBUG=1`) |
| `chains/` | Tool chains + pipeline summaries |
| `evals/` | Batch eval reports, scores, events |

---

## Tech stack

- **Python 3.12** + **uv** (dependency management)
- **LangGraph** — pipeline orchestration and retry flow
- **Pydantic v2** — structured LLM outputs and internal contracts
- **Crawl4AI** — async/threaded web scraping
- **Chroma** — local vector store for semantic search and caching
- **Rich** — terminal output and progress
- **Ruff** — linting
- **pytest** — test suite (198 tests)

LLM providers supported (configurable in `.env`):

| Mode | Description |
|---|---|
| `openrouter_free` | OpenRouter free tier; automatic fallback to Ollama local |
| `ollama_local` | Local Ollama instance |

---

## Installation

```bash
# 1. Create and activate a virtual environment
uv venv --python 3.12
source .venv/bin/activate

# 2. Install dependencies
uv sync

# 3. Copy and fill in environment variables
cp .env.example .env
$EDITOR .env
```

---

## Environment variables (`.env`)

```env
# ── Provider ────────────────────────────────────────────────────────────────
# openrouter_free | ollama_local
LLM_PROVIDER=openrouter_free

# ── Models per role (required) ───────────────────────────────────────────────
LLM_MODEL_RESEARCHER=<model-id>
LLM_MODEL_ANALYST=<model-id>
LLM_MODEL_WRITER=<model-id>
LLM_MODEL_CRITIC=<model-id>

# ── OpenRouter ────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY=<your-key>
# OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# ── Fallback: if OpenRouter fails, fall back to local Ollama ─────────────────
# Global fallback model (all roles):
# LLM_MODEL_FALLBACK_LOCAL=qwen2.5:14b
# Per-role fallbacks:
# LLM_MODEL_RESEARCHER_FALLBACK_LOCAL=qwen2.5:14b-instruct-q5_K_M
# LLM_MODEL_ANALYST_FALLBACK_LOCAL=gemma4:26b
# LLM_MODEL_WRITER_FALLBACK_LOCAL=qwen3.6:35b
# LLM_MODEL_CRITIC_FALLBACK_LOCAL=deepseek-r1:14b
# LLM_MODEL_CRITIC_FAST=qwen2.5:7b-instruct-q5_K_M

# ── Ollama local ──────────────────────────────────────────────────────────────
# OLLAMA_LOCAL_BASE_URL=http://localhost:11434

# ── Chroma embeddings (optional) ─────────────────────────────────────────────
# CHROMA_EMBEDDING_PROVIDER=ollama
# CHROMA_EMBED_MODEL=nomic-embed-text:latest
# CHROMA_EMBED_OLLAMA_URL=http://localhost:11434

# ── Debug ─────────────────────────────────────────────────────────────────────
# SDD_HTML_DEBUG=1   # save raw HTML to output/debug_html_<tool>/

# ── LangSmith (optional tracing) ─────────────────────────────────────────────
# LANGSMITH_API_KEY=
# LANGSMITH_PROJECT=
# LANGSMITH_DATASET=
```

---

## Usage

### Run the pipeline

```bash
python main.py
python main.py --refresh-search          # force fresh web search
```

The CLI prompts for tool name (e.g. `Docker vs Podman`) and focus context, then runs the full pipeline. Articles are saved to `artigos/`.

### Monitor events in real time

```bash
# One-shot snapshot of all events
python -m utils.watch_events

# Filter by event type
python -m utils.watch_events url_found

# Show last 30 events
python -m utils.watch_events --tail=30

# Watch mode (refresh every 2s)
python -m utils.watch_events --watch

# Tail -f style (continuous stream)
python -m utils.watch_events --follow
```

### Chroma utilities

```bash
# Re-index historical research files into Chroma
python -m utils.repopulate_chroma

# Interactive query tester / integrity check
python -m utils.test_chroma_queries
```

### Batch evals

```bash
uv run python -m evals.batch_runner
uv run python -m evals.batch_runner --limit 2
uv run python -m evals.batch_runner --case-id docker_vs_podman_dev_linux
```

---

## Developer workflow

```bash
# Lint
uv run ruff check .

# Test suite (198 tests)
uv run pytest -q
```

---

## Spec and behaviour

Core behaviour is controlled by `spec/article_spec.yaml` (validated against `spec/schema.json`). Key settings:

| Key | Default | Notes |
|---|---|---|
| `pipeline.orchestration.backend` | `langgraph` | Must not change |
| `llm.context_length.{role}` | `16000` | Per-role context window |
| `llm.writer_input.max_research_chars` | `16000` | Research cap for writer |
| `llm.writer_input.max_analysis_chars` | `16000` | Analysis cap for writer |
| `llm.writer_input.max_correction_chars` | `4000` | Critic feedback cap |

---

## Maintenance notes

- Prefer editing `prompts/*.yaml` over hardcoding prompt strings in Python.
- When adding a new prompt template, integrate it in the flow and add validation tests.
- When changing spec keys, keep `spec/schema.json` in sync.
- `evidence_summary` must stay in the volatile section (after `<<<CACHE_BREAKPOINT>>>`) of `prompts/writer.yaml` — it contains run-specific URL data and must not be cached.
