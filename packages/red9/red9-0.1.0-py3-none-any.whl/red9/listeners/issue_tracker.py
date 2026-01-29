"""Issue tracker listener for decoupled database updates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from red9.logging import get_logger

logger = get_logger(__name__)


class IssueTrackerListener:
    """Listens for task progress signals and updates IssueDB."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def on_task_progress(self, sender: Any, **kwargs: Any) -> None:
        """Handle task progress signal."""
        issue_id = kwargs.get("issue_id")
        comment = kwargs.get("comment")

        if not issue_id or not comment:
            return

        try:
            from issuedb.repository import IssueRepository

            repo = IssueRepository(db_path=str(self.db_path))
            repo.add_comment(issue_id, comment)
        except Exception as e:
            logger.warning(f"Failed to track issue progress: {e}")
