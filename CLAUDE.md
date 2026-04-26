# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## Current Architecture

`main.py` collects user inputs and runs `SDDPipeline` (`pipeline.py`).

Pipeline stages (high-level):
1. `researcher` (`skills/researcher.py`)
2. `analyst` (`skills/analyst.py`)
3. `writer` (`skills/writer.py`)
4. `critic` (`skills/critic.py`)

LangGraph orchestration is handled by `orchestration/langgraph_runner.py` with explicit nodes:
- `research` → `analysis` → `writer`
- `question_coverage` (deterministic check before critic)
- `critic`
- `after_failure` (retry writer or enrich research/analysis)
- `finalize`

## Prompt System (Template-Driven)

Prompts are defined in YAML files under `prompts/` and loaded through `prompts/manager.py`.

Active prompt files:
- `prompts/researcher.yaml`
- `prompts/analyst.yaml`
- `prompts/writer.yaml`
- `prompts/critic.yaml`
- `prompts/orchestrator.yaml`
- `prompts/research_enricher.yaml`
- `prompts/fact_checker.yaml`

Startup validation runs `TemplateValidator` (`validators/template_validator.py`) and fails fast if required templates are missing/invalid.

## Spec and Schema

Behavior is controlled by:
- `spec/article_spec.yaml`
- `spec/schema.json`

Important settings:
- `pipeline.orchestration.backend`: must be `langgraph`
- `llm.context_length`: role-specific context windows
- `llm.writer_input.max_research_chars`
- `llm.writer_input.max_analysis_chars`
- `llm.writer_input.max_correction_chars`

Current defaults are aligned to 16k context by role and 16k/16k/4k writer input caps.

## Memory and Persistence

- Chroma vector storage: `.memory/chroma_db/` via `memory/research_chroma.py`
- Episodic/procedural memory JSON files under `.memory/`
- Run outputs under `output/`

Common output artifacts:
- `output/pipeline_events.jsonl`
- `output/metrics.json`
- `output/urls_*.txt`
- `output/debug_html_<tool>/`
- `output/debug_research_<tool>.md` (saved per-tool research)
- `output/chains/` (tool chains + pipeline summaries)
- `output/evals/` (batch eval reports/scores/events)

## Evals

Batch eval runner:
- `evals/batch_runner.py`
- Dataset: `evals/cases.jsonl`

Typical commands:
```bash
uv run python -m evals.batch_runner
uv run python -m evals.batch_runner --limit 2
uv run python -m evals.batch_runner --case-id docker_vs_podman_dev_linux
```

Optional LangSmith env vars:
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`
- `LANGSMITH_DATASET`

## Developer Workflow

Install/sync dependencies:
```bash
uv sync
```

Run tests:
```bash
uv run pytest -q
```

Run lint:
```bash
uv run ruff check .
```

Run app:
```bash
python main.py
python main.py --refresh-search
```

Interactive run also supports:
- Reusing previously saved URL lists (`output/urls_*.txt`)
- Reusing previously saved research snapshots (`output/debug_research_<tool>.md`)

Observe events:
```bash
python watch_events.py
python watch_events.py --tail=30
python watch_events.py --watch
```

## Implementation Notes

- Prefer editing templates in `prompts/*.yaml` over hardcoded prompt strings.
- Keep orchestration logic inside LangGraph path; avoid reintroducing parallel manual flows in `pipeline.py`.
- Preserve `question_coverage` before `critic` and the retry/enrichment behavior in `after_failure`.
- If adding a new prompt file/template, integrate and validate it (runtime + tests).
- If changing spec keys, keep `spec/schema.json` in sync and update relevant tests.
