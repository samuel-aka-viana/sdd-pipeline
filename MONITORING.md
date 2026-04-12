# 🔍 Real-time Scraping Monitoring

Este projeto agora registra **todos os eventos do pipeline** em tempo real, permitindo você acompanhar exatamente o que o sistema está fazendo e **por quanto tempo**.

## Como usar

### 1️⃣ **Monitorar em TEMPO REAL** (enquanto o pipeline roda)

Em um terminal separado, execute:

```bash
python3 tail_events.py
```

Isso mostrará **todos os eventos** conforme aparecem:
- URLs sendo consultadas
- Queries de busca
- Tempos de scraping
- Erros

Exemplo de output:

```
👀 Monitoring: output/pipeline_events.jsonl
   (Pressione Ctrl+C para sair)

[12:34:56] 🚀 Pipeline START
           Tools: DuckDB, Polars
           Context: Comparison

[12:35:01] ━━━ [1/4] Pesquisando ━━━
[12:35:02] 🔍 Search: duckdb vs polars benchmark
[12:35:04] ✓ https://docs.getdbt.com/... (2.3s)
[12:35:06] ⚠ https://github.com/... (timeout)
[12:35:10] ✓ https://stackoverflow.com/... (1.1s)
```

### 2️⃣ **Filtrar apenas URLs**

Para ver APENAS os links sendo consultados:

```bash
python3 tail_events.py url_found
```

### 3️⃣ **Analisar depois (histórico)**

Após o pipeline terminar, analise o que aconteceu:

```bash
# Ver todos os eventos
python3 watch_events.py

# Ver últimos 20 eventos
python3 watch_events.py --tail=20

# Ver apenas URLs
python3 watch_events.py url_found
```

Exemplo de análise:

```
[15:30:45] url_found        ✓ https://docs.duckdb.org/... — Understanding DuckDB Syntax (1.2s)
[15:30:46] url_found        ✓ https://polars.readthedocs.io/... — Polars API Reference (0.8s)
[15:30:48] url_found        ⚠ https://example.com/... — [timeout]
[15:30:48] url_found        ⊘ https://reddit.com/... (skipped)

📊 RESUMO DE EVENTOS
=================================================================
Tipos de eventos encontrados:
  url_found            : 42 evento(s)
  search_query         : 12 evento(s)
  task_completed       :  4 evento(s)

🔗 URLs encontradas:
  ✓ OK (extraído): 32
  ⚠ Falhado (fallback): 8
  ⊘ Pulado: 2

⏱️  Tempo de scraping:
  Min:  0.50s
  Max:  5.20s
  Avg:  1.85s

⏳ Duração total: 245.3s
```

## 📊 O que está sendo registrado

**pipeline_events.jsonl** contém eventos estruturados em JSON Lines:

```jsonl
{"timestamp": "2026-04-12T12:34:56.123", "type": "pipeline_start", "ferramentas": "DuckDB, Polars", "contexto": "Comparison"}
{"timestamp": "2026-04-12T12:34:57.456", "type": "url_found", "url": "https://docs.duckdb.org", "title": "DuckDB Documentation", "status": "ok", "elapsed_seconds": 1.2}
{"timestamp": "2026-04-12T12:35:00.789", "type": "url_found", "url": "https://example.com", "title": "Timeout error", "status": "scrape_failed", "elapsed_seconds": 15.0}
```

## 🎯 Casos de uso

### Diagnóstico de lentidão

Se o pipeline demora muito:
1. Execute `python3 tail_events.py url_found` e veja quais URLs estão demorando
2. Verifique se há um padrão (ex: todos os GitHub demorando, ou Stackoverflow?)
3. Analise `elapsed_seconds` para saber qual fase demora mais

### Verificar qualidade de URLs

```bash
python3 watch_events.py url_found
```

Procure por:
- URLs de domínios oficiais (docs.*, github.com, official sites)
- Taxa de sucesso (✓ vs ⚠)
- Quantidade vs qualidade

### Integração com Gradio/FastAPI

O arquivo `pipeline_events.jsonl` pode ser consumido diretamente:

```python
from pathlib import Path
import json

def get_scraping_progress():
    """Retorna progresso em tempo real para WebSocket."""
    events = []
    with open("output/pipeline_events.jsonl", "r") as f:
        for line in f:
            events.append(json.loads(line))
    
    # Calcula estatísticas
    urls_ok = sum(1 for e in events if e.get("type") == "url_found" and e.get("status") == "ok")
    urls_failed = sum(1 for e in events if e.get("type") == "url_found" and e.get("status") == "scrape_failed")
    
    return {
        "total_events": len(events),
        "urls_success": urls_ok,
        "urls_failed": urls_failed,
        "events": events[-10:]
    }
```

## 📝 Notas de implementação

- **EventLog** gera `output/pipeline_events.jsonl` (append-only)
- Cada evento tem **timestamp ISO 8601** para análise temporal
- **Tempos de scraping** são medidos em segundos com precisão
- Scripts são independentes - não bloqueiam o pipeline
- Compatível com futuras integrações de UI (Gradio, FastAPI WebSocket, etc)
