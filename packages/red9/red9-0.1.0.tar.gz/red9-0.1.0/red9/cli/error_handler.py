"""Smart error handler with contextual hints."""

from __future__ import annotations

import difflib
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()


class ErrorHints:
    """Provides contextual hints for common errors."""

    @staticmethod
    def file_not_found(filepath: str, project_root: Path) -> str:
        """Suggest similar files when a file is not found."""
        # Collect all files in project
        all_files: list[str] = []
        for pattern in ["**/*.py", "**/*.ts", "**/*.js", "**/*.md"]:
            all_files.extend(str(f.relative_to(project_root)) for f in project_root.glob(pattern))

        # Find similar filenames
        filename = Path(filepath).name
        filenames = [Path(f).name for f in all_files]
        similar = difflib.get_close_matches(filename, filenames, n=3, cutoff=0.6)

        if similar:
            # Find full paths for similar files
            suggestions = []
            for name in similar:
                for f in all_files:
                    if Path(f).name == name:
                        suggestions.append(f)
                        break

            hint = f"[red]✗ File not found:[/red] {filepath}\n\n"
            hint += "[dim]Did you mean:[/dim]\n"
            for s in suggestions[:3]:
                hint += f"  • {s}\n"
            return hint

        return f"[red]✗ File not found:[/red] {filepath}"

    @staticmethod
    def command_not_found(command: str) -> str:
        """Suggest similar commands."""
        available = [
            "task",
            "chat",
            "ask",
            "init",
            "status",
            "resume",
            "todos",
            "memory",
            "lessons",
            "tune",
        ]
        similar = difflib.get_close_matches(command, available, n=3, cutoff=0.5)

        hint = f"[red]✗ Unknown command:[/red] {command}\n\n"
        if similar:
            hint += "[dim]Did you mean:[/dim]\n"
            for s in similar:
                hint += f"  • red9 {s}\n"
        else:
            hint += "[dim]Available commands:[/dim]\n"
            for cmd in available[:5]:
                hint += f"  • red9 {cmd}\n"
        return hint

    @staticmethod
    def connection_error(error: Exception) -> str:
        """Provide hints for connection errors."""
        error_str = str(error).lower()

        if "connection refused" in error_str or "11434" in error_str:
            return (
                "[red]✗ Cannot connect to Ollama[/red]\n\n"
                "[dim]Hints:[/dim]\n"
                "  • Is Ollama running? Try: [cyan]ollama serve[/cyan]\n"
                "  • Check if port 11434 is available\n"
                "  • Verify base_url in .red9/config.yaml"
            )

        if "timeout" in error_str:
            return (
                "[red]✗ Request timed out[/red]\n\n"
                "[dim]Hints:[/dim]\n"
                "  • The model may be loading. Try again in a moment.\n"
                "  • Increase timeout in .red9/config.yaml (provider.timeout)\n"
                "  • Check system resources (memory, GPU)"
            )

        return f"[red]✗ Connection error:[/red] {error}"

    @staticmethod
    def model_not_found(model: str) -> str:
        """Provide hints for model not found errors."""
        return (
            f"[red]✗ Model not found:[/red] {model}\n\n"
            "[dim]Hints:[/dim]\n"
            f"  • Pull the model: [cyan]ollama pull {model}[/cyan]\n"
            "  • List available models: [cyan]ollama list[/cyan]\n"
            "  • Update model in .red9/config.yaml"
        )

    @staticmethod
    def permission_error(path: str) -> str:
        """Provide hints for permission errors."""
        return (
            f"[red]✗ Permission denied:[/red] {path}\n\n"
            "[dim]Hints:[/dim]\n"
            "  • Check file permissions\n"
            "  • Ensure you own the file or have write access\n"
            "  • Try running with appropriate permissions"
        )

    @staticmethod
    def syntax_error(filepath: str, line: int | None, error: str) -> str:
        """Provide hints for syntax errors."""
        hint = f"[red]✗ Syntax error in {filepath}"
        if line:
            hint += f" (line {line})"
        hint += "[/red]\n\n"
        hint += f"[dim]{error}[/dim]\n\n"
        hint += "[dim]Hints:[/dim]\n"
        hint += "  • Check for missing brackets, quotes, or colons\n"
        hint += "  • Verify indentation (Python is sensitive to whitespace)\n"
        hint += f"  • Run linter: [cyan]ruff check {filepath}[/cyan]"
        return hint


def format_error(error: Exception, project_root: Path | None = None) -> str:
    """Format an error with contextual hints.

    Args:
        error: The exception to format.
        project_root: Project root for file suggestions.

    Returns:
        Formatted error string with hints.
    """
    error_str = str(error).lower()

    # File not found
    if isinstance(error, FileNotFoundError):
        if project_root:
            return ErrorHints.file_not_found(str(error.filename or error), project_root)
        return f"[red]✗ File not found:[/red] {error}"

    # Permission denied
    if isinstance(error, PermissionError):
        return ErrorHints.permission_error(str(error.filename or error))

    # Connection errors
    if "connection" in error_str or "timeout" in error_str or "refused" in error_str:
        return ErrorHints.connection_error(error)

    # Model not found
    if "model" in error_str and ("not found" in error_str or "does not exist" in error_str):
        # Try to extract model name
        import re

        match = re.search(r"model[:\s]+['\"]?(\S+)['\"]?", str(error), re.IGNORECASE)
        if match:
            return ErrorHints.model_not_found(match.group(1))
        return f"[red]✗ Model error:[/red] {error}"

    # Syntax error
    if isinstance(error, SyntaxError):
        return ErrorHints.syntax_error(
            error.filename or "unknown", error.lineno, str(error.msg or error)
        )

    # Generic error with class name
    error_type = type(error).__name__
    return f"[red]✗ {error_type}:[/red] {error}"


def display_error(error: Exception, project_root: Path | None = None) -> None:
    """Display an error with contextual hints in a panel.

    Args:
        error: The exception to display.
        project_root: Project root for file suggestions.
    """
    formatted = format_error(error, project_root)
    console.print(Panel(formatted, title="[bold red]Error[/bold red]", border_style="red"))


def display_warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"[yellow]⚠ {message}[/yellow]")


def display_success(message: str) -> None:
    """Display a success message."""
    console.print(f"[green]✓ {message}[/green]")


def display_info(message: str) -> None:
    """Display an info message."""
    console.print(f"[cyan]ℹ {message}[/cyan]")
