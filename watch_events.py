"""
Monitor de eventos em tempo real do pipeline SDD.
Lê o arquivo pipeline_events.jsonl e mostra o que está acontecendo.

Uso:
  python3 watch_events.py          # Mostra todos os eventos (one-shot)
  python3 watch_events.py url_found # Filtra por tipo de evento
  python3 watch_events.py --tail 20 # Mostra últimos 20 eventos
  python3 watch_events.py --watch    # Modo watch (atualiza a cada 2s)
  python3 watch_events.py --watch=1  # Watch com intervalo customizado (segundos)
  python3 watch_events.py --watch url_found  # Watch filtrando por tipo
  python3 watch_events.py --help     # Mostra essa ajuda
"""

import json
import sys
import time
import os
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


def clear_screen():
    """Clear terminal screen in a cross-platform way.
    
    Example:
        clear_screen()  # Terminal is cleared
    """
    os.system('clear' if os.name != 'nt' else 'cls')


def draw_header(watch_interval: int = None):
    """Draw header with timestamp and optional watch indicator.
    
    Args:
        watch_interval: If set, shows watch mode info with interval
        
    Example:
        draw_header()  # Regular header
        draw_header(watch_interval=2)  # Shows "Watch mode (2s)"
    """
    now = datetime.now().strftime("%H:%M:%S")
    watch_info = f" | Watch mode (atualiza a cada {watch_interval}s)" if watch_interval else ""
    print("=" * 70)
    print(f"📊 MONITOR DE EVENTOS — {now}{watch_info}")
    print("=" * 70)


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


def display_events(events: list, filter_type: str = None, tail: int = None):
    """Display filtered events with summary statistics.
    
    Args:
        events: List of event dicts from read_events()
        filter_type: Optional event type filter
        tail: Show only last N events
        
    Returns:
        Filtered list of events
        
    Example:
        events = read_events()
        filtered = display_events(events, filter_type="url_found", tail=10)
    """
    filtered_events = events
    
    if filter_type:
        filtered_events = [e for e in filtered_events if e.get("type") == filter_type]
    
    if tail:
        filtered_events = filtered_events[-tail:]
    
    if not filtered_events:
        print(f"❌ Nenhum evento encontrado")
        return []
    
    print(f"\n📋 Mostrando {len(filtered_events)} evento(s)\n")
    for event in filtered_events:
        print_event(event)
    
    stats_summary(filtered_events)
    return filtered_events


def watch_mode(log_file: str, watch_interval: int, filter_type: str = None, tail: int = None):
    """Continuously monitor events with screen updates (like 'watch' command).
    
    Polls log file every watch_interval seconds and redraw screen with updated data.
    Press Ctrl+C to exit.
    
    Args:
        log_file: Path to JSONL file to monitor
        watch_interval: Seconds between updates (default 2)
        filter_type: Optional event type filter
        tail: Show only last N events (default: all)
        
    Example:
        watch_mode("output/pipeline_events.jsonl", watch_interval=2, filter_type="url_found")
    """
    print(f"👀 Modo watch ativado (atualiza a cada {watch_interval}s)")
    print(f"   Pressione Ctrl+C para sair\n")
    
    last_count = 0
    
    try:
        while True:
            events = read_events(log_file)
            
            if len(events) != last_count:
                clear_screen()
                draw_header(watch_interval=watch_interval)
                display_events(events, filter_type=filter_type, tail=tail)
                last_count = len(events)
            
            time.sleep(watch_interval)
    
    except KeyboardInterrupt:
        print("\n\n👋 Modo watch finalizado")


def main():
    """Entry point for watch_events.py script.
    
    Reads events from JSONL and displays them with optional filtering, tailing, or watch mode.
    
    Usage:
        python3 watch_events.py              # All events with summary
        python3 watch_events.py url_found    # Filter by event type
        python3 watch_events.py --tail=20    # Show last 20 events
        python3 watch_events.py --watch      # Watch mode (updates every 2s)
        python3 watch_events.py --watch=1    # Watch with custom interval
        python3 watch_events.py --watch url_found  # Watch with filter
        python3 watch_events.py --help       # Show usage
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        return

    log_file = "output/pipeline_events.jsonl"
    filter_type = None
    tail = None
    watch_interval = None

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--watch":
            watch_interval = 2
        elif arg.startswith("--watch="):
            try:
                watch_interval = int(arg.split("=")[1])
            except ValueError:
                print(f"❌ Intervalo inválido: {arg}")
                return
        elif arg.startswith("--tail"):
            parts = arg.split("=")
            if len(parts) > 1:
                try:
                    tail = int(parts[1])
                except ValueError:
                    print(f"❌ Valor inválido para tail: {parts[1]}")
                    return
            else:
                tail = 20
        elif not arg.startswith("--"):
            if i == 1 and watch_interval is None:
                filter_type = arg
            elif i == 2 and watch_interval is not None:
                filter_type = arg

    if watch_interval is not None:
        watch_mode(log_file, watch_interval, filter_type=filter_type, tail=tail)
        return

    events = read_events(log_file)

    if not events:
        print(f"❌ Nenhum evento encontrado em {log_file}")
        print(f"   (O pipeline está rodando? Verifique com: python3 main.py ...)")
        return

    draw_header()
    display_events(events, filter_type=filter_type, tail=tail)


if __name__ == "__main__":
    main()
