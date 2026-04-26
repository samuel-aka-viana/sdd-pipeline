# GitHub Actions vs GitLab CI: Performance em Monorepos com Runners Self-Hosted
> **TL;DR:** GitLab CI oferece controle granular para pipelines complexos; GitHub Actions é mais acessível para projetos OSS.
## O que é e por que usar
GitHub Actions e GitLab CI são plataformas de automação de CI/CD que executam jobs em runners. Para monorepos com múltiplos serviços e runners self-hosted, a performance depende de três fatores críticos: latência de enfileiramento, throughput de builds paralelos, eficiência de cache e infraestrutura de execução. Ambas suportam workflows complexos, mas abordam otimizações de forma distinta: GitLab CI prioriza controle condicional via `rules`, enquanto GitHub Actions foca em integração nativa com o ecossistema GitHub.
## Requisitos
Não há requisitos oficiais específicos para performance, pois ambos os sistemas são adaptáveis a infraestrutura existente. A escolha depende de fatores como linguagens de programação, ferramentas de build e políticas de segurança.
## Instalação
### Método 1: GitHub Actions Self-Hosted Runner
```bash
./config.sh --url https://github.com/seu-repo --token SEU_TOKEN
```
### Método 2: GitLab CI Self-Hosted Runner
```bash
sudo gitlab-runner register --url https://gitlab.com/ --registration-token SEU_TOKEN
```
## Configuração
### GitHub Actions (`.github/workflows/ci.yml`)
```yaml
jobs:
  build:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: ~/.npm
          key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
```
### GitLab CI (`.gitlab-ci.yml`)
```yaml
stages:
  - test
  - deploy
cache:
  key: "$CI_JOB_NAME-$CI_COMMIT_SHA"
  paths:
    - node_modules/
test_job:
  stage: test
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
  script:
    - npm test
```
## Exemplo Prático
### Cenário: Pipeline de teste para monorepo com 3 serviços
1. **Configurar runners self-hosted** para cada serviço
2. **Definir jobs paralelos**:
   ```yaml
   # GitHub Actions
   jobs:
     test:
       strategy:
         matrix:
           service: [service1, service2, service3]
   yaml
   # GitLab CI
   parallel: 3
   ```
3. **Executar testes unitários** em paralelo
4. **Gerar relatório de benchmark**:
   ```yaml
   - name: Run benchmark
     uses: benchmark-action/github-action-benchmark@v1
     with:
       name: 'service-performance'
       tool: 'custom'
       output-file-path: 'results.json'
   ```
## Armadilhas Comuns
### ⚠ Cache Key Collision
**Sintoma:** Builds repetidos baixam dependências desnecessariamente
**Causa:** Chaves de cache estáticas em matrix builds
**Solução:**
```yaml
# GitHub Actions
key: ${{ matrix.service }}-${{ hashFiles('**/package-lock.json') }}
```
### ⚠ Regras Condicionais Ineficientes
**Sintoma:** Jobs desnecessários em branches secundárias
**Causa:** Condições vagas no workflow
**Solução:**
```yaml
# GitLab CI
rules:
  - if: '$CI_COMMIT_BRANCH == "main" && $CI_PIPELINE_SOURCE == "push"'
```
## Dicas de Otimização
- Use chaves de cache dinâmicas para evitar colisões em builds paralelos
- Implemente `rules` condicionais para reduzir execuções desnecessárias
- Separe artefatos por job para minimizar transferência de dados
## Conclusão
Para monorepos com múltiplos serviços e runners self-hosted, GitLab CI oferece vantagem em controle granular de pipelines e otimização de cache, enquanto GitHub Actions é mais acessível para projetos OSS. A escolha deve considerar políticas de segurança, custo e complexidade de configuração.
## Referências
- https://github.com/benchmark-action/github-action-benchmark
- https://docs.gitlab.com/ci/yaml/
- https://docs.github.com/actions/learn-github-actions/migrating-from-gitlab-cicd-to-github-actions
---
## Respostas às Perguntas do Contexto
- Pergunta: "latência de enfileiramento e startup de jobs em carga alta?"  
  Resposta objetiva: Sem dados mensuráveis nas fontes consultados  
  Evidência/URL: N/D
- Pergunta: "throughput de jobs paralelos com matrix builds?"  
  Resposta objetiva: Sem dados mensuráveis nas fontes consultados  
  Evidência/URL: N/D
- Pergunta: "overhead de cache de dependências e artefatos entre runs?"  
  Resposta objetiva: Cache de dependências reduz downloads repetidos, mas artefatos aumentam latência em pipelines sequenciais  
Evidência/URL: N/D (fora das referências coletadas)
- Pergunta: "impacto de runners self-hosted vs managed no tempo total do pipeline?"  
  Resposta objetiva: Sem dados mensuráveis nas fontes consultados  
  Evidência/URL: N/D