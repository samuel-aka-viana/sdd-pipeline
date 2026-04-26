# AGENTS.md

## Objetivo
Este documento descreve a arquitetura atual do `sdd-ollama` no estado real do repositório em `2026-04-26`.

Ele substitui a visão antiga baseada em `pipeline.py`, `skills/` e `orchestration/`.
Hoje o caminho principal roda em `main.py` + `sdd/graph/*`, mas ainda existem componentes legados necessários para compatibilidade.

## Fluxo principal atual

Entrada:
- `main.py`: coleta parâmetros, reaproveitamento opcional de URLs/pesquisa e dispara o pipeline.

Orquestração:
- `sdd/graph/runner.py`: monta `StateGraph`, compila com `MemorySaver` e grava `output/pipeline_events.jsonl` via `graph.stream(..., stream_mode="updates")`.
- `sdd/graph/state.py`: define `PipelineState`.
- `sdd/graph/nodes.py`: nós `research -> evidence -> analysis -> writer -> critic -> finalize`.
- `sdd/graph/routing.py`: decisão determinística após o critic.

Etapas do pipeline:
1. `research`
2. `evidence`
3. `analysis`
4. `writer`
5. `critic`
6. `finalize`

## Estrutura por área

### Runtime e CLI
- `main.py`: CLI interativa principal.
- `cli/prompts.py`: prompts de coleta de entrada no terminal.
- `utils/watch_events.py`: monitor operacional do `output/pipeline_events.jsonl`.
- `utils/logger.py`: logger local e formatação de eventos auxiliares.

### Pacote `sdd/`

#### Núcleo
- `sdd/base.py`: base compartilhada dos agentes atuais; ainda carrega `spec/article_spec.yaml`, `LLMClient` e `PromptManager`.
- `sdd/schemas.py`: modelos Pydantic centrais.
- `sdd/constraints.py`: constantes e padrões compartilhados.
- `sdd/templates.py`, `sdd/utils.py`, `sdd/relevance_filter.py`: helpers reutilizados no pacote novo.

#### Agentes
- `sdd/agents/researcher.py`: pesquisa, scraping e indexação no Chroma.
- `sdd/agents/evidence.py`: monta `EvidencePack`.
- `sdd/agents/analyst.py`: análise estruturada.
- `sdd/agents/writer.py`: geração do artigo.
- `sdd/agents/critic.py`: checks determinísticos + crítica semântica.

#### Checks determinísticos
- `sdd/checks/placeholder.py`
- `sdd/checks/groundedness.py`
- `sdd/checks/question_coverage.py`
- `sdd/checks/structural.py`
- `sdd/checks/__init__.py`: ordem de execução dos checks.

#### Grafo
- `sdd/graph/state.py`: estado do pipeline.
- `sdd/graph/nodes.py`: execução direta dos agentes por nó.
- `sdd/graph/routing.py`: roteamento determinístico.
- `sdd/graph/runner.py`: compilação + execução + stream de eventos.

#### Configuração nova
- `sdd/config/models.yaml`: modelos por papel com `provider` explícito.
- `sdd/config/pipeline.yaml`: limites do pipeline.
- `sdd/config/quality.yaml`: regras de qualidade.
- `sdd/config/infra.yaml`: parâmetros de infraestrutura/pesquisa.

Observação importante:
- A árvore `sdd/config/` já existe, mas o runtime ainda não foi migrado por completo para ela. O código principal ainda lê `spec/article_spec.yaml` em vários pontos.

#### Pesquisador fatiado
- `sdd/researcher_modules/*`: implementação detalhada do fluxo do pesquisador, incluindo scrape, relevância, debug, reanálise e cache semântico.

#### Prompts atuais
- `sdd/prompts_manager/*.yaml`: templates ativos hoje.
- `sdd/prompts_manager/manager.py`: loader/renderizador ainda em uso.

## LLM e inferência
- `llm/client.py`: cliente central atual.
- `llm/provider_config.py`: resolve provider/model/config.
- `llm/structured.py`: structured output com repair loop; ainda necessário no estado atual.
- `llm/token_counter.py`: estimativa de tokens.

Estado real:
- O handoff previa migração para `with_fallbacks()` e `.with_structured_output()`.
- Essa migração ainda não foi concluída.
- `llm/client.py` ainda usa `generate_structured()` e `llm/structured.py`.

## Memória e persistência
- `memory/research_chroma.py`: índice vetorial da pesquisa.
- `memory/memory_store.py`: memória operacional usada pelo CLI, pelos nós do grafo e por evals.

Estado real:
- `memory/research_persistence.py` já não existe mais no tree principal.
- `memory/memory_store.py` continua necessário hoje; não remover até migrar `main.py`, `sdd/graph/nodes.py` e `evals/batch_runner.py`.

## Tools de coleta
- `tools/search_tool.py`: busca web.
- `tools/scraper_factory.py`: seleção de scraper.
- `tools/scraper_crawl4ai.py`: implementação Crawl4AI.
- `tools/scraper_tool.py`: scraper alternativo/fallback.
- `tools/source_ranker.py`: ranking de fontes.

## Prompts, contratos e validação
- `spec/article_spec.yaml`: contrato de runtime ainda ativo.
- `spec/schema.json`: schema da spec legada.
- `validators/spec_validator.py`: ainda valida a spec legada.
- `validators/template_validator.py`: valida templates.
- `validators/question_coverage.py`, `validators/rules_engine.py`: validações auxiliares ainda presentes.

## Testes e evals
- `tests/test_graph.py`: cobertura do grafo novo.
- `tests/test_agents_contract.py`: contratos dos agentes.
- `tests/test_checks.py`: checks determinísticos.
- `tests/test_chroma_persistence.py`: persistência do Chroma.
- `tests/test_pipeline_e2e.py`: smoke/e2e ainda com componentes legados.
- `tests/test_evidence_builder.py`, `tests/test_spec_schema.py`: ainda contêm referências a arquitetura antiga para compatibilidade/pendências de migração.
- `evals/batch_runner.py`: runner de evals ainda dependente de `MemoryStore`.

## O que já saiu da arquitetura antiga
Estes diretórios/arquivos não são mais o caminho principal e já foram removidos do tree:
- `pipeline_stages/`
- `orchestration/`
- `skills/`

## Componentes legados ainda presentes e por que não excluir agora

Não excluir ainda:
- `spec/article_spec.yaml`
  Motivo: `sdd/base.py`, `llm/client.py`, `sdd/graph/nodes.py`, `validators/spec_validator.py` e parte dos testes ainda dependem dele.
- `memory/memory_store.py`
  Motivo: usado por `main.py`, `sdd/graph/nodes.py`, `evals/batch_runner.py` e testes.
- `llm/structured.py`
  Motivo: `sdd/agents/critic.py` ainda usa `self.llm.generate_structured(...)`.
- `sdd/prompts_manager/manager.py`
  Motivo: `sdd/base.py` e `sdd/agents/researcher.py` ainda o usam.
- `tests/test_evidence_builder.py`
  Motivo: ainda cobre restos de compatibilidade; precisa ser migrado ou removido conscientemente, não apagado no escuro.
- `tests/test_spec_schema.py`
  Motivo: ainda verifica a spec legada e referência de compatibilidade com `pipeline`.

Podem ser tratados como candidatos claros de migração/remoção depois:
- referências de testes a `pipeline`, `pipeline_stages` e `orchestration`
- dependência de `spec/article_spec.yaml`
- `PromptManager`
- `generate_structured()` / `llm/structured.py`
- `MemoryStore` no fluxo principal

## Fonte da verdade para operação e debug
- Estado da execução: `output/pipeline_events.jsonl`
- Visualização operacional: `utils/watch_events.py`
- Artefatos de debug: `output/`
- Índice vetorial/local state: `.memory/`

## Comandos de verificação
- Testes: `uv run pytest -q`
- Lint: `uv run ruff check`

## Estado atual resumido
- O pacote novo `sdd/` e o grafo LangGraph já existem e são o caminho principal.
- A migração ainda não terminou: runtime, validação e parte dos testes continuam híbridos.
- Ao atualizar código, documente e preserve explicitamente essa convivência entre arquitetura nova e compatibilidade legada.
