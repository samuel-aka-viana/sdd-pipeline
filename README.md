# SDD Tech Writer

Pipeline para geração de artigos técnicos com 4 etapas de alto nível (research, analysis, writing, critic), orquestrado por **LangGraph** e dirigido por **templates YAML**.

## Estado atual

- Orquestração: `langgraph` (`orchestration/langgraph_runner.py`)
- Prompts: `prompts/*.yaml` + `prompts/manager.py`
- Validação de templates no startup: `validators/template_validator.py`
- Persistência semântica: Chroma (`.memory/chroma_db/`)
- Evals batch com dataset fixo: `evals/cases.jsonl`

## Arquitetura

Fluxo principal:
1. `skills/researcher.py`
2. `skills/analyst.py`
3. `skills/writer.py`
4. `skills/critic.py`

No LangGraph (`orchestration/langgraph_runner.py`) o fluxo inclui nós explícitos:
- `research` → `analysis` → `writer`
- `question_coverage` (validação determinística de cobertura das perguntas)
- `critic`
- `after_failure` (retry do writer ou enriquecimento de pesquisa/análise)
- `finalize`

Entrada via `main.py`, coordenação em `pipeline.py`.

## Configuração

### 1) Ambiente

```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync
```

### 2) Variáveis (`.env`)

Defina provider/modelos por role, por exemplo:

```env
LLM_PROVIDER=openrouter_free
LLM_MODEL_RESEARCHER=...
LLM_MODEL_ANALYST=...
LLM_MODEL_WRITER=...
LLM_MODEL_CRITIC=...
```

### 3) Spec (`spec/article_spec.yaml`)

Pontos importantes:
- `pipeline.orchestration.backend: langgraph`
- `llm.context_length.{default,researcher,analyst,writer,critic}`
- `llm.writer_input.max_research_chars`
- `llm.writer_input.max_analysis_chars`
- `llm.writer_input.max_correction_chars`

No estado atual, os contextos por role estão em **16000** e writer input caps em **16000/16000/4000**.

## Como rodar

```bash
python main.py
python main.py --refresh-search
```

## Observabilidade

```bash
python watch_events.py
python watch_events.py --tail=30
python watch_events.py --watch
```

Artefatos comuns:
- `output/pipeline_events.jsonl`
- `output/metrics.json`
- `output/urls_*.txt`
- `output/debug_html_<tool>/`
- `output/debug_research_<tool>.md` (pesquisa salva por ferramenta)
- `output/chains/` (cadeias por ferramenta + resumo de pipeline)

## Evals

```bash
uv run python -m evals.batch_runner
uv run python -m evals.batch_runner --limit 2
uv run python -m evals.batch_runner --case-id docker_vs_podman_dev_linux
```

Saídas:
- `output/evals/run_YYYYMMDD_HHMMSS.json`
- `output/evals/scores.jsonl`
- `output/evals/events_*.jsonl`

LangSmith opcional:
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`
- `LANGSMITH_DATASET`

## Qualidade

```bash
uv run ruff check .
uv run pytest -q
```

## Estrutura

```text
spec/           contrato e schema
prompts/        templates YAML de prompt
skills/         etapas do pipeline
orchestration/  LangGraph runner
validators/     validações de spec/regras/templates
memory/         integração com Chroma e memória local
evals/          batch runner + dataset fixo
output/         artefatos de execução (events, chains, debug_research)
artigos/        artigos gerados
```

## Nota de manutenção

- Evite prompt hardcoded em código; prefira `prompts/*.yaml`.
- Ao criar template novo, integre no fluxo e valide nos testes.
- Ao mudar spec, ajuste também `spec/schema.json`.
