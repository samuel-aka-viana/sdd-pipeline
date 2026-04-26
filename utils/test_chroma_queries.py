#!/usr/bin/env python3
"""Interactive Chroma query tester for research data verification."""

import sys
from memory.research_chroma import ResearchChroma
from rich.console import Console
from rich.table import Table

console = Console()


def print_stats():
    """Show Chroma database statistics."""
    console.print("\n[bold cyan]📊 Estatísticas do Chroma[/bold cyan]")
    chroma = ResearchChroma()

    # Get all data
    all_data = chroma.collection.get(include=["metadatas"])
    metadatas = all_data.get("metadatas", [])

    if not metadatas:
        console.print("[yellow]⚠ Chroma está vazio (nenhuma pesquisa salva ainda)[/yellow]")
        return

    # Count by tool
    tools_count = {}
    urls_count = {}

    for metadata in metadatas:
        tool = metadata.get("tool", "unknown")
        url = metadata.get("url", "unknown")

        tools_count[tool] = tools_count.get(tool, 0) + 1
        if url not in urls_count.get(tool, []):
            if tool not in urls_count:
                urls_count[tool] = []
            urls_count[tool].append(url)

    # Display
    stats_table = Table(title="Dados por Ferramenta", border_style="dim")
    stats_table.add_column("Ferramenta", style="cyan")
    stats_table.add_column("Chunks", style="white")
    stats_table.add_column("URLs Únicas", style="green")

    for tool in sorted(tools_count.keys()):
        chunks = tools_count[tool]
        urls = len(urls_count.get(tool, []))
        stats_table.add_row(tool, str(chunks), str(urls))

    console.print(stats_table)
    console.print(f"\n[dim]Total: {len(metadatas)} chunks de {len(tools_count)} ferramentas[/dim]")


def test_tool_isolation():
    """Verify that tool-based filtering works correctly."""
    console.print("\n[bold cyan]🔒 Teste de Isolamento por Ferramenta[/bold cyan]")
    chroma = ResearchChroma()

    # Get all tools
    all_data = chroma.collection.get(include=["metadatas"])
    metadatas = all_data.get("metadatas", [])

    if not metadatas:
        console.print("[yellow]⚠ Chroma está vazio[/yellow]")
        return

    tools = set(m.get("tool") for m in metadatas)

    for tool in sorted(tools):
        # Query WITH tool filter
        results_filtered = chroma.query_similar(
            query_text=f"{tool} overview",
            tool=tool,
            k=3
        )

        # Query WITHOUT tool filter
        results_all = chroma.query_similar(
            query_text=f"{tool} overview",
            tool=None,
            k=3
        )

        # Verify all filtered results have correct tool
        for result in results_filtered:
            if result.get("tool") != tool:
                console.print(f"[red]✗ ERRO: Resultado filtrado tem tool errado![/red]")
                console.print(f"  Esperado: {tool}, Recebido: {result.get('tool')}")
                return

        console.print(f"  [green]✓[/green] {tool}: {len(results_filtered)} resultados (filtrado) vs {len(results_all)} (global)")

    console.print("\n[green]✓ Isolamento por ferramenta: OK[/green]")


def search_demo():
    """Interactive search demo."""
    console.print("\n[bold cyan]🔍 Busca Semântica Interativa[/bold cyan]")
    chroma = ResearchChroma()

    # Get available tools
    all_data = chroma.collection.get(include=["metadatas"])
    metadatas = all_data.get("metadatas", [])

    if not metadatas:
        console.print("[yellow]⚠ Chroma está vazio[/yellow]")
        return

    tools = sorted(set(m.get("tool") for m in metadatas))

    console.print("\n[dim]Ferramentas disponíveis:[/dim]")
    for i, tool in enumerate(tools, 1):
        console.print(f"  {i}. {tool}")

    try:
        tool_idx = int(console.input("\n[bold]Escolha ferramenta (número):[/bold] ")) - 1
        if 0 <= tool_idx < len(tools):
            selected_tool = tools[tool_idx]
        else:
            console.print("[red]Índice inválido[/red]")
            return
    except ValueError:
        console.print("[red]Número inválido[/red]")
        return

    query = console.input(f"\n[bold]Query para {selected_tool}:[/bold] ").strip()
    if not query:
        return

    k = 5
    try:
        k_input = console.input(f"[dim]Quantos resultados? (padrão {k}):[/dim] ").strip()
        if k_input:
            k = int(k_input)
    except ValueError:
        pass

    # Query with tool filter
    console.print(f"\n[dim]Buscando em {selected_tool}...[/dim]")
    results = chroma.query_similar(
        query_text=query,
        tool=selected_tool,
        k=k
    )

    if not results:
        console.print("[yellow]Nenhum resultado encontrado[/yellow]")
        return

    # Display results
    for i, result in enumerate(results, 1):
        console.print(f"\n[bold]{i}. Similaridade: {result['similarity']:.3f}[/bold]")
        console.print(f"   [cyan]URL:[/cyan] {result['url'][:70]}...")
        console.print(f"   [cyan]Título:[/cyan] {result['title'][:60]}")
        console.print(f"   [dim]Chunk {result['chunk_index']}/{result['chunk_count']}[/dim]")

        text_preview = result['text'][:200]
        console.print(f"   [dim]Preview:[/dim] {text_preview}...")


def cross_tool_search():
    """Test cross-tool knowledge transfer."""
    console.print("\n[bold cyan]🔗 Busca Cross-Tool (Conhecimento Transferível)[/bold cyan]")
    chroma = ResearchChroma()

    # Get available tools
    all_data = chroma.collection.get(include=["metadatas"])
    metadatas = all_data.get("metadatas", [])

    if not metadatas:
        console.print("[yellow]⚠ Chroma está vazio[/yellow]")
        return

    tools = sorted(set(m.get("tool") for m in metadatas))

    if len(tools) < 2:
        console.print(f"[yellow]⚠ Precisa de pelo menos 2 ferramentas (tem {len(tools)})[/yellow]")
        return

    console.print("\n[dim]Ferramentas disponíveis:[/dim]")
    for i, tool in enumerate(tools, 1):
        console.print(f"  {i}. {tool}")

    try:
        exclude_idx = int(console.input("\n[bold]Ferramentas a EXCLUIR (número):[/bold] ")) - 1
        if 0 <= exclude_idx < len(tools):
            exclude_tool = tools[exclude_idx]
        else:
            console.print("[red]Índice inválido[/red]")
            return
    except ValueError:
        console.print("[red]Número inválido[/red]")
        return

    query = console.input(f"\n[bold]Query (sem {exclude_tool}):[/bold] ").strip()
    if not query:
        return

    console.print(f"\n[dim]Buscando em outras ferramentas (excluindo {exclude_tool})...[/dim]")
    results = chroma.cross_tool_search(
        query_text=query,
        exclude_tool=exclude_tool,
        k=5
    )

    if not results:
        console.print("[yellow]Nenhum resultado encontrado[/yellow]")
        return

    console.print(f"[green]✓[/green] {len(results)} resultado(s):\n")
    for i, result in enumerate(results, 1):
        console.print(f"{i}. [{result['tool'].upper()}] {result['title'][:50]}")
        console.print(f"   Sim: {result['similarity']:.3f} | {result['url'][:60]}...")


def verify_data_integrity():
    """Check for data corruption or inconsistencies."""
    console.print("\n[bold cyan]✅ Verificação de Integridade[/bold cyan]")
    chroma = ResearchChroma()

    all_data = chroma.collection.get(include=["metadatas", "documents"])
    metadatas = all_data.get("metadatas", [])
    documents = all_data.get("documents", [])

    if not metadatas:
        console.print("[yellow]Chroma está vazio[/yellow]")
        return

    issues = []

    # Check 1: Metadata consistency
    for i, metadata in enumerate(metadatas):
        required_fields = ["tool", "url", "title", "chunk_index", "chunk_count"]
        for field in required_fields:
            if field not in metadata:
                issues.append(f"Chunk {i}: falta campo '{field}'")

    # Check 2: Chunk count consistency
    tool_chunks = {}
    for metadata in metadatas:
        tool = metadata.get("tool")
        url = metadata.get("url")
        key = f"{tool}#{url}"
        tool_chunks[key] = tool_chunks.get(key, 0) + 1

    for (tool, url), count in list(tool_chunks.items())[:5]:
        # Get metadata for this URL
        url_metadata = [m for m in metadatas if m.get("url") == url and m.get("tool") == tool.split("#")[0]]
        if url_metadata:
            expected_count = int(url_metadata[0].get("chunk_count", 0))
            if count != expected_count:
                issues.append(f"{tool}#{url}: tem {count} chunks, esperado {expected_count}")

    # Check 3: Document consistency
    if len(documents) != len(metadatas):
        issues.append(f"Documentos ({len(documents)}) ≠ Metadados ({len(metadatas)})")

    # Report
    if issues:
        console.print("[red]⚠ Problemas encontrados:[/red]")
        for issue in issues[:10]:
            console.print(f"  • {issue}")
        if len(issues) > 10:
            console.print(f"  ... e {len(issues) - 10} mais")
    else:
        console.print("[green]✓ Integridade OK[/green]")
        console.print(f"  • {len(metadatas)} chunks válidos")
        console.print(f"  • {len(set(m.get('tool') for m in metadatas))} ferramentas")
        console.print(f"  • {len(set(m.get('url') for m in metadatas))} URLs únicas")


def show_menu():
    """Display main menu."""
    console.print("\n[bold cyan]Chroma Query Tester[/bold cyan]")
    console.print("[dim]Teste de dados e isolamento de ferramenta[/dim]\n")

    options = [
        ("1", "📊 Estatísticas do Chroma"),
        ("2", "🔒 Teste de isolamento por ferramenta"),
        ("3", "🔍 Busca semântica interativa"),
        ("4", "🔗 Busca cross-tool (conhecimento transferível)"),
        ("5", "✅ Verificação de integridade dos dados"),
        ("0", "Sair"),
    ]

    for key, desc in options:
        console.print(f"  [cyan]{key}[/cyan] {desc}")


def main():
    """Main loop."""
    while True:
        show_menu()
        choice = console.input("\n[bold]Escolha:[/bold] ").strip()

        if choice == "1":
            print_stats()
        elif choice == "2":
            test_tool_isolation()
        elif choice == "3":
            search_demo()
        elif choice == "4":
            cross_tool_search()
        elif choice == "5":
            verify_data_integrity()
        elif choice == "0":
            console.print("[dim]Saindo...[/dim]")
            sys.exit(0)
        else:
            console.print("[red]Opção inválida[/red]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelado.[/dim]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Erro:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
