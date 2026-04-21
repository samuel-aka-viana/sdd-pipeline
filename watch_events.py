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
        source = event.get("source", "")
        scrape_status = event.get("scrape_status", "")

        status_emoji = {
            "ok": "✓",
            "scrape_failed": "⚠",
            "skipped": "⊘"
        }.get(status, "•")

        elapsed_str = f" ({elapsed:.1f}s)" if elapsed else ""
        title_str = f" — {title}" if title else ""
        source_str = f" [src={source}]" if source else ""
        scrape_status_str = f" [status={scrape_status}]" if scrape_status and scrape_status != "ok" else ""

        print(f" {status_emoji} {url}{title_str}{source_str}{scrape_status_str}{elapsed_str}")

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

    elif event_type == "chroma_save":
        tool = event.get("tool", "?")
        chunk_count = event.get("chunk_count", "?")
        content_chars = event.get("content_chars", "?")
        print(f" 💾 {tool} | {chunk_count} chunks ({content_chars} chars)")

    elif event_type == "chroma_query":
        query = event.get("query", "?")
        tool = event.get("tool", "")
        results = event.get("results_count", "?")
        tool_str = f" [{tool}]" if tool else ""
        print(f" 🔍 Chroma{tool_str}: '{query}' → {results} results")

    elif event_type == "weak_search_query":
        tool = event.get("tool", "?")
        query = event.get("query", "?")
        results = event.get("results_count", "?")
        print(f" ⚠️  Weak query: {tool} | '{query}' ({results} results)")

    elif event_type == "reanalyze_urls":
        reason = event.get("reason", "?")
        urls_count = event.get("urls_count", "?")
        elapsed = event.get("elapsed_seconds", None)
        elapsed_str = f" ({elapsed:.1f}s)" if elapsed else ""
        print(f" 🔄 Reanalyze: {reason} | {urls_count} URLs{elapsed_str}")

    elif event_type == "enrichment_via_chroma":
        tool = event.get("tool", "?")
        enrichment_type = event.get("enrichment_type", "?")
        sources = event.get("sources_count", "?")
        elapsed = event.get("elapsed_seconds", None)
        elapsed_str = f" ({elapsed:.1f}s)" if elapsed else ""
        print(f" ⚡ Enrich {enrichment_type}: {tool} | {sources} sources{elapsed_str}")

    elif event_type == "scraped_content_preview":
        tool = event.get("tool", "?")
        url = event.get("url", "?")
        preview = event.get("preview", "")
        total_chars = event.get("total_chars", 0)
        # Show first 100 chars of preview
        preview_short = preview[:100].replace("\n", " ").strip()
        print(f" 📄 [{tool}] {url}")
        print(f"    → '{preview_short}...' ({total_chars} chars)")

    elif event_type == "content_extracted":
        url = event.get("url", "?")
        status = event.get("status", "?")
        preview = event.get("preview", "[vazio]")
        chars = event.get("chars", 0)
        icon = "✓" if status == "ok" and chars > 0 else "⚠"
        print(f" {icon} Extracted: {url[:50]}")
        print(f"    → {preview} ({chars} chars)")

    elif event_type == "content_extraction_failed":
        url = event.get("url", "?")
        error = event.get("error", "unknown")
        elapsed = event.get("elapsed", "?")
        print(f" ✗ FALHOU: {url}")
        print(f"    → Erro: {error} ({elapsed}s)")

    else:
        details = {key: value for key, value in event.items() if key not in ["timestamp", "type"]}
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
    for event_type, count in sorted(counts.items(), key=lambda type_count_pair: type_count_pair[1], reverse=True):
        print(f"  {event_type:20}: {count:3} evento(s)")

    urls_ok = sum(1 for event_item in events if event_item.get("type") == "url_found" and event_item.get("status") == "ok")
    urls_failed = sum(1 for event_item in events if event_item.get("type") == "url_found" and event_item.get("status") == "scrape_failed")
    urls_skipped = sum(1 for event_item in events if event_item.get("type") == "url_found" and event_item.get("status") == "skipped")
    cloudflare_challenges = sum(
        1
        for event_item in events
        if event_item.get("type") == "url_found"
        and event_item.get("scrape_status") == "cloudflare_challenge"
    )
    extracted_via_playwright = sum(
        1
        for event_item in events
        if event_item.get("type") == "url_found"
        and event_item.get("status") == "ok"
        and event_item.get("source") == "playwright"
    )

    print(f"\n🔗 URLs encontradas:")
    print(f"  ✓ OK (extraído): {urls_ok}")
    print(f"  ⚠ Falhado (fallback): {urls_failed}")
    print(f"  ⊘ Pulado: {urls_skipped}")
    print(f"\n🛡️ Telemetria Cloudflare/Browser:")
    print(f"  ☁️ Challenge detectado: {cloudflare_challenges}")
    print(f"  🧭 Extraído via Playwright: {extracted_via_playwright}")

    elapsed_times = []
    for event_item in events:
        if event_item.get("type") == "url_found" and event_item.get("elapsed_seconds"):
            elapsed_times.append(event_item.get("elapsed_seconds"))

    if elapsed_times:
        print(f"\n⏱️  Tempo de scraping:")
        print(f"  Min:  {min(elapsed_times):.2f}s")
        print(f"  Max:  {max(elapsed_times):.2f}s")
        print(f"  Avg:  {sum(elapsed_times) / len(elapsed_times):.2f}s")

    # Chroma stats
    chroma_saves = sum(1 for e in events if e.get("type") == "chroma_save")
    chroma_queries = sum(1 for e in events if e.get("type") == "chroma_query")
    weak_queries = sum(1 for e in events if e.get("type") == "weak_search_query")
    enrichments = sum(1 for e in events if e.get("type") in ["enrichment_via_chroma", "reanalyze_urls"])

    if chroma_saves or chroma_queries or weak_queries or enrichments:
        print(f"\n🗄️  Chroma Vector Database:")
        if chroma_saves:
            print(f"  💾 Saves: {chroma_saves}")
        if chroma_queries:
            print(f"  🔍 Queries: {chroma_queries}")
        if weak_queries:
            print(f"  ⚠️  Weak searches: {weak_queries}")
        if enrichments:
            print(f"  ⚡ Smart enrichments: {enrichments}")

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
        filtered_events = [
            event_item for event_item in filtered_events
            if event_item.get("type") == filter_type
        ]
    
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


def parse_watch_interval(arg: str):
    if arg == "--watch":
        return 2
    if not arg.startswith("--watch="):
        return None
    try:
        return int(arg.split("=")[1])
    except ValueError:
        print(f"❌ Intervalo inválido: {arg}")
        return "invalid"


def parse_tail_value(arg: str):
    if not arg.startswith("--tail"):
        return None
    parts = arg.split("=")
    if len(parts) == 1:
        return 20
    try:
        return int(parts[1])
    except ValueError:
        print(f"❌ Valor inválido para tail: {parts[1]}")
        return "invalid"


def parse_cli_args(args: list[str]):
    if args and args[0] == "--help":
        return {"show_help": True}

    parsed = {
        "log_file": "output/pipeline_events.jsonl",
        "filter_type": None,
        "tail": None,
        "watch_interval": None,
        "show_help": False,
    }
    positional_args = []

    for arg in args:
        watch_interval = parse_watch_interval(arg)
        if watch_interval == "invalid":
            return None
        if watch_interval is not None:
            parsed["watch_interval"] = watch_interval
            continue

        tail_value = parse_tail_value(arg)
        if tail_value == "invalid":
            return None
        if tail_value is not None:
            parsed["tail"] = tail_value
            continue

        if not arg.startswith("--"):
            positional_args.append(arg)

    if positional_args:
        if parsed["watch_interval"] is None:
            parsed["filter_type"] = positional_args[0]
        elif len(positional_args) > 1:
            parsed["filter_type"] = positional_args[1]
        else:
            parsed["filter_type"] = positional_args[0]
    return parsed


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
    parsed_args = parse_cli_args(sys.argv[1:])
    if parsed_args is None:
        return

    if parsed_args["show_help"]:
        print(__doc__)
        return

    if parsed_args["watch_interval"] is not None:
        watch_mode(
            parsed_args["log_file"],
            parsed_args["watch_interval"],
            filter_type=parsed_args["filter_type"],
            tail=parsed_args["tail"],
        )
        return

    events = read_events(parsed_args["log_file"])

    if not events:
        print(f"❌ Nenhum evento encontrado em {parsed_args['log_file']}")
        print(f"   (O pipeline está rodando? Verifique com: python3 main.py ...)")
        return

    draw_header()
    display_events(
        events,
        filter_type=parsed_args["filter_type"],
        tail=parsed_args["tail"],
    )


if __name__ == "__main__":
    main()
