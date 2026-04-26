# Handoff - Pipeline Evidence Pack Refactor

Data: 2026-04-25

## Objetivo

Refatorar o pipeline para reduzir ruido entre estagios e tornar a geracao do
artigo mais auditavel. O ponto central e trocar o fluxo baseado em "research
textao" por um pacote estruturado de evidencias que seja consumido pelo analyst,
writer e critic.

Nao implementar nesta rodada:
- Langfuse.
- Multi-agent novo.
- Tracing externo sofisticado.
- Mudanca de provider/modelo como solucao principal.

## Estado Atual Confirmado

Fluxo atual:

```text
main.py
  -> SDDPipeline.run(...)
    -> LangGraphOrchestrator.run(...)
      -> bootstrap
      -> research
      -> relevance_filter
      -> analysis
      -> start_write
      -> writer
      -> question_coverage
      -> critic
      -> after_failure, se reprovar
      -> writer de novo, se retry
      -> finalize
    -> salva artigo em artigos/<slug>_<timestamp>.md
```

Arquivos importantes:
- `orchestration/langgraph_runner.py`: grafo LangGraph e estado entre nos.
- `pipeline_stages/research.py`: gera `research` e salva historico por ferramenta.
- `pipeline_stages/relevance.py`: hoje adiciona anotacao de URLs priorizadas.
- `pipeline_stages/analysis.py`: chama `AnalystSkill`.
- `pipeline_stages/writer.py`: chama `WriterSkill`.
- `pipeline_stages/critic.py`: chama `CriticSkill`.
- `skills/relevance_filter.py`: ranking atual de URLs.
- `skills/analyst.py`: monta prompt do analyst.
- `skills/writer.py`: compacta research/analysis e chama writer.
- `skills/critic.py`: validacao deterministica e semantica.
- `skills/schemas.py`: lugar natural para contratos Pydantic novos.
- `spec/article_spec.yaml` e `spec/schema.json`: config e validacao da spec.
- `watch_events.py`: unica superficie detalhada de observabilidade.

Artefatos atuais em `output/`:
- `debug_context_<tool>.md`: contexto bruto do scraping.
- `debug_research_<tool>.md`: sintese do researcher por ferramenta.
- `debug_research.md`: consolidado atual, redundante.
- `debug_research_filtered.md`: research + anotacao de URLs priorizadas, redundante/confuso.
- `debug_analysis.md`: saida humana do analyst.
- `debug_html_<tool>/`: HTML bruto por URL, muito ruidoso para default.
- `pipeline_events.jsonl`: evento canonico para observabilidade.
- `chains/`: fases por ferramenta/run.

## Decisoes Ja Tomadas

1. O analyst nao deve mais depender do `research` bruto/textao como entrada
   principal. Ele deve ler um `EvidencePack` estruturado.
2. O `relevance_filter` atual deve ser substituido por um `evidence_builder`
   real. O nome "filtered" e enganoso porque hoje ele nao remove o research
   original, so adiciona anotacao.
3. O critic deve validar groundedness contra as URLs/fontes presentes no
   `EvidencePack`.
4. Recuperacao pos-critic deve continuar cache/Chroma-only. Nao reintroduzir
   busca web nesse fluxo.
5. Verificacao local deve seguir a ordem do repo: `pytest` primeiro, depois
   `ruff`.

## Lista De Tarefas

### 1. Limpar artefatos/debug

Objetivo:
- reduzir ambiguidade sobre "qual arquivo o proximo estagio leu".

Implementar:
- Parar de salvar `output/debug_research.md` por default.
- Parar de salvar `output/debug_research_filtered.md`.
- Manter `output/debug_research_<tool>.md`.
- Manter `output/debug_context_<tool>.md`.
- Colocar HTML debug atras de config/env desligado por default.

Arquivos provaveis:
- `pipeline_stages/research.py`
- `pipeline_stages/relevance.py` ou seu substituto
- `pipeline.py`
- `researcher_modules/constants.py`
- `researcher_modules/debug_io.py`
- `spec/article_spec.yaml`
- `spec/schema.json`
- `README.md`
- `AGENTS.md`

Testes esperados:
- Teste garantindo que research por ferramenta continua salvo.
- Teste garantindo que debug consolidado/filtered nao e salvo por default.
- Teste garantindo que HTML debug respeita config/env.

### 2. Criar EvidencePack

Objetivo:
- transformar research bruto em contrato estruturado de evidencias.

Contrato inicial sugerido:

```python
class EvidenceItem(BaseModel):
    id: str
    tool: str
    topic: str
    claim: str
    source_url: str
    source_title: str = ""
    source_quality: str = "unknown"
    evidence: str
    confidence: float = 0.0

class EvidenceGap(BaseModel):
    topic: str
    reason: str

class EvidencePack(BaseModel):
    ferramentas: str
    foco: str
    total_urls_found: int = 0
    retained_urls: list[str] = []
    items: list[EvidenceItem] = []
    gaps: list[EvidenceGap] = []
```

Implementar:
- Novo modulo/skill para construir evidence pack.
- Pode reaproveitar heuristicas de `skills/relevance_filter.py`.
- Salvar `output/evidence_pack.json`.
- Opcional: salvar `output/evidence_pack.md` como visao humana se for util.
- Registrar evento `evidence_pack_built` em `pipeline_events.jsonl`.

Arquivos provaveis:
- `skills/evidence_builder.py` novo
- `pipeline_stages/evidence.py` novo
- `skills/schemas.py`
- `orchestration/langgraph_runner.py`
- `pipeline.py`
- `spec/article_spec.yaml`
- `spec/schema.json`
- `tests/test_evidence_builder.py` novo

Regras:
- Comecar simples. Nao criar parser perfeito de claim extraction.
- Primeiro milestone pode extrair URLs, snippets proximos e topicos basicos.
- A evidencia precisa ser auditavel: cada item deve ter `source_url`.

### 3. Mudar LangGraph para usar EvidencePack

Objetivo:
- trocar o caminho `research -> relevance_filter -> analysis` por
  `research -> evidence -> analysis`.

Implementar:
- `PipelineState` ganha `evidence_pack`.
- Grafo troca o node `relevance_filter` por `evidence`.
- `analysis` recebe `evidence_pack`.
- O `research` pode continuar no estado para writer/debug/recovery, mas nao deve
  ser a entrada primaria do analyst.

Arquivos provaveis:
- `orchestration/langgraph_runner.py`
- `pipeline.py`
- `pipeline_stages/analysis.py`
- `tests/test_pipeline_e2e.py`
- `tests/test_pipeline.py`

Testes esperados:
- Teste do grafo ou stage garantindo que `analysis` recebe evidence pack.
- Teste de compatibilidade para research historico, `skip_search`, e run normal.

### 4. Estruturar saida do analyst

Objetivo:
- fazer o analyst produzir uma analise controlada baseada no evidence pack.

Implementar:
- Adicionar contrato `AnalysisReport` em `skills/schemas.py`.
- Ajustar `AnalystSkill.run(...)` para aceitar `evidence_pack`.
- Prompt do analyst deve receber evidencia estruturada, nao research bruto.
- Manter retorno final como string/Markdown por compatibilidade com writer, se
  isso reduzir risco.
- Salvar `output/debug_analysis.md` como visao humana.

Arquivos provaveis:
- `skills/schemas.py`
- `skills/analyst.py`
- `prompts/analyst.yaml`
- `pipeline_stages/analysis.py`
- `tests/test_skills_mocked.py`
- `tests/test_prompt_integration.py`
- `tests/test_template_validator.py`

Regra importante:
- Nao deixar o analyst inventar dados ausentes. Gaps do evidence pack devem
  aparecer como limites da analise.

### 5. Ajustar writer para consumir evidencia estruturada

Objetivo:
- writer deve usar `evidence_pack + analysis`, nao depender do research textao.

Implementar:
- Passar `evidence_pack` para writer.
- Compactar evidence pack com formato deterministico antes do prompt.
- Manter `research` como fallback temporario se necessario, mas marcar como
  legado no codigo.
- Prompt do writer deve exigir referencias vindas do evidence pack.

Arquivos provaveis:
- `skills/writer.py`
- `prompts/writer.yaml`
- `pipeline_stages/writer.py`
- `orchestration/langgraph_runner.py`
- `tests/test_skills_mocked.py`
- `tests/test_prompt_integration.py`

### 6. Groundedness no critic

Objetivo:
- reprovar referencias/URLs e afirmacoes centrais que nao estejam apoiadas no
  evidence pack.

Implementar:
- Passar `evidence_pack` para critic.
- Extrair URLs do artigo e comparar com `evidence_pack.retained_urls` e
  `EvidenceItem.source_url`.
- Se artigo usar URL fora do evidence pack, gerar problema claro.
- Se artigo responder questao com URL fora das referencias coletadas, manter
  politica atual de sanitizacao para `N/D (fora das referencias coletadas)`.
- Opcional em fase 1: groundedness por URL e topico. Evitar semantic matching
  sofisticado nesta rodada.

Arquivos provaveis:
- `skills/critic.py`
- `pipeline_stages/critic.py`
- `orchestration/langgraph_runner.py`
- `validators/question_coverage.py`
- `tests/test_skills_mocked.py`
- `tests/test_pipeline.py`

### 7. Atualizar docs operacionais

Objetivo:
- manter bootstrap e docs alinhados com o runtime.

Atualizar:
- `AGENTS.md`: nova arquitetura e responsabilidades.
- `README.md`: artefatos atuais e fluxo novo.
- Este `HANDOFF.md`: marcar o que foi feito, se a implementacao for parcial.

## Ordem De Execucao Amanhã

1. Rodar baseline rapido:

```bash
uv run pytest
uv run ruff check .
```

Se `uv` falhar por cache, usar:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .
```

2. Criar testes RED:
- `tests/test_evidence_builder.py`
- teste de `pipeline_stages/evidence.py`
- teste de wiring do LangGraph
- teste de analyst com evidence pack
- teste de critic groundedness por URL

3. Implementar GREEN minimo:
- `EvidencePack`/`EvidenceItem`
- `EvidenceBuilderSkill`
- `pipeline_stages/evidence.py`
- wiring no LangGraph
- prompts ajustados
- critic URL groundedness

4. Refatorar so o necessario:
- remover `relevance_filter` do caminho principal.
- manter codigo legado apenas se testes existentes dependerem dele.
- evitar broad rewrite em researcher.

5. Rodar verificacao:

```bash
uv run pytest
uv run ruff check .
```

## Success Criteria

Considerar pronto quando:
- O grafo roda com `research -> evidence -> analysis`.
- `output/evidence_pack.json` e gerado.
- Analyst recebe evidence pack como entrada primaria.
- Writer recebe evidence pack e analysis.
- Critic reprova URL fora do evidence pack.
- `debug_research.md` e `debug_research_filtered.md` nao sao gerados por default.
- HTML debug fica desligado por default ou controlado por config/env.
- `README.md` e `AGENTS.md` refletem o novo fluxo.
- `pytest` passa.
- `ruff check .` passa.

## Riscos E Cuidados

- Nao quebrar reutilizacao de pesquisa historica (`existing_research`).
- Nao quebrar `skip_search` com URLs/cache.
- Nao reintroduzir web search no recovery pos-critic.
- Nao transformar evidence builder em outro LLM caro. Comecar deterministico.
- Nao apagar artefatos existentes do usuario sem pedido explicito.
- Nao refatorar researcher alem do necessario.
- Se surgir mudanca grande em contrato, atualizar `spec/schema.json` junto com
  `spec/article_spec.yaml`.

## Notas De Contexto

- O ponto fraco atual e contrato de dados entre estagios, nao provider/modelo.
- `output/debug_research_filtered.md` e enganoso: parece filtro, mas hoje e o
  research original com uma secao extra de URLs priorizadas.
- `pipeline_events.jsonl` deve continuar sendo a verdade operacional.
- `watch_events.py` deve continuar como monitor unico.
- Manter `main.py` alto nivel.
