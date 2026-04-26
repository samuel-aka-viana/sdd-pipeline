# SDD Tech Writer

A local technical article generator that operates entirely within the Ollama ecosystem. The pipeline ingests tools, context, focus areas, and questions; conducts technical source research; assembles evidence; generates analysis; writes the article; and subjects the output to deterministic and semantic critique.

## Architecture Overview

```mermaid
flowchart TD
    A["SDD Tech Writer<br/>(Local Technical Article Generator)"]

    A --> EP

    subgraph EP["ENTRY POINT"]
        U["User Input"]
        M["main.py<br/>(CLI Entry)"]
        P["CLI Prompts<br/>cli/prompts.py<br/><br/>Collects tool, context, focus, and questions<br/>Optional: reuse URLs/research from prior runs"]

        U --> M --> P
    end

    EP --> LG

    subgraph LG["LANGGRAPH ORCHESTRATION<br/>sdd/graph/runner.py"]
        SG["State Graph<br/>(Compiled)"]
        MS["MemorySaver<br/>(Persistence)"]
        ST["State<br/>PipelineState"]
        ND["Nodes<br/>Agent Nodes"]
        RT["Routing<br/>(Deterministic)"]

        SG --- MS --- ST --- ND --- RT

        subgraph PF["PIPELINE EXECUTION FLOW"]
            R["research<br/>Node"]
            E["evidence<br/>Node"]
            AN["analysis<br/>Node"]
            W["writer<br/>Node"]
            C["critic<br/>Node"]
            F["finalize<br/>Node"]

            R --> E --> AN --> W --> C --> F

            C -->|"routing decision: pass"| F
            C -->|"routing decision: fail"| LOOP["fail<br/>(loop)"]
            LOOP -->|"return to analysis/writer<br/>for revision"| AN
        end
    end

    LG --> RA
    LG --> EA
    LG --> AA

    subgraph RA["RESEARCH AGENT<br/>sdd/agents/researcher"]
        WS["Web Search<br/>search_tool"]
        SC["Scraping<br/>Crawl4AI"]
        CH["Chroma Vector Store<br/>Indexing"]

        WS --> SC --> CH
    end

    subgraph EA["EVIDENCE AGENT<br/>sdd/agents/evidence"]
        EB["EvidencePack<br/>Builder"]
    end

    subgraph AA["ANALYST AGENT<br/>sdd/agents/analyst"]
        SA["Structured<br/>Analysis"]
    end

    R --> RA
    E --> EA
    AN --> AA
````

The main path today is `main.py` + `sdd/graph/*` + `sdd/agents/*`. The old architecture based on `pipeline.py`, `skills/`, `pipeline_stages/`, and `orchestration/` has already been removed.

---

## Current Architecture

| Area                        | Responsibility                                                                           |
| --------------------------- | ---------------------------------------------------------------------------------------- |
| `main.py`                   | Interactive CLI; collects input, optionally reuses URLs/research, and triggers the graph |
| `cli/prompts.py`            | Terminal prompt helpers                                                                  |
| `sdd/graph/`                | LangGraph: state, nodes, routing, and runner with `MemorySaver`                          |
| `sdd/agents/`               | Researcher, Evidence, Analyst, Writer, and Critic                                        |
| `sdd/checks/`               | Deterministic checks before LLM critique                                                 |
| `sdd/config/`               | Split configuration: models, pipeline, quality, and infrastructure                       |
| `sdd/constraints.py`        | Domain constants, queries, blacklist, and source heuristics                              |
| `sdd/researcher_modules/`   | Researcher internals: scrape, relevance, context, cache, and debug                       |
| `sdd/prompts_manager/`      | YAML prompts and current loader                                                          |
| `llm/`                      | LLM client, provider config, structured output, and token counter                        |
| `memory/research_chroma.py` | Local Chroma for indexing and semantic search                                            |
| `memory/memory_store.py`    | Operational memory still used by the CLI/graph/evals                                     |
| `tools/`                    | Search, Crawl4AI/fallback scraping, and source ranking                                   |
| `utils/`                    | Observability, logger, and Chroma operational utilities                                  |
| `evals/`                    | Batch evaluation runner                                                                  |

## Real Migration Status

Completed:

* LangGraph graph in `sdd/graph`.
* Agents in `sdd/agents`.
* Deterministic checks in `sdd/checks`.
* Split config in `sdd/config`.
* Researcher constants moved to `sdd/constraints.py`.
* `researcher_modules/run_flow.py` removed.
* `utils/article_sanitizer.py` removed.
* Weak-source blacklist centralized in `LOW_SIGNAL_DOMAINS`.

Still hybrid:

* `PromptManager` is still used by `sdd/base.py` and by the researcher.
* `llm/structured.py` and `generate_structured()` are still used by the critic.
* `memory/memory_store.py` is still a dependency of the main flow.
* LangSmith exists in evals, but the main pipeline still only writes local events to `output/pipeline_events.jsonl`.

---

## Configuration

The main source of the new configuration is in `sdd/config/`:

| File            | Contents                                |
| --------------- | --------------------------------------- |
| `models.yaml`   | Models by role and explicit provider    |
| `pipeline.yaml` | Iterations, timeout, and backend        |
| `quality.yaml`  | Quality rules and required sections     |
| `infra.yaml`    | Search, scraper, and external providers |

`spec/article_spec.yaml` still exists for compatibility with old validations, but the new runtime uses `sdd.config.load_runtime_config()` as the consolidated view.

---

## Installation

```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync
cp .env.example .env
```

If using Ollama embeddings in Chroma:

```bash
uv add ollama
```

Important: a persisted Chroma collection cannot switch embedding functions. If `.memory/chroma_db` was created with the default embedding and you enable `CHROMA_EMBEDDING_PROVIDER=ollama`, recreate/reindex the database.

---

## `.env`

Main variables:

```env
LLM_PROVIDER=openrouter_free

LLM_MODEL_RESEARCHER=<model-id>
LLM_MODEL_ANALYST=<model-id>
LLM_MODEL_WRITER=<model-id>
LLM_MODEL_CRITIC=<model-id>

OPENROUTER_API_KEY=<your-key>
OLLAMA_LOCAL_BASE_URL=http://localhost:11434

# Optional: Chroma with Ollama embeddings
# CHROMA_EMBEDDING_PROVIDER=ollama
# CHROMA_EMBED_MODEL=nomic-embed-text:latest
# CHROMA_EMBED_OLLAMA_URL=http://localhost:11434

# Raw HTML debug
# SDD_HTML_DEBUG=1
```

---

## Usage

Run the pipeline:

```bash
python main.py
python main.py --refresh-search
```

Main output:

```text
output/article.md
output/pipeline_events.jsonl
output/urls_<tool>.txt
output/debug_context_<tool>.md
output/chains/
```

Monitor events:

```bash
python -m utils.watch_events
python -m utils.watch_events url_found
python -m utils.watch_events --tail=30
python -m utils.watch_events --watch
python -m utils.watch_events --follow
```

Chroma:

```bash
python -m utils.repopulate_chroma
python -m utils.test_chroma_queries
```

Evals:

```bash
uv run python -m evals.batch_runner
uv run python -m evals.batch_runner --limit 2
uv run python -m evals.batch_runner --case-id docker_vs_podman_dev_linux
```

---

## Filters and Blacklist

The source filter lives in `sdd/constraints.py`.

Main layers:

* `DEFAULT_SKIP_DOMAINS`: social networks, video, media, and domains outside the technical scope.
* `LOW_SIGNAL_DOMAINS`: SEO/listicles, marketplaces, generic comparison sites, job search, and shallow content.
* `LOW_SIGNAL_PATH_MARKERS`: path patterns such as `/compare/`.
* `TRUSTED_TECH_DOMAINS`: trusted technical domains.

After analyzing `output/urls_ansible.txt`, domains such as `guru99.com`, `bobcares.com`, `alternativeto.net`, `freelancer.com`, `speakerdeck.com`, `webkkk.net`, `dohost.us`, `a-listware.com`, and similar domains were added to the blacklist.

Sources kept as potentially useful:

* official docs (`docs.ansible.com`, `docs.redhat.com`)
* GitHub when the result is a relevant project/repository
* technical vendors such as AWS, HashiCorp, Elastic
* technical blogs with specific content, provided they pass the relevance filters

---

## Scraping

Main scraper:

* `tools/scraper_crawl4ai.py`

Fallback:

* `tools/scraper_tool.py`
* `tools/scraper_factory.py`

Applied handling:

* `CrawlerRunConfig.wait_until = "load"` to reduce capture during navigation.
* `Page.content ... navigating and changing the content` error classified as `navigation_in_progress`.
* `navigation_in_progress` is retryable with a larger backoff.
* weak domains are added to the blacklist to reduce scraping cost.

---

## Verification

Most recently validated state:

```bash
uv run pytest -q
# 213 passed, 1 skipped
```

Lint:

```bash
uv run ruff check
```

`ruff` still fails due to complexity (`C901`) in old structural points:

* `memory/research_chroma.py::chunk_content`
* `sdd/researcher_modules/context_builder.py::build_context`
* `sdd/researcher_modules/reanalyze.py::reanalyze_urls_for_tips_and_errors`
* `sdd/researcher_modules/scrape_async.py::async_crawl_task`
* `utils/repopulate_chroma.py::repopulate_from_files`
* `utils/test_chroma_queries.py::verify_data_integrity`
* `utils/watch_events.py::print_event`, `stats_summary`, `parse_cli_args`

---

## Maintenance Rules

* `main.py` must stay thin.
* Detailed observability lives in `output/pipeline_events.jsonl` and `utils/watch_events.py`.
* Fix quality in the pipeline/agents/filters, not by manually editing generated artifacts.
* The blacklist must block clearly weak domains; do not block official docs, vendor docs, or useful repositories without evidence.
* If the Chroma embedding changes, reindex the collection.
* Before declaring ready: `uv run pytest -q`; then address `ruff` when the change touches files with lint issues.
