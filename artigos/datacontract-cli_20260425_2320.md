# DataContract CLI: Padronizando Contratos de Dados em Ambientes Distribuídos
> **TL;DR:** Ferramenta CLI para definir, versionar e validar contratos de dados entre produtores e consumidores com integração nativa em CI/CD.
## O que é e por que usar
O DataContract CLI é uma ferramenta de linha de comando que implementa o padrão Open Data Contract Standard (ODCS), permitindo definir contratos de dados em arquivos YAML. Ela é especialmente valiosa para integração entre times produtores (quem gera os dados) e consumidores (quem consome os dados), pois estabelece um contrato formal sobre estrutura, qualidade e formato dos dados. Ao automatizar validações em CI/CD e detectar breaking changes proativamente, elimina incompatibilidades entre sistemas e reduz custos de integração. Suporte nativo para múltiplos ambientes (dev, staging, prod) e exportação para Schema Registry/Data Catalogs torna-se essencial em arquiteturas de dados modernas.
## Requisitos
Não há requisitos de hardware específicos. O DataContract CLI é compatível com qualquer ambiente que execute Python 3.10+ ou Docker, sem exigências adicionais de RAM/CPU. A única dependência é a instalação das bibliotecas necessárias para os conectores de banco de dados utilizados.
## Instalação
### Método 1: Via pip (com todas as dependências)
```bash
pip install "datacontract-cli[all]"
```
### Método 2: Via Docker
```bash
docker run --rm -v "${PWD}:/home/datacontract" datacontract/cli:latest
```
## Configuração
Exemplo de arquivo `datacontract.yaml` com múltiplos ambientes e checks de qualidade:
```yaml
dataContractSpecification: 0.9.2
id: orders-api
info:
  title: Orders API
  version: 1.0.0
servers:
  dev:
    type: postgres
    host: dev-db.example.com
    port: 5432
    database: dev_orders
    schema: public
  prod:
    type: postgres
    host: prod-db.example.com
    port: 5432
    database: prod_orders
    schema: public
fields:
  order_id:
    type: string
    required: true
    description: Unique identifier for the order
  total_amount:
    type: decimal
    required: true
    quality:
      - type: range
        config:
          min: 0
          max: 1000000
quality:
  - type: completeness
    config:
      field: order_id
      min_percentage: 99.5
  - type: uniqueness
    config:
      field: order_id
```
## Exemplo Prático
### Cenário: Validar integridade de pedidos entre time de e-commerce e time de faturamento
1. **Definir contrato**:
```bash
datacontract create --format yaml > datacontract.yaml
```
2. **Configurar ambientes**:
   - Adicionar seção `servers` no YAML para `dev` e `prod`
3. **Executar testes no ambiente de desenvolvimento**:
```bash
datacontract test --server dev datacontract.yaml
```
4. **Verificar breaking changes antes do merge**:
```bash
datacontract breaking --with main/datacontract.yaml
```
5. **Exportar schema para Confluent Schema Registry**:
```bash
datacontract export --format avro datacontract.yaml > orders.avsc
```
6. **Validar qualidade em produção**:
```bash
datacontract test --server prod datacontract.yaml
```
## Armadilhas Comuns
### ⚠ Erro de autenticação
**Sintoma:** Falha de conexão com banco de dados durante testes
**Causa:** Credenciais não configuradas nas variáveis de ambiente
**Solução:**
```bash
export DATACONTRACT_POSTGRES_USERNAME=dev_user
export DATACONTRACT_POSTGRES_PASSWORD=secure_password
```
### ⚠ Schema inválido
**Sintoma:** Comando `datacontract lint` retorna erros
**Causa:** Definição de campos incompatíveis com o tipo de servidor
**Solução:**
```bash
datacontract lint datacontract.yaml --server dev
```
### ⚠ Breaking changes não detectados
**Sintoma:** Mudanças incompatíveis passam sem alerta
**Causa:** Comparação incorreta entre versões do contrato
**Solução:**
```bash
datacontract breaking --with stable/datacontract.yaml --format markdown
```
## Dicas de Otimização
- Use alias Docker para reduzir repetição de comandos:
```bash
alias datacontract='docker run --rm -v "${PWD}:/home/datacontract" datacontract/cli:latest'
```
- Valifique contratos em PRs com GitHub Actions:
```yaml
- name: Check breaking changes
  run: datacontract breaking --with main/datacontract.yaml
```
- Gere changelog automático entre versões:
```bash
datacontract changelog v1.odcs.yaml v2.odcs.yaml > changelog.md
```
## Conclusão
O DataContract CLI oferece uma solução robusta para integração de dados entre produtores e consumidores, com vantagens significativas em automação de validações e detecção proativa de breaking changes. Suas limitações incluem dependência de configurações manuais para Data Catalogs e Schema Registry, mas isso é compensado pela flexibilidade de exportação para múltiplos formatos. Para equipes que priorizam qualidade de dados e compatibilidade contínua, a combinação de CI/CD com comandos `breaking` e `test` torna-se indispensável, especialmente em ambientes com múltiplos estágios de deploy.
## Referências
- https://github.com/datacontract/datacontract-cli/blob/main/README.md
- https://deepwiki.com/datacontract/datacontract-cli/9.2-cicd-pipeline
- https://docs.confluent.io/platform/current/schema-registry/index.html
## Respostas às Perguntas do Contexto
- Pergunta: "como integrar datacontract test em CI/CD (GitHub Actions / GitLab CI)?"
  Resposta objetiva: Use a action `datacontract/datacontract-action@main` no GitHub Actions ou execute via Docker no GitLab CI com comandos como `datacontract test datacontract.yaml` e `datacontract breaking --with stable/datacontract.yaml` para validar contratos em PRs.
  Evidência/URL: https://deepwiki.com/datacontract/datacontract-cli/9.2-cicd-pipeline
- Pergunta: "estratégia de versionamento e detecção de breaking change com datacontract diff?"
  Resposta objetiva: Utilize `datacontract breaking --with stable/datacontract.yaml` para detectar breaking changes (falha com código de saída 1 se encontrados) e `datacontract diff --with stable/datacontract.yaml` para identificar diferenças entre versões, ideal para pipelines CI.
  Evidência/URL: https://github.com/datacontract/datacontract-cli/blob/main/README.md
- Pergunta: "como mapear contrato para schema registry (Confluent, Glue) e catálogo (DataHub, OpenMetadata)?"
  Resposta objetiva: Exporte schemas com `datacontract export --format avro datacontract.yaml` para Confluent Schema Registry ou AWS Glue. Para DataHub, exporte como JSON Schema (`--format jsonschema`), e para OpenMetadata, use `--format dbt` para integração via dbt.
  Evidência/URL: https://docs.confluent.io/platform/current/schema-registry/index.html
- Pergunta: "como configurar servers e quality checks para múltiplos environments (dev, prod)?"
  Resposta objetiva: Defina múltiplos ambientes na seção `servers` do datacontract.yaml e execute testes específicos com `datacontract test --server dev datacontract.yaml`. Use variáveis de ambiente como `DATACONTRACT_POSTGRES_USERNAME` para credenciais.
  Evidência/URL: https://github.com/datacontract/datacontract-cli/blob/main/README.md