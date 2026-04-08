# SDD Tech Writer

Gerador de artigos técnicos comparativos usando LLMs locais via Ollama.

Você informa as ferramentas, o contexto de uso e as perguntas que o artigo deve responder. O sistema pesquisa (via DuckDuckGo + scraping), analisa, escreve e valida. Tudo roda na sua máquina sem enviar dados para APIs pagas ou depender de chaves externas.

---

## Por que SDD

SDD (Spec-Driven Development) é uma abordagem onde a **especificação é a fonte de verdade**, não o código ou o texto gerado. Todo output deriva de um contrato formal definido antes da execução.

No desenvolvimento tradicional de conteúdo técnico, o que é um "bom artigo" vive na cabeça de quem escreve. Aqui, vive em `spec/article_spec.yaml`. Isso significa que:

- O modelo não decide o que é aceitável. A spec decide.
- A validação é determinística e não subjetiva.
- Quando a spec muda, o comportamento muda junto em todo o pipeline.

O resultado prático é que o sistema **rejeita outputs ruins automaticamente** e tenta corrigir antes de entregar.

---

## O que está sendo usado e por quê

### Spec (`spec/article_spec.yaml`)
Define o contrato do artigo: seções obrigatórias, regras de qualidade, configuração do scraper, modelos a usar e configuração do Ollama. É o único arquivo que você precisa editar para mudar o comportamento global do sistema.

### Skills
Cada etapa do pipeline é uma classe especializada com responsabilidade única. Modelos locais menores performam melhor em tarefas focadas do que em prompts gigantes que pedem tudo de uma vez.

| Skill | Responsabilidade |
|-------|-----------------|
| `ResearcherSkill` | Busca na web (DuckDuckGo) + scraping (Trafilatura/curl_cffi/Playwright) para extrair dados factuais |
| `AnalystSkill` | Transforma dados brutos em análise (comparativa, integração ou ferramenta única) |
| `WriterSkill` | Monta o artigo seguindo a spec |
| `CriticSkill` | Valida o artigo em duas camadas |

### Critic em duas camadas
**Camada 1 (Determinística):** Verifica estrutura, placeholders, URLs inventadas, soluções vazias e mínimos de qualidade. Sem LLM, sem custo de tokens, sempre confiável.

**Camada 2 (Semântica):** Pergunta ao modelo se há contradições internas, comandos inexistentes ou números impossíveis. Só roda se a camada 1 passou. Problemas semânticos agora também reprovam o artigo e geram correções.

Se o artigo reprovar, o pipeline tenta corrigir automaticamente (máximo 3 iterações) antes de salvar.

### Memory
O sistema aprende entre execuções. Quando uma correção resolve um problema recorrente, isso é salvo e injetado como contexto nas próximas execuções. Lições são priorizadas por frequência de uso, não apenas por recência.

| Tipo | O que guarda |
|------|-------------|
| Working | Estado da sessão atual |
| Episódica | Log do que aconteceu (persistente, com rotação) |
| Procedural | Receitas de correção que funcionaram |

### Observability
Cada etapa mostra spinner, tempo de execução e resultado em tempo real. Métricas de cada execução são salvas em `output/metrics.json` para análise posterior.

---

## Estrutura do projeto

```text
projeto/
├── spec/
│   └── article_spec.yaml      # contrato - edite aqui para mudar comportamento
├── memory/
│   └── memory_store.py        # memória persistente entre execuções
├── validators/
│   └── spec_validator.py      # validação determinística
├── skills/
│   ├── researcher.py          # busca e extração de dados
│   ├── analyst.py             # análise comparativa / integração / single
│   ├── writer.py              # geração do artigo
│   └── critic.py              # validação em duas camadas
├── tools/
│   ├── search_tool.py         # integração DuckDuckGo (com retry)
│   └── scraper_tool.py        # extração de conteúdo (Trafilatura + curl_cffi + Playwright)
├── logger.py                  # output visual com Rich
├── pipeline.py                # orquestração do fluxo
├── main.py                    # CLI interativo
├── .memory/                   # criado automaticamente
├── output/                    # criado automaticamente
└── artigos/                   # artigos gerados
```

---

## Instalação

### 1. Pré-requisitos

**Rust** (necessário para compilar dependências Python):
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
rustup default stable
```

**Ollama:**
```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# baixe em https://ollama.com/download/windows
```

**uv** (gerenciador de pacotes):
```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone e configure o projeto

```bash
git clone <seu-repositorio>
cd sdd-ollama

# cria ambiente virtual com Python 3.12
uv venv --python 3.12
uv add ollama requests python-dotenv pyyaml rich duckduckgo-search trafilatura curl_cffi

# opcional — fallback para páginas JavaScript-heavy
uv add playwright
playwright install chromium
```

### 3. Baixe os modelos

Escolha os modelos de acordo com o seu hardware.

**8GB de RAM (sem GPU dedicada):**
```bash
ollama pull qwen3:8b
```

**32GB de RAM + 8GB de VRAM (recomendado):**
```bash
ollama pull qwen3:8b          # researcher, analyst, critic
ollama pull qwen3:30b-a3b     # writer (MoE — só 3B ativos por token)
```

Verifique se estão disponíveis:
```bash
ollama list
```

### 4. Verifique a configuração

Nenhuma chave de API é necessária. Confirme apenas que o Ollama está rodando:
```bash
curl http://localhost:11434
# deve retornar: Ollama is running
```

---

## Uso

```bash
python main.py
```

O CLI vai guiar você por cinco etapas:

**1. Ferramentas** (o que você quer comparar ou analisar):
```text
podman e docker
kafka e flink
ollama
prometheus e grafana
```

**2. Contexto** (para qual situação específica):
```text
ambiente de desenvolvimento local no Linux
pipeline de ingestão de logs em tempo real
rodando LLMs com até 8GB de RAM
observability em stack FastAPI com docker compose
```

**3. Foco** (qual aspecto aprofundar):
```text
1. comparação geral
2. performance / throughput
3. custo
4. migração
5. integração
6. segurança
7. hardware limitado / edge
8. quantização / modelos locais
```

**4. Perguntas** (o que o artigo deve responder explicitamente):
```text
como configurar modo rootless?
docker-compose funciona sem mudanças no podman?
qual tem menor uso de RAM em idle?
[enter para terminar]
```

**5. Critérios de validação** (checklist manual após a geração):
```text
menciona que podman é daemonless
tem tabela comparativa com pelo menos 4 critérios
[enter para terminar]
```

---

## O que é gerado

```text
artigos/
└── podman-e-docker_20250407_1430.md   # artigo final

output/
├── debug_research.md                  # dados brutos da pesquisa
├── debug_analysis.md                  # análise antes da escrita
├── urls_podman.txt                    # URLs consultadas por ferramenta
├── urls_docker.txt
└── metrics.json                       # métricas de cada execução

.memory/
├── episodic.json                      # log de eventos
└── procedural.json                    # correções que funcionaram
```

---

## Configuração avançada

Edite `spec/article_spec.yaml` para personalizar.

```yaml
# modelos — ajuste ao seu hardware
models:
  researcher: "qwen3:8b"
  analyst:    "qwen3:8b"
  writer:     "qwen3:30b-a3b"   # fallback: qwen3:14b se ficar lento
  critic:     "qwen3:8b"

# temperatura
ollama:
  temperature:
    researcher: 0.1   # mais baixo = mais factual
    writer:     0.3   # mais alto = mais criativo

# contexto por role
  context_length:
    default: 8192
    writer:  16384

# scraper
research:
  scraper:
    max_chars_per_page: 4000
    max_scrapes_per_tool: 10
    timeout_seconds: 15

# regras de qualidade
article:
  quality_rules:
    min_references: 3
    min_errors: 2
    min_solution_chars: 20
```

---

## Limitações Críticas e Conhecidas

**Scraping pode falhar em páginas JavaScript-heavy.** O sistema tenta 3 estratégias em cascata: curl_cffi (bypass Cloudflare básico) → Trafilatura (extração HTML estático) → Playwright (renderização JS completa). Se todas falharem, usa o snippet do DuckDuckGo como fallback.

**Rate Limits do DuckDuckGo.** A busca usa a API não-oficial do DuckDuckGo com delay de 1.5s entre queries e retry automático. Ainda assim, rodar o pipeline muitas vezes em sequência pode resultar em bloqueio temporário do seu IP.

**Atenção aos limites de memória RAM.** O modelo `qwen3:30b-a3b` é MoE e roda com offload, mas ainda exige 32GB de RAM. Se seu hardware for mais limitado, use `qwen3:8b` em todos os roles.

**Ferramentas obscuras geram artigos mais rasos.** Se o DuckDuckGo não retorna bons resultados e o scraper falha nas páginas encontradas, o artigo vai ter lacunas. O sistema agora omite dados ao invés de inventar, mas o conteúdo será mais curto.

---

## Como a memória melhora o sistema ao longo do tempo

Na primeira execução a memória está vazia. O sistema se comporta como qualquer pipeline sem estado.

A partir da segunda execução, se houve correções na primeira, essas lições são injetadas no contexto do writer antes de gerar. Lições são priorizadas por frequência de uso — correções que resolveram problemas em múltiplas execuções aparecem primeiro.

Para inspecionar o que foi aprendido:
```bash
cat .memory/procedural.json
cat .memory/episodic.json
```

### Referência rápida — qual foco usar

| Situação | Foco recomendado |
|----------|-----------------|
| Duas ferramentas que fazem a mesma coisa | comparação geral |
| Preciso decidir qual adotar para o time | comparação geral |
| Ferramentas que trabalham juntas | integração |
| Hardware com pouca RAM ou CPU | hardware limitado / edge |
| Rodando modelos de IA localmente | quantização / modelos locais |
| Migrando de uma ferramenta para outra | migração |
| Custo é o critério principal | custo |
| Ambiente de produção com requisitos de segurança | segurança |
| Pipeline de dados com volume alto | performance / throughput |

---

## Roadmap

- [x] ~~Plugar extrator de web scraping (Trafilatura) para ler conteúdo completo das páginas~~
- [x] ~~Bypass Cloudflare básico com curl_cffi~~
- [ ] Fallback com Playwright para páginas JavaScript-heavy que o Trafilatura não consegue extrair
- [ ] Testes unitários para componentes determinísticos (validator, memory, search)
- [ ] Feedback loop: checklist manual alimenta a memória automaticamente
- [ ] Observability persistente com histórico de execuções
- [ ] Suporte a múltiplos idiomas na spec