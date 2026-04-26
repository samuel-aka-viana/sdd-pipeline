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

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.


## Objetivo
Este documento descreve a arquitetura atual do projeto `sdd-ollama`, com o nome dos arquivos e o contexto/responsabilidade de cada um.

## Visão de camadas
- Entrada e orquestração: recebe parâmetros, monta estado e executa o pipeline de geração.
- Skills: implementam comportamento por papel (researcher, analyst, writer, critic etc.).
- LLM: cliente de providers, fallback, circuit breaker, structured outputs, token usage.
- Memória: persistência de contexto, aprendizado, indexação vetorial.
- Pipeline stages: estágios finos usados na execução LangGraph.
- Prompts e spec: contratos de entrada/saída, prompts e regras.
- Tools: busca, scraping e ranking de fontes.
- Validação e testes: validação de spec/template e suíte automatizada.

## Entrada e runtime
- `main.py`: CLI principal para rodar o pipeline e coordenar execução ponta-a-ponta.
- `pipeline.py`: orquestrador principal do fluxo (research -> evidence -> analysis -> writer -> critic), com integração de memória e LLM.
- `orchestration/langgraph_runner.py`: execução do fluxo via LangGraph, incluindo nós e transições.
- `watch_events.py`: monitor único de eventos (one-shot, `--watch` e `--follow`/tail) para acompanhar execução em tempo real.
- `logger.py`: estrutura de logging de eventos e utilitários de telemetria local.

## Skills (papéis)
- `skills/base.py`: classe base compartilhada entre skills (LLM, prompts, spec, config por papel).
- `skills/researcher.py`: skill de pesquisa técnica (queries, scrape, indexação e síntese de pesquisa).
- `skills/analyst.py`: skill de análise estruturada dos dados de pesquisa.
- `skills/writer.py`: skill de geração do artigo final com prompt caching.
- `skills/critic.py`: skill de avaliação semântica/estrutural com outputs estruturados.
- `skills/evidence_builder.py`: constrói EvidencePack estruturado a partir do research bruto (determinístico, sem LLM).
- `skills/router.py`: roteamento/seleção de skills no fluxo.

## Módulos de suporte às skills
- `skills/schemas.py`: todos os modelos Pydantic de saída estruturada (EvidencePack, EvidenceItem, EvidenceGap, critic + orchestrator).
- `skills/templates.py`: builders de template puros sem estado (analyst + writer).
- `skills/utils.py`: constantes e funções utilitárias puras compartilhadas pelas skills.

## Módulos do Researcher (fatiamento)
- `researcher_modules/constants.py`: constantes de domínio (queries padrão, domínios, limites, stopwords).
- `researcher_modules/queries.py`: construção de queries por foco e por perguntas direcionadas.
- `researcher_modules/relevance.py`: filtros de relevância e score de fontes/resultados.
- `researcher_modules/markdown.py`: extração/qualidade de markdown e redirects.
- `researcher_modules/source_quality.py`: carga de stats por domínio e inferência de qualidade da fonte.
- `researcher_modules/crawl4ai_config.py`: criação de config do Crawl4AI com filtros opcionais.
- `researcher_modules/debug_io.py`: persistência de artefatos de debug de contexto e HTML.
- `researcher_modules/chain_run.py`: lifecycle de chain run e persistência de fases/summary.
- `researcher_modules/scrape_async.py`: scraping assíncrono em lote com limite por domínio.
- `researcher_modules/scrape_threaded.py`: scraping paralelo com throttling por domínio e fallback para async batch.
- `researcher_modules/context_builder.py`: construção de contexto de pesquisa (discovery, scrape, extract, index).
- `researcher_modules/run_flow.py`: orquestração completa do fluxo `run()` do researcher.
- `researcher_modules/reanalyze.py`: reanálise de conteúdo já coletado para dicas/erros.
- `researcher_modules/cached_search.py`: expansão de queries e busca semântica no cache Chroma.

## Pipeline stages (granularização do pipeline)
- `pipeline_stages/research.py`: estágio de pesquisa por ferramenta (inclui paralelização por ferramenta).
- `pipeline_stages/evidence.py`: estágio de construção do EvidencePack (research → evidence_pack estruturado).
- `pipeline_stages/analysis.py`: estágio de análise com execução sequencial/paralela.
- `pipeline_stages/writer.py`: estágio de escrita por iteração.
- `pipeline_stages/critic.py`: estágio de crítica por iteração.

## LLM e inferência
- `llm/client.py`: cliente LLM unificado (geração normal/cached/structured, delegando provider config e fallback).
- `llm/provider_config.py`: `ProviderConfigResolver` — resolve provider mode, models, config e local fallback model; `LLMRuntimeConfig` dataclass.
- `llm/fallback.py`: `try_provider()` — helper que envolve chamadas de provider capturando CircuitOpenError/RuntimeError/TimeoutException.
- `llm/circuit_breaker.py`: controle de saúde/cooldown de providers.
- `llm/structured.py`: parse/validação de respostas estruturadas com retry de reparo.
- `llm/token_counter.py`: contagem/estimativa de tokens para observabilidade.
- `llm/__init__.py`: exportações do pacote LLM.

## Memória e indexação
- `memory/memory_store.py`: armazenamento de memória operacional e lições.
- `memory/research_chroma.py`: integração com Chroma para indexar e buscar chunks de pesquisa.
- `memory/research_persistence.py`: persistência de dados/artefatos de pesquisa.
- `repopulate_chroma.py`: utilitário para repovoar índice vetorial.

## Tools (coleta de dados)
- `tools/search_tool.py`: busca web e normalização de resultados.
- `tools/scraper_tool.py`: interface de scraping síncrono usada pela skill.
- `tools/scraper_crawl4ai.py`: implementação de scraping usando Crawl4AI.
- `tools/scraper_factory.py`: fábrica/seleção de scraper conforme configuração.
- `tools/source_ranker.py`: ranking/heurísticas de qualidade de fontes.

## Prompts e contratos
- `prompts/manager.py`: carregamento/renderização de prompts e separação stable/volatile para cache.
- `prompts/researcher.yaml`: templates do pesquisador.
- `prompts/research_enricher.yaml`: templates de reanálise/enriquecimento.
- `prompts/analyst.yaml`: templates do analista.
- `prompts/writer.yaml`: templates do writer (inclui breakpoint de cache).
- `prompts/critic.yaml`: templates do critic.
- `prompts/fact_checker.yaml`: templates de fact-check.
- `prompts/orchestrator.yaml`: templates para decisões do orquestrador.
- `spec/article_spec.yaml`: especificação principal de comportamento/limites/modelos.
- `spec/schema.json`: schema de validação da spec.

## Validação e utilitários
- `validators/spec_validator.py`: validação do artigo/fluxo contra a spec.
- `validators/template_validator.py`: validação de templates/padrões de prompt.
- `validators/rules_engine.py`: regras complementares de validação.
- `utils.py`: utilitários compartilhados usados no pipeline.

## Evals e artefatos
- `evals/batch_runner.py`: runner de avaliações em lote.
- `evals/cases.jsonl`: casos de avaliação.
- `output/`: artefatos de debug, chains, métricas e eventos da execução.
- `artigos/`: saídas de artigo geradas.

## Testes
- `tests/test_pipeline.py`: testes do pipeline e regras críticas de timeout/fluxo.
- `tests/test_pipeline_e2e.py`: testes ponta-a-ponta do fluxo.
- `tests/test_skills.py`: testes de contrato das skills com base na spec.
- `tests/test_skills_mocked.py`: testes de skills com LLM mockado.
- `tests/test_researcher_modules_refactor.py`: testes unitários dos módulos extraídos do researcher.
- `tests/test_chroma_persistence.py`: testes de persistência do Chroma.
- `tests/test_spec_schema.py`: validação do schema da spec.
- `tests/test_spec_validator.py`: testes do validador da spec.
- `tests/test_template_validator.py`: testes do validador de templates.
- `tests/test_prompt_integration.py`: testes de integração de prompts.
- `tests/test_evals_batch_runner.py`: testes do runner de evals.
- `tests/conftest.py`: fixtures e setup de testes.

## Estado atual de referência
- `skills/researcher.py`: facade para `researcher_modules/*`.
- Skills suportadas por três módulos centralizados: `schemas.py`, `templates.py`, `utils.py`.
- `llm/client.py` delega config de provider para `llm/provider_config.py` e fallback para `llm/fallback.py`.
- Suíte local de referência: `198 passed, 1 skipped`.
