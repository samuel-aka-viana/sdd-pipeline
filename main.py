import sys
import faulthandler
import traceback
from pathlib import Path
from dotenv import load_dotenv

faulthandler.enable()
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from sdd.graph.runner import run_pipeline as graph_run_pipeline
from memory.memory_store import MemoryStore
from cli.prompts import FOCOS_DISPONIVEIS, prompt_list, prompt_menu_choice

load_dotenv()
console = Console()
MENU_INDEX_START = 1

SECOES_PADRAO = [
    "tldr", "o_que_e", "requisitos", "instalacao",
    "configuracao", "exemplo_pratico", "armadilhas",
    "otimizacoes", "conclusao", "referencias",
]


def parse_main_flags(args: list[str]) -> dict:
    refresh_search = "--refresh-search" in args
    return {"refresh_search": refresh_search}


def perguntar_foco() -> str:
    return prompt_menu_choice(
        console,
        FOCOS_DISPONIVEIS,
        "Foco da pesquisa",
        default="comparação geral",
    )


def perguntar_questoes() -> list[str]:
    return prompt_list(
        console,
        [
            "[dim]Digite perguntas que o artigo DEVE responder.",
            "[dim]Seja específico — o modelo vai usar isso diretamente.",
            "[dim]Enter vazio para terminar.\n",
            "[dim]Exemplos:[/dim]",
            "[dim]  → como configurar modo rootless?[/dim]",
            "[dim]  → docker-compose funciona sem mudanças?[/dim]",
            "[dim]  → qual tem menor uso de RAM em idle?[/dim]\n",
        ],
        "Pergunta",
    )


def coletar_validacoes() -> list[str]:
    return prompt_list(
        console,
        [
            "[dim]Digite critérios que o artigo DEVE conter.",
            "[dim]Enter vazio para terminar.\n",
        ],
        "Critério",
    )


def perguntar_pesquisa_existente() -> str | None:
    """Ask if user wants to reuse an existing research file.

    Returns:
        research_content if chosen, None if should run new research
    """
    console.print("\n[dim]Pesquisas históricas:[/dim]")

    # List existing research files from output directory
    output_dir = Path("output")
    research_files = sorted(output_dir.glob("debug_research_*.md"))

    if research_files:
        console.print("[dim]Arquivos de pesquisa disponíveis:[/dim]")
        console.print("  [cyan]0.[/cyan] Executar nova pesquisa (padrão)")
        for menu_index, research_file in enumerate(research_files, MENU_INDEX_START):
            size = research_file.stat().st_size
            size_kb = size / 1024
            console.print(f"  [cyan]{menu_index}.[/cyan] {research_file.name} ({size_kb:.1f}KB)")

        escolha = Prompt.ask(
            "\n[bold]Usar pesquisa existente?[/bold] [dim](número, ou enter para nova)[/dim]",
            default="0",
        )

        if escolha.strip() == "0" or not escolha.strip():
            return None  # Run new research

        try:
            file_index = int(escolha.strip())
            if 1 <= file_index <= len(research_files):
                research_file = research_files[file_index - MENU_INDEX_START]
                research_content = research_file.read_text(encoding="utf-8")
                console.print(f"\n[green]✓[/green] Pesquisa carregada de {research_file.name} ({len(research_content)} chars)")
                return research_content
        except (ValueError, IndexError):
            pass  # Fall through to run new research

    return None  # Default: run new research


def perguntar_urls() -> tuple[list[str] | None, bool]:
    """Ask if user wants to reuse existing URLs or search new ones.

    Supports multiple file selection (comma-separated indices).

    Returns:
        (urls, skip_search) where:
        - urls: List of URLs if chosen, None if should search
        - skip_search: True if should skip web search
    """
    console.print("\n[dim]URLs para scraping:[/dim]")

    # Find existing URL files
    output_dir = Path("output")
    url_files = sorted(output_dir.glob("urls_*.txt"))

    if url_files:
        console.print("[dim]Arquivos de URLs disponíveis:[/dim]")
        console.print("  [cyan]0.[/cyan] Buscar novos URLs (padrão)")
        for menu_index, url_file in enumerate(url_files, MENU_INDEX_START):
            file_size = url_file.stat().st_size
            num_urls = len(url_file.read_text().strip().split('\n'))
            console.print(f"  [cyan]{menu_index}.[/cyan] {url_file.name} ({num_urls} URLs, {file_size} bytes)")

        escolha = Prompt.ask(
            "\n[bold]Usar URLs existentes?[/bold] [dim](números separados por vírgula, ou enter para buscar novos)[/dim]",
            default="0",
        )

        if escolha.strip() == "0" or not escolha.strip():
            return None, False  # Search new URLs

        # Parse multiple file indices (comma-separated)
        all_urls = []
        selected_files = []

        try:
            indices = [int(idx.strip()) for idx in escolha.split(",")]
            for file_index in indices:
                if 1 <= file_index <= len(url_files):
                    selected_file = url_files[file_index - MENU_INDEX_START]
                    file_urls = [url.strip() for url in selected_file.read_text().strip().split('\n') if url.strip()]
                    all_urls.extend(file_urls)
                    selected_files.append(selected_file.name)

            if all_urls:
                files_str = ", ".join(selected_files)
                console.print(f"\n[green]✓[/green] Carregados {len(all_urls)} URLs de {files_str}")
                return all_urls, True  # Skip search
        except (ValueError, IndexError):
            pass  # Fall through to search new URLs

    return None, False  # Default: search new URLs


def exibir_resumo(ferramentas, contexto, foco, questoes, validacoes):
    resumo_table = Table(show_header=False, box=None, padding=(0, 2))
    resumo_table.add_column(style="dim", width=16)
    resumo_table.add_column(style="white")

    resumo_table.add_row("Ferramentas", f"[yellow]{ferramentas}[/yellow]")
    resumo_table.add_row("Contexto",    f"[yellow]{contexto}[/yellow]")
    resumo_table.add_row("Foco",        f"[cyan]{foco}[/cyan]")
    resumo_table.add_row(
        "O artigo deve\nresponder",
        "\n".join(f"→ {pergunta}" for pergunta in questoes) if questoes else "[dim]sem perguntas adicionais[/dim]",
    )
    resumo_table.add_row(
        "Validações",
        "\n".join(f"☐ {validacao}" for validacao in validacoes) if validacoes else "[dim]nenhuma[/dim]",
    )

    console.print()
    console.print(Panel(resumo_table, title="[bold cyan]Resumo[/bold cyan]", border_style="cyan"))
    console.print()


def checklist_pos_execucao(validacoes: list[str], output_path: str):
    if not validacoes:
        return

    console.print(Panel.fit(
        "[bold white]Checklist de validação manual[/bold white]",
        border_style="yellow",
    ))
    console.print(f"[dim]Artigo: {output_path}[/dim]\n")

    aprovados = 0
    for validacao in validacoes:
        ok = Confirm.ask(f"  [white]{validacao}[/white]")
        if ok:
            aprovados += 1
            console.print("  [green]✓[/green]\n")
        else:
            console.print("  [red]✗[/red]\n")

    total = len(validacoes)
    cor = "green" if aprovados == total else "yellow" if aprovados > 0 else "red"
    console.print(f"[{cor}]Resultado: {aprovados}/{total} critérios atendidos[/{cor}]\n")


def main():
    cli_flags = parse_main_flags(sys.argv[1:])

    console.print()
    console.print(Panel.fit(
        "[bold cyan]SDD Tech Writer[/bold cyan]\n"
        "[dim]Geração de artigos técnicos com LLM configurável[/dim]",
        border_style="cyan",
    ))
    console.print()

    try:
        ferramentas = Prompt.ask("[bold]Ferramentas[/bold] [dim](ex: podman e docker)[/dim]")
        contexto    = Prompt.ask("[bold]Contexto[/bold]    [dim](ex: ambiente de dev local no Linux)[/dim]")
        foco        = perguntar_foco()
        questoes    = perguntar_questoes()
        validacoes  = coletar_validacoes()
        urls, skip_search = perguntar_urls()
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelado.[/dim]")
        sys.exit(0)

    exibir_resumo(ferramentas, contexto, foco, questoes, validacoes)

    if not Confirm.ask("[bold]Iniciar pipeline?[/bold]", default=True):
        console.print("[dim]Cancelado.[/dim]")
        sys.exit(0)

    if cli_flags["refresh_search"]:
        console.print("[yellow]Modo refresh-search ativo: ignorando cache de busca nesta execução.[/yellow]")

    # Ask if user wants to reuse existing research
    existing_research = None
    try:
        existing_research = perguntar_pesquisa_existente()
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelado.[/dim]")
        sys.exit(0)

    try:
        # Initialize memory store
        memory = MemoryStore()
        memory.set("ferramentas", ferramentas)
        memory.set("contexto", contexto)
        memory.set("foco", foco)
        memory.set("questoes", questoes)

        # Build pipeline inputs
        pipeline_inputs = {
            "ferramentas": ferramentas,
            "contexto": contexto,
            "foco": foco,
            "questoes": questoes,
            "urls": urls,
            "skip_search": skip_search,
            "existing_research": existing_research,
            "refresh_search": cli_flags["refresh_search"],
            "memory": memory,
        }

        # Run the pipeline
        final_state = graph_run_pipeline(pipeline_inputs)
        output_path = Path("output") / "article.md"
        if "article" in final_state:
            output_path.parent.mkdir(exist_ok=True)
            output_path.write_text(final_state["article"], encoding="utf-8")

        console.print(f"\n[green]✓[/green] Artigo finalizado: {output_path}")
    except BaseException as error:
        if isinstance(error, KeyboardInterrupt):
            console.print("\n[dim]Cancelado.[/dim]")
            sys.exit(0)
        console.print()
        console.print(Panel.fit(
            f"[bold red]Falha: {type(error).__name__}[/bold red]\n"
            f"[white]{error}[/white]\n\n"
            f"[dim]{traceback.format_exc()}[/dim]\n"
            f"[dim]Dica: configure fallback em .env (cloud/local) para evitar rate-limit.[/dim]",
            border_style="red",
        ))
        sys.exit(1)

    checklist_pos_execucao(validacoes, str(output_path))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException as error:
        console.print()
        console.print(Panel.fit(
            f"[bold red]Erro não tratado: {type(error).__name__}[/bold red]\n"
            f"[white]{error}[/white]\n\n"
            f"[dim]{traceback.format_exc()}[/dim]",
            border_style="red",
        ))
        sys.exit(1)
