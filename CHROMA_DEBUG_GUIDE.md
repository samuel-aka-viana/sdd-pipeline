# Chroma Debug Guide: Por que dados não aparecem?

## O Bug que Estava Acontecendo

**Sintoma:** 
- Log diz "Chroma save successful" ✓
- Mas quando faz query, dados não aparecem ❌

**Causa:**
```python
# ANTES (BUG):
if self.chroma:
    self.chroma.save_scraped_content(...)  # Pode falhar!
    self.memory.log_event("chroma_save", {...})  # Loga SEMPRE!
```

Mesmo se `save_scraped_content()` **falhasse** (retornasse False), o código **ainda registrava o log de sucesso**!

**Resultado:** Você vê o log mas os dados não estão realmente no Chroma.

---

## Correção Implementada

Agora o código verifica o return value:

```python
# DEPOIS (CORRIGIDO):
success = self.chroma.save_scraped_content(...)
if success:
    self.memory.log_event("chroma_save", {...})  # Só loga se sucesso!
else:
    logger.warning(f"Failed to save to Chroma: {url}")  # Registra erro
```

---

## Como Verificar se Chroma Está Salvando

### 1️⃣ Durante a Pesquisa

Rode `python main.py` e observe os logs:

```
✓ Pesquisando docker...
   ✓ https://docs.docker.com (30KB) ← Scrapeado com sucesso
   ✓ Chroma: 1 chunks (official) ← Salvo no Chroma!
```

Se não tiver a linha "Chroma:", pode ser:
- `HAS_CHROMA = False` (Chroma não importou)
- Erro silencioso no Chroma

### 2️⃣ Verificar HAS_CHROMA

```bash
python -c "
from skills.researcher import HAS_CHROMA, logger
print(f'HAS_CHROMA: {HAS_CHROMA}')
if not HAS_CHROMA:
    print('⚠️  Chroma não está disponível!')
    print('Instale: pip install chromadb')
"
```

### 3️⃣ Checar eventos registrados

```bash
grep "chroma_save" .memory/episodic.json | head -3
# Deve mostrar eventos de salvamento bem-sucedido
```

### 4️⃣ Consultar Chroma diretamente

```bash
python test_chroma_queries.py
# [1] Estatísticas → mostra chunks por ferramenta
```

---

## Cenários Comuns

### Cenário A: Dados em disco, não no Chroma

**Sinais:**
- ✅ `output/debug_research_docker.md` existe (40KB)
- ❌ `test_chroma_queries.py [1]` mostra 0 chunks

**Causa:** HAS_CHROMA era False

**Solução:**
```bash
python repopulate_chroma.py
# Carrega arquivo histórico para Chroma
```

---

### Cenário B: Chroma vazio completamente

**Sinais:**
- ❌ Nenhum arquivo em `output/debug_research_*.md`
- ❌ Chroma.get() retorna vazio

**Causa:** Nunca rodou pesquisa completa

**Solução:**
```bash
python main.py
# Execute pesquisa de uma ferramenta
# Deixe completar totalmente
```

---

### Cenário C: Chroma com alguns dados, não todos

**Sinais:**
- ✅ Docker (1 chunk) no Chroma
- ❌ Flink/Spark não aparecem, mas existem em `output/debug_research_*.md`

**Causa:** Pesquisas antigas rodaram quando Chroma não estava disponível

**Solução:**
```bash
python repopulate_chroma.py
# Carrega todos os arquivos históricos
```

---

## Checklist de Diagnóstico

```bash
# 1. Chroma está instalado?
python -c "import chromadb; print(chromadb.__version__)"
# Deve retornar versão (ex: 1.1.1)

# 2. HAS_CHROMA está True?
python -c "from skills.researcher import HAS_CHROMA; print(HAS_CHROMA)"
# Deve retornar True

# 3. Arquivos históricos existem?
ls output/debug_research_*.md
# Deve listar arquivos

# 4. Chroma tem dados?
python test_chroma_queries.py
# [1] Estatísticas → deve mostrar ferramentas

# 5. Se faltam dados, repopular
python repopulate_chroma.py
# Carrega tudo do disco para Chroma
```

---

## Fluxo Esperado

```
1. python main.py
   ├─ Scrape URLs → content em disco
   ├─ Save em debug_research_docker.md ✓
   ├─ Save no Chroma (se HAS_CHROMA=True) ✓
   └─ Log: "chroma_save" event ✓

2. Verificar
   python test_chroma_queries.py [1]
   └─ Deve mostrar Docker chunks ✓

3. Se falta dados no Chroma
   python repopulate_chroma.py
   └─ Carrega arquivo histórico pro Chroma ✓

4. Verificar novamente
   python test_chroma_queries.py [1]
   └─ Agora mostra Docker ✓
```

---

## Logs para Monitorar

### ✅ Sucesso
```json
{"type": "chroma_save", "tool": "docker", "chunk_count": 5, "content_chars": 1200}
```

### ❌ Falha (agora registrado)
```
[WARNING] Failed to save to Chroma: https://docs.docker.com/...
```

---

## Performance

**Com Chroma disponível:**
- Pesquisa: 10 minutos
- Scraping: 5 minutos
- Chroma save: Automático (embeded em paralelo)

**Sem Chroma disponível:**
- Pesquisa: 10 minutos (igual)
- Scraping: 5 minutos (igual)
- Chroma save: **Pulado** (dados em disco apenas)
- Repopular depois: 5 segundos com `repopulate_chroma.py`

---

## Próximas Melhorias

- [ ] Mostrar warning se HAS_CHROMA=False durante startup
- [ ] Autodetectar falta de dados no Chroma e sugerir repopulation
- [ ] Dashboard de saúde do Chroma em `watch_events.py`
