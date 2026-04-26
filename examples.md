# Exemplos de Inputs — SDD Tech Writer

Curadoria focada em **benchmark e comparação técnica**.
Cada exemplo tem versão **leigo** e **técnica**.

Regra global anti-ruído para todas as perguntas:
- use termos curtos e técnicos (evite linguagem conversacional longa)
- peça métrica/comando/evidência sempre que possível
- prefira "latência p95", "throughput", "RAM/CPU", "comando exato"
- evite perguntas vagas como "qual é melhor?" sem contexto

---

## MiniStack

### MiniStack — setup inicial e operação

**Versão leigo:**
```
Ferramentas: ministack
Contexto:    quero subir um ambiente local simples para testar aplicações
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  o que o ministack resolve na prática?
  quais são os requisitos mínimos de máquina?
  qual o passo a passo mais simples para instalar?
  quais erros mais comuns aparecem no primeiro uso?

Critérios:
  tem comandos reais de instalação e verificação
  explica os erros sem linguagem complexa
  inclui checklist de pós-instalação
  usa https://ministack.org/ como referência principal
```

**Versão técnica:**
```
Ferramentas: ministack
Contexto:    ambiente de desenvolvimento local para times com Docker e CI/CD
Foco:        5 (integração)

Perguntas (objetivas, anti-ruído):
  quais componentes do ministack são obrigatórios e quais são opcionais?
  como integrar com docker compose sem quebrar serviços já existentes?
  como configurar logs e healthchecks para troubleshooting rápido?
  quais parâmetros impactam consumo de RAM/CPU em idle?

Critérios:
  inclui arquitetura resumida com fluxo entre componentes
  tem comandos de diagnóstico e troubleshooting
  cita limitações conhecidas e trade-offs
  referências incluem https://ministack.org/ e repositório GitHub oficial
```

---

## Container Runtime

### Docker vs Podman — benchmark de consumo e operação

**Versão leigo:**
```
Ferramentas: docker e podman
Contexto:    quero rodar containers no Linux com baixo consumo de recursos
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  qual usa menos RAM e CPU parado?
  qual inicia container mais rápido?
  tempo de setup inicial (passos + minutos) em ambiente padrão?
  o que muda na prática entre daemon e daemonless?

Critérios:
  traz tabela com memória, CPU idle e tempo de start
  inclui comandos reproduzíveis
  explica diferenças sem jargão excessivo
  não recomenda sem justificar pelo contexto
```

**Versão técnica:**
```
Ferramentas: docker e podman
Contexto:    workstations Linux e runners de CI self-hosted
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  qual latência média de start para N containers curtos?
  qual overhead por container em idle?
  como rootless afeta performance e segurança?
  qual impacto no build cache e I/O de imagens?

Critérios:
  benchmark com metodologia clara (máquina, versão, comandos)
  inclui p50/p95 para start time
  separa resultado de runtime e build
  lista limitações do teste
```

---

## Orquestração de Containers

### k3s vs microk8s — Kubernetes leve

**Versão leigo:**
```
Ferramentas: k3s e microk8s
Contexto:    quero Kubernetes leve para laboratório local
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  qual instala mais rápido?
  qual usa menos memória em idle?
  esforço operacional mensal (rotinas, incidentes e tuning)?
  desempenho em hardware limitado (RAM/CPU) com carga básica?

Critérios:
  compara recursos mínimos de hardware
  inclui passos de instalação e teste
  mostra quando escolher cada um
  evita respostas genéricas
```

**Versão técnica:**
```
Ferramentas: k3s e microk8s
Contexto:    clusters pequenos para edge e ambientes de homologação
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  qual tempo de bootstrap até cluster ficar pronto?
  qual consumo de RAM/CPU em idle com addons mínimos?
  qual latência de deploy de workload simples?
  qual overhead de upgrades e gestão de addons?

Critérios:
  inclui comandos e métricas objetivas
  compara bootstrap, idle e deploy time
  explicita trade-offs operacionais
  referencia documentação oficial
```

---

## Dados e Analytics

### SQLite vs DuckDB — analytics local

**Versão leigo:**
```
Ferramentas: sqlite e duckdb
Contexto:    quero analisar arquivos grandes CSV/Parquet no notebook
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  latência p95 para agregações em datasets grandes?
  esforço operacional diário (tarefas e tempo)
  tempo de execução de consultas analíticas locais (p50/p95)?
  gatilhos objetivos para migrar (volume, latência e complexidade)?

Critérios:
  inclui benchmark reprodutível de leitura e agregação
  usa exemplos com dados reais
  compara tempo e consumo de memória
  explica limitações de cada engine
```

**Versão técnica:**
```
Ferramentas: sqlite e duckdb
Contexto:    analytics embarcado em aplicação Python
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  qual throughput em scans e joins com dados colunares?
  qual impacto de formatos (CSV vs Parquet)?
  como cada engine se comporta em concorrência local?
  qual estratégia para cache e compactação?

Critérios:
  traz queries de benchmark reproduzíveis
  reporta tempo, memória e versão das ferramentas
  separa cenários OLTP e OLAP
  apresenta conclusão com cenário de uso
```

---

### DuckDB vs Polars — engine SQL vs DataFrame

**Versão leigo:**
```
Ferramentas: duckdb e polars
Contexto:    preciso decidir ferramenta para análises de dados no time
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  cenário SQL-first vs DataFrame-first: ganhos e perdas mensuráveis?
  latência p95 e throughput em agregações grandes?
  esforço de integração com Python (libs, compatibilidade e manutenção)?
  arquitetura combinada: quando usar ambos no mesmo pipeline?

Critérios:
  compara curva de aprendizado e performance
  inclui exemplos práticos simples
  mostra cenários de uso complementar
  evita recomendação absoluta
```

**Versão técnica:**
```
Ferramentas: duckdb e polars
Contexto:    pipeline analítico em Python com arquivos Parquet particionados
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  benchmark de groupby, join e filtros seletivos em datasets grandes
  diferença de consumo de memória em lazy/eager execution
  custo de conversão entre DataFrame e tabelas SQL
  quando combinar Polars para ETL e DuckDB para serving SQL?

Critérios:
  inclui scripts/queries reprodutíveis
  apresenta p50/p95 e memória pico
  traz recomendação por tipo de workload
  documenta limitações do benchmark
```

---

### PySpark vs Trino — ETL e SQL distribuído

**Versão leigo:**
```
Ferramentas: pyspark e trino
Contexto:    preciso processar muitos dados e também consultar rápido para BI
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  em quais workloads (ETL pesado vs serving SQL) cada um vence?
  latência p95 de consultas para dashboard em carga concorrente?
  complexidade operacional (deploy, tuning, incidentes) por equipe/mês?
  arquitetura de integração ponta a ponta com etapas e handoff de dados?

Critérios:
  explica processamento vs consulta de forma clara
  inclui fluxo simples de ponta a ponta
  compara custo operacional básico
  não recomenda sem contexto
```

**Versão técnica:**
```
Ferramentas: pyspark e trino
Contexto:    lakehouse com S3/MinIO + BI em produção
Foco:        5 (integração)

Perguntas (objetivas, anti-ruído):
  qual estratégia para ETL pesado (joins, deduplicação, janelas)?
  como otimizar tabelas Iceberg/Delta para leitura no Trino?
  quais parâmetros afetam throughput no Spark e latência no Trino?
  como instrumentar SLA de jobs e queries ponta a ponta?

Critérios:
  inclui arquitetura Spark (transform) + Trino (serving)
  tem comandos reais e queries de validação
  cobre particionamento, compactação e small files
  lista gargalos típicos e mitigação
```

---

### Kafka + Flink — streaming de alto volume

**Versão leigo:**
```
Ferramentas: kafka e flink
Contexto:    preciso processar eventos em tempo real sem perder mensagens
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  como validar garantia de entrega (at-least-once/exactly-once) na prática?
  throughput sustentado realista (eventos/s) em ambiente médio?
  erros mais frequentes com evidência de causa e mitigação?
  métricas e alertas para detectar lag/backpressure?

Critérios:
  explica conceitos de forma simples
  tem exemplo de pipeline mínimo reproduzível
  traz métricas de throughput e atraso
  inclui troubleshooting de produção
```

**Versão técnica:**
```
Ferramentas: kafka e flink
Contexto:    processamento de eventos críticos com SLA de baixa latência
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  throughput máximo por partição e por cluster em cenário controlado
  latência end-to-end p50/p95/p99 com janelas e estado
  impacto de exactly-once e checkpointing no desempenho
  tuning de paralelismo, backpressure e retention

Critérios:
  metodologia de benchmark explícita
  métricas de latência e throughput por estágio
  inclui comandos/configs reais
  mostra gargalos e trade-offs de consistência
```

---

## Observability

### Prometheus vs VictoriaMetrics — métricas em escala

**Versão leigo:**
```
Ferramentas: prometheus e victoriametrics
Contexto:    quero monitorar muitos serviços sem gastar recursos demais
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  ingestão máxima (samples/s) por custo mensal?
  esforço operacional diário (tarefas e tempo) por ferramenta?
  custo e latência para retenção longa e consultas históricas?
  limites objetivos para migração (cardinalidade, custo, latência)?

Critérios:
  compara ingestão, armazenamento e consulta
  inclui benchmark reprodutível simples e reproduzível
  traz custo operacional estimado
  explica trade-offs sem viés
```

**Versão técnica:**
```
Ferramentas: prometheus e victoriametrics
Contexto:    plataforma com alta cardinalidade e retenção longa
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  ingestão sustentada (samples/s) com cardinalidade alta
  latência de query em range curto e longo
  compressão e uso de disco por série
  impacto de federation/remote_write na arquitetura

Critérios:
  inclui dataset, carga e hardware do teste
  reporta ingestão, latência, RAM e disco
  separa cenário single-node e cluster
  recomenda por perfil de uso
```

---

### Loki vs Elasticsearch — logs

**Versão leigo:**
```
Ferramentas: loki e elasticsearch
Contexto:    quero centralizar logs de aplicações e servidores
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  custo de armazenamento por GB de log útil?
  latência p95 de busca para troubleshooting em produção?
  esforço de operação e manutenção mensal?
  comportamento de escala com aumento de ingestão (x2/x5)?

Critérios:
  compara ingestão e busca
  mede custo de armazenamento
  mostra limites e riscos operacionais
  inclui comandos de consulta reais
```

**Versão técnica:**
```
Ferramentas: loki e elasticsearch
Contexto:    observabilidade com alto volume de logs e retenção de 30+ dias
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  throughput de ingestão com diferentes tamanhos de linha
  latência de busca em índices frios e quentes
  custo de storage por GB ingerido
  efeito de parsing/indexação no desempenho

Critérios:
  benchmark com dataset e queries definidos
  p50/p95 de ingestão e busca
  custo operacional por cenário
  conclusão orientada ao contexto
```

---

## IA Local

### Ollama vs LM Studio — inferência local

**Versão leigo:**
```
Ferramentas: ollama e lm studio
Contexto:    quero rodar IA local no notebook para uso diário
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de setup inicial (passos + minutos) para uso local?
  desempenho em CPU-only e baixo VRAM?
  latência p95 e tokens/s em prompts comuns?
  esforço de uso para operação diária (UX e troubleshooting)?

Critérios:
  compara facilidade, desempenho e consumo
  inclui comandos reais com sintaxe validada de instalação
  mostra limitações por hardware
  não usa placeholders
```

**Versão técnica:**
```
Ferramentas: ollama e lm studio
Contexto:    uso local para desenvolvimento com modelos 7B/13B
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  tokens/s por modelo e quantização em CPU/GPU
  tempo de warmup e latência da primeira resposta
  uso de RAM/VRAM em idle e carga
  comportamento sob concorrência local (latência, fila e estabilidade)?

Critérios:
  benchmark reproduzível com mesma máquina/modelo
  reporta tokens/s, p95 e memória
  diferencia UX de operação e API de automação
  recomenda por perfil de workload
```

---

## Backend e Cache

### FastAPI vs Django vs Flask — API web

**Versão leigo:**
```
Ferramentas: fastapi, django e flask
Contexto:    preciso construir API para produto novo
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de setup inicial (passos + minutos) para API funcional?
  throughput sustentado (req/s) por esforço operacional?
  cobertura de recursos nativos relevantes para produção?
  custo de manutenção a longo prazo (migrations, testes, observabilidade)?

Critérios:
  compara produtividade e performance
  inclui benchmark reprodutível básico de requests/s
  mostra curva de aprendizado
  indica quando cada um faz sentido
```

**Versão técnica:**
```
Ferramentas: fastapi, django e flask
Contexto:    API de produção com autenticação, observabilidade e scaling horizontal
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  latência p50/p95/p99 sob carga concorrente
  throughput por worker e impacto de async/sync
  overhead de middleware e validação
  custo de operação e manutenção por framework

Critérios:
  benchmark com mesmas rotas e mesmas regras de negócio
  métricas claras de latência e throughput
  inclui análise de ergonomia de desenvolvimento
  conclusão por cenário de produto
```

---

### Redis vs Dragonfly vs KeyDB — cache

**Versão leigo:**
```
Ferramentas: redis, dragonfly e keydb
Contexto:    preciso acelerar aplicação com cache em memória
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  throughput por GB de RAM em carga mista?
  taxa de erro e comportamento em falha/recovery sob carga?
  esforço operacional mensal para cache em produção?
  custo por throughput com SLA definido?

Critérios:
  compara operações de leitura/escrita
  mede consumo de memória e CPU
  inclui cenário realista de uso
  evita recomendação sem dados
```

**Versão técnica:**
```
Ferramentas: redis, dragonfly e keydb
Contexto:    cache distribuído para APIs com alto tráfego
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  throughput em GET/SET com concorrência alta
  latência p95/p99 em carga mista
  impacto de persistência (AOF/RDB) no desempenho
  comportamento em failover e replicação

Critérios:
  benchmark reproduzível com workload definido
  reporta latência, throughput e memória pico
  inclui tuning mínimo necessário
  mostra riscos operacionais de cada opção
```

---

## Object Storage

### Ceph vs MinIO vs SeaweedFS — storage distribuído

**Versão leigo:**
```
Ferramentas: ceph, minio e seaweedfs
Contexto:    quero armazenar arquivos em infraestrutura própria
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de setup + esforço de operação mensal?
  latência p95 e throughput para upload/download em carga concorrente?
  estratégia de escala horizontal e impacto em custo/performance?
  custo operacional mensal por TB útil?

Critérios:
  compara instalação, operação e desempenho
  inclui benchmark reprodutível básico de leitura/escrita
  aponta limitações de cada solução
  recomenda conforme contexto
```

**Versão técnica:**
```
Ferramentas: ceph, minio e seaweedfs
Contexto:    object storage self-hosted para dados críticos e tráfego alto
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  throughput de leitura/escrita em objetos pequenos e grandes
  latência p95/p99 em carga concorrente
  custo de replicação/erasure coding no desempenho
  complexidade operacional e MTTR de incidentes

Critérios:
  benchmark com hardware e topologia descritos
  métricas por tipo de objeto
  inclui custo operacional estimado
  conclusão baseada em trade-offs reais
```

---

## Banco de Dados Analítico

### PostgreSQL vs ClickHouse — OLTP vs OLAP

**Versão leigo:**
```
Ferramentas: postgresql e clickhouse
Contexto:    tenho dados transacionais e também preciso de relatórios rápidos
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  cenário OLTP (transação): quem vence e por quê?
  cenário OLAP (analítico): quem vence e por quê?
  arquitetura conjunta com sincronização OLTP->OLAP?
  custo mensal estimado por workload (compute + storage + operação)?

Critérios:
  compara escrita transacional e leitura analítica
  inclui benchmark reprodutível simples de insert e query
  explica quando combinar ambos
  não recomenda sem contexto
```

**Versão técnica:**
```
Ferramentas: postgresql e clickhouse
Contexto:    plataforma com workload misto (transações + BI)
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  throughput de inserts/updates no PostgreSQL vs ingestão em lote no ClickHouse
  latência p50/p95 de agregações em tabelas grandes
  impacto de particionamento, índices e compressão
  estratégia de replicação/CDC entre OLTP e OLAP

Critérios:
  metodologia de benchmark reproduzível
  métricas de throughput, latência e custo
  separa claramente cenários OLTP e OLAP
  conclusão por tipo de carga
```

---

## Streaming Engine

### Spark Structured Streaming vs Flink — stream processing

**Versão leigo:**
```
Ferramentas: spark structured streaming e flink
Contexto:    quero processar eventos em tempo real com confiabilidade
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de setup inicial (passos + minutos)
  latência de processamento com eventos atrasados/out-of-order?
  latência p95/p99 sob carga contínua?
  esforço de operação em produção (SLO, tuning, incidentes)?

Critérios:
  explica conceitos sem jargão excessivo
  inclui exemplo mínimo de pipeline
  compara latência e estabilidade
  mostra trade-offs operacionais
```

**Versão técnica:**
```
Ferramentas: spark structured streaming e flink
Contexto:    processamento contínuo com SLA de baixa latência
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  latência p50/p95/p99 com stateful operations
  impacto de watermark/checkpoint no throughput
  comportamento sob backpressure
  recuperação após falha e tempo de retomada

Critérios:
  benchmark com carga sintética e real
  métricas de latência, throughput e recovery time
  inclui tuning de paralelismo e state backend
  traz limitações do experimento
```

---

## Transformação SQL

### dbt Core vs SQLMesh — engenharia analítica

**Versão leigo:**
```
Ferramentas: dbt core e sqlmesh
Contexto:    quero organizar transformações SQL com menos retrabalho
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de adoção e curva de aprendizado da equipe?
  cobertura de testes/validações para qualidade de dados?
  versionamento e deploy: diferenças práticas por cenário?
  redução de erros em produção com evidência operacional?

Critérios:
  compara curva de aprendizado e fluxo de trabalho
  inclui exemplo de pipeline com testes
  mostra ganhos reais de governança
  evita recomendação vaga
```

**Versão técnica:**
```
Ferramentas: dbt core e sqlmesh
Contexto:    transformação SQL em ambiente com múltiplos domínios de dados
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  tempo de build incremental vs full refresh
  overhead de testes e validações
  impacto em custo computacional por execução
  observabilidade de lineage e deploy seguro

Critérios:
  benchmark por volume de modelos e dados
  reporta tempo, custo e falhas detectadas
  inclui estratégia de CI para transformação
  conclusão por maturidade de equipe
```

---

## Orquestração de Dados

### Airflow vs Dagster — orquestração de pipelines

**Versão leigo:**
```
Ferramentas: airflow e dagster
Contexto:    preciso agendar e monitorar pipelines de dados
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  esforço de manutenção diária (alertas, retries, backfills)?
  visibilidade de falhas (logs, lineage, observabilidade)?
  velocidade de evolução de pipelines com segurança?
  taxa de falha e MTTR em produção?

Critérios:
  compara usabilidade, operação e manutenção
  inclui exemplo de DAG/job simples
  mostra diferenças de observabilidade
  recomenda por contexto
```

**Versão técnica:**
```
Ferramentas: airflow e dagster
Contexto:    orquestração de pipelines críticos com dependências complexas
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  overhead do scheduler com muitos jobs
  latência entre tarefas encadeadas
  comportamento de retries e backfills
  impacto operacional de upgrades/migrações

Critérios:
  benchmark com volume crescente de DAGs/jobs
  métricas de scheduling delay e taxa de falha
  inclui estratégia de observabilidade
  detalha trade-offs de operação
```

---

## Mensageria

### NATS JetStream vs Kafka — pub/sub e streams

**Versão leigo:**
```
Ferramentas: nats jetstream e kafka
Contexto:    preciso trocar mensagens entre serviços com confiabilidade
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de setup + complexidade operacional (cluster e upgrades)?
  throughput sustentado com carga concorrente
  latência p95/p99 sob carga
  melhor escolha para equipe pequena com restrição de operação?

Critérios:
  compara complexidade operacional e desempenho
  inclui cenário de uso realista
  mostra custos de manutenção
  evita resposta absolutista
```

**Versão técnica:**
```
Ferramentas: nats jetstream e kafka
Contexto:    arquitetura event-driven com múltiplos consumidores
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  throughput sustentado por tópico/subject
  latência p95/p99 em carga alta
  garantias de entrega e replay
  impacto de retenção e replicação

Critérios:
  benchmark reproduzível com payloads distintos
  métricas de latência, throughput e durabilidade
  inclui tuning mínimo necessário
  conclusão por perfil de workload
```

---

## Busca e Logs

### OpenSearch vs Elasticsearch — indexação e consulta

**Versão leigo:**
```
Ferramentas: opensearch e elasticsearch
Contexto:    quero buscar logs e documentos com boa performance
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  esforço administrativo mensal (tuning, upgrades, incidentes)?
  latência p95 de consulta em volume alto?
  custo operacional mensal e complexidade técnica com evidência
  integração com dashboards e stack de observabilidade

Critérios:
  compara custo, desempenho e operação
  inclui benchmark reprodutível básico de indexação e busca
  mostra trade-offs de ecossistema
  recomenda por contexto
```

**Versão técnica:**
```
Ferramentas: opensearch e elasticsearch
Contexto:    plataforma de observabilidade e busca com alta ingestão
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  throughput de indexação com shards equivalentes
  latência p50/p95 de queries complexas
  custo de storage e retenção
  impacto de tuning de refresh e merge

Critérios:
  benchmark com mesma topologia de cluster
  reporta ingestão, busca e consumo de recursos
  inclui custos operacionais estimados
  detalha limitações metodológicas
```

---

## LLM

### GPT-4.1 vs Claude 3.7 Sonnet vs Gemini 2.0 Flash — qualidade e custo

**Versão leigo:**
```
Ferramentas: gpt-4.1, claude 3.7 sonnet e gemini 2.0 flash
Contexto:    quero escolher um modelo para assistente do time
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  taxa de acerto/falha em suíte de prompts representativa?
  latência p50/p95 por classe de prompt?
  custo mensal estimado por workload de uso
  cenário de uso diário: qualidade x latência x custo?

Critérios:
  compara qualidade, velocidade e custo
  usa conjunto de prompts representativo
  inclui limitações e riscos
  evita viés por um único caso
```

**Versão técnica:**
```
Ferramentas: gpt-4.1, claude 3.7 sonnet e gemini 2.0 flash
Contexto:    plataforma com RAG, automação e análise de documentos
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  latência p50/p95 por tamanho de prompt/resposta
  taxa de acerto em benchmark interno de tarefas
  custo por 1k requests em cenários reais
  robustez a prompt injection e alucinação

Critérios:
  benchmark com dataset interno e avaliação cega
  métricas de qualidade, latência e custo
  separa tasks simples e complexas
  conclusão por risco e ROI
```

---

## NLP

### spaCy vs Stanza vs Hugging Face Transformers — pipeline de NLP

**Versão leigo:**
```
Ferramentas: spacy, stanza e hugging face transformers
Contexto:    preciso extrair entidades e classificar textos
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de setup inicial (passos + minutos)
  qualidade em português (f1/accuracy ou avaliação cega)?
  throughput/latência em CPU para tarefas de NLP?
  qualidade e estabilidade em domínio real de produção?

Critérios:
  compara qualidade e velocidade
  inclui exemplos de tarefas comuns de NLP
  mostra quando cada opção é melhor
  evita resposta genérica
```

**Versão técnica:**
```
Ferramentas: spacy, stanza e hugging face transformers
Contexto:    processamento de alto volume de textos multilíngues
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  throughput de NER e classificação por segundo
  latência por documento em CPU e GPU
  impacto de batch size e quantização
  precisão/recall por domínio textual

Critérios:
  benchmark com corpus representativo
  reporta f1, precisão, recall e latência
  inclui custo operacional por hardware
  conclusão por cenário de negócio
```

---

## Banco Vetorial

### pgvector vs Qdrant vs Weaviate — busca semântica

**Versão leigo:**
```
Ferramentas: pgvector, qdrant e weaviate
Contexto:    quero implementar busca semântica no meu produto
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de setup para ambiente funcional de busca vetorial?
  latência p95 de busca ANN em base grande?
  esforço de operação mensal (reindexação, backup, tuning)?
  integração com pipeline de embeddings/RAG com baixo atrito?

Critérios:
  compara simplicidade, desempenho e operação
  inclui exemplo de ingestão e consulta
  mostra trade-offs de custo e escalabilidade
  recomenda por contexto
```

**Versão técnica:**
```
Ferramentas: pgvector, qdrant e weaviate
Contexto:    RAG em produção com alto volume de documentos
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  recall@k e latência p95 em ANN sob carga
  impacto de index types e parâmetros de busca
  custo de atualização/reindexação em produção
  comportamento com filtros híbridos (vetor + metadata)

Critérios:
  benchmark com dataset e embeddings fixos
  reporta recall, latência, throughput e custo
  inclui estratégia de particionamento/sharding
  conclusão por perfil de escala
```

---

## IaC e Automação

### Terraform vs Pulumi — infraestrutura como código

**Versão leigo:**
```
Ferramentas: terraform e pulumi
Contexto:    quero provisionar infraestrutura em nuvem de forma repetível
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de setup inicial e curva de aprendizado por perfil de time?
  esforço operacional mensal (plan, apply, drift, state)?
  comportamento em falhas parciais e rollback?
  compatibilidade com múltiplos providers e módulos existentes?

Critérios:
  compara legibilidade e manutenção de código de infraestrutura
  inclui exemplo mínimo de provisionamento e destruição
  mostra diferenças de estado e lock de recursos
  recomenda por perfil de time (DevOps experiente vs dev generalista)
```

**Versão técnica:**
```
Ferramentas: terraform e pulumi
Contexto:    plataforma multi-cloud com pipelines de CI/CD
Foco:        5 (integração)

Perguntas (objetivas, anti-ruído):
  latência de plan e apply em workspaces com muitos recursos?
  overhead de state backend (S3/GCS) com locking concorrente?
  estratégia de modularização e reutilização em múltiplos times?
  integração com secrets, OIDC e policy-as-code (OPA/Sentinel)?

Critérios:
  benchmark de plan/apply com número crescente de recursos
  compara drift detection e reconciliação
  inclui estratégia de CI para infraestrutura
  detalha trade-offs de linguagem (HCL vs linguagem geral)
```

---

## CI/CD

### GitHub Actions vs GitLab CI — pipelines de integração contínua

**Versão leigo:**
```
Ferramentas: github actions e gitlab ci
Contexto:    quero automatizar build, testes e deploy do meu projeto
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de setup inicial para pipeline funcional (passos + minutos)?
  esforço de manutenção mensal (atualizações, runners, secrets)?
  custo por minuto de execução com plano free vs pago?
  facilidade de reutilização de pipelines entre projetos?

Critérios:
  compara onboarding e manutenção
  inclui exemplo de pipeline completo (build + test + deploy)
  mostra diferenças de marketplace e actions reutilizáveis
  indica quando self-hosted runners fazem diferença
```

**Versão técnica:**
```
Ferramentas: github actions e gitlab ci
Contexto:    monorepo com múltiplos serviços e runners self-hosted
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  latência de enfileiramento e startup de jobs em carga alta?
  throughput de jobs paralelos com matrix builds?
  overhead de cache de dependências e artefatos entre runs?
  impacto de runners self-hosted vs managed no tempo total do pipeline?

Critérios:
  benchmark com pipelines equivalentes em workloads reais
  métricas de queue time, execution time e cache hit rate
  inclui estratégia de otimização por estágio
  detalha limites de concorrência e cotas
```

---

## Service Mesh

### Istio vs Linkerd — malha de serviços

**Versão leigo:**
```
Ferramentas: istio e linkerd
Contexto:    quero observabilidade e segurança entre serviços no Kubernetes
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de instalação e esforço de adoção inicial?
  overhead de latência p95 com sidecar proxy ativo?
  esforço operacional mensal (upgrades, configuração, incidentes)?
  funcionalidades mínimas para mTLS e traffic management?

Critérios:
  compara complexidade de instalação e operação
  inclui benchmark de overhead de latência com e sem mesh
  mostra diferenças de CRDs e modelo de configuração
  recomenda por maturidade de time e requisitos de segurança
```

**Versão técnica:**
```
Ferramentas: istio e linkerd
Contexto:    cluster de produção com múltiplos namespaces e políticas de rede
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  overhead de CPU/memória por sidecar em idle e carga?
  latência p50/p95/p99 adicionada pelo data plane?
  impacto no throughput de requisições com mTLS ativo?
  comportamento em circuit breaking e retries sob falha?

Critérios:
  benchmark com mesma workload e mesma topologia de cluster
  métricas de latência, CPU e memória por sidecar
  inclui estratégia de rollout progressivo
  detalha trade-offs de controle-plane e extensibilidade
```

---

## Banco de Dados de Séries Temporais

### InfluxDB vs TimescaleDB — time series

**Versão leigo:**
```
Ferramentas: influxdb e timescaledb
Contexto:    quero armazenar métricas e eventos com timestamp para monitoramento
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de setup e esforço de operação mensal?
  latência p95 de ingestão e consulta em janela recente?
  esforço de integração com Grafana e stack de observabilidade?
  comportamento de retenção e compressão ao longo do tempo?

Critérios:
  compara ingestão, armazenamento e consulta
  inclui exemplo de schema e query de agregação
  mostra curva de compressão por volume
  recomenda por caso de uso (IoT vs métricas de infra vs eventos)
```

**Versão técnica:**
```
Ferramentas: influxdb e timescaledb
Contexto:    ingestão contínua de métricas com alta cardinalidade e retenção longa
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  throughput de ingestão (pontos/s) em carga sustentada?
  latência p95 de queries com range longo e agregações por janela?
  taxa de compressão e custo de storage por série?
  comportamento com alta cardinalidade (tags/labels)?

Critérios:
  benchmark com dataset de métricas real ou sintético descrito
  métricas de ingestão, latência e compressão
  compara linguagem de query (Flux vs SQL/PromQL)
  detalha limites de cardinality e retenção automática
```

---

## ML e Experimentação

### MLflow vs Weights & Biases — rastreamento de experimentos

**Versão leigo:**
```
Ferramentas: mlflow e weights & biases
Contexto:    quero rastrear experimentos de ML e comparar modelos treinados
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de setup inicial para rastrear primeiro experimento?
  esforço de integração com frameworks (PyTorch, sklearn, HuggingFace)?
  custo mensal para time pequeno com volume moderado de runs?
  funcionalidades de colaboração e comparação de runs?

Critérios:
  compara onboarding e integração com código existente
  inclui exemplo mínimo de log de métricas e artefatos
  mostra diferenças de UI para comparação de experimentos
  indica quando self-hosted faz sentido vs SaaS
```

**Versão técnica:**
```
Ferramentas: mlflow e weights & biases
Contexto:    pipeline de treinamento contínuo com múltiplos experimentos paralelos
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  overhead de logging no tempo de treino com muitas métricas?
  latência de registro de artefatos grandes (modelos, datasets)?
  comportamento com runs paralelas e acesso concorrente ao tracking server?
  custo de armazenamento de artefatos e metadados em escala?

Critérios:
  benchmark de overhead de logging por frequência e volume de métricas
  compara versionamento de modelos e registro de artefatos
  inclui estratégia de integração com CI/CD de ML
  detalha trade-offs de self-hosted vs managed
```

---

## Python Tooling

### uv vs pip vs Poetry — gerenciamento de dependências Python

**Versão leigo:**
```
Ferramentas: uv, pip e poetry
Contexto:    quero gerenciar dependências Python de forma rápida e reprodutível
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de instalação de dependências em ambiente limpo?
  esforço de migração de projeto existente?
  compatibilidade com ambientes de CI e containers?
  curva de aprendizado para time com experiência variada?

Critérios:
  compara velocidade de resolução e instalação
  inclui comandos de setup para projeto novo e existente
  mostra diferenças de lock file e reprodutibilidade
  indica quando cada ferramenta faz sentido
```

**Versão técnica:**
```
Ferramentas: uv, pip e poetry
Contexto:    monorepo Python com múltiplos pacotes e CI em escala
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  tempo de resolução e instalação com dependências complexas (benchmark)?
  overhead de criação de venv em pipeline de CI cold start?
  comportamento com conflitos de versão e extras opcionais?
  suporte a workspaces e editable installs em monorepo?

Critérios:
  benchmark reproduzível de install time com dependências fixas
  compara cache hit rate em CI e tempo de cold start
  inclui estratégia de lock file em equipes grandes
  detalha compatibilidade com PEP e ferramentas do ecossistema
```

---

## Banco de Dados de Grafo

### Neo4j vs TigerGraph vs ArangoDB — grafo e multi-modelo

**Versão leigo:**
```
Ferramentas: neo4j, tigergraph e arangodb
Contexto:    quero modelar e consultar dados com relacionamentos complexos
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de setup e complexidade de modelagem inicial?
  latência p95 de traversal em grafos de médio porte?
  esforço operacional mensal (backup, scaling, upgrades)?
  suporte a queries analíticas além de traversal simples?

Critérios:
  compara modelo de dados e linguagem de query (Cypher vs GSQL vs AQL)
  inclui exemplo de grafo com traversal e agregação
  mostra diferenças de licença e custo operacional
  recomenda por tipo de grafo (social, fraude, knowledge graph)
```

**Versão técnica:**
```
Ferramentas: neo4j, tigergraph e arangodb
Contexto:    detecção de fraude e análise de rede com grafos grandes
Foco:        2 (performance / throughput)

Perguntas (objetivas, anti-ruído):
  throughput de traversal com N hops em grafo de milhões de nós?
  latência p95 de queries de vizinhança e shortest path?
  overhead de ingestão em lote vs streaming de arestas?
  comportamento de scaling horizontal e particionamento?

Critérios:
  benchmark com dataset de grafo real ou sintético descrito
  métricas de throughput, latência e consumo de memória
  compara expressividade das linguagens de query
  detalha limites de escala e operação em cluster
```

---

## Data Contracts

### Datacontract Framework — setup, uso e integração

**Versão leigo:**
```
Ferramentas: datacontract cli
Contexto:    quero definir e validar contratos de dados entre times produtores e consumidores
Foco:        1 (comparação geral)

Perguntas (objetivas, anti-ruído):
  tempo de setup para primeiro contrato publicado e validado (passos + minutos)?
  quais campos mínimos obrigatórios num contrato funcional?
  como rodar validação de schema e qualidade com um comando?
  quais erros mais comuns no primeiro uso e como resolver?

Critérios:
  inclui exemplo real de datacontract.yaml com campos essenciais
  mostra comandos de lint, test e diff com saída esperada
  explica o modelo produtor/consumidor sem jargão excessivo
  usa https://datacontract.com/ e repositório oficial como referência
```

**Versão técnica:**
```
Ferramentas: datacontract cli
Contexto:    plataforma de data mesh com múltiplos domínios e pipelines em produção
Foco:        5 (integração)

Perguntas (objetivas, anti-ruído):
  como integrar datacontract test em CI/CD (GitHub Actions / GitLab CI)?
  estratégia de versionamento e detecção de breaking change com datacontract diff?
  como mapear contrato para schema registry (Confluent, Glue) e catálogo (DataHub, OpenMetadata)?
  como configurar servers e quality checks para múltiplos environments (dev, prod)?

Critérios:
  inclui pipeline completo: definição, lint, test e publish
  mostra exemplo de datacontract.yaml com servers, quality e SLA
  detalha integração com dbt, Spark e Kafka via campo servers
  cobre estratégia de ownership, aprovação e versionamento semântico
```

---

## Referência rápida — foco para benchmark

| Situação | Foco recomendado |
|----------|-----------------|
| Comparar duas ferramentas de mesma categoria | comparação geral |
| Medir latência, throughput e consumo | performance / throughput |
| Integrar engines no mesmo pipeline | integração |
| Hardware limitado (edge/notebook) | hardware limitado / edge |
| Avaliar impacto financeiro da arquitetura | custo |
| Ambientes de produção com compliance | segurança |
| Migração entre stacks existentes | migração |
