"""RED9 todos command implementation."""

from __future__ import annotations

from pathlib import Path

from red9.cli.output import (
    console,
    format_priority,
    format_status,
    print_error,
    print_header,
    print_info,
    print_table,
)
from red9.config import config_exists, load_config


def run_todos(
    priority: str | None,
    issue_status: str | None,
    limit: int,
) -> None:
    """List pending issues/tasks.

    Args:
        priority: Filter by priority.
        issue_status: Filter by status.
        limit: Maximum number of issues to show.
    """
    project_root = Path.cwd()

    if not config_exists(project_root):
        print_error("RED9 is not initialized. Run 'red9 init' first.")
        return

    config = load_config(project_root)
    issuedb_path = project_root / config.issuedb.db_path

    if not issuedb_path.exists():
        print_info("No issues found. The project has no .issue.db yet.")
        return

    try:
        from issuedb.repository import IssueRepository

        repo = IssueRepository(db_path=str(issuedb_path))

        # Build filter kwargs
        kwargs = {"limit": limit}
        if priority:
            kwargs["priority"] = priority
        if issue_status:
            kwargs["status"] = issue_status.replace("-", "_")

        issues = repo.list_issues(**kwargs)

        if not issues:
            print_info("No matching issues found.")
            return

        print_header(f"Issues ({len(issues)} shown)")

        # Build table data
        rows = []
        for issue in issues:
            rows.append(
                [
                    str(issue.id),
                    format_priority(
                        issue.priority.value
                        if hasattr(issue.priority, "value")
                        else str(issue.priority)
                    ),
                    format_status(
                        issue.status.value if hasattr(issue.status, "value") else str(issue.status)
                    ),
                    issue.title[:60] + ("..." if len(issue.title) > 60 else ""),
                ]
            )

        print_table(
            headers=["ID", "Priority", "Status", "Title"],
            rows=rows,
        )

        # Show summary
        console.print(f"\n[dim]Showing {len(issues)} issues. Use --limit to see more.[/dim]")

    except ImportError:
        print_error("IssueDB is not installed.")
    except Exception as e:
        print_error(f"Error reading issues: {e}")
