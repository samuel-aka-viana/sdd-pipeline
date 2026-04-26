#!/usr/bin/env python3
"""Repopulate Chroma from historical research files (debug_research_*.md)."""

import sys
from pathlib import Path
from memory.research_chroma import ResearchChroma
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

console = Console()


def extract_tool_from_filename(filename: str) -> str:
    """Extract tool name from debug_research_*.md filename.

    Examples:
    - debug_research_docker.md → docker
    - debug_research_spark_structured_streaming.md → spark_structured_streaming
    """
    return filename.replace("debug_research_", "").replace(".md", "")


def repopulate_from_files():
    """Load research files and index them in Chroma."""
    console.print("\n[bold cyan]🔄 Repopulando Chroma[/bold cyan]")
    console.print("[dim]Carregando arquivos históricos de pesquisa...[/dim]\n")

    output_dir = Path("output")
    research_files = sorted(output_dir.glob("debug_research_*.md"))

    if not research_files:
        console.print("[yellow]⚠ Nenhum arquivo debug_research_*.md encontrado em output/[/yellow]")
        return False

    chroma = ResearchChroma()
    stats = {
        "files_processed": 0,
        "tools_indexed": set(),
        "total_chars": 0,
        "chunks_created": 0,
        "errors": []
    }

    console.print(f"[cyan]Encontrados {len(research_files)} arquivo(s):[/cyan]\n")
    for f in research_files:
        tool = extract_tool_from_filename(f.name)
        size_kb = f.stat().st_size / 1024
        console.print(f"  • {f.name:<50} ({tool:<30}) {size_kb:>6.1f}KB")

    console.print()

    if not console.input("[bold]Prosseguir com repopulação?[/bold] [dim](s/n)[/dim] ").lower().startswith('s'):
        console.print("[dim]Cancelado.[/dim]")
        return False

    # Process each file
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:

        for research_file in research_files:
            tool = extract_tool_from_filename(research_file.name)
            task_id = progress.add_task(f"Indexando {tool}...", total=None)

            try:
                # Read file
                content = research_file.read_text(encoding="utf-8")
                stats["total_chars"] += len(content)

                # Extract title from first heading or use tool name
                lines = content.split('\n')
                title = tool.replace('_', ' ').title()
                for line in lines[:10]:
                    if line.startswith('# '):
                        title = line.replace('# ', '').strip()
                        break

                # Save to Chroma
                # Use a synthetic URL to track source
                url = f"historical://{research_file.name}"

                success = chroma.save_scraped_content(
                    tool=tool,
                    url=url,
                    title=title,
                    content=content,
                    markdown_raw=content,
                    source_quality="historical",  # Mark as historical data
                    scrape_elapsed_seconds=None,
                )

                if success:
                    stats["files_processed"] += 1
                    stats["tools_indexed"].add(tool)

                    # Count chunks created
                    chunks = chroma.chunk_content(content)
                    stats["chunks_created"] += len(chunks)
                else:
                    stats["errors"].append(f"{tool}: falha ao salvar")

                progress.update(task_id, completed=True)

            except Exception as e:
                stats["errors"].append(f"{tool}: {str(e)}")
                progress.update(task_id, completed=True)

    # Report
    console.print("\n[bold cyan]📊 Resultado[/bold cyan]\n")

    result_table = Table(show_header=False, box=None)
    result_table.add_column("Métrica", style="cyan", width=30)
    result_table.add_column("Valor", style="white")

    result_table.add_row("Arquivos processados", str(stats["files_processed"]))
    result_table.add_row("Ferramentas indexadas", ", ".join(sorted(stats["tools_indexed"])))
    result_table.add_row("Total de caracteres", f"{stats['total_chars']:,}")
    result_table.add_row("Chunks criados", str(stats["chunks_created"]))
    result_table.add_row("Erros", str(len(stats["errors"])))

    console.print(result_table)

    if stats["errors"]:
        console.print("\n[yellow]⚠ Erros encontrados:[/yellow]")
        for error in stats["errors"]:
            console.print(f"  • {error}")

    # Verification
    console.print("\n[bold cyan]✅ Verificando Chroma[/bold cyan]\n")

    all_data = chroma.collection.get(include=["metadatas"])
    metadatas = all_data.get("metadatas", [])

    tools_in_chroma = set(m.get("tool") for m in metadatas)
    chunks_in_chroma = len(metadatas)

    verify_table = Table(show_header=False, box=None)
    verify_table.add_column("", style="dim", width=25)
    verify_table.add_column("", style="white")

    verify_table.add_row("Chroma total chunks", str(chunks_in_chroma))
    verify_table.add_row("Ferramentas no Chroma", ", ".join(sorted(tools_in_chroma)))

    console.print(verify_table)

    if stats["files_processed"] > 0 and len(stats["errors"]) == 0:
        console.print("\n[green]✓ Repopulação bem-sucedida![/green]")
        console.print(f"[dim]Chroma agora tem {chunks_in_chroma} chunks de {len(tools_in_chroma)} ferramentas[/dim]")
        return True
    elif len(stats["errors"]) > 0:
        console.print("\n[yellow]⚠ Alguns erros ocorreram durante repopulação[/yellow]")
        return False
    else:
        console.print("\n[yellow]⚠ Nenhum arquivo foi processado[/yellow]")
        return False


def show_before_after():
    """Show what's in Chroma before and after."""
    chroma = ResearchChroma()
    all_data = chroma.collection.get(include=["metadatas"])
    metadatas = all_data.get("metadatas", [])

    if not metadatas:
        console.print("[dim]Chroma está vazio[/dim]")
        return

    tools_count = {}
    for metadata in metadatas:
        tool = metadata.get("tool", "unknown")
        tools_count[tool] = tools_count.get(tool, 0) + 1

    table = Table(title="Dados Atuais no Chroma")
    table.add_column("Ferramenta", style="cyan")
    table.add_column("Chunks", style="white")

    for tool in sorted(tools_count.keys()):
        table.add_row(tool, str(tools_count[tool]))

    console.print(Panel(table, border_style="dim"))


def main():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Chroma Repopulator[/bold cyan]\n"
        "[dim]Carrega arquivos históricos de pesquisa em Chroma[/dim]",
        border_style="cyan"
    ))

    show_before_after()

    success = repopulate_from_files()

    if success:
        console.print("\n[bold]Próximos passos:[/bold]")
        console.print("  1. python -m utils.test_chroma_queries")
        console.print("  2. Escolha [1] para ver estatísticas")
        console.print("  3. Escolha [3] para fazer buscas")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelado.[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Erro:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
