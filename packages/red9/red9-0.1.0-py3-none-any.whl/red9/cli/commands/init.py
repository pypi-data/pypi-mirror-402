"RED9 init command implementation."

from __future__ import annotations

from pathlib import Path

from red9.cli.output import (
    console,
    create_status,
    print_step,
    print_success,
    print_warning,
)
from red9.config import config_exists
from red9.core.session import Red9Session


def run_init(
    provider: str,
    model: str | None,
    embedding_model: str | None,
) -> None:
    """Initialize RED9 in the current directory.

    Args:
        provider: LLM provider to use.
        model: Model to use for generation.
        embedding_model: Model to use for embeddings.
    """
    project_root = Path.cwd()

    # Check if already initialized
    if config_exists(project_root):
        print_warning("RED9 is already initialized in this directory")
        if not console.input("[yellow]?[/yellow] Reinitialize? [y/N]: ").strip().lower() == "y":
            return

    console.print("\n[bold]Initializing RED9...[/bold]\n")

    session = Red9Session(project_root)

    # Step 1: Create directory structure and configuration
    print_step(1, 3, "Creating configuration...")
    config_path = session.initialize_project(
        provider=provider,
        model=model,
        embedding_model=embedding_model,
    )
    print_success(f"Created {config_path}")

    # Step 2: Initialize IssueDB is handled by session.initialize_project automatically now

    # Step 3: Index codebase
    print_step(2, 3, "Indexing codebase for semantic search...")
    try:
        with create_status("Indexing files..."):
            indexed_count = session.index_codebase()
        print_success(f"Indexed {indexed_count} files")
    except Exception as e:
        print_warning(f"Could not index codebase: {e}")

    console.print("\n[bold green]RED9 initialized successfully![/bold green]")
    console.print("\nNext steps:")
    console.print("  [cyan]red9 ask[/cyan] 'How does this codebase work?'")
    console.print("  [cyan]red9 task[/cyan] 'Add a new feature'")
    console.print("  [cyan]red9 todos[/cyan] to see pending issues")
