# SDD Tech Writer

Gerador de artigos técnicos com pipeline em 4 etapas:
1. pesquisa
2. análise
3. escrita
4. validação automática

Você informa ferramentas + contexto + perguntas, e o sistema gera um artigo em Markdown.

## O que este projeto faz

- Busca dados na web (DuckDuckGo + scraping)
- Estrutura análise técnica
- Escreve artigo com template consistente
- Reprova automaticamente artigo ruim e tenta corrigir (até 3 iterações)
- Salva saídas e métricas em disco

## Arquitetura rápida

- `skills/researcher.py`: pesquisa e extração
- `skills/analyst.py`: análise técnica
- `skills/writer.py`: geração do artigo
- `skills/critic.py`: validação
- `pipeline.py`: orquestração
- `spec/article_spec.yaml`: regras, validação e parâmetros de geração
- `.env`: seleção de provider e modelos em runtime

## Modos de LLM suportados

- `openrouter_free`
- `ollama_local`
- `ollama_cloud`

A escolha é feita por `LLM_PROVIDER` no `.env`.

## Quickstart

### 1) Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

Opcional (melhora scraping em páginas JS):
- `playwright` + Chromium

### 2) Instalação

```bash
git clone <seu-repositorio>
cd sdd-ollama

uv venv --python 3.12
source .venv/bin/activate
uv sync
```

Se precisar de fallback JS no scraping:

```bash
uv add playwright
playwright install chromium
```

### 3) Configuração de LLM

Copie o exemplo:

```bash
cp .env.example .env
```

Preencha no mínimo:

```env
LLM_PROVIDER=openrouter_free

LLM_MODEL_RESEARCHER=z-ai/glm-4.5-air:free
LLM_MODEL_ANALYST=z-ai/glm-4.5-air:free
LLM_MODEL_WRITER=z-ai/glm-4.5-air:free
LLM_MODEL_CRITIC=z-ai/glm-4.5-air:free
```

Se usar `openrouter_free`, também precisa:

```env
OPENROUTER_API_KEY=sk-or-v1-sua-chave
```

Se usar `ollama_local`:

```env
LLM_PROVIDER=ollama_local
# opcional
# OLLAMA_LOCAL_BASE_URL=http://localhost:11434
```

E garanta que o Ollama esteja de pé:

```bash
ollama list
curl http://localhost:11434
```

Se usar `ollama_cloud`:

```env
LLM_PROVIDER=ollama_cloud
# opcional
# OLLAMA_CLOUD_BASE_URL=https://ollama.com
# OLLAMA_CLOUD_API_KEY=
```

## Como rodar

```bash
python main.py
```

O CLI pede:
- ferramentas
- contexto
- foco
- perguntas obrigatórias
- checklist manual

## Saídas geradas

- `artigos/*.md`: artigo final
- `output/debug_research.md`: dados de pesquisa
- `output/debug_analysis.md`: análise intermediária
- `output/metrics.json`: métricas por execução
- `.memory/*.json`: memória entre execuções

## Configuração: quem controla o quê

- `.env`:
  - provider em runtime (`LLM_PROVIDER`)
  - modelos por role (`LLM_MODEL_*`)
- `spec/article_spec.yaml`:
  - regras de qualidade
  - seções obrigatórias
  - timeout/temperature/context_length
  - timeout global da execução (`pipeline.timeout_total_seconds`)
  - fallback de provider/modelos

## Limitações conhecidas

- OpenRouter free pode limitar requisições (429 em pico)
- Qualidade em `ollama_local` depende do modelo/hardware
- Scraping pode falhar em sites complexos (há fallback)
- Sem bons resultados de busca, o artigo fica mais raso

## Estrutura do projeto

```text
spec/        contrato e regras
skills/      etapas de geração
tools/       busca e scraping
validators/  validação determinística
memory/      persistência de memória
output/      artefatos de execução
artigos/     artigos finais
```

## Próximos passos recomendados

1. Testar com `openrouter_free` para validar fluxo fim a fim
2. Trocar para `ollama_local` quando quiser custo zero recorrente
3. Ajustar `LLM_MODEL_*` por role para qualidade/velocidade
