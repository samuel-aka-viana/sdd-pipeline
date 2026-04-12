from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from contextlib import contextmanager
import time
import json
from pathlib import Path
from datetime import datetime


class EventLog:
    """Centralizado event log para análise posterior (pode ser consumido por WebSocket/Gradio)."""
    
    def __init__(self, log_file: str = "output/pipeline_events.jsonl"):
        """Initialize event log with JSONL file path.
        
        Args:
            log_file: Path to JSONL file. Parent directory created automatically.
            
        Example:
            event_log = EventLog()
            event_log.log_event("url_found", {"url": "https://...", "elapsed_seconds": 1.2})
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_event(self, event_type: str, data: dict):
        """Append event to JSONL file with ISO timestamp.
        
        Args:
            event_type: Type of event (e.g., "url_found", "task_completed")
            data: Event-specific data dict
            
        Example:
            event_log.log_event("url_found", {
                "url": "https://example.com",
                "title": "Example",
                "status": "ok",
                "elapsed_seconds": 2.5
            })
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            **data
        }
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')


class PipelineLogger:

    def __init__(self):
        self.console = Console()
        self.event_log = EventLog()

    def pipeline_start(self, ferramentas: str, contexto: str):
        self.console.print()
        self.console.print(Panel.fit(
            f"[bold cyan]SDD Pipeline[/bold cyan]\n"
            f"[white]Ferramentas:[/white] [yellow]{ferramentas}[/yellow]\n"
            f"[white]Contexto:[/white]    [yellow]{contexto}[/yellow]",
            border_style="cyan"
        ))
        self.console.print()
        self.event_log.log_event("pipeline_start", {
            "ferramentas": ferramentas,
            "contexto": contexto
        })

    def section(self, number: int, total: int, title: str):
        self.console.print("[bold white]──────────────────────────────────────[/bold white]")
        self.console.print(
            f"[bold cyan][{number}/{total}][/bold cyan] [bold white]{title}[/bold white]"
        )
        self.event_log.log_event("section_start", {
            "number": number,
            "total": total,
            "title": title
        })

    @contextmanager
    def task(self, description: str):
        """Context manager for tracking task execution time with spinner animation.
        
        Logs task completion or failure with elapsed time. Handles exceptions gracefully.
        
        Args:
            description: Task description shown in spinner and logs
            
        Example:
            logger = PipelineLogger()
            with logger.task("Extracting URLs"):
                # do work here
                pass
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True
        ) as progress:
            progress.add_task(description, total=None)
            start = time.time()
            try:
                yield progress
                elapsed = time.time() - start
                progress.stop()
                self.console.print(
                    f"   [green]✓[/green] {description} [dim]({elapsed:.1f}s)[/dim]"
                )
                self.event_log.log_event("task_completed", {
                    "description": description,
                    "elapsed_seconds": elapsed
                })
            except Exception as e:
                elapsed = time.time() - start
                progress.stop()
                self.console.print(
                    f"   [red]✗[/red] {description} [dim]({elapsed:.1f}s)[/dim] — [red]{e}[/red]"
                )
                self.event_log.log_event("task_failed", {
                    "description": description,
                    "elapsed_seconds": elapsed,
                    "error": str(e)
                })
                raise

    def search_query(self, query: str):
        self.console.print(f"   [dim]🔍 {query}[/dim]")
        self.event_log.log_event("search_query", {"query": query})

    def found_url(self, url: str, title: str = "", status: str = "", elapsed: float = None):
        """Log URL found during research with scraping status and elapsed time.
        
        Emits visual indicator (✓ ok, ⚠ failed, ⊘ skipped) and timing data.
        
        Args:
            url: Full URL found
            title: Page title or snippet (max 60 chars in output)
            status: One of "ok", "scrape_failed", "skipped"
            elapsed: Scraping elapsed time in seconds
            
        Example:
            logger.found_url(
                "https://example.com",
                title="Example Article",
                status="ok",
                elapsed=1.5
            )
        """
        status_indicator = {
            "ok": "[green]✓[/green]",
            "scrape_failed": "[yellow]⚠[/yellow]",
            "skipped": "[dim]⊘[/dim]",
        }.get(status, "[cyan]•[/cyan]")
        
        title_str = f" — {title[:60]}" if title else ""
        elapsed_str = f" ({elapsed:.1f}s)" if elapsed else ""
        self.console.print(f"   {status_indicator} [cyan]{url}[/cyan]{title_str}{elapsed_str}")
        
        self.event_log.log_event("url_found", {
            "url": url,
            "title": title,
            "status": status,
            "elapsed_seconds": elapsed
        })

    def search_done(self, tool: str, n_results: int, n_queries: int):
        self.console.print(
            f"   [green]✓[/green] [white]{tool}[/white] — "
            f"[cyan]{n_results} resultados[/cyan] de "
            f"[cyan]{n_queries} queries[/cyan]"
        )
        self.event_log.log_event("search_done", {
            "tool": tool,
            "n_results": n_results,
            "n_queries": n_queries
        })

    def iteration(self, current: int, total: int):
        self.console.print()
        self.console.print(f"   [bold]Iteração {current}/{total}[/bold]")
        self.event_log.log_event("iteration", {
            "current": current,
            "total": total
        })

    def critic_passed(self, layer: str, warnings: list = None):
        self.console.print(f"   [green]✓ Critic ({layer}): aprovado[/green]")
        if warnings:
            for w in warnings:
                self.console.print(f"   [yellow]⚠ {w}[/yellow]")
        self.event_log.log_event("critic_passed", {
            "layer": layer,
            "warnings": warnings or []
        })

    def critic_failed(self, problems: list):
        self.console.print(f"   [red]✗ Critic: {len(problems)} problema(s)[/red]")
        for p in problems:
            self.console.print(f"   [red]  • {p}[/red]")
        self.event_log.log_event("critic_failed", {
            "problems": problems
        })

    def memory_hit(self, lesson: str):
        self.console.print(f"   [magenta]💡 Memória: {lesson[:80]}[/magenta]")
        self.event_log.log_event("memory_hit", {"lesson": lesson[:200]})

    def saved(self, path: str):
        self.console.print()
        self.console.print(Panel.fit(
            f"[bold green]✓ Concluído[/bold green]\n"
            f"[white]Salvo em:[/white] [cyan]{path}[/cyan]",
            border_style="green"
        ))
        self.event_log.log_event("pipeline_completed", {"output_path": path})

    def validation_report(self, result):
        t = Table(show_header=False, box=None, padding=(0, 1))
        t.add_column(style="bold", width=4)
        t.add_column()

        for p in result.problems:
            t.add_row("[red]✗[/red]", f"[red]{p}[/red]")
        for w in result.warnings:
            t.add_row("[yellow]⚠[/yellow]", f"[yellow]{w}[/yellow]")
        if result.passed:
            t.add_row("[green]✓[/green]", "[green]Todas as validações passaram[/green]")

        self.console.print(t)
        self.event_log.log_event("validation_report", {
            "passed": result.passed,
            "problems": result.problems,
            "warnings": result.warnings
        })

    def error(self, msg: str):
        self.console.print(f"\n[bold red]ERRO:[/bold red] [red]{msg}[/red]\n")
        self.event_log.log_event("error", {"message": msg})

    def metrics(self, data: dict):
        t = Table(title="Métricas", border_style="dim")
        t.add_column("Campo", style="cyan")
        t.add_column("Valor", style="white")
        for k, v in data.items():
            t.add_row(str(k), str(v))
        self.console.print(t)
        self.event_log.log_event("metrics", data)
