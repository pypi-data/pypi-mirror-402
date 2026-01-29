"""Issue complete task - final stage of every workflow."""

from __future__ import annotations

from pathlib import Path

from stabilize import Task, TaskResult
from stabilize.models.stage import StageExecution
from stabilize.models.status import WorkflowStatus

from red9.logging import get_logger

logger = get_logger(__name__)


class IssueCompleteTask(Task):
    """Final stage of every workflow.

    Updates IssueDB issue with results:
    - On success: closes issue, adds summary comment
    - On failure: keeps issue open, adds error comment
    - Captures lessons learned
    """

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the issue completion task.

        Args:
            stage: Stage execution context.

        Returns:
            TaskResult with completion status.
        """
        issue_id = stage.context.get("issue_id")
        workflow_id = stage.context.get("workflow_id")
        project_root = stage.context.get("project_root")

        # Determine actual workflow status by checking upstream stages
        workflow_status, error_message = self._determine_workflow_status(stage)

        # Collect results from upstream stages
        summary = stage.context.get("summary", "")
        files_modified = stage.context.get("files_modified", [])

        if not issue_id:
            return TaskResult.terminal(error="issue_id is required in stage context")

        try:
            # Import IssueDB
            from issuedb.models import LessonLearned
            from issuedb.repository import IssueRepository

            # Determine database path
            if project_root:
                db_path = Path(project_root) / ".red9" / ".issue.db"
            else:
                db_path = Path(".red9/.issue.db")

            repo = IssueRepository(db_path=str(db_path))

            # Get issue details for lesson learned
            issue = repo.get_issue(issue_id)

            if workflow_status == "success":
                # Close the issue (use string value)
                repo.update_issue(issue_id, status="closed")

                # Add completion comment
                files_list = ", ".join(files_modified) if files_modified else "No files modified"
                comment = (
                    f"✅ Completed successfully\n\n"
                    f"**Files modified:** {files_list}\n\n"
                    f"**Summary:** {summary or 'Task completed'}"
                )
                repo.add_comment(issue_id, comment)

                # Capture lesson learned
                if issue:
                    summary_text = summary or "Task completed successfully"
                    lesson_text = f"Completed: {issue.title[:80]} - {summary_text}"
                    repo.add_lesson(
                        LessonLearned(
                            issue_id=issue_id,
                            lesson=lesson_text[:500],
                            category="completed_tasks",
                        )
                    )

                return TaskResult.success(
                    outputs={
                        "issue_id": issue_id,
                        "workflow_id": workflow_id,
                        "status": "closed",
                        "files_modified": files_modified,
                    }
                )

            else:
                # Keep issue open with error comment
                error_detail = error_message or summary or "Unknown error"
                comment = f"❌ Workflow failed\n\n**Error:** {error_detail}"
                repo.add_comment(issue_id, comment)

                return TaskResult.success(
                    outputs={
                        "issue_id": issue_id,
                        "workflow_id": workflow_id,
                        "status": "failed",
                        "error": error_detail,
                    }
                )

        except ImportError:
            # IssueDB not available - continue without issue tracking
            return TaskResult.success(
                outputs={
                    "issue_id": issue_id,
                    "workflow_id": workflow_id,
                    "status": workflow_status,
                    "warning": "IssueDB not available - skipping issue update",
                }
            )
        except Exception as e:
            # Log error but don't fail workflow
            return TaskResult.success(
                outputs={
                    "issue_id": issue_id,
                    "workflow_id": workflow_id,
                    "status": workflow_status,
                    "warning": f"Failed to update issue: {e}",
                }
            )

    def _determine_workflow_status(self, stage: StageExecution) -> tuple[str, str | None]:
        """Determine actual workflow status by checking upstream stages.

        Checks the execution's stages for any failures. This is more reliable
        than relying on context values that may not be set.

        Args:
            stage: Current stage execution.

        Returns:
            Tuple of (status, error_message) where status is "success" or "failed".
        """
        # Check if there's an exception in context (set by Stabilize on errors)
        exception_info = stage.context.get("exception")
        if exception_info:
            error_details = exception_info.get("details", {})
            error_msg = error_details.get("error", "Unknown error")
            logger.info(f"Found exception in context: {error_msg}")
            return "failed", error_msg

        # Check upstream stages via the execution object
        execution = stage.execution
        if execution is None:
            logger.warning("No execution object available, assuming success")
            return "success", None

        # Get all stages from the execution
        stages = getattr(execution, "stages", [])
        if not stages:
            logger.warning("No stages found in execution, assuming success")
            return "success", None

        # Check for failed stages (excluding the current 'complete' stage)
        failed_statuses = {
            WorkflowStatus.TERMINAL,
            WorkflowStatus.STOPPED,
            WorkflowStatus.CANCELED,
        }

        for s in stages:
            if s.ref_id == stage.ref_id:
                continue  # Skip current stage

            if s.status in failed_statuses:
                # Extract error from the failed stage's context
                stage_exception = s.context.get("exception", {})
                error_details = stage_exception.get("details", {})
                error_msg = error_details.get("error", f"Stage {s.name} failed")
                logger.info(f"Found failed stage {s.name}: {error_msg}")
                return "failed", error_msg

        # Also check for FAILED_CONTINUE status (partial failure)
        for s in stages:
            if s.ref_id == stage.ref_id:
                continue
            if s.status == WorkflowStatus.FAILED_CONTINUE:
                stage_exception = s.context.get("exception", {})
                error_details = stage_exception.get("details", {})
                error_msg = error_details.get("error", f"Stage {s.name} had errors")
                logger.info(f"Found stage with errors {s.name}: {error_msg}")
                return "failed", error_msg

        logger.info("All upstream stages succeeded")
        return "success", None
