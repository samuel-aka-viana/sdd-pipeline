"""CLI prompt helpers for user input collection."""

from rich.console import Console
from rich.prompt import Prompt


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

MENU_INDEX_START = 1


def prompt_menu_choice(
    console: Console, options: list[str], header: str, default: str | None = None
) -> str:
    """Display menu options and prompt user for choice.

    Args:
        console: Rich console for output.
        options: List of menu options.
        header: Header text for the prompt.
        default: Default option text (if None, uses first option).

    Returns:
        Selected option text, or default if user provides empty input.
    """
    console.print("\n[dim]Focos disponíveis:[/dim]")
    for menu_index, option in enumerate(options, MENU_INDEX_START):
        console.print(f"  [cyan]{menu_index}.[/cyan] {option}")

    default_option = default or options[0]
    escolha = Prompt.ask(
        f"\n[bold]{header}[/bold] [dim](número ou texto livre, enter para padrão)[/dim]",
        default="",
    )

    if not escolha.strip():
        return default_option

    if escolha.strip().isdigit():
        option_index = int(escolha.strip()) - MENU_INDEX_START
        if 0 <= option_index < len(options):
            return options[option_index]

    return escolha.strip()


def prompt_list(
    console: Console, header_lines: list[str], item_label: str
) -> list[str]:
    """Prompt user to enter a list of items (one per line).

    Args:
        console: Rich console for output.
        header_lines: List of header lines to display (as context).
        item_label: Label for each item (e.g., "Pergunta", "Critério").

    Returns:
        List of non-empty user inputs.
    """
    for line in header_lines:
        console.print(line)

    items = []
    item_index = MENU_INDEX_START
    while True:
        item = Prompt.ask(f"  [cyan]{item_label} {item_index}[/cyan]", default="")
        if not item.strip():
            break
        items.append(item.strip())
        item_index += 1
    return items
