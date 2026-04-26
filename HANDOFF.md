# HANDOFF — SDD Pipeline

Pipeline que gera artigos técnicos de comparação de ferramentas em português.

```
Pesquisa web → Indexação Chroma → Evidence pack → Análise → Escrita → Crítica → (retry/enrich)
```

Entrada: nome de ferramentas + contexto + perguntas do usuário
Saída: artigo markdown com seções fixas, referências verificadas, respostas às perguntas

---

## 1. Como Executar Sessões

Regras operacionais fixas. Seguir em toda sessão de trabalho neste projeto.

### Modelo por tipo de tarefa

O usuário troca o modelo via `/model` no terminal. A AI indica qual usar antes de iniciar cada tarefa.

| Tarefa | Modelo |
|---|---|
| Planejar fase, decidir arquitetura, resolver ambiguidade | Opus |
| Escrever código com lógica de negócio | Sonnet |
| Editar config, renomear, mover arquivo, ajuste mecânico | Haiku |

### Compactação de contexto

A cada 3 tarefas concluídas, a AI avisa: **"3 tarefas concluídas — rode `/compact` antes de continuar"**.
O usuário roda `/compact` no terminal. A AI não executa este comando.
Após `/compact`, a AI retoma pelo estado das tasks (`TaskCreate`/`TaskUpdate`).

### Ferramentas por tipo de operação

| Operação | Ferramenta correta |
|---|---|
| Explorar codebase, buscar padrões, analisar arquivo >100 linhas | `ctx_batch_execute` ou `ctx_search` |
| Editar arquivo (já sabe o que mudar) | `Edit` |
| Criar arquivo novo | `Write` |
| Ler arquivo antes de editar | `Read` |
| Qualquer outra coisa (git, pip, wc) | `Bash` |

`Bash cat` e `Read` para análise são proibidos — produzem output bruto que consome contexto sem necessidade.

### Subagentes

Usar subagente quando: exploração de codebase, revisão pós-fase, geração de testes para módulo isolado.

Não usar subagente quando:
- O resultado é necessário antes de continuar (bloqueante)
- A tarefa edita arquivos: subagente não tem o contexto da conversa atual, só vê o estado dos arquivos em disco
- A tarefa tem menos de 3 passos

### Revisão de qualidade

`/ultrareview` ou `code-reviewer` (subagente Opus) rodam **somente após a Fase 7** — nunca no meio da reconstrução. Revisão prematura fragmenta o contexto sem benefício.

### Antes de qualquer tarefa

Invocar `Skill` tool para verificar se há skill aplicável. Sem exceção.

---

## 2. Padrões de Código Python

Aplicados a todo arquivo novo criado na reconstrução.

### Nomes

- Sem prefixo `_nome` em métodos, variáveis ou atributos próprios. `__init__`, `__str__`, `__repr__` são protocolos Python — permitidos. O proibido é pseudo-privado: `_build_prompt`, `self._cache`.
- Sem variável de uma letra em nenhum contexto: loops, comprehensions, lambdas, condicionais.

```python
# errado
for i, x in enumerate(items):
    results = [x for x in data if x > 0]

# certo
for index, item in enumerate(items):
    results = [value for value in data if value > 0]
```

Exceção: `except Exception as exc` — `exc` é padrão amplamente aceito.

### Condicionais

Mais de 2 `elif` para despachar comportamento → dicionário de handlers.
`if` de guarda (`if not valid: raise`) continua como `if` — a regra é para despacho, não validação.

```python
# errado
if action == "RETRY_WRITER":
    return handle_retry(state)
elif action == "ENRICH_RESEARCH":
    return handle_enrich(state)
elif action == "FINALIZE_APPROVED":
    return handle_finalize(state)

# certo
ACTION_HANDLERS = {
    "RETRY_WRITER":      handle_retry,
    "ENRICH_RESEARCH":   handle_enrich,
    "FINALIZE_APPROVED": handle_finalize,
}
return ACTION_HANDLERS[action](state)
```

### Classes

Criar classe quando: 3+ funções compartilham o mesmo estado, ou há ciclo de vida init → use → cleanup.

Não criar classe quando:
- Só agrupa funções relacionadas → usar módulo
- Só tem `__init__` e um método → usar função direta

### Docstrings

Obrigatória em: classes com lógica de estado não-óbvia, funções públicas com contrato implícito ou comportamento surpreendente.

Proibida em: métodos cujo nome descreve o que fazem, funções de uma linha, getters/setters.

Formato: uma linha, imperativo, descreve o contrato — não o que o código faz linha a linha.

```python
# errado
def build_evidence_pack(urls, chroma):
    """Esta função constrói um EvidencePack a partir de uma lista de URLs
    consultando o banco de dados Chroma para recuperar os conteúdos."""

# certo
def build_evidence_pack(urls: list[str], chroma: ChromaStore) -> EvidencePack:
    """Constrói EvidencePack via Chroma; levanta ValueError se nenhuma URL tem conteúdo indexado."""
```

### Constantes

Todo valor estático vai em `sdd/constraints.py`: regex patterns, thresholds numéricos, listas de palavras-chave, nomes de seções obrigatórias.

`llm/` e `memory/` ficam fora de `sdd/` e têm constantes internas próprias — não importam de `sdd.constraints`.

O que **não** vai para `constraints.py`: valores que mudam por ambiente, valores que vêm dos YAMLs de `config/`.

```python
# em sdd/constraints.py
CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```")
REQUIRED_SECTIONS = ["Instalação", "Configuração", "Armadilhas Comuns"]

# em sdd/checks/groundedness.py
from sdd.constraints import CODE_BLOCK_PATTERN
```

### Type hints

Tipar: assinaturas de funções públicas com tipos não-óbvios, retorno de funções que retornam `Union` ou tipos compostos, parâmetros de boundary (entrada/saída de agente).

Não tipar: variáveis locais com tipo óbvio pelo valor, parâmetros com default que revelam o tipo.

```python
# errado
def run(self) -> None:
    result: str = self.llm.invoke(prompt)
    items: list = result.split("\n")

# certo
def run(self, evidence_pack: EvidencePack, correction: str | None = None) -> ArticleResult:
    result = self.llm.invoke(prompt)
    items = result.split("\n")
```

---

## 3. Estado Atual do Código

- 198 testes passando (`uv run pytest -q`)
- Orchestrator LLM removido — decisão retry/enrich é 100% determinística (`orchestration/decision.py`)
- Critic local: `gemma4:26b` via Ollama
- Analyst: `meta-llama/llama-3.3-70b-instruct:free` via OpenRouter
- Provider routing: `"/" in model` → OpenRouter, sem `/` → Ollama (heurístico frágil, substituído na Fase 2)
- Bug ativo: `https://github.com/seu-repo` em blocos bash reprova no groundedness check (corrigido na Fase 3)

---

## 4. O que Funciona Bem (lógica preservada na reconstrução)

| O que | Detalhe |
|---|---|
| Evidence pack + groundedness check | Writer só cita URLs que o researcher validou — evita alucinação estruturalmente |
| question_coverage determinístico | Verifica número/frase padrão antes de chamar LLM critic — falha rápida |
| Spec como configuração | Thresholds e modelos fora do código — decisão certa |
| Stagnation detection | Para loop quando mesmo problema aparece N vezes seguidas |
| Chroma para reuso | Enriquecimento sem nova busca web |
| pipeline_events.jsonl | O arquivo de observabilidade fica. A implementação (28 `log_event()` em 9 arquivos) é substituída por `graph.stream()` |

---

## 5. Problemas a Resolver na Reconstrução

### Fluxo

| Problema | Causa | Solução na reconstrução |
|---|---|---|
| ENRICH refaz análise inteira | Nó de enriquecimento não tem granularidade | Fase 5: nó enriquece só os tópicos com gap |
| Segunda iteração não vê artigo anterior | State não preserva `article_v1` | Fase 5: `graph/state.py` separa versões |
| Enriquecimento repete busca vazia | Sem memória de tentativas anteriores | Fase 5: nó registra gaps tentados |

### Checks

| Problema | Causa | Solução |
|---|---|---|
| `seu-repo` em bash reprova groundedness | URL scan não exclui code blocks | Fase 3: `checks/groundedness.py` exclui ``` blocos ``` |
| `SEU_TOKEN` não é detectado como placeholder | Não está no spec | Fase 3: `checks/placeholder.py` |
| question_coverage aceita número inventado | Número não precisa vir do evidence pack | Fase 3: verificar âncora no pack |
| min_references conta qualquer URL | Métrica sem peso de qualidade | Pós-reconstrução |

### Arquitetura

| Problema | Causa | Solução |
|---|---|---|
| 4 arquivos para entender qualquer mudança | Lógica em pipeline.py, stages e skills ao mesmo tempo | Reconstrução inteira |
| Provider inferido pelo nome do modelo | `"/" in model` quebra silenciosamente | Fase 2: `config/models.yaml` com `provider:` explícito |
| PipelineState cresce sem controle | Sem separação entre estado persistente e volátil | Fase 5: `graph/state.py` com zonas |
| Chroma consultado por 5 lugares diferentes | Sem ponto único de responsabilidade | Fase 4: só `agents/evidence.py` acessa Chroma |
| Chroma usa ChromaDB raw sem LangChain | Não integra com retriever nativo do LangGraph | Fase 4: refatorar `ResearchChroma` internamente |

---

## 6. O que LangGraph/LangChain Já Entrega (não recriar)

| O que existe hoje | Linhas | Substituto nativo |
|---|---|---|
| `llm/circuit_breaker.py` | 98 | `primary_llm.with_fallbacks([fallback_llm])` |
| `llm/fallback.py` | 23 | absorvido pelo anterior |
| `memory/research_persistence.py` | 360 | **código morto** — nunca chamado |
| `memory/memory_store.py` (metade event log) | ~60 | `graph.stream(mode="updates")` |
| Writer heartbeat a cada 10s | ~20 | `graph.stream()` nativo |
| 28× `log_event()` em 9 arquivos | ~30 | viram campos no state do nó |
| **Total deletável** | **~591** | |

**Como `graph.stream()` substitui o event log:**
```python
# graph/runner.py — substitui todo o sistema de log_event()
for chunk in graph.stream(inputs, stream_mode="updates"):
    node_name, state_delta = next(iter(chunk.items()))
    append_to_jsonl("output/pipeline_events.jsonl", {
        "event": node_name, "details": state_delta, "ts": time.time(),
    })
```

**Recursos do LangGraph não usados hoje que entram na reconstrução:**

| Recurso | O que elimina |
|---|---|
| `MemorySaver` checkpointer | Retomar pipeline de onde parou após falha |
| `graph.stream()` | Todo o sistema de log_event() manual |
| `Annotated` reducers no state | Merge de listas sem código manual |

---

### Descobertas adicionais — o que ainda não estava mapeado

Cinco áreas além do que já estava documentado.

---

#### A. `llm/structured.py` + repair loop em `client.py` → `model.with_structured_output()`

`llm/structured.py` implementa manualmente: injetar JSON schema no prompt (`build_schema_hint`), parsear a resposta (`parse_response`), e construir um prompt de reparo quando o JSON falha (`build_repair_prompt`). Em `client.py`, o loop `generate_structured()` repete isso até 3 vezes.

LangChain resolve com uma linha:
```python
structured_llm = llm.with_structured_output(Schema)
result = structured_llm.invoke(prompt)  # retry com reparo automático incluso
```

`PydanticOutputParser` + `OutputFixingParser` (do `langchain_core`) fazem exatamente o mesmo ciclo: parse → falha → repair prompt → retry. São ~100 linhas (`structured.py` + repair loop no `client.py`) substituídas por um encadeamento nativo.

`llm/structured.py` vai para a lista de **deletar**. O `client.py` perde o método `generate_structured()` e passa a expor o LLM com `.with_structured_output()` diretamente.

---

#### B. `skills/prompts/manager.py` → `ChatPromptTemplate`

`PromptManager` carrega YAML, faz cache em memória, formata com `.format(**kwargs)`, e loga `prompt_used` via `log_event()`. São ~73 linhas para fazer o que `ChatPromptTemplate` já faz:

```python
# hoje — PromptManager.get("researcher", "main", tool=tool, foco=foco)
# novo — template carregado do YAML na inicialização do agente
template = ChatPromptTemplate.from_template(yaml_content["main"])
prompt = template.format_messages(tool=tool, foco=foco)
```

**O que fica:** `CACHE_BREAKPOINT` — a separação entre prefixo cacheável e sufixo volátil é uma otimização específica do Anthropic prompt caching que LangChain não implementa. A lógica de split permanece, mas não precisa do `PromptManager` como classe — pode ser uma função de 5 linhas em `sdd/constraints.py`.

**O que vai:** o `PromptManager` inteiro como classe. O log de `prompt_used` some com os demais `log_event()`.

---

#### C. `tools/search_tool.py` → `BaseTool` do LangChain

`SearchTool` usa `ddgs` (DuckDuckGo) diretamente com cache JSON, retry manual com `time.sleep()`, e multi-query com delay. É uma classe custom de ~127 linhas que faz o que `DuckDuckGoSearchResults` do LangChain já entrega — mas com caching e ranking que o LangChain não tem.

**Decisão:** não deletar, mas envolver como `BaseTool`:
- Manter: cache JSON com TTL de 24h, `SourceRanker`, `search_multi` com delay
- Substituir: retry manual (`time.sleep * attempt`) → `@retry` do LangChain, integração com LangGraph via herança de `BaseTool`

Como `BaseTool`, o `SearchTool` passa a ser invocável pelo agente researcher dentro do LangGraph nativamente, sem adaptador. Hoje ele é chamado manualmente via injeção de dependência.

---

#### D. `researcher_modules/run_flow.py` — 35 parâmetros injetados → desaparece

`run_research()` tem **35 parâmetros**, todos funções injetadas: `build_queries_fn`, `search_multi_fn`, `filter_search_results_fn`, `save_context_debug_fn`, etc. Isso existe porque o researcher original foi extraído do god object (`pipeline.py`) sem remover o acoplamento — cada dependência virou um parâmetro.

Na nova arquitetura, o nó do grafo chama `researcher.run(tool, foco, questoes)` diretamente. O agente tem suas dependências no `__init__` (search tool, chroma, config). Os 35 parâmetros desaparecem junto com o arquivo `run_flow.py`.

198 linhas deletadas — nenhuma linha de lógica de negócio perdida.

---

#### E. `researcher_modules/queries.py` → `PromptTemplate`

As queries de busca são templates com `.replace("{tool}", tool)`:
```python
query_template.replace("{tool}", tool).replace("{alternative}", alt)
```

LangChain: `PromptTemplate.from_template("{tool} vs {alternative} benchmark").format(tool=tool, alternative=alt)`. O dicionário `FOCUS_QUERIES` com os templates por foco é lógica de domínio — fica. O mecanismo de substituição manual vira `PromptTemplate`. ~30 linhas de infra eliminadas.

---

#### Resumo atualizado — total deletável pelo framework

| Arquivo / área | Linhas | Substituto |
|---|---|---|
| `llm/circuit_breaker.py` | 98 | `with_fallbacks()` |
| `llm/fallback.py` | 23 | absorvido |
| `llm/structured.py` + repair loop | ~100 | `with_structured_output()` |
| `llm/token_counter.py` | 40 | `model.get_num_tokens()` |
| `memory/research_persistence.py` | 360 | código morto |
| `memory/memory_store.py` (event log) | ~60 | `graph.stream()` |
| `skills/prompts/manager.py` | 73 | `ChatPromptTemplate` |
| `researcher_modules/run_flow.py` | 198 | nó chama agente direto |
| `researcher_modules/queries.py` (infra) | ~30 | `PromptTemplate` |
| Writer heartbeat + 28× `log_event()` | ~50 | `graph.stream()` |
| **Total** | **~1.032** | |

**O que fica e não é trocado:**
- `researcher_modules/relevance.py` (257 linhas) — lógica de domínio: domain trust, URL scoring, keyword matching — sem equivalente no LangChain
- `researcher_modules/source_quality.py` (38 linhas) — idem
- `researcher_modules/constants.py` (322 linhas) — vai para `sdd/constraints.py`
- `tools/search_tool.py` — refatorar para `BaseTool`, não deletar
- `CACHE_BREAKPOINT` do `PromptManager` — lógica única para Anthropic caching

---

### Chroma — integração profunda com LangChain

`ResearchChroma` tem ~370 linhas. Aproximadamente 270 são infraestrutura manual que LangChain já entrega. Apenas ~100 são lógica específica do projeto que vale preservar.

**O que existe hoje de forma manual e o substituto:**

| Camada manual atual | Linhas | Substituto LangChain |
|---|---|---|
| `chromadb.PersistentClient(path=...)` | ~15 | `langchain_chroma.Chroma(persist_directory=...)` |
| `chromadb.utils.embedding_functions` + config via env var | ~25 | `OllamaEmbeddings(model=..., base_url=...)` |
| `chunk_content()` + `split_long_text()` custom | ~40 | `RecursiveCharacterTextSplitter(chunk_size=650, chunk_overlap=120)` |
| Dicts manuais `{id, content, metadata, tool, url}` | ~20 | `Document(page_content=..., metadata={...})` |
| 5 métodos de query com `k` fixo cada | ~60 | `vectorstore.as_retriever(search_kwargs={"k": N, "filter": {"tool": X}})` |
| Deduplicação manual por ID | ~15 | `vectorstore.add_documents()` gerencia por ID nativamente |
| **Total substituível** | **~175** | |

**O que permanece como lógica própria do projeto (~95 linhas):**

| Método | Por quê fica |
|---|---|
| `find_research_context(ferramentas, foco)` | Fachada com semântica de domínio — nome comunica intenção |
| `find_analysis_patterns(ferramentas, foco)` | Idem |
| `find_writing_examples(ferramentas)` | Idem |
| `find_historical_articles(ferramentas)` | Idem |
| `cross_tool_search(query, tools)` | Lógica multi-ferramenta específica deste projeto |
| `get_tool_coverage(tool)` | Observabilidade: quantos chunks existem por ferramenta |
| `parse_primary_tool(ferramentas)` | Parser de string de entrada do projeto (renomeado: sem `_`) |

Esses métodos ficam, mas internamente chamam `vectorstore.similarity_search()` com filtros — não ChromaDB raw.

**Como o retriever integra com LangGraph:**

`langchain_chroma.Chroma.as_retriever()` retorna um `BaseRetriever` padrão do LangChain. O nó `evidence` no grafo pode invocar diretamente sem adaptador. O resultado já vem como lista de `Document` com metadata, pronto para montar o `EvidencePack`.

```python
# sdd/agents/evidence.py — padrão do nó após refatoração
retriever = chroma.as_retriever(search_kwargs={"k": 5, "filter": {"tool": primary_tool}})
docs = retriever.invoke(query)  # BaseRetriever — interface padrão LangChain
evidence_pack = build_pack_from_docs(docs)
```

**Regra de acesso (repetida aqui por ser crítica):**

Após a Fase 4, apenas `sdd/agents/evidence.py` importa `ResearchChroma`. Os outros 4 pontos de acesso atuais (`analyst`, `writer`, `critic`, `enrichment/coordinator`) são removidos ao reescrever os agentes. Eles recebem o `EvidencePack` pronto — não sabem que Chroma existe.

**Resultado final:** `ResearchChroma` passa de ~370 para ~100 linhas. Toda a camada de infraestrutura (embedding setup, chunking, collection management, deduplication) some e é gerenciada pelo LangChain.

---

## 7. Mapa Completo: O que Fazer com Cada Arquivo

### Deletar direto (sem reaproveitamento)

```
llm/circuit_breaker.py             — with_fallbacks() do LangChain
llm/fallback.py                    — absorvido por with_fallbacks()
llm/structured.py                  — with_structured_output() do LangChain
memory/memory_store.py             — event log → graph.stream(); learn/recall → InMemoryStore
memory/research_persistence.py     — código morto, nunca chamado
pipeline.py                        — lógica vai para nós do grafo
pipeline_stages/                   — duplicata de skills/, inteiro
enrichment/coordinator.py          — absorvido pelo nó de enriquecimento
orchestration/langgraph_runner.py  — reescrito limpo em graph/
orchestration/decision.py          — lógica portada para graph/routing.py
skills/prompts/manager.py          — ChatPromptTemplate do LangChain
researcher_modules/run_flow.py     — desaparece: nó chama researcher.run() diretamente
```

### Modificar (não usar como está)

```
llm/client.py              — duas mudanças obrigatórias:
                             1. remover imports de circuit_breaker (linha 11) e fallback (linha 16)
                                → substituir por with_fallbacks() do LangChain
                             2. remover método generate_structured()
                                → expor llm com .with_structured_output(Schema)

llm/token_counter.py       — substituir count_tokens() por model.get_num_tokens()
                             manter arquivo apenas se ainda usado após migração do client.py

memory/research_chroma.py  — refatorar internamente (fachadas de domínio preservadas):
                             · chromadb.PersistentClient → langchain_chroma.Chroma
                             · chromadb.utils.embedding_functions → OllamaEmbeddings
                             · chunking manual → RecursiveCharacterTextSplitter(chunk_size=650, chunk_overlap=120)
                             · 5 métodos de query → similarity_search() com filtros de metadata
                             · renomear _parse_primary_tool → parse_primary_tool (sem prefixo _)
                             · manter como fachadas: find_research_context, find_analysis_patterns,
                               find_writing_examples, find_historical_articles, cross_tool_search, get_tool_coverage

tools/search_tool.py       — refatorar para BaseTool do LangChain:
                             · manter: cache JSON TTL 24h, SourceRanker, search_multi com delay
                             · substituir: retry manual time.sleep → @retry do LangChain
                             · herdar BaseTool para integração nativa com LangGraph

researcher_modules/queries.py — substituir .replace("{tool}", tool) por PromptTemplate
                                 manter: dicionário FOCUS_QUERIES com templates por foco (lógica de domínio)
```

**Regra de acesso ao Chroma — escrita vs leitura:**
- `sdd/agents/researcher.py` **escreve** no Chroma: indexa conteúdo scrapeado via `save_scraped_content()`
- `sdd/agents/evidence.py` **lê** do Chroma: monta EvidencePack via `find_research_context()` e similares
- `analyst`, `writer`, `critic` **não acessam Chroma** — recebem EvidencePack pronto
- Os 4 acessos atuais em `skills/analyst.py`, `skills/writer.py`, `skills/critic.py`, `enrichment/coordinator.py` são removidos

### Mover sem alterar conteúdo

```
skills/schemas.py              → sdd/schemas.py  (atualizar todos os imports)
researcher_modules/constants.py → sdd/constraints.py  (renomear, mesmo conteúdo)
tools/source_ranker.py         → sdd/tools/source_ranker.py  (usado por search_tool)
skills/prompts/*.yaml          → prompts/*.yaml  (mesma raiz, sem mover — já estão lá)
validators/                    → validators/ (mesma raiz, sem mover)
evals/                         → evals/ (mesma raiz, sem mover)
```

### Ordem segura para limpar `sdd/researcher_modules/`

Objetivo: remover o que ainda sustenta a arquitetura antiga sem quebrar a lógica de domínio útil do pesquisador.

1. `constants.py` → mover para `sdd/constraints.py`
   Critério de saída: `sdd/agents/researcher.py`, `relevance.py`, `source_quality.py` e `queries.py` deixam de importar `sdd.researcher_modules.constants`.

2. `queries.py` → manter apenas o conteúdo de domínio
   Manter: `FOCUS_QUERIES`, templates por foco, builders conceituais.
   Remover/refatorar: substituição manual `.replace("{tool}", ...)` em favor de `PromptTemplate`.
   Critério de saída: o arquivo deixa de ser “infra manual de string templating”.

3. `run_flow.py` → remover
   Motivo: é o acoplamento mais explícito com a extração antiga do god object.
   Critério de saída: `ResearcherAgent.run()` chama helpers internos/instância diretamente, sem 35 funções injetadas.

4. `chain_run.py` → reavaliar após a remoção de `run_flow.py`
   Manter se continuar gerando artefato operacional realmente usado.
   Remover se for apenas lifecycle manual que poderia virar estado/evento do `graph.stream()`.

5. `debug_io.py` → manter por enquanto
   Motivo: ainda serve à estratégia atual de depuração via artefatos em `output/`.
   Só remover quando houver superfície equivalente e suficiente em `pipeline_events.jsonl` + `watch_events.py`.

6. `cached_search.py`, `context_builder.py`, `markdown.py`, `crawl4ai_config.py`, `scrape_async.py`, `scrape_threaded.py`, `reanalyze.py`, `relevance.py`, `source_quality.py`
   Status: manter.
   Motivo: continuam sendo lógica útil do pesquisador ou infraestrutura local de scrape/contexto sem substituto claro no handoff.

Regra prática:
- Primeiro mover `constants.py`
- Depois refatorar `queries.py`
- Depois eliminar `run_flow.py`
- Só então decidir `chain_run.py`
- O restante fica até aparecer um substituto melhor no runtime novo

### Reescrever (preservar lógica, trocar esqueleto)

```
skills/researcher.py       → sdd/agents/researcher.py  (usa SearchTool como BaseTool, indexa Chroma)
skills/analyst.py          → sdd/agents/analyst.py     (sem acesso direto ao Chroma)
skills/writer.py           → sdd/agents/writer.py      (sem ResearchPersistence, sem acesso ao Chroma)
skills/critic.py           → sdd/agents/critic.py      (sem acesso ao Chroma)
skills/evidence_builder.py → sdd/agents/evidence.py   (único leitor do Chroma)
```

### Manter sem alterar

```
llm/provider_config.py
spec/article_spec.yaml         (até Fase 2, depois substituído por sdd/config/)
spec/schema.json
skills/prompts/*.yaml          (conteúdo dos prompts — só o manager.py é deletado)
validators/spec_validator.py
validators/template_validator.py
evals/batch_runner.py
evals/cases.jsonl
examples.md
```

---

## 8. Nova Estrutura

```
sdd/
├── agents/
│   ├── researcher.py       busca + scrape + indexa Chroma
│   ├── evidence.py         monta EvidencePack a partir do Chroma
│   ├── analyst.py          gera análise estruturada
│   ├── writer.py           escreve artigo (evidence_pack obrigatório — TypeError sem ele)
│   └── critic.py           checks determinísticos + LLM semântico
│
├── checks/
│   ├── placeholder.py      detecta SEU_TOKEN, seu-repo, frases genéricas
│   ├── groundedness.py     URLs do artigo ∈ evidence_pack, exclui code blocks
│   ├── question_coverage.py perguntas métricas têm número ancorado no pack
│   └── structural.py       seções obrigatórias, min_refs, min_errors, min_tips
│
├── graph/
│   ├── state.py            PipelineState TypedDict com zonas: persistente / volátil por iteração
│   ├── nodes.py            cada nó chama agents/ ou checks/ diretamente — sem pipeline.py no meio
│   ├── routing.py          retry/enrich/finalize determinístico (portado de orchestration/decision.py)
│   └── runner.py           graph.compile() + graph.stream(), sem lógica de negócio
│
├── config/
│   ├── quality.yaml        placeholders, min_refs, min_errors, url_patterns
│   ├── models.yaml         por papel: model + provider (explícito, sem heurístico de "/")
│   ├── pipeline.yaml       timeouts, max_iterations, max_enrichments
│   └── infra.yaml          scraper, skip_domains, search_queries
│
├── schemas.py              movido de skills/schemas.py (EvidencePack, ArticleResult, etc.)
├── constraints.py          regex patterns, thresholds, keyword lists — só para módulos dentro de sdd/
│
├── llm/                    client.py (modificado), provider_config.py, token_counter.py (structured.py deletado)
├── memory/                 research_chroma.py apenas
├── tools/                  search_tool.py (refatorado para BaseTool), source_ranker.py (movido de tools/)
├── prompts/                sem alteração
├── validators/             sem alteração
├── evals/                  sem alteração
│
├── main.py                 coleta inputs, chama graph/runner.py
└── tests/                  migrados + novos por check e agente
```

**Regra dos nós:** cada nó chama o agente diretamente. Sem intermediário. Sem método em arquivo separado.

```python
# graph/nodes.py — padrão de todos os nós
def node_writer(state: PipelineState) -> PipelineState:
    result = writer.run(
        evidence_pack=state["evidence_pack"],
        analysis=state["analysis"],
        correction=state.get("correction"),
    )
    return {"article": result.text, "article_meta": result.meta}
```

**Regra do evidence pack:** `writer.run()` sem `evidence_pack` levanta `TypeError`. O type system impede chamada incompleta. O grafo não chega no writer sem evidence pack construído.

**Regra do provider:** declarado em `config/models.yaml`, lido diretamente por `llm/client.py`. Sem heurístico.

```yaml
# config/models.yaml
researcher:
  model: "z-ai/glm-4.5-air:free"
  provider: openrouter
critic:
  model: "gemma4:26b"
  provider: ollama
```

---

## 9. Fases de Execução

Cada fase tem critério de saída. Só avança quando o critério passa. Sem exceção.

---

**Fase 1 — Estrutura e limpeza** · Modelo: Haiku · 1 sessão

O que fazer:
1. Criar diretório `sdd/` com `__init__.py` vazio
2. Criar subdiretórios vazios: `agents/`, `checks/`, `graph/`, `config/`
3. Deletar: `llm/circuit_breaker.py`, `llm/fallback.py`, `memory/research_persistence.py`
4. Modificar `llm/client.py`: remover imports das linhas 11–16, substituir por `with_fallbacks()`
5. Mover `skills/schemas.py` → `sdd/schemas.py`, atualizar todos os imports
6. Criar `sdd/constraints.py` vazio
7. Atualizar `pyproject.toml`: adicionar `sdd` como pacote

→ verificar: `uv run pytest -q` passa sem alteração · `from sdd.schemas import EvidencePack` funciona

---

**Fase 2 — Config** · Modelo: Sonnet · 1 sessão

O que fazer:
1. Quebrar `spec/article_spec.yaml` em 4 arquivos dentro de `sdd/config/`:
   - `quality.yaml`: placeholders, min_refs, min_errors, url_patterns
   - `models.yaml`: por papel com campo `provider:` explícito
   - `pipeline.yaml`: timeouts, max_iterations, max_enrichments, max_stagnant
   - `infra.yaml`: scraper config, skip_domains, search_queries
2. Atualizar `validators/spec_validator.py` para validar os 4 arquivos novos
3. Manter `spec/article_spec.yaml` intacto até testes existentes serem migrados (Fase 6)

→ verificar: spec_validator aceita os 4 novos YAMLs · `uv run pytest -q` passa

---

**Fase 3 — Checks** · Modelo: Sonnet · 1 sessão

O que fazer (cada check = função pura: recebe artigo + contexto, retorna `list[str]` de problemas):
1. `sdd/checks/groundedness.py`: extrair do critic atual + adicionar exclusão de code blocks (regex ```` ```[\s\S]*?``` ````)
2. `sdd/checks/placeholder.py`: extrair do critic atual + adicionar `SEU_TOKEN`, `seu-repo`, `SEU-TOKEN`
3. `sdd/checks/question_coverage.py`: extrair do critic atual + verificar se número vem do evidence pack
4. `sdd/checks/structural.py`: seções obrigatórias, min_refs, min_errors, min_tips
5. Escrever teste unitário por check — input artigo falho → lista de problemas esperada

Ordem de execução dos checks (hardcoded em `sdd/checks/__init__.py`):
```
1. placeholder      (0ms) — falha: não chama LLM
2. groundedness     (0ms) — falha: não chama LLM
3. question_coverage (0ms) — falha: não chama LLM
4. structural       (0ms) — falha: não chama LLM
5. semantic (LLM)         — só executa se os 4 anteriores passaram
```

→ verificar: `uv run pytest tests/test_checks/ -q` passa · `seu-repo` em bloco bash não reprova

---

**Fase 4 — Agentes** · Modelo: Sonnet · 2 sessões

Cada agente em `sdd/agents/`: lê config de `sdd/config/models.yaml`, carrega prompt de `prompts/`, chama `llm/client.py`, valida output com schema de `sdd/schemas.py`. Nenhum agente importa outro agente.

1. `researcher.py`: busca + scrape + indexa Chroma
2. `evidence.py`: monta EvidencePack a partir do Chroma
3. `analyst.py`: gera análise estruturada a partir do EvidencePack
4. `writer.py`: `run(evidence_pack, analysis, correction=None)` — `evidence_pack` sem default, `TypeError` se omitido
5. `critic.py`: recebe artigo + contexto, chama checks em ordem, chama LLM semântico se todos passarem

→ verificar: cada agente tem teste de contrato (input válido → output com schema correto · input inválido → erro esperado)

---

**Fase 5 — Grafo** · Modelo: Sonnet · 1 sessão

1. `sdd/graph/state.py`: `PipelineState` TypedDict com duas zonas:
   - Persistente entre iterações: `evidence_pack`, `analysis`, `article_v1`, `iteration`, `stagnant_count`
   - Volátil por iteração: `article`, `critic_result`, `correction`
2. `sdd/graph/nodes.py`: um nó por agente, chamada direta sem intermediário
3. `sdd/graph/routing.py`: lógica de `orchestration/decision.py` portada — `FINALIZE_APPROVED`, `FINALIZE_INCOMPLETE`, `RETRY_WRITER`, `ENRICH_RESEARCH`
4. `sdd/graph/runner.py`:
   - `graph.compile(checkpointer=MemorySaver())`
   - `graph.stream(inputs, stream_mode="updates")` → grava `output/pipeline_events.jsonl`
   - Sem lógica de negócio — só monta e executa

**Observabilidade (decisão para esta fase):** usar **LangSmith** (cloud, já integrado ao LangChain via `LANGSMITH_API_KEY`) ou **Langfuse** (self-hosted, `langfuse` + `langfuse.integrations.langchain`). O `graph.stream()` gera o `pipeline_events.jsonl` local independentemente da escolha. A integração com LangSmith ou Langfuse é opcional e entra aqui — não antes, pois depende do grafo pronto.

Recomendação: LangSmith para desenvolvimento (zero config, dashboard imediato), Langfuse para produção (dados locais, sem custo por trace).

→ verificar: fluxo completo com mocks (0 chamadas LLM reais) · `pipeline_events.jsonl` gerado via stream · `MemorySaver` retoma de onde parou

---

**Fase 6 — Integração e testes** · Modelo: Sonnet · 1 sessão

1. Migrar testes existentes: substituir imports de `skills.*` por `sdd.*`

→ verificar: contagem de testes

---

**Fase 7 — Delete final** · Modelo: Haiku · 30 min

```bash
rm -rf pipeline.py pipeline_stages/ enrichment/ orchestration/
rm -rf skills/  # exceto schemas.py que já foi movido para sdd/schemas.py na Fase 1
```

→ verificar: `uv run pytest -q` passa · `grep -r "from pipeline\|from skills\|from orchestration\|from enrichment" . --include="*.py"` retorna vazio

---

**Fase 8 — Code review** · Modelo: Sonnet · subagente

Rodar `/ultrareview` ou `code-reviewer` subagente. Só aqui. Não antes.

---

## 10. O que Melhora Automaticamente (sem esforço extra)

| Melhoria | Como acontece |
|---|---|
| Code block exclusion no groundedness | `checks/` escrito do zero, sem herança de lógica antiga |
| Provider explícito | `config/models.yaml` com campo `provider:` |
| Enrich cirúrgico | Nó de enriquecimento conhece só os gaps |
| Diff entre iterações | `article_v1` separado no state |
| Checks em ordem garantida | `checks/__init__.py` define sequência hardcoded |
| Event log sem código manual | `graph.stream()` no runner |
| Pipeline retomável | `MemorySaver` checkpointer ativo |

## 11. O que Precisa de Esforço Extra (pós-reconstrução)

- Few-shot de artigos aprovados no prompt do writer
- Evidence traceability: número no artigo → `EvidenceItem` no pack
- Score por seção para rastrear evolução de qualidade
- `min_references` com peso por tipo de fonte
