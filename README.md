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
        P["CLI Prompts<br/>cli/prompts.py<br/><br/>Collects tool, context, focus and questions<br/>Optional: reuse URLs/research from prior runs"]

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

O caminho principal hoje é `main.py` + `sdd/graph/*` + `sdd/agents/*`. A arquitetura antiga baseada em `pipeline.py`, `skills/`, `pipeline_stages/` e `orchestration/` já foi removida.

---

## Arquitetura Atual

| Área                        | Responsabilidade                                                                  |
| --------------------------- | --------------------------------------------------------------------------------- |
| `main.py`                   | CLI interativa; coleta entrada, reuso opcional de URLs/pesquisa e dispara o grafo |
| `cli/prompts.py`            | Helpers de prompt do terminal                                                     |
| `sdd/graph/`                | LangGraph: state, nodes, routing e runner com `MemorySaver`                       |
| `sdd/agents/`               | Researcher, Evidence, Analyst, Writer e Critic                                    |
| `sdd/checks/`               | Checks determinísticos antes da crítica LLM                                       |
| `sdd/config/`               | Configuração split: modelos, pipeline, qualidade e infraestrutura                 |
| `sdd/constraints.py`        | Constantes de domínio, queries, blacklist e heurísticas de fonte                  |
| `sdd/researcher_modules/`   | Internals do researcher: scrape, relevância, contexto, cache e debug              |
| `sdd/prompts_manager/`      | Prompts YAML e loader atual                                                       |
| `llm/`                      | Cliente LLM, provider config, structured output e token counter                   |
| `memory/research_chroma.py` | Chroma local para indexação e busca semântica                                     |
| `memory/memory_store.py`    | Memória operacional ainda usada por CLI/grafo/evals                               |
| `tools/`                    | Busca, scraping Crawl4AI/fallback e ranking de fontes                             |
| `utils/`                    | Observabilidade, logger e utilitários operacionais de Chroma                      |
| `evals/`                    | Runner de avaliação em lote                                                       |

## Estado Real da Migração

Concluído:

* Grafo LangGraph em `sdd/graph`.
* Agentes em `sdd/agents`.
* Checks determinísticos em `sdd/checks`.
* Config split em `sdd/config`.
* Constantes do researcher movidas para `sdd/constraints.py`.
* `researcher_modules/run_flow.py` removido.
* `utils/article_sanitizer.py` removido.
* Blacklist de fontes fracas centralizada em `LOW_SIGNAL_DOMAINS`.

Ainda híbrido:

* `PromptManager` ainda é usado por `sdd/base.py` e pelo researcher.
* `llm/structured.py` e `generate_structured()` ainda são usados pelo critic.
* `memory/memory_store.py` ainda é dependência do fluxo principal.
* LangSmith existe nos evals, mas o pipeline principal ainda só grava eventos locais em `output/pipeline_events.jsonl`.

---

## Configuração

A fonte principal de configuração nova fica em `sdd/config/`:

| Arquivo         | Conteúdo                                  |
| --------------- | ----------------------------------------- |
| `models.yaml`   | Modelos por papel e provider explícito    |
| `pipeline.yaml` | Iterações, timeout e backend              |
| `quality.yaml`  | Regras de qualidade e seções obrigatórias |
| `infra.yaml`    | Search, scraper e providers externos      |

`spec/article_spec.yaml` ainda existe por compatibilidade com validações antigas, mas o runtime novo usa `sdd.config.load_runtime_config()` como visão consolidada.

---

## Instalação

```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync
cp .env.example .env
```

Se usar embeddings Ollama no Chroma:

```bash
uv add ollama
```

Importante: uma collection Chroma persistida não pode trocar de embedding function. Se `.memory/chroma_db` foi criado com embedding default e você ligar `CHROMA_EMBEDDING_PROVIDER=ollama`, recrie/reindexe o banco.

---

## `.env`

Principais variáveis:

```env
LLM_PROVIDER=openrouter_free

LLM_MODEL_RESEARCHER=<model-id>
LLM_MODEL_ANALYST=<model-id>
LLM_MODEL_WRITER=<model-id>
LLM_MODEL_CRITIC=<model-id>

OPENROUTER_API_KEY=<your-key>
OLLAMA_LOCAL_BASE_URL=http://localhost:11434

# Opcional: Chroma com Ollama embeddings
# CHROMA_EMBEDDING_PROVIDER=ollama
# CHROMA_EMBED_MODEL=nomic-embed-text:latest
# CHROMA_EMBED_OLLAMA_URL=http://localhost:11434

# Debug HTML bruto
# SDD_HTML_DEBUG=1
```

---

## Uso

Rodar pipeline:

```bash
python main.py
python main.py --refresh-search
```

Saída principal:

```text
output/article.md
output/pipeline_events.jsonl
output/urls_<tool>.txt
output/debug_context_<tool>.md
output/chains/
```

Monitorar eventos:

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

## Filtros e Blacklist

O filtro de fontes vive em `sdd/constraints.py`.

Camadas principais:

* `DEFAULT_SKIP_DOMAINS`: redes sociais, vídeo, mídia, domínios fora do escopo técnico.
* `LOW_SIGNAL_DOMAINS`: SEO/listicles, marketplaces, comparadores genéricos, job search, conteúdo raso.
* `LOW_SIGNAL_PATH_MARKERS`: padrões de path como `/compare/`.
* `TRUSTED_TECH_DOMAINS`: domínios técnicos confiáveis.

Depois da análise de `output/urls_ansible.txt`, foram adicionados à blacklist domínios como `guru99.com`, `bobcares.com`, `alternativeto.net`, `freelancer.com`, `speakerdeck.com`, `webkkk.net`, `dohost.us`, `a-listware.com` e similares.

Fontes mantidas como potencialmente úteis:

* docs oficiais (`docs.ansible.com`, `docs.redhat.com`)
* GitHub quando o resultado é projeto/repositório relevante
* fornecedores técnicos como AWS, HashiCorp, Elastic
* blogs técnicos com conteúdo específico, caso passem pelos filtros de relevância

---

## Scraping

Scraper principal:

* `tools/scraper_crawl4ai.py`

Fallback:

* `tools/scraper_tool.py`
* `tools/scraper_factory.py`

Tratamentos já aplicados:

* `CrawlerRunConfig.wait_until = "load"` para reduzir captura durante navegação.
* erro `Page.content ... navigating and changing the content` classificado como `navigation_in_progress`.
* `navigation_in_progress` é retryável com backoff maior.
* domínios fracos entram em blacklist para reduzir custo de scraping.

---

## Verificação

Estado mais recente validado:

```bash
uv run pytest -q
# 213 passed, 1 skipped
```

Lint:

```bash
uv run ruff check
```

O `ruff` ainda falha por complexidade (`C901`) em pontos estruturais antigos:

* `memory/research_chroma.py::chunk_content`
* `sdd/researcher_modules/context_builder.py::build_context`
* `sdd/researcher_modules/reanalyze.py::reanalyze_urls_for_tips_and_errors`
* `sdd/researcher_modules/scrape_async.py::async_crawl_task`
* `utils/repopulate_chroma.py::repopulate_from_files`
* `utils/test_chroma_queries.py::verify_data_integrity`
* `utils/watch_events.py::print_event`, `stats_summary`, `parse_cli_args`

---

## Regras de Manutenção

* `main.py` deve continuar fino.
* Observabilidade detalhada fica em `output/pipeline_events.jsonl` e `utils/watch_events.py`.
* Corrigir qualidade no pipeline/agentes/filtros, não em artefatos gerados manualmente.
* Blacklist deve bloquear domínios claramente fracos; não bloquear docs oficiais, vendor docs ou repositórios úteis sem evidência.
* Se trocar embedding do Chroma, reindexar a collection.
* Antes de declarar pronto: `uv run pytest -q`; depois atacar `ruff` quando a mudança tocar arquivos com lint.
