# gitlab ci
## URLS CONSULTADAS
https://github.com/kprasad7/k8s-loadtest-ci  
https://docs.gitlab.com/runner/  
https://yrkan.com/es/blog/matrix-testing-in-ci-cd-pipelines/  
https://dev.to/drakulavich/gitlab-ci-cache-and-artifacts-explained-by-example-2opi  
https://tildalice.io/github-actions-vs-gitlab-ci-cache-speed-benchmark/  
https://devops-daily.com/comparisons/gitlab-ci-vs-github-actions  
https://docs.gitlab.com/administration/instance_limits/  
https://faun.dev/sensei/academy/go/cloud-native-cicd-with-gitlab-9ddf2c-b12fdd-50a685/cloud-native-gitlab-runners-on-kubernetes-scalab-2/concurrency-limits-and-request-concurrency-8d0fe0/  
https://clickhouse.com/blog/how-gitlab-uses-clickhouse-to-scale-analytical-workloads  
https://docs.gitlab.com/ci/yaml/  
https://devops.stackexchange.com/questions/9359/gitlab-ci-error-during-connect-get-http-docker2375-v1-40-containers-jsonall  

---

## REQUISITOS DE HARDWARE
Sem dados nos resultados para esta seção.

---

## COMANDOS DE INSTALAÇÃO
Sem dados nos resultados para esta seção.

---

## ERROS COMUNS
1. **Docker-in-Docker (DinD) Privilege Error**  
   - **Causa**: Jobs usando `services: - docker:dind` exigem `privileged: true` no runner.  
   - **Solução**: Adicionar `privileged: true` na configuração do runner.  
   - **Exemplo**:  
     ```yaml
     tags:
       - docker
     script:
       - docker info
     ```

2. **Cache Ineficiente para Dependências Grandes**  
   - **Causa**: Cache de `node_modules` (arquivos pequenos) é lento.  
   - **Solução**: Usar cache do diretório do npm (`npm_config_cache`) em vez de `node_modules`.  
   - **Exemplo**:  
     ```yaml
     cache:
       key:
         files:
           - package-lock.json
       paths:
         - .npm
     ```

3. **Imagens Docker com Tag `latest`**  
   - **Causa**: Builds não reprodutíveis devido a atualizações não controladas.  
   - **Solução**: Especificar versão exata (ex: `node:16.3.0`).  

---

## DADOS RELEVANTES PARA: performance / throughput
### Latência de enfileiramento e startup de jobs em carga alta
- **Latência estável**: Em testes de carga, um serviço relacionado ao GitLab CI apresentou latência média de **1.41ms** (p95: **1.63ms**) com 300 usuários concorrentes.  
- **Throughput**: O serviço suportou **322 requisições/segundo** sem falhas ou timeouts.  
- **Limites de instância**: GitLab impõe limites para manter performance, mas valores específicos não foram detalhados.  

### Throughput de jobs paralelos com matrix builds
- **Matrix builds suportados**: GitLab CI permite jobs paralelos em múltiplas combinações (ex: SO + versões de Node.js).  
- **Exemplo**:  
  ```yaml
  .test_template:
    stage: test
    script:
      - echo "Teste em $OS com Node $NODE_VERSION"
  matrix:
    os: [ubuntu, macos, windows]
    node_version: [14, 16, 18]
  ```  
- **Dados quantitativos**: Não foram encontrados benchmarks específicos de throughput para matrix builds.  

### Overhead de cache de dependências e artefatos entre runs
- **Cache de dependências**:  
  - Para **400MB de `node_modules`**, o cache do GitLab CI levou **10.5s**, enquanto GitHub Actions levou **2.1s**.  
  - **Recomendação**: Usar cache do diretório do npm (ex: `.npm`) em vez de `node_modules` para reduzir overhead.  
- **Artefatos**:  
  - Armazenados no servidor GitLab, baixados por jobs subsequentes.  
  - **Limitação**: Artefatos grandes (ex: >2GB) podem causar gargalos.  

### Impacto de runners self-hosted vs managed no tempo total do pipeline
- **Runners gerenciados (SaaS)**:  
  - Lentos durante horários de pico devido à alta demanda.  
- **Runners auto-hospedados**:  
  - **Autoscaling**: Suportado via Docker Machine ou Kubernetes, reduzindo tempos de espera.  
  - **Exemplo de configuração**:  
    ```yaml
    runners:
      executor: kubernetes
      kubernetes:
        autoscaler: true
    ```  
- **Concorrência**: Excesso de jobs paralelos pode causar contenção de recursos (CPU/disco), aumentando latência.  

---

## ALTERNATIVAS MENCIONADAS
- **GitHub Actions**:  
  - Cache mais rápido (2.1s vs 10.5s para 400MB de `node_modules`).  
  - Runners gerenciados mais rápidos durante picos.  
- **Kaniko**:  
  - Alternativa ao Docker-in-Docker para builds de imagens Docker, mais rápida e segura.  
- **ClickHouse**:  
  - Usado pelo GitLab para analytics de alta performance (sub-second para 100M+ linhas).