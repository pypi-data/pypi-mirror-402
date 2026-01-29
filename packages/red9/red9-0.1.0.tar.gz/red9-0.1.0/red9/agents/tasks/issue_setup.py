"""Issue setup task - first stage of every workflow."""

from __future__ import annotations

from pathlib import Path

from stabilize import Task, TaskResult
from stabilize.models.stage import StageExecution


class IssueSetupTask(Task):
    """First stage of every workflow.

    Creates or updates IssueDB issue and marks it as IN_PROGRESS.
    Links workflow ID to issue for tracking.
    """

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the issue setup task.

        Args:
            stage: Stage execution context.

        Returns:
            TaskResult with issue setup status.
        """
        issue_id = stage.context.get("issue_id")
        workflow_id = stage.context.get("workflow_id")
        project_root = stage.context.get("project_root")

        if not issue_id:
            return TaskResult.terminal(error="issue_id is required in stage context")

        if not workflow_id:
            return TaskResult.terminal(error="workflow_id is required in stage context")

        try:
            # Import IssueDB
            from issuedb.repository import IssueRepository

            # Determine database path
            if project_root:
                db_path = Path(project_root) / ".red9" / ".issue.db"
            else:
                db_path = Path(".red9/.issue.db")

            repo = IssueRepository(db_path=str(db_path))

            # Update issue status to IN_PROGRESS (use string value with hyphen)
            repo.update_issue(issue_id, status="in-progress")

            # Store workflow ID in memory for tracking
            repo.add_memory(
                key=f"issue:{issue_id}:workflow_id",
                value=workflow_id,
                category="issue_workflow_mapping",
            )

            # Add start comment
            repo.add_comment(
                issue_id,
                f"🚀 Started workflow `{workflow_id}`",
            )

            return TaskResult.success(
                outputs={
                    "issue_id": issue_id,
                    "workflow_id": workflow_id,
                    "status": "in_progress",
                }
            )

        except ImportError:
            # IssueDB not available - continue without issue tracking
            return TaskResult.success(
                outputs={
                    "issue_id": issue_id,
                    "workflow_id": workflow_id,
                    "status": "in_progress",
                    "warning": "IssueDB not available - skipping issue tracking",
                }
            )
        except Exception as e:
            # Log error but don't fail workflow
            return TaskResult.success(
                outputs={
                    "issue_id": issue_id,
                    "workflow_id": workflow_id,
                    "status": "in_progress",
                    "warning": f"Failed to update issue: {e}",
                }
            )
