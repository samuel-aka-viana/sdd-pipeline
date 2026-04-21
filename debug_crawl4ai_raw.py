#!/usr/bin/env python3
"""Debug script to see RAW markdown extracted by Crawl4AI."""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
import asyncio

console = Console()


async def extract_and_show(url: str):
    """Extract from URL and show raw markdown."""
    try:
        from tools.scraper_crawl4ai import ScraperCrawl4AI
    except ImportError:
        console.print("[red]✗ Crawl4AI não está instalado[/red]")
        console.print("[dim]Install: pip install crawl4ai[/dim]")
        return False

    console.print(f"\n[bold cyan]🔍 Extracting from:[/bold cyan] {url}\n")

    scraper = ScraperCrawl4AI()
    result = await scraper.extract_text_async(url)

    if not result or result.get("status") != "ok":
        console.print(f"[red]✗ Extraction failed:[/red] {result}")
        return False

    # Show metadata
    console.print("[bold cyan]📊 Metadata:[/bold cyan]")
    metadata_panel = Panel(
        f"""Status: {result.get('status')}
Title: {result.get('title', 'N/A')}
URL: {result.get('url', 'N/A')}
Chars (markdown): {len(result.get('text', ''))}
Chars (html): {len(result.get('html', ''))}
Source: {result.get('source', 'N/A')}
Elapsed: {result.get('elapsed', 'N/A')}s""",
        border_style="dim"
    )
    console.print(metadata_panel)

    # Show markdown
    markdown = result.get("text", "")
    if not markdown:
        console.print("[yellow]⚠ No markdown extracted[/yellow]")
        return False

    console.print(f"\n[bold cyan]📝 Markdown Extraído ({len(markdown)} chars):[/bold cyan]\n")

    # Show first 3000 chars in syntax-highlighted panel
    preview = markdown[:3000]
    syntax = Syntax(preview, "markdown", theme="monokai", line_numbers=True)
    console.print(syntax)

    if len(markdown) > 3000:
        console.print(f"\n[dim]... ({len(markdown) - 3000} mais chars)[/dim]")

    # Save full markdown to file
    output_file = Path(f"output/debug_crawl4ai_{url.split('/')[-1][:20]}.md")
    output_file.write_text(markdown, encoding="utf-8")
    console.print(f"\n[green]✓[/green] Markdown completo salvo em: [cyan]{output_file}[/cyan]")

    # Show statistics
    console.print(f"\n[bold cyan]📈 Estatísticas:[/bold cyan]")
    lines = markdown.split("\n")
    headers = len([l for l in lines if l.startswith("#")])
    code_blocks = markdown.count("```")
    links = markdown.count("[")

    stats_panel = Panel(
        f"""Total de linhas: {len(lines)}
Headers (#): {headers}
Code blocks: {code_blocks // 2}
Links: {links}
Parágrafos: {len([l for l in lines if l.strip() and not l.startswith('#')])}""",
        border_style="dim"
    )
    console.print(stats_panel)

    return True


def main():
    if len(sys.argv) < 2:
        console.print("\n[bold]Uso:[/bold]")
        console.print("  python debug_crawl4ai_raw.py <URL>\n")
        console.print("[dim]Exemplos:[/dim]")
        console.print("  python debug_crawl4ai_raw.py https://docs.docker.com/engine/")
        console.print("  python debug_crawl4ai_raw.py https://github.com/moby/moby\n")
        sys.exit(1)

    url = sys.argv[1]

    console.print()
    console.print(Panel.fit(
        "[bold cyan]Crawl4AI Raw Debug[/bold cyan]\n"
        "[dim]Visualiza markdown extraído sem filtros[/dim]",
        border_style="cyan"
    ))

    try:
        success = asyncio.run(extract_and_show(url))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelado.[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Erro:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
