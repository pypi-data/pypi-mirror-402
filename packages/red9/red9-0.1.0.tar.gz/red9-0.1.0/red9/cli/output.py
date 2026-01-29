"""Terminal output utilities using Rich."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

# Global console instance
console = Console()


def print_success(message: str) -> None:
    """Print a success message in green."""
    console.print(f"[bold green]✓ {message}[/bold green]")


def print_error(message: str) -> None:
    """Print an error message in red."""
    console.print(f"[bold red]✗ {message}[/bold red]")


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    console.print(f"[bold yellow]! {message}[/bold yellow]")


def print_info(message: str) -> None:
    """Print an info message in blue."""
    console.print(f"[bold blue]• {message}[/bold blue]")


def print_step(step: int, total: int, message: str) -> None:
    """Print a step progress message."""
    console.print(f"[dim]{step}/{total}[/dim] [bold]{message}[/bold]")


def print_header(title: str) -> None:
    """Print a section header."""
    console.print()
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", border_style="dim"))


def print_code(code: str, language: str = "python") -> None:
    """Print syntax-highlighted code."""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def print_diff(diff: str) -> None:
    """Print a unified diff with syntax highlighting."""
    syntax = Syntax(diff, "diff", theme="monokai")
    console.print(syntax)


def print_panel(content: str, title: str | None = None, style: str = "blue") -> None:
    """Print content in a panel."""
    console.print(Panel(content, title=title, border_style=style))


def print_table(
    headers: list[str],
    rows: list[list[Any]],
    title: str | None = None,
) -> None:
    """Print a formatted table."""
    table = Table(title=title)

    for header in headers:
        table.add_column(header, style="cyan")

    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    console.print(table)


def print_markdown(content: str) -> None:
    """Print rendered markdown."""
    md = Markdown(content)
    console.print(md)


def create_progress() -> Progress:
    """Create a progress bar context manager."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )


def create_status(message: str) -> Any:
    """Create a status spinner context manager."""
    return console.status(message, spinner="dots")


def confirm(message: str, default: bool = False) -> bool:
    """Ask for user confirmation."""
    suffix = " [Y/n]" if default else " [y/N]"
    response = console.input(f"[yellow]?[/yellow] {message}{suffix}: ").strip().lower()

    if not response:
        return default

    return response in ("y", "yes")


def format_file_path(path: str) -> str:
    """Format a file path for display."""
    return f"[cyan]{path}[/cyan]"


def format_status(status: str) -> str:
    """Format a status string with appropriate color."""
    status_colors = {
        "open": "yellow",
        "in-progress": "blue",
        "in_progress": "blue",
        "closed": "green",
        "wont-do": "dim",
        "wont_do": "dim",
        "succeeded": "green",
        "failed": "red",
        "terminal": "red",
        "running": "blue",
        "pending": "yellow",
    }
    color = status_colors.get(status.lower(), "white")
    return f"[{color}]{status}[/{color}]"


def format_priority(priority: str) -> str:
    """Format a priority string with appropriate color."""
    priority_colors = {
        "critical": "red bold",
        "high": "red",
        "medium": "yellow",
        "low": "dim",
    }
    color = priority_colors.get(priority.lower(), "white")
    return f"[{color}]{priority}[/{color}]"
