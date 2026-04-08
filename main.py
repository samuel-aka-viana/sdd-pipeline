import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from pipeline import SDDPipeline

load_dotenv()
console = Console()

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


def perguntar_foco() -> str:
    console.print("\n[dim]Focos disponíveis:[/dim]")
    for i, f in enumerate(FOCOS_DISPONIVEIS, 1):
        console.print(f"  [cyan]{i}.[/cyan] {f}")

    escolha = Prompt.ask(
        "\n[bold]Foco da pesquisa[/bold] [dim](número ou texto livre, enter para padrão)[/dim]",
        default="",
    )

    if not escolha.strip():
        return "comparação geral"

    if escolha.strip().isdigit():
        idx = int(escolha.strip()) - 1
        if 0 <= idx < len(FOCOS_DISPONIVEIS):
            return FOCOS_DISPONIVEIS[idx]

    return escolha.strip()


def perguntar_questoes() -> list[str]:
    console.print("\n[dim]Digite perguntas que o artigo DEVE responder.")
    console.print("[dim]Seja específico — o modelo vai usar isso diretamente.")
    console.print("[dim]Enter vazio para terminar.\n")
    console.print("[dim]Exemplos:[/dim]")
    console.print("[dim]  → como configurar modo rootless?[/dim]")
    console.print("[dim]  → docker-compose funciona sem mudanças?[/dim]")
    console.print("[dim]  → qual tem menor uso de RAM em idle?[/dim]\n")

    items = []
    i = 1
    while True:
        q = Prompt.ask(f"  [cyan]Pergunta {i}[/cyan]", default="")
        if not q.strip():
            break
        items.append(q.strip())
        i += 1
    return items


def coletar_validacoes() -> list[str]:
    console.print("\n[dim]Digite critérios que o artigo DEVE conter.")
    console.print("[dim]Enter vazio para terminar.\n")

    items = []
    i = 1
    while True:
        v = Prompt.ask(f"  [cyan]Critério {i}[/cyan]", default="")
        if not v.strip():
            break
        items.append(v.strip())
        i += 1
    return items


def exibir_resumo(ferramentas, contexto, foco, questoes, validacoes):
    t = Table(show_header=False, box=None, padding=(0, 2))
    t.add_column(style="dim", width=16)
    t.add_column(style="white")

    t.add_row("Ferramentas", f"[yellow]{ferramentas}[/yellow]")
    t.add_row("Contexto",    f"[yellow]{contexto}[/yellow]")
    t.add_row("Foco",        f"[cyan]{foco}[/cyan]")
    t.add_row(
        "O artigo deve\nresponder",
        "\n".join(f"→ {q}" for q in questoes) if questoes else "[dim]sem perguntas adicionais[/dim]",
    )
    t.add_row(
        "Validações",
        "\n".join(f"☐ {v}" for v in validacoes) if validacoes else "[dim]nenhuma[/dim]",
    )

    console.print()
    console.print(Panel(t, title="[bold cyan]Resumo[/bold cyan]", border_style="cyan"))
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
    for v in validacoes:
        ok = Confirm.ask(f"  [white]{v}[/white]")
        if ok:
            aprovados += 1
            console.print("  [green]✓[/green]\n")
        else:
            console.print("  [red]✗[/red]\n")

    total = len(validacoes)
    cor = "green" if aprovados == total else "yellow" if aprovados > 0 else "red"
    console.print(f"[{cor}]Resultado: {aprovados}/{total} critérios atendidos[/{cor}]\n")


def main():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]SDD Tech Writer[/bold cyan]\n"
        "[dim]Geração de artigos técnicos com LLM local[/dim]",
        border_style="cyan",
    ))
    console.print()

    try:
        ferramentas = Prompt.ask("[bold]Ferramentas[/bold] [dim](ex: podman e docker)[/dim]")
        contexto    = Prompt.ask("[bold]Contexto[/bold]    [dim](ex: ambiente de dev local no Linux)[/dim]")
        foco        = perguntar_foco()
        questoes    = perguntar_questoes()
        validacoes  = coletar_validacoes()
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelado.[/dim]")
        sys.exit(0)

    exibir_resumo(ferramentas, contexto, foco, questoes, validacoes)

    if not Confirm.ask("[bold]Iniciar pipeline?[/bold]", default=True):
        console.print("[dim]Cancelado.[/dim]")
        sys.exit(0)

    pipeline    = SDDPipeline()
    output_path = pipeline.run(
        ferramentas=ferramentas,
        contexto=contexto,
        foco=foco,
        questoes=questoes,
    )

    checklist_pos_execucao(validacoes, output_path)


if __name__ == "__main__":
    main()