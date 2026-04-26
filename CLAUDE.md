# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them; don't pick silently.
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
- If you notice unrelated dead code, mention it; don't delete it blindly.

When your changes create orphans:
- Remove imports/variables/functions that your changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```text
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## Repositório: arquitetura atual

Este repositório está em arquitetura híbrida.

O caminho principal já foi movido para:
- `main.py`
- `sdd/graph/*`
- `sdd/agents/*`
- `sdd/checks/*`

Mas ainda existem dependências legadas necessárias:
- `spec/article_spec.yaml`
- `memory/memory_store.py`
- `llm/structured.py`
- `sdd/prompts_manager/manager.py`

Não trate a migração como concluída se esses pontos continuarem em uso.

## Fluxo principal atual

Entrada e execução:
1. `main.py` coleta ferramentas, contexto, foco, questões e opções de reuso.
2. `sdd/graph/runner.py` compila o `StateGraph` com `MemorySaver`.
3. `sdd/graph/nodes.py` executa:
   - `research`
   - `evidence`
   - `analysis`
   - `writer`
   - `critic`
   - `finalize`
4. `output/pipeline_events.jsonl` é a trilha operacional principal.

## Áreas do código

### `sdd/graph/`
- `runner.py`: compila e executa o grafo.
- `state.py`: define `PipelineState`.
- `nodes.py`: chama agentes diretamente.
- `routing.py`: decide retry/finalização.

### `sdd/agents/`
- `researcher.py`: pesquisa, scraping e indexação.
- `evidence.py`: constrói `EvidencePack`.
- `analyst.py`: análise estruturada.
- `writer.py`: gera o artigo.
- `critic.py`: roda checks determinísticos e crítica semântica.

### `sdd/checks/`
Checks determinísticos que devem rodar antes de depender do LLM:
- `placeholder.py`
- `groundedness.py`
- `question_coverage.py`
- `structural.py`

### `llm/`
- `client.py`: cliente central atual.
- `provider_config.py`: resolução de provider/model.
- `structured.py`: structured output com repair loop; ainda ativo.
- `token_counter.py`: estimativa de tokens.

### `memory/`
- `research_chroma.py`: cache vetorial/local de pesquisa.
- `memory_store.py`: memória operacional ainda usada pelo fluxo atual.

### Config e contratos
- `sdd/config/*.yaml`: configuração nova introduzida na reconstrução.
- `spec/article_spec.yaml`: contrato legado ainda usado no runtime atual.
- `spec/schema.json`: schema da spec legada.

## Regras operacionais para este repo

- Leia o estado real do repositório antes de afirmar que a arquitetura antiga morreu.
- `output/pipeline_events.jsonl` é a primeira fonte de verdade para travamento, silêncio ou fluxo quebrado.
- `utils/watch_events.py` é o monitor principal de execução.
- Se a dúvida for "o que o estágio X realmente consome", trace o valor em memória e o artefato de debug correspondente.
- Em mudanças de qualidade/runtime, prefira corrigir o pipeline ou os agentes, não editar artefatos gerados manualmente.
- `main.py` deve continuar fino; a superfície detalhada de observabilidade fica em `utils/watch_events.py`.

## O que já foi removido

Estes diretórios não são mais a arquitetura ativa:
- `pipeline_stages/`
- `orchestration/`
- `skills/`

## O que ainda não deve ser excluído

- `spec/article_spec.yaml`
  Ainda é lido por `sdd/base.py`, `llm/client.py`, `sdd/graph/nodes.py`, `validators/spec_validator.py` e testes.
- `memory/memory_store.py`
  Ainda é usado por `main.py`, `sdd/graph/nodes.py`, `evals/batch_runner.py` e alguns testes.
- `llm/structured.py`
  Ainda é requerido por `sdd/agents/critic.py` via `generate_structured()`.
- `sdd/prompts_manager/manager.py`
  Ainda é requerido por `sdd/base.py` e `sdd/agents/researcher.py`.

## O que é candidato real de migração/remoção

- Uso direto de `spec/article_spec.yaml`
- `PromptManager`
- `generate_structured()` / `llm/structured.py`
- `MemoryStore` no caminho principal
- Testes que ainda importam `pipeline`, `pipeline_stages` ou `orchestration`

## Verificação

Ordem padrão neste repo:
1. `uv run pytest -q`
2. `uv run ruff check`

Não declare a migração concluída sem passar pelas duas verificações.
