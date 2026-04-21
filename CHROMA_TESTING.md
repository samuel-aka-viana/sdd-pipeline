# Chroma Query Testing Guide

## Overview

O arquivo `test_chroma_queries.py` fornece um ambiente interativo para testar e verificar dados no Chroma.

---

## Como Usar

### Iniciar o Teste

```bash
python test_chroma_queries.py
```

### Menu Principal

```
Chroma Query Tester
Teste de dados e isolamento de ferramenta

  1 📊 Estatísticas do Chroma
  2 🔒 Teste de isolamento por ferramenta
  3 🔍 Busca semântica interativa
  4 🔗 Busca cross-tool (conhecimento transferível)
  5 ✅ Verificação de integridade dos dados
  0 Sair

Escolha:
```

---

## Opções Detalhadas

### 1️⃣ Estatísticas do Chroma (📊)

Mostra um resumo dos dados armazenados.

**Output:**
```
Dados por Ferramenta
┌─────────────┬────────┬──────────────┐
│ Ferramenta  │ Chunks │ URLs Únicas  │
├─────────────┼────────┼──────────────┤
│ docker      │ 45     │ 8            │
│ podman      │ 38     │ 7            │
│ postgresql  │ 52     │ 9            │
└─────────────┴────────┴──────────────┘

Total: 135 chunks de 3 ferramentas
```

**O que verificar:**
- ✅ Se há dados de todas as ferramentas que você pesquisou
- ✅ Quanto de dados foi armazenado (chunks = segmentos semânticos)
- ✅ Quantas URLs únicas por ferramenta

---

### 2️⃣ Teste de Isolamento por Ferramenta (🔒)

Verifica se o isolamento de dados está funcionando corretamente.

**O que testa:**
- Cada ferramenta retorna APENAS seus próprios dados
- Não há contaminação cruzada (Docker tips → Podman)
- Filtro por `tool=` está funcionando

**Output esperado:**
```
  ✓ docker: 5 resultados (filtrado) vs 35 (global)
  ✓ podman: 4 resultados (filtrado) vs 33 (global)
  ✓ postgresql: 3 resultados (filtrado) vs 39 (global)

✓ Isolamento por ferramenta: OK
```

**Se der erro:**
```
✗ ERRO: Resultado filtrado tem tool errado!
  Esperado: docker, Recebido: podman
```
→ Há um problema de isolamento! Verifique `skills/analyst.py` e `pipeline.py`.

---

### 3️⃣ Busca Semântica Interativa (🔍)

Permite fazer queries manuais e ver resultados com scores.

**Fluxo:**
```
Ferramentas disponíveis:
  1. docker
  2. podman
  3. postgresql

Escolha ferramenta (número): 1

Query para docker: performance optimization rootless

Quantos resultados? (padrão 5): 5

Buscando em docker...

1. Similaridade: 0.878
   URL: https://docs.docker.com/engine/security/rootless/...
   Título: Run the Docker daemon as a non-root user
   Chunk 2/5
   Preview: Rootless mode allows running the Docker daemon...

2. Similaridade: 0.832
   ...
```

**Como interpretar:**
- `Similaridade: 0.878` = quão similar é o resultado (0-1, maior = melhor)
- `Chunk 2/5` = este é o chunk 2 de um documento com 5 chunks
- Preview mostra primeiros 200 caracteres

**Usar para:**
- ✅ Testar se a busca semântica funciona
- ✅ Ver que score é necessário para bom resultado
- ✅ Verificar relevância dos chunks armazenados

---

### 4️⃣ Busca Cross-Tool (🔗)

Testa transferência de conhecimento entre ferramentas.

**Exemplo:**
```
Ferramentas disponíveis:
  1. docker
  2. podman
  3. kubernetes

Ferramentas a EXCLUIR (número): 1

Query (sem docker): rootless containers security

Buscando em outras ferramentas (excluindo docker)...

✓ 3 resultado(s):

1. [PODMAN] Run as rootless user
   Sim: 0.876 | https://podman.io/docs/rootless...

2. [KUBERNETES] Pod Security Standards
   Sim: 0.654 | https://kubernetes.io/docs/concepts/...

3. [PODMAN] Rootless networking configuration
   Sim: 0.821 | https://podman.io/docs/networking...
```

**Usar para:**
- ✅ Verificar que cross-tool knowledge transfer funciona
- ✅ Encontrar insights de um tool para aplicar em outro
- ✅ Validar que Chroma está indexando semântica, não apenas keywords

---

### 5️⃣ Verificação de Integridade (✅)

Valida consistência dos dados armazenados.

**O que verifica:**
- Todos os chunks têm metadados obrigatórios (tool, url, title, chunk_index)
- Chunk count está correto (número de chunks por documento)
- Documentos = Metadados (sem desincronização)

**Output esperado:**
```
✓ Integridade OK
  • 135 chunks válidos
  • 3 ferramentas
  • 24 URLs únicas
```

**Se der erro:**
```
⚠ Problemas encontrados:
  • Chunk 42: falta campo 'tool'
  • docker#https://docs.docker.com: tem 3 chunks, esperado 5
  • Documentos (130) ≠ Metadados (135)
```

→ Há corrupção de dados! Considere executar `rm -rf .memory/chroma_db` e recolher dados.

---

## Cenários de Teste

### Cenário 1: Verificar após primeira pesquisa

```bash
# Run
$ python main.py
# (Escolha Docker, contexto, etc)

# Test
$ python test_chroma_queries.py
# [1] Estatísticas → deve mostrar Docker
# [2] Isolamento → Docker filter OK
# [5] Integridade → OK
```

### Cenário 2: Verificar isolamento com múltiplas ferramentas

```bash
# Run 1
$ python main.py  # Docker
# Run 2
$ python main.py  # Podman

# Test
$ python test_chroma_queries.py
# [1] Stats → Docker + Podman
# [2] Isolamento → Nenhum dado de Docker em Podman query
# [3] Search Docker → Só Docker
# [3] Search Podman → Só Podman
# [4] Cross-tool → Docker tips aparece ao buscar Podman
```

### Cenário 3: Validar performance de busca

```bash
$ python test_chroma_queries.py
# [3] Search interativa
# Query: "performance benchmarks"
# Resultados com similaridade > 0.7?
# Se não, dados de benchmark não foram bem indexados
```

### Cenário 4: Debug de contaminação

Se você suspeita que dados estão sendo misturados:

```bash
$ python test_chroma_queries.py
# [2] Isolamento por ferramenta
# Se alguma ferramenta falhar → há isolamento quebrado
# Verifique analyst.py e pipeline.py para tool filtering
```

---

## Troubleshooting

### "Chroma está vazio"
**Causa:** Nenhuma pesquisa foi executada ainda.
```bash
python main.py
# Execute uma pesquisa
```

### Similaridade sempre baixa (< 0.5)
**Possível causa:** Query mal formulada ou dados irrelevantes.
```bash
# Tente query mais específica
Query anterior: "performance"
Query melhor: "docker performance optimization"
```

### Isolamento quebrado (Docker dados aparecendo em Podman)
**Causa:** Filtering não está funcionando em analyst.py ou pipeline.py.
```bash
# Verifique:
grep -n "tool=primary_tool" skills/analyst.py
grep -n "tool=" pipeline.py
```

### "Chunk count mismatch"
**Causa:** Dados corrompidos no Chroma.
```bash
# Reset Chroma
rm -rf .memory/chroma_db
# Re-execute pesquisa
python main.py
```

---

## Automação

Para testar automaticamente sem interação:

```python
from test_chroma_queries import *

# Stats
print_stats()

# Isolation
test_tool_isolation()

# Integrity
verify_data_integrity()
```

Ou via shell:

```bash
echo -e "1\n2\n5\n0" | python test_chroma_queries.py
```

---

## Métricas Esperadas

| Métrica | Esperado | Alerta |
|---------|----------|--------|
| Chunks por URL | 3-10 | < 3 ou > 20 |
| URLs por tool | 5+ | < 3 |
| Similaridade top-1 | > 0.8 | < 0.5 |
| Isolamento | 100% | Qualquer falha |
| Integridade | OK | Qualquer erro |

---

## Próximas Melhorias

- [ ] Exportar resultados para CSV (análise)
- [ ] Benchmark de performance (query latency)
- [ ] Visualização de embedding clusters
- [ ] Teste de deduplicação (URL duplicadas?)
