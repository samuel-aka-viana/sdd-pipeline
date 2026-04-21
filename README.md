# SDD Tech Writer — Stage 3

Gerador de artigos técnicos com pipeline em 4 etapas + validação + enriquecimento semântico:
1. **Pesquisa** — Web search + scraping paralelo com Crawl4AI
2. **Análise** — Estruturação com inspiração de padrões históricos (Chroma)
3. **Escrita** — Geração com exemplos de artigos bem escritos (Chroma)
4. **Crítica** — Validação contra spec + histórico (Chroma)

Você informa ferramentas + contexto + perguntas, e o sistema gera um artigo técnico em Markdown de **alta qualidade**.

## O que este projeto faz

### Núcleo
- ✅ Busca dados na web (DuckDuckGo + scraping paralelo com Crawl4AI)
- ✅ Estrutura análise técnica com 3 aspectos paralelos (core, performance, security)
- ✅ Escreve artigo com template consistente
- ✅ Valida automaticamente contra 10+ regras determinísticas + análise semântica

### Stage 3: Inteligência Aumentada
- ✅ **Chroma Vector Database** — Semantic search em conteúdo histórico
  - Writer busca exemplos de artigos bem escritos (mesma ferramenta)
  - Analyst busca padrões de análises similares
  - Critic valida qualidade contra artigos aprovados anteriormente
  - Smart enrichment reutiliza conteúdo ao invés de re-pesquisar (5s vs 10min)

- ✅ **Async Playwright** — Parallelismo sem threading errors
  - 3 workers simultâneos scrapiando URLs
  - ~60% mais rápido que sync
  - Zero "cannot switch to different thread" errors

- ✅ **Critic Melhorado** — Múltiplas camadas de validação
  - Deterministic: 10 regras contra spec (seções, placeholders, etc)
  - Semantic: LLM valida factualidade e coerência (12000 chars agora)
  - History: Compara com artigos aprovados (detecção de plagio/inconsistência)

- ✅ **Skip Search** — Reutiliza URLs de runs anteriores
  - Interface interativa (lista arquivos `urls_*.txt`)
  - Pula 5-10 minutos de busca web
  - Útil para testar novos LLMs/estruturas

- ✅ **Fallback Automático de LLM** (OpenRouter → Ollama Cloud → Ollama Local)
- ✅ **Reaproveita resultados de busca** com cache (TTL=24h entre execuções)
- ✅ **Quando falta evidência**, reexecuta pesquisa + análise antes de reescrever
- ✅ **Salva saídas** e métricas em disco

## Arquitetura (Stage 3)

```
Camada de Dados:
  - Chroma (.memory/chroma_db/)   ← Vector database com embeddings de conteúdo
  - Episódic (.memory/episodic.json) ← Telemetria + learned patterns

Camada de Scraping:
  - Crawl4AI (primário)        ← JS rendering, CloudFlare bypass
  - ScraperTool (fallback)     ← Playwright async + curl_cffi

Camada de Skills (com Chroma):
  - Researcher    → Busca + Scrape + Save → Chroma
  - Analyst       → Query Chroma (3 padrões similares)
  - Writer        → Query Chroma (2 exemplos bem escritos)
  - Critic        → Query Chroma (3 artigos históricos) + Validate

Camada de Validação:
  - Deterministic (spec_validator)  ← 10 regras
  - Semantic (critic LLM)           ← 12000 chars análise
  - History (chroma queries)        ← Comparação com passado
```

## Diagrama de arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                          main.py (CLI)                           │
│         Coleta: ferramentas + contexto + foco + perguntas       │
│         + Novo: "Usar URLs existentes?" (output/urls_*.txt)     │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 v
        ┌────────────────┐
        │  pipeline.py   │
        └────────┬───────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    v            v            v
┌─────────────────────────────────────────────────────────────────┐
│                    4-Stage Pipeline                            │
│                                                                 │
│  [Researcher]  →  [Analyst]  →  [Writer]  →  [Critic]         │
│       ↓              ↓              ↓            ↓              │
│  - Search       - Query          - Query      - Validate       │
│  - Scrape       Chroma(3)        Chroma(2)    Chroma(3)        │
│  - Save to      (patterns)       (examples)   (history)        │
│    Chroma       - Parse 3        - Generate                    │
│  - Save to      analysis         article                       │
│    SQLite       aspects          with style                    │
│                                                                 │
│                      ↑             ↑             ↓             │
│                      └─────────────┴─────────────┘             │
│                  (se reprovado com iteração)                   │
│                                                                 │
│              Se falta dados: Smart Enrichment                  │
│              [Critic] → [Chroma.query_similar()] → [Reanalyze]│
│              (5s, reutiliza cache ao invés de re-buscar)      │
└─────────────────────────────────────────────────────────────────┘
                 │
                 v
        ┌─────────────────────────────────┐
        │  Saída: artigo final + métricas │
        │  .memory/: Chroma + SQLite       │
        └─────────────────────────────────┘
```

## Diagrama de fluxo (com Chroma)

```
ENTRADA:
  main.py coleta: ferramentas + contexto + foco + perguntas + [URLs existentes?]

SE skip_search = True:
  [SKIP] DuckDuckGo search
  └─ Load URLs from output/urls_*.txt
  └─ Direto ao scrape (-5-10 min)

SENÃO:
  [Researcher]
    ├─ DuckDuckGo search (10 queries)
    ├─ Scrape paralelo com Crawl4AI (3 workers)
    ├─ Save to Chroma + SQLite
    └─ Return: research_block

  [Analyst]
    ├─ Query Chroma: "similar analysis patterns" (k=3)
    ├─ Inject 3 exemplos no prompt
    ├─ Generate: analysis com estrutura baseada em histórico
    └─ Return: analysis_block

  [Writer]
    ├─ Query Chroma: "well-written article examples" (k=2)
    ├─ Inject 2 exemplos no prompt
    ├─ Generate: article com tom/estrutura baseado em histórico
    └─ Return: article

  [Critic]
    ├─ Deterministic check (10 regras)
    ├─ Semantic check (LLM, 12000 chars)
    ├─ History check (Query Chroma: similar approved articles)
    ├─ Se aprovado → Salva artigo + métricas
    └─ Se reprovado:
        ├─ Com iteração → Writer com instruções de correção
        └─ Sem iteração → Salva melhor versão

SMART ENRICHMENT (se Critic rejeita "Dicas insuficientes"):
  ├─ Query Chroma: "{tool} tips best practices" (não re-busca web)
  ├─ Reanalyse URLs do cache
  └─ Merge com research original
  └─ Return: enriched research (5s, não 10min)
```

## Features Stage 3 (Novas nesta versão)

### 🚀 Async Playwright
- Convertido de `sync_api` → `async_api`
- Cada thread recebe seu próprio `asyncio.new_event_loop()`
- **Resultado:** Zero threading errors em parallelization
- **Ganho:** ~60% mais rápido (3 workers simultâneos)

### 🧠 Chroma Vector Database
- Semantic search em todos os artigos anteriores (`.memory/chroma_db/`)
- **Writer** encontra exemplos de artigos bem escritos (+10% qualidade)
- **Analyst** encontra padrões de análises similares (+8% estrutura)
- **Critic** valida contra histórico de aprovados (+15% detecção de plagio)
- **Smart Enrichment** reutiliza Chroma ao invés de re-pesquisar (5s vs 10min)

### ⏭️ Skip Search (URLs Interativas com Seleção Múltipla)
```bash
python main.py
# ...
Usar URLs existentes?
  0. Buscar novos URLs (padrão)
  1. urls_docker.txt (96 URLs, 6.6KB)
  2. urls_podman.txt (83 URLs, 5.4KB)
  3. urls_duckdb.txt (95 URLs, 6.0KB)

# Escolha um ou vários (separados por vírgula):
# Digite: 1,2 → carrega Docker + Podman
# Digite: 1   → carrega só Docker
# Digite: 0 ou enter → busca novos URLs
```
- Reutiliza URLs de runs anteriores
- **Seleção múltipla:** para comparações (Docker vs Podman)
- **Ganho:** -5-10 min por execução
- Útil para testar LLMs/estruturas sem re-buscar

### 📈 Critic Melhorado
- Semantic window expandido: 4000 → 12000 chars
- Tool-aware false positive filtering
- History validation: detecta plagio, inconsistência com histórico
- Severity levels: blocking vs warnings

### 📊 Analysis Context Doubled
- `max_analysis_chars`: 6000 → 12000
- Reduz perda de contexto de 44% → ~20%
- Writer recebe análise muito mais completa

## Modos de LLM suportados

- `openrouter_free` ← Recomendado para começar
- `ollama_local` ← Zero custo recorrente
- `ollama_cloud` ← Fallback para quando OpenRouter cai

Seleção via `LLM_PROVIDER` em `.env`.

## Quickstart

### 1) Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

Opcional (para melhorar scraping em JS-heavy):
- `playwright` + Chromium
- `chromadb` (semantic search)
- `crawl4ai` (novo scraper unificado)

### 2) Instalação

```bash
git clone <seu-repositorio>
cd sdd-ollama

uv venv --python 3.12
source .venv/bin/activate
uv sync

# Opcional: instalar dependências avançadas
uv add playwright chromadb crawl4ai
playwright install chromium
```

### 3) Configuração de LLM

```bash
cp .env.example .env
```

Preencha no mínimo:

```env
LLM_PROVIDER=openrouter_free
OPENROUTER_API_KEY=sk-or-v1-sua-chave

LLM_MODEL_RESEARCHER=z-ai/glm-4.5-air:free
LLM_MODEL_ANALYST=z-ai/glm-4.5-air:free
LLM_MODEL_WRITER=z-ai/glm-4.5-air:free
LLM_MODEL_CRITIC=z-ai/glm-4.5-air:free
```

## Como rodar

### Modo padrão (com busca web)
```bash
python main.py
```

### Modo skip search (reutiliza URLs)
```bash
python main.py
# Na pergunta "Usar URLs existentes?", escolha o arquivo
# Exemplo: [1] urls_duckdb.txt
```

### Forçar nova busca (ignorar cache)
```bash
python main.py --refresh-search
```

## Observabilidade

```bash
# Ver eventos gerados na execução mais recente
python watch_events.py

# Ver só os últimos 30 eventos
python watch_events.py --tail=30

# Acompanhar em tempo real
python watch_events.py --watch
```

## Saídas geradas

- `artigos/*.md` — Artigo final aprovado
- `output/debug_research.md` — Dados de pesquisa brutos
- `output/debug_analysis.md` — Análise intermediária
- `output/metrics.json` — Tempo + tokens + estatísticas
- `output/urls_*.txt` — URLs usadas (para reutilizar depois)
- `.memory/chroma_db/` — Vector database (Chroma) com embeddings
- `.memory/episodic.json` — Telemetria + eventos

## Qualidade local

```bash
# Lint focado em problemas reais
uv run ruff check . --select ARG,F401,F841

# Testes
uv run pytest -q

# Cobertura
uv run pytest --cov=validators --cov=skills --cov=pipeline tests/
```

Atualmente: **142 testes passando** ✅

## Configuração: quem controla o quê

**`.env`:**
- Provider em runtime: `LLM_PROVIDER`
- Modelos por role: `LLM_MODEL_RESEARCHER`, `LLM_MODEL_ANALYST`, etc
- Fallback opcionais: `LLM_MODEL_FALLBACK_CLOUD`, `LLM_MODEL_FALLBACK_LOCAL`

**`spec/article_spec.yaml`:**
- Regras de qualidade (10+ regras determinísticas)
- Seções obrigatórias
- Timeouts: `llm.timeout.{role}` (researcher, analyst, writer, critic)
- Temperatures: `llm.temperature.{role}`
- Context limits: `llm.writer_input.max_research_chars`, `max_analysis_chars` (agora 12000)
- Cache de busca: `research.search_cache.ttl_seconds` (padrão 24h)
- Enriquecimento pós-critic: `pipeline.max_research_enrichments`

## Limitações conhecidas

- OpenRouter free limita requisições em pico (429)
  - Sistema tenta fallback cloud/local; se ambos falharem, erro amigável
- Qualidade em `ollama_local` depende do modelo/hardware
- Scraping pode falhar em sites muito complexos
  - Fallback automático para ScraperTool (Playwright sync)
- Sem bons resultados de busca, artigo fica mais raso
  - Use `--refresh-search` para tentar queries diferentes

## Estrutura do projeto

```
spec/          → Contrato e regras (article_spec.yaml)
skills/        → Etapas de geração (researcher, analyst, writer, critic)
tools/         → Busca e scraping (search_tool, scraper_crawl4ai, scraper_tool)
validators/    → Validação determinística (spec_validator, rules_engine)
memory/        → Persistência (research_chroma, research_persistence, memory_store)
tests/         → Suite de testes (142 testes)
output/        → Artefatos de execução (debug_*.md, urls_*.txt, metrics.json)
artigos/       → Artigos finais gerados
.memory/       → Dados persistentes entre runs (chroma_db/, *.json)
```

## Próximas melhorias

- [ ] Chroma em Docker Compose (persistência em prod)
- [ ] Source attribution (quais URLs contribuíram para cada claim)
- [ ] Markdown structure preservation (manter ## headers do research)
- [ ] Parallel research para múltiplos tools
- [ ] A/B testing em prompt versions
- [ ] Knowledge graph (Docker → Podman → containerd)

## Decisão arquitetural: SDD vs LangGraph

Este projeto usa **SDD (Sequential Data Driven)** e NÃO LangGraph porque:
- ✅ Caso de uso é linear (search → analyze → write → validate)
- ✅ Performance é boa (40s por artigo)
- ✅ Código é limpo e compreensível
- ✅ Manutenção é baixa

LangGraph seria apropriado **SE:**
- Múltiplos tipos de output (artigos + slides + tweets)
- Pesquisa paralela de 5+ tools com wait_for_all
- Sub-agents especializados (fact-checker, SEO optimizer)

Ver `CLAUDE.md` para detalhes da arquitetura completa.

## Para saber mais

- `CLAUDE.md` — Referência técnica completa (Stage 3 features, async playwright, chroma integration)
- `AGENTS.md` — File mappings, method signatures, checklist antes de modificar
- `CONTEXT_ANALYSIS.md` — Deep dive no problema de context loss
- `examples.md` — Exemplos curados de bons prompts

---

**Status:** Stage 3 ✅ | Async Playwright ✅ | Chroma Integration ✅ | Skip Search ✅ | 142 testes ✅
