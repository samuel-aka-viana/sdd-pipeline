# github actions
## URLS CONSULTADAS
https://github.com/marketplace/actions/publish-test-results  
https://gist.github.com/denji/8333630  
https://github.com/marketplace/actions/azure-load-testing  
https://github.com/Azure/load-testing  
https://thenewstack.io/simple-load-testing-with-github-actions/  
https://github.com/Kadle11/CPU_Heatmap  
https://microsoftlearning.github.io/AZ400-DesigningandImplementingMicrosoftDevOpsSolutions/Instructions/Labs/AZ400_M02_L05_Implement_GitHub_Actions_for_CI_CD.html  
https://lifetips.alibaba.com/tech-efficiency/github-actions-vs-gitlab-ci-which-fails-faster  
https://www.devtoolreviews.com/reviews/github-actions-vs-circleci-vs-gitlab-ci  
https://github.com/open-feature/flagd-evaluator  
https://github.com/fasterci/rules_gitops  
https://lab.amalitsky.com/posts/2021/optimize-github-actions-with-cache/  
https://firebase.google.com/docs/auth/ios/github-auth  
https://wpaiwriter.com/github-actions-wp-test/  
https://docs.github.com/en/actions/reference/limits  
https://wellarchitected.github.com/library/collaboration/recommendations/scaling-actions-reusability/  
https://github.com/Developer-Y/Scalable-Software-Architecture  
https://medium.com/@aayushpaigwar/understanding-github-actions-artifact-storage-limits-and-how-to-manage-them-a577939f1c57  
https://medium.com/@alex.ivenin/understanding-and-overcoming-limitations-of-github-actions-52956e9e2823  
https://github.com/orgs/community/discussions/39697  
https://austen.info/blog/actions-is-the-ai-native-platform/  
https://knapsackpro.com/ci_comparisons/github-actions/vs/gitlab-ci  
https://traderoom.info/gitlab-ci-vs-github-actions/  
https://www.futurevistaacademy.com/platform-engineering/jenkins-vs-github-actions-vs-gitlab-ci-2025  
https://squareops.com/blog/jenkins-vs-github-actions-vs-gitlab-ci-2026/  
https://stacktrack.com/posts/post-the-great-ci-cd-showdown-jenkins-vs-gitlab-vs-github-actions/  
https://dev.to/renzoflv/github-actions-vs-gitlab-ci-comparacion-completa-de-herramientas-cicd-2dj1  
https://attractgroup.com/blog/continuous-integration-tools-for-devops-jenkins-vs-gitlab-ci-vs-github-action/  
https://saucelabs.com/resources/blog/circleci-vs-github-actions-vs-gitlab-key-differences  
https://hackanons.com/gitlab-ci-vs-github-actions-2026/  
https://github.com/  
https://www.tech-blog.startup-technology.com/2020/85c36da0a4b51cf9ccfd/  
https://github.blog/changelog/2024-03-04-github-actions58-larger-runners-windows-11-beta/  
https://github.com/orgs/community/discussions/175886  
https://medium.com/@hanoi.fragata/github-actions-potencia-el-despliegue-con-matrix-1d6be4ff1d51  
https://pockit.tools/es/blog/github-actions-monorepo-runners-guide-2026/  
https://jacobian.org/til/github-actions-poetry/  
https://www.freelancer.pt/jobs/api-developmet/  
https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching  
https://docs.github.com/en/actions  
https://dev.to/github/caching-dependencies-to-speed-up-workflows-in-github-actions-3efl  
https://medium.com/@pmagyei/github-actions-understanding-data-flow-with-inputs-outputs-caching-artefacts-e233051bd132  
https://www.codegenes.net/blog/github-actions-how-to-cache-dependencies-between-workflow-runs-of-different-branches/  
https://docs.github.com/en/actions/concepts/runners/self-hosted-runners  
https://blog.4linux.com.br/github-actions-self-hosted-runner-no-kubernetes/  
https://jakeinsight.com/tech/2026-03-24-github-actions-selfhosted-runner-docker-container/  
https://x-apps.com.br/guia-cicd-times-pequenos-performance-cache-runners/  
https://faun.pub/setting-up-github-self-hosted-runners-on-ec2-24ad1bd2248c  
https://github.com/benchmark-action/github-action-benchmark  
https://bencher.dev/docs/how-to/github-actions/  
https://deepwiki.com/benchmark-action/github-action-benchmark/5.2-custom-benchmarks  
https://runs-on.com/benchmarks/  
https://blog.martincostello.com/continuous-benchmarks-on-a-budget/  
https://dev.to/_d7eb1c1703182e3ce1782/github-actions-vs-gitlab-cicd-complete-cicd-comparison-2026-48ac  
https://devops-daily.com/comparisons/gitlab-ci-vs-github-actions  
https://tech-insider.org/github-vs-gitlab-2026-2/  
https://fastbuilder.ai/blog/github-actions-vs-gitlab-ci  
https://www.bytebase.com/blog/gitlab-ci-vs-github-actions/  
https://docs.computeblade.com/blog/2024/12/26/cicd_part_1  
https://github.com/team  

## REQUISITOS DE HARDWARE  
Não foram encontrados requisitos de hardware específicos nos resultados. Os dados mencionam especificações dos runners hospedados pelo GitHub (ex: 4 vCPUs e 16 GB RAM para runners padrão), mas não há requisitos de hardware para o usuário.  

## COMANDOS DE INSTALAÇÃO  
Não foram encontrados comandos de instalação nos resultados.  

## ERROS COMUNS  
Não foram encontrados erros comuns com soluções nos resultados.  

## DADOS RELEVANTES PARA: performance / throughput  
- **Latência de enfileiramento e startup de jobs em carga alta**:  
  - GitHub-hosted runners: startup típico de 15–45 segundos (https://dev.to/_d7eb1c1703182e3ce1782/github-actions-vs-gitlab-cicd-complete-cicd-comparison-2026-48ac).  
  - Jobs com warm-pooling: startup em 4–5 segundos (https://tech-insider.org/github-vs-gitlab-2026-2/).  
  - Sob carga alta, o tempo de enfileiramento pode aumentar, mas não há dados quantitativos específicos.  

- **Throughput de jobs paralelos com matrix builds**:  
  - Matrix builds são suportados e facilitam testes multiplataforma e multi-versão (https://dev.to/_d7eb1c1703182e3ce1782/github-actions-vs-gitlab-cicd-complete-cicd-comparison-2026-48ac).  
  - Não há números específicos de throughput (ex: jobs por minuto) nos resultados.  

- **Overhead de cache de dependências e artefatos entre runs**:  
  - Cache de dependências via `actions/cache` para acelerar recriação de arquivos (https://dev.to/github/caching-dependencies-to-speed-up-workflows-in-github-actions-3efl).  
  - Artesfatos gerenciados via `actions/upload-artifact` e `actions/download-artifact` (https://devops-daily.com/comparisons/gitlab-ci-vs-github-actions).  
  - Não há números específicos de overhead (ex: tempo salvo ou tempo de operação de cache) nos resultados.  

- **Impacto de runners self-hosted vs managed no tempo total do pipeline**:  
  - Managed (hosted) runners: startup de 15–45 segundos (https://dev.to/_d7eb1c1703182e3ce1782/github-actions-vs-gitlab-cicd-complete-cicd-comparison-2026-48ac).  
  - Self-hosted runners com pré-aquecimento (pre-warmed images): startup inferior a 5 segundos (https://dev.to/_d7eb1c1703182e3ce1782/github-actions-vs-gitlab-cicd-complete-cicd-comparison-2026-48ac).  
  - Sem pré-aquecimento, o tempo de startup pode ser maior.  

## ALTERNATIVAS MENCIONADAS  
- GitLab CI  
- CircleCI  
- Jenkins  
- Bitbucket  
- BuildKite  
- Flux CD  
- Argo CD  
- StrongDM  
- Bytebase