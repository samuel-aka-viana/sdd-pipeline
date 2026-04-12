"""
Monitora eventos em TEMPO REAL enquanto o pipeline roda.
Semelhante a 'tail -f' para o arquivo JSONL.

Uso:
  python3 tail_events.py              # Mostra todos eventos conforme aparecem
  python3 tail_events.py url_found    # Mostra apenas URLs
  python3 tail_events.py --detailed   # Mostra detalhes completos

Pressione Ctrl+C para sair.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path


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


def format_event(event: dict, detailed: bool = False) -> str:
    """Format event dict into human-readable output line with emoji indicators.
    
    Handles different event types: url_found, search_query, section_start, task events, etc.
    
    Args:
        event: Event dict from JSONL with "type", "timestamp", and type-specific fields
        detailed: If True, multi-line output with extra fields (e.g., page title on new line)
        
    Returns:
        Formatted string ready for console output
        
    Example:
        event = {"type": "url_found", "url": "https://example.com", 
                 "status": "ok", "elapsed_seconds": 1.2, "timestamp": "2026-04-12T12:34:56.123"}
        print(format_event(event))
        # Output: "[12:34:56] ✓ https://example.com (1.2s)"
    """
    time_str = format_time(event.get("timestamp", ""))
    event_type = event.get("type", "unknown")

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

        if detailed:
            title_str = f"\n           Title: {title}" if title else ""
            return f"[{time_str}] {status_emoji} URL\n           {url}{elapsed_str}{title_str}"
        else:
            title_str = f" — {title[:40]}" if title else ""
            return f"[{time_str}] {status_emoji} {url}{title_str}{elapsed_str}"

    elif event_type == "search_query":
        query = event.get("query", "?")
        return f"[{time_str}] 🔍 Search: {query}"

    elif event_type == "section_start":
        number = event.get("number", "?")
        total = event.get("total", "?")
        title = event.get("title", "?")
        return f"\n[{time_str}] ━━━ [{number}/{total}] {title} ━━━"

    elif event_type == "task_completed":
        desc = event.get("description", "?")
        elapsed = event.get("elapsed_seconds", 0)
        return f"[{time_str}] ✓ {desc} ({elapsed:.1f}s)"

    elif event_type == "task_failed":
        desc = event.get("description", "?")
        error = event.get("error", "?")
        return f"[{time_str}] ✗ {desc}\n           Error: {error}"

    elif event_type == "search_done":
        tool = event.get("tool", "?")
        n_results = event.get("n_results", "?")
        n_queries = event.get("n_queries", "?")
        return f"[{time_str}] ✓ {tool}: {n_results} results / {n_queries} queries"

    elif event_type == "pipeline_start":
        ferramentas = event.get("ferramentas", "?")
        contexto = event.get("contexto", "?")
        return f"[{time_str}] 🚀 Pipeline START\n           Tools: {ferramentas}\n           Context: {contexto}"

    else:
        return f"[{time_str}] {event_type}"


def tail_file(log_file: str, filter_type: str = None, detailed: bool = False):
    """Monitor JSONL log file continuously with real-time streaming (like tail -f).
    
    Tracks file position and reads only new lines as they're appended. 
    Polls every 0.2s for new events.
    
    Args:
        log_file: Path to JSONL file to monitor
        filter_type: Optional event type filter (e.g., "url_found"). None shows all.
        detailed: If True, shows expanded multi-line output for each event
        
    Example:
        # Monitor all events in real-time
        tail_file("output/pipeline_events.jsonl")
        
        # Monitor only URL events
        tail_file("output/pipeline_events.jsonl", filter_type="url_found")
    """
    path = Path(log_file)

    print(f"👀 Monitoring: {path}")
    print(f"   (Pressione Ctrl+C para sair)\n")

    if filter_type:
        print(f"🔍 Filtrando por: {filter_type}\n")

    last_pos = 0

    while True:
        try:
            if not path.exists():
                time.sleep(0.5)
                continue

            with open(path, 'r') as f:
                f.seek(last_pos)

                for line in f:
                    try:
                        event = json.loads(line)

                        if filter_type and event.get("type") != filter_type:
                            continue

                        output = format_event(event, detailed=detailed)
                        print(output)

                    except json.JSONDecodeError:
                        pass

                last_pos = f.tell()

            time.sleep(0.2)

        except KeyboardInterrupt:
            print("\n\n👋 Monitoramento finalizado")
            break
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(1)


def main():
    """Entry point for tail_events.py script.
    
    Parses command-line arguments and starts monitoring.
    
    Usage:
        python3 tail_events.py              # All events
        python3 tail_events.py url_found    # Filter by event type
        python3 tail_events.py --detailed   # Expanded output
        python3 tail_events.py --help       # Show usage
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        return

    log_file = "output/pipeline_events.jsonl"
    filter_type = None
    detailed = False

    for arg in sys.argv[1:]:
        if arg == "--detailed":
            detailed = True
        elif not arg.startswith("--"):
            filter_type = arg

    tail_file(log_file, filter_type=filter_type, detailed=detailed)


if __name__ == "__main__":
    main()
