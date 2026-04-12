"""
Monitor de eventos em tempo real do pipeline SDD.
Lê o arquivo pipeline_events.jsonl e mostra o que está acontecendo.

Uso:
  python3 watch_events.py          # Mostra todos os eventos
  python3 watch_events.py url_found # Mostra apenas URLs encontradas
  python3 watch_events.py --tail 20 # Mostra últimos 20 eventos
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def read_events(log_file: str = "output/pipeline_events.jsonl"):
    """Read all events from JSONL log file into memory.
    
    Skips malformed JSON lines silently.
    
    Args:
        log_file: Path to JSONL file
        
    Returns:
        List of parsed event dicts
        
    Example:
        events = read_events("output/pipeline_events.jsonl")
        print(f"Read {len(events)} events")
    """
    path = Path(log_file)
    if not path.exists():
        return []

    events = []
    with open(path, 'r') as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except:
                pass
    return events


def format_time(iso_string: str) -> str:
    """Convert ISO 8601 timestamp to HH:MM:SS format.
    
    Args:
        iso_string: ISO format timestamp string
        
    Returns:
        Formatted time string or original input if parsing fails
        
    Example:
        time_str = format_time("2026-04-12T12:34:56.123")
        # Returns: "12:34:56"
    """
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%H:%M:%S")
    except:
        return iso_string


def print_event(event: dict):
    """Format and print single event in compact table row format.
    
    Args:
        event: Event dict from JSONL
        
    Example:
        print_event({"type": "url_found", "url": "https://example.com", ...})
        # Output: "[12:34:56] url_found       ✓ https://example.com"
    """
    time_str = format_time(event.get("timestamp", ""))
    event_type = event.get("type", "unknown")

    print(f"[{time_str}] {event_type:20}", end="")

    if event_type == "url_found":
        url = event.get("url", "?")
        title = event.get("title", "")
        status = event.get("status", "")
        elapsed = event.get("elapsed_seconds", None)

        status_emoji = {
            "ok": "✓",
            "scrape_failed": "⚠",
            "skipped": "⊘"
        }.get(status, "•")

        elapsed_str = f" ({elapsed:.1f}s)" if elapsed else ""
        title_str = f" — {title}" if title else ""

        print(f" {status_emoji} {url}{title_str}{elapsed_str}")

    elif event_type == "search_query":
        query = event.get("query", "?")
        print(f" 🔍 {query}")

    elif event_type == "section_start":
        number = event.get("number", "?")
        total = event.get("total", "?")
        title = event.get("title", "?")
        print(f" [{number}/{total}] {title}")

    elif event_type == "task_completed":
        desc = event.get("description", "?")
        elapsed = event.get("elapsed_seconds", 0)
        print(f" ✓ {desc} ({elapsed:.1f}s)")

    elif event_type == "task_failed":
        desc = event.get("description", "?")
        error = event.get("error", "?")
        print(f" ✗ {desc} — {error}")

    elif event_type == "search_done":
        tool = event.get("tool", "?")
        n_results = event.get("n_results", "?")
        n_queries = event.get("n_queries", "?")
        print(f" {tool}: {n_results} results from {n_queries} queries")

    else:
        details = {k: v for k, v in event.items() if k not in ["timestamp", "type"]}
        if details:
            print(f" {details}")
        else:
            print()


def stats_summary(events: list):
    """Print summary statistics from all events.
    
    Generates counts by event type, URL success/fail breakdown, 
    scraping timing (min/max/avg), and total pipeline duration.
    
    Args:
        events: List of event dicts from read_events()
        
    Example:
        events = read_events()
        stats_summary(events)
    """
    print("\n" + "=" * 70)
    print("📊 RESUMO DE EVENTOS")
    print("=" * 70)

    counts = defaultdict(int)
    for evt in events:
        counts[evt.get("type", "unknown")] += 1

    print("\nTipos de eventos encontrados:")
    for event_type, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {event_type:20}: {count:3} evento(s)")

    urls_ok = sum(1 for e in events if e.get("type") == "url_found" and e.get("status") == "ok")
    urls_failed = sum(1 for e in events if e.get("type") == "url_found" and e.get("status") == "scrape_failed")
    urls_skipped = sum(1 for e in events if e.get("type") == "url_found" and e.get("status") == "skipped")

    print(f"\n🔗 URLs encontradas:")
    print(f"  ✓ OK (extraído): {urls_ok}")
    print(f"  ⚠ Falhado (fallback): {urls_failed}")
    print(f"  ⊘ Pulado: {urls_skipped}")

    elapsed_times = []
    for e in events:
        if e.get("type") == "url_found" and e.get("elapsed_seconds"):
            elapsed_times.append(e.get("elapsed_seconds"))

    if elapsed_times:
        print(f"\n⏱️  Tempo de scraping:")
        print(f"  Min:  {min(elapsed_times):.2f}s")
        print(f"  Max:  {max(elapsed_times):.2f}s")
        print(f"  Avg:  {sum(elapsed_times) / len(elapsed_times):.2f}s")

    if events:
        first_time = datetime.fromisoformat(events[0].get("timestamp", ""))
        last_time = datetime.fromisoformat(events[-1].get("timestamp", ""))
        total_duration = (last_time - first_time).total_seconds()
        print(f"\n⏳ Duração total: {total_duration:.1f}s")

    print()


def main():
    """Entry point for watch_events.py script.
    
    Reads all events from JSONL and displays them with optional filtering and tailing.
    
    Usage:
        python3 watch_events.py              # All events with summary
        python3 watch_events.py url_found    # Filter by event type
        python3 watch_events.py --tail=20    # Show last 20 events
        python3 watch_events.py --help       # Show usage
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        return

    log_file = "output/pipeline_events.jsonl"
    filter_type = None
    tail = None

    for arg in sys.argv[1:]:
        if arg.startswith("--tail"):
            parts = arg.split("=")
            if len(parts) > 1:
                tail = int(parts[1])
            else:
                tail = 20
        elif not arg.startswith("--"):
            filter_type = arg

    events = read_events(log_file)

    if not events:
        print(f"❌ Nenhum evento encontrado em {log_file}")
        print(f"   (O pipeline está rodando? Verifique com: python3 main.py ...)")
        return

    if filter_type:
        events = [e for e in events if e.get("type") == filter_type]
        if not events:
            print(f"❌ Nenhum evento do tipo '{filter_type}' encontrado")
            return

    if tail:
        events = events[-tail:]

    print(f"📋 Mostrando {len(events)} evento(s)\n")
    for event in events:
        print_event(event)

    stats_summary(events)


if __name__ == "__main__":
    main()
