"""Merge agent task - aggregates results from parallel stages.

Collects files_modified from all parallel stages, detects conflicts,
and provides unified output to downstream stages (like run_tests).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from stabilize import Task, TaskResult
from stabilize.models.stage import StageExecution

from red9.logging import get_logger

logger = get_logger(__name__)


class MergeAgentTask(Task):
    """Merge agent that aggregates results from parallel stages.

    This is a Stabilize Task that:
    1. Collects files_modified from all parallel stage outputs
    2. Detects conflicts (same file modified by multiple stages)
    3. Returns unified list of modified files for downstream stages

    This task does NOT use an LLM - it's pure aggregation logic.
    """

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the merge agent.

        Args:
            stage: Stage execution context with parallel stage outputs.

        Returns:
            TaskResult with aggregated files or conflict error.
        """
        issue_id = stage.context.get("issue_id")
        project_root = stage.context.get("project_root")

        try:
            # Collect all files_modified from parallel stages
            all_files: list[str] = []
            file_sources: dict[str, list[str]] = {}  # file -> list of stages that modified it
            stage_summaries: list[dict[str, Any]] = []
            test_files: list[str] = []
            backup_dirs: list[str] = []

            # Iterate through context looking for parallel stage outputs
            for key, value in stage.context.items():
                if not isinstance(value, dict):
                    continue

                # Look for outputs from parallel stages
                files_modified = value.get("files_modified", [])
                if files_modified:
                    stage_name = key
                    for f in files_modified:
                        all_files.append(f)
                        if f not in file_sources:
                            file_sources[f] = []
                        file_sources[f].append(stage_name)

                # Collect test files
                test_files_created = value.get("test_files_created", [])
                if test_files_created:
                    test_files.extend(test_files_created)

                # Collect backup directories
                backup_dir = value.get("backup_dir")
                if backup_dir:
                    backup_dirs.append(backup_dir)

                # Collect stage summaries
                summary = value.get("summary")
                if summary:
                    stage_summaries.append(
                        {
                            "stage": key,
                            "summary": summary[:200],
                            "files": files_modified,
                        }
                    )

            # Check for conflicts - same file modified by multiple stages
            conflicts = {f: sources for f, sources in file_sources.items() if len(sources) > 1}

            if conflicts:
                conflict_details = ", ".join(
                    f"{f} (by {', '.join(sources)})" for f, sources in conflicts.items()
                )
                error_msg = (
                    f"Conflict detected: Multiple stages modified same files: {conflict_details}"
                )

                # Add comment to issue
                self._add_issue_comment(
                    project_root,
                    issue_id,
                    f"⚠️ Merge conflict detected:\n\n{error_msg}",
                )

                return TaskResult.terminal(error=error_msg)

            # Deduplicate files
            unique_files = list(set(all_files))
            unique_test_files = list(set(test_files))

            # Build merge summary
            num_files = len(unique_files)
            num_stages = len(stage_summaries)
            merge_summary = f"Merged {num_files} files from {num_stages} parallel stages"
            if unique_test_files:
                merge_summary += f", {len(unique_test_files)} test files"

            # Add success comment to issue
            self._add_issue_comment(
                project_root,
                issue_id,
                f"✅ Parallel merge complete:\n\n"
                f"**Files modified:** {', '.join(unique_files) if unique_files else 'None'}\n"
                f"**Test files:** {', '.join(unique_test_files) if unique_test_files else 'None'}",
            )

            return TaskResult.success(
                outputs={
                    "files_modified": unique_files,
                    "test_files_created": unique_test_files,
                    "merge_summary": merge_summary,
                    "stage_summaries": stage_summaries,
                    "backup_dirs": backup_dirs,
                    "parallel_stages_merged": len(stage_summaries),
                }
            )

        except Exception as e:
            logger.error(f"Merge agent error: {e}")
            return TaskResult.terminal(error=f"Merge agent error: {e}")

    def _add_issue_comment(
        self,
        project_root: str | None,
        issue_id: int | None,
        comment: str,
    ) -> None:
        """Add a comment to the issue.

        Args:
            project_root: Project root directory.
            issue_id: Issue ID (optional).
            comment: Comment text.
        """
        if not issue_id:
            return

        try:
            from issuedb.repository import IssueRepository

            if project_root:
                db_path = str(Path(project_root) / ".red9" / ".issue.db")
            else:
                db_path = ".red9/.issue.db"

            repo = IssueRepository(db_path=db_path)
            repo.add_comment(issue_id, comment)
        except Exception as e:
            logger.warning(f"Failed to add issue comment: {e}")
