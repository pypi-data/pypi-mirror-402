"""Knowledge management using IssueDB.

Replaces the file-based Notepad with IssueDB's Memory system.
Stores persistent learnings, decisions, and patterns.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from red9.logging import get_logger

logger = get_logger(__name__)


class Notepad:
    """Manages persistent knowledge via IssueDB Memory."""

    def __init__(self, root: Path, workflow_id: str | None = None):
        self.project_root = root
        self.workflow_id = workflow_id
        self.db_path = str(root / ".red9" / ".issue.db")

        # Ensure DB is accessible
        try:
            from issuedb.repository import IssueRepository

            self.repo = IssueRepository(db_path=self.db_path)
        except ImportError:
            logger.error("IssueDB not available")
            self.repo = None
        except Exception as e:
            # Handle database errors gracefully - don't fail the task
            logger.warning(f"Failed to initialize IssueDB for Notepad: {e}")
            self.repo = None

    def add_entry(self, category: str, content: Any, source_task: str) -> None:
        """Add a knowledge entry to IssueDB."""
        if not self.repo:
            return

        # Ensure content is a string
        if isinstance(content, (dict, list)):
            content = json.dumps(content, indent=2)
        else:
            content = str(content)

        db_category = category
        if category == "issue":
            db_category = "issue_log"

        # Create a unique key for this entry
        # Structure: workflow_id:source:timestamp_ns:random
        import uuid

        wf_id = self.workflow_id or "global"
        timestamp_ns = time.time_ns()
        random_suffix = str(uuid.uuid4())[:8]
        key = f"{wf_id}:{source_task}:{timestamp_ns}:{random_suffix}"

        # Store as Memory
        try:
            self.repo.add_memory(key=key, value=content, category=db_category)
            logger.debug(f"Added memory: [{db_category}] {key}")
        except Exception as e:
            logger.error(f"Failed to add memory to IssueDB: {e}")

    def get_summary(self) -> str:
        """Get a combined summary of all knowledge for prompt injection."""
        if not self.repo:
            return ""

        summary = ["## INHERITED WISDOM FROM ISSUE DB"]
        has_content = False

        categories = ["learning", "decision", "pattern", "issue_log"]

        for cat in categories:
            try:
                memories = self.repo.list_memory(category=cat)
                if not memories:
                    continue

                recent_memories = memories[-10:] if len(memories) > 10 else memories

                cat_title = cat.replace("_", " ").capitalize()
                summary.append(f"\n### {cat_title}s")

                for mem in recent_memories:
                    source = mem.key.split(":")[1] if ":" in mem.key else "unknown"
                    summary.append(f"- [{source}]: {mem.value}")

                has_content = True
            except Exception as e:
                logger.warning(f"Failed to list memories for {cat}: {e}")

        if not has_content:
            return ""

        return "\n".join(summary)
