"""RED9 memory command implementation."""

from __future__ import annotations

from pathlib import Path

from red9.cli.output import (
    console,
    print_error,
    print_header,
    print_info,
    print_success,
)
from red9.config import config_exists, load_config


def add_memory(key: str, value: str, category: str) -> None:
    """Store a memory value.

    Args:
        key: Memory key.
        value: Memory value.
        category: Memory category.
    """
    project_root = Path.cwd()

    if not config_exists(project_root):
        print_error("RED9 is not initialized. Run 'red9 init' first.")
        return

    config = load_config(project_root)
    issuedb_path = project_root / config.issuedb.db_path

    try:
        from issuedb.repository import IssueRepository

        repo = IssueRepository(db_path=str(issuedb_path))

        # Check if memory exists
        existing = repo.get_memory(key)
        if existing:
            repo.update_memory(key, value=value, category=category)
            print_success(f"Updated memory: {key}")
        else:
            repo.add_memory(key, value, category=category)
            print_success(f"Added memory: {key} ({category})")

    except ImportError:
        print_error("IssueDB is not installed.")
    except Exception as e:
        print_error(f"Error adding memory: {e}")


def list_memory(category: str | None) -> None:
    """List stored memory.

    Args:
        category: Filter by category.
    """
    project_root = Path.cwd()

    if not config_exists(project_root):
        print_error("RED9 is not initialized. Run 'red9 init' first.")
        return

    config = load_config(project_root)
    issuedb_path = project_root / config.issuedb.db_path

    if not issuedb_path.exists():
        print_info("No memory entries found.")
        return

    try:
        from issuedb.repository import IssueRepository

        repo = IssueRepository(db_path=str(issuedb_path))

        kwargs = {}
        if category:
            kwargs["category"] = category

        memories = repo.list_memory(**kwargs)

        if not memories:
            print_info("No memory entries found.")
            return

        print_header("Agent Guidelines (Memory)")

        # Group by category
        by_category: dict[str, list] = {}
        for mem in memories:
            cat = mem.category or "general"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(mem)

        for cat, mems in sorted(by_category.items()):
            console.print(f"\n[cyan][{cat}][/cyan]")
            for mem in mems:
                # Truncate long values
                value = mem.value
                if len(value) > 80:
                    value = value[:77] + "..."
                console.print(f"  [bold]{mem.key}[/bold]: {value}")

    except ImportError:
        print_error("IssueDB is not installed.")
    except Exception as e:
        print_error(f"Error listing memory: {e}")


def delete_memory(key: str) -> None:
    """Delete a memory entry.

    Args:
        key: Memory key to delete.
    """
    project_root = Path.cwd()

    if not config_exists(project_root):
        print_error("RED9 is not initialized. Run 'red9 init' first.")
        return

    config = load_config(project_root)
    issuedb_path = project_root / config.issuedb.db_path

    try:
        from issuedb.repository import IssueRepository

        repo = IssueRepository(db_path=str(issuedb_path))
        repo.delete_memory(key)
        print_success(f"Deleted memory: {key}")

    except ImportError:
        print_error("IssueDB is not installed.")
    except Exception as e:
        print_error(f"Error deleting memory: {e}")
