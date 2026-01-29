"""RED9 lessons command implementation."""

from __future__ import annotations

from pathlib import Path

from red9.cli.output import (
    console,
    print_error,
    print_header,
    print_info,
    print_panel,
)
from red9.config import config_exists, load_config


def run_lessons(category: str | None, issue_id: int | None) -> None:
    """Show lessons learned.

    Args:
        category: Filter by category.
        issue_id: Filter by issue ID.
    """
    project_root = Path.cwd()

    if not config_exists(project_root):
        print_error("RED9 is not initialized. Run 'red9 init' first.")
        return

    config = load_config(project_root)
    issuedb_path = project_root / config.issuedb.db_path

    if not issuedb_path.exists():
        print_info("No lessons found.")
        return

    try:
        from issuedb.repository import IssueRepository

        repo = IssueRepository(db_path=str(issuedb_path))

        kwargs = {}
        if category:
            kwargs["category"] = category
        if issue_id:
            kwargs["issue_id"] = issue_id

        lessons = repo.list_lessons(**kwargs)

        if not lessons:
            print_info("No lessons found.")
            return

        print_header(f"Lessons Learned ({len(lessons)} total)")

        for lesson in lessons:
            title = f"Lesson #{lesson.id}"
            if lesson.category:
                title += f" [{lesson.category}]"
            if lesson.issue_id:
                title += f" (Issue #{lesson.issue_id})"

            print_panel(
                lesson.lesson,
                title=title,
                style="green",
            )
            console.print()

    except ImportError:
        print_error("IssueDB is not installed.")
    except Exception as e:
        print_error(f"Error listing lessons: {e}")
