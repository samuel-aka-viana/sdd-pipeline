import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from pipeline import SDDPipeline

load_dotenv()
console = Console()
MENU_INDEX_START = 1

SECOES_PADRAO = [
    "tldr", "o_que_e", "requisitos", "instalacao",
    "configuracao", "exemplo_pratico", "armadilhas",
    "otimizacoes", "conclusao", "referencias",
]

FOCOS_DISPONIVEIS = [
    "comparação geral",
    "performance / throughput",
    "custo",
    "migração",
    "integração",
    "segurança",
    "hardware limitado / edge",
    "quantização / modelos locais",
]


def parse_main_flags(args: list[str]) -> dict:
    refresh_search = "--refresh-search" in args
    return {"refresh_search": refresh_search}


def perguntar_foco() -> str:
    console.print("\n[dim]Focos disponíveis:[/dim]")
    for menu_index, foco_disponivel in enumerate(FOCOS_DISPONIVEIS, MENU_INDEX_START):
        console.print(f"  [cyan]{menu_index}.[/cyan] {foco_disponivel}")

    escolha = Prompt.ask(
        "\n[bold]Foco da pesquisa[/bold] [dim](número ou texto livre, enter para padrão)[/dim]",
        default="",
    )

    if not escolha.strip():
        return "comparação geral"

    if escolha.strip().isdigit():
        foco_index = int(escolha.strip()) - MENU_INDEX_START
        if 0 <= foco_index < len(FOCOS_DISPONIVEIS):
            return FOCOS_DISPONIVEIS[foco_index]

    return escolha.strip()


def perguntar_questoes() -> list[str]:
    console.print("\n[dim]Digite perguntas que o artigo DEVE responder.")
    console.print("[dim]Seja específico — o modelo vai usar isso diretamente.")
    console.print("[dim]Enter vazio para terminar.\n")
    console.print("[dim]Exemplos:[/dim]")
    console.print("[dim]  → como configurar modo rootless?[/dim]")
    console.print("[dim]  → docker-compose funciona sem mudanças?[/dim]")
    console.print("[dim]  → qual tem menor uso de RAM em idle?[/dim]\n")

    perguntas = []
    pergunta_index = MENU_INDEX_START
    while True:
        pergunta = Prompt.ask(f"  [cyan]Pergunta {pergunta_index}[/cyan]", default="")
        if not pergunta.strip():
            break
        perguntas.append(pergunta.strip())
        pergunta_index += 1
    return perguntas


def coletar_validacoes() -> list[str]:
    console.print("\n[dim]Digite critérios que o artigo DEVE conter.")
    console.print("[dim]Enter vazio para terminar.\n")

    criterios = []
    criterio_index = MENU_INDEX_START
    while True:
        criterio = Prompt.ask(f"  [cyan]Critério {criterio_index}[/cyan]", default="")
        if not criterio.strip():
            break
        criterios.append(criterio.strip())
        criterio_index += 1
    return criterios


def perguntar_pesquisa_existente(pipeline) -> str | None:
    """Ask if user wants to reuse an existing research file.

    Returns:
        research_content if chosen, None if should run new research
    """
    console.print("\n[dim]Pesquisas históricas:[/dim]")

    # List existing research files
    research_files = pipeline.list_research_files()

    if research_files:
        console.print("[dim]Arquivos de pesquisa disponíveis:[/dim]")
        console.print("  [cyan]0.[/cyan] Executar nova pesquisa (padrão)")
        for menu_index, (filename, tool, size) in enumerate(research_files, MENU_INDEX_START):
            size_kb = size / 1024
            console.print(f"  [cyan]{menu_index}.[/cyan] {filename} ({tool}, {size_kb:.1f}KB)")

        escolha = Prompt.ask(
            "\n[bold]Usar pesquisa existente?[/bold] [dim](número, ou enter para nova)[/dim]",
            default="0",
        )

        if escolha.strip() == "0" or not escolha.strip():
            return None  # Run new research

        try:
            file_index = int(escolha.strip())
            if 1 <= file_index <= len(research_files):
                _, tool, _ = research_files[file_index - MENU_INDEX_START]
                research_content = pipeline.load_research_history(tool)
                if research_content:
                    console.print(f"\n[green]✓[/green] Pesquisa de {tool} carregada ({len(research_content)} chars)")
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

    pipeline    = SDDPipeline(verbosity="minimal")

    # Ask if user wants to reuse existing research
    existing_research = None
    try:
        existing_research = perguntar_pesquisa_existente(pipeline)
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelado.[/dim]")
        sys.exit(0)

    try:
        output_path = pipeline.run(
            ferramentas=ferramentas,
            contexto=contexto,
            foco=foco,
            questoes=questoes,
            refresh_search=cli_flags["refresh_search"],
            urls=urls,
            skip_search=skip_search,
            existing_research=existing_research,
        )
    except Exception as error:
        console.print()
        console.print(Panel.fit(
            f"[bold red]Falha na execução do pipeline[/bold red]\n"
            f"[white]{error}[/white]\n\n"
            f"[dim]Dica: configure fallback em .env (cloud/local) para evitar rate-limit.[/dim]",
            border_style="red",
        ))
        sys.exit(1)

    checklist_pos_execucao(validacoes, output_path)


if __name__ == "__main__":
    main()
