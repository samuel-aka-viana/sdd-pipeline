import gzip
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse


def save_context_debug(
    tool: str,
    context: str,
    last_scrape_stats: dict,
    max_scrapes_per_tool: int,
    max_chars_per_scrape: int,
    logger,
) -> str:
    """Persist raw research context to simplify scrape/fallback diagnosis."""
    try:
        Path("output").mkdir(exist_ok=True)
        tool_safe = (tool or "unknown").lower().replace(" ", "_")
        path = Path(f"output/debug_context_{tool_safe}.md")
        header = (
            f"# CONTEXTO BRUTO - {tool}\n\n"
            f"- stats: {json.dumps(last_scrape_stats, ensure_ascii=False)}\n"
            f"- max_scrapes_per_tool: {max_scrapes_per_tool}\n"
            f"- max_chars_per_scrape: {max_chars_per_scrape}\n\n"
        )
        path.write_text(header + context, encoding="utf-8")
        return str(path)
    except Exception as exc:
        logger.debug(f"Failed to save raw context debug for {tool}: {exc}")
        return ""


def save_html_debug(
    tool: str,
    url: str,
    html: str,
    status: str,
    source: str,
    snippet: str,
    html_debug_enabled: bool,
    memory,
    logger,
) -> str:
    """Persist per-URL debug artifact (raw HTML when available)."""
    if not html_debug_enabled:
        return ""
    try:
        tool_safe = (tool or "unknown").lower().replace(" ", "_")
        domain = (urlparse(url).netloc or "unknown").lower()
        slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", domain)[:80] or "unknown"
        url_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        debug_dir = Path(f"output/debug_html_{tool_safe}")
        debug_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{slug}_{status}_{url_hash}.html.gz"
        path = debug_dir / filename
        with gzip.open(path, "wt", encoding="utf-8") as file:
            file.write(f"<!-- URL: {url} -->\n")
            file.write(f"<!-- status: {status} source: {source} -->\n")
            if html:
                file.write("<!-- html_present: true -->\n")
                file.write(html)
            else:
                file.write("<!-- html_present: false -->\n")
                if snippet:
                    file.write("\n<!-- snippet_fallback -->\n")
                    file.write(snippet)
                else:
                    file.write("\n<!-- no_html_and_no_snippet -->\n")
        memory.log_event("html_debug_saved", {
            "tool": tool,
            "url": url[:120],
            "status": status,
            "source": source,
            "path": str(path),
            "html_chars": len(html),
            "snippet_chars": len(snippet or ""),
        })
        return str(path)
    except Exception as exc:
        logger.debug(f"Failed to save HTML debug for {url[:80]}: {exc}")
        return ""
