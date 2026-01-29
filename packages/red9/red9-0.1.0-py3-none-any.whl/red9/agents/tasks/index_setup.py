"""Index setup task - ensures RAG index is ready before other stages."""

from __future__ import annotations

from pathlib import Path

from stabilize import Task, TaskResult
from stabilize.models.stage import StageExecution

from red9.config import load_config
from red9.indexing import IndexManager
from red9.logging import get_logger

logger = get_logger(__name__)


class IndexSetupTask(Task):
    """First stage of the workflow - ensures RAG index is ready.

    This task:
    1. Loads configuration and creates IndexManager
    2. Checks for file changes using IndexTracker
    3. Loads RAG assistant from cache (fast) or builds it (slow)
    4. Makes rag_ready status available via stage outputs
    """

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the index setup task.

        Args:
            stage: Stage execution context.

        Returns:
            TaskResult with index setup status.
        """
        project_root_str = stage.context.get("project_root")
        workflow_id = stage.context.get("workflow_id")

        if not project_root_str:
            logger.error("IndexSetupTask: project_root is required")
            return TaskResult.terminal(error="project_root is required in stage context")

        project_root = Path(project_root_str)

        try:
            # Load configuration
            config = load_config(project_root)

            # Create index manager
            index_manager = IndexManager(project_root, config)

            # Check what files changed
            needs_update, added, modified, deleted = index_manager.needs_update()
            if needs_update:
                logger.info(f"Index needs update: +{added} ~{modified} -{deleted} files")
            else:
                logger.info("No file changes detected")

            # Load or build RAG assistant (uses cache if available)
            rag_assistant = index_manager.get_rag_assistant(provider=None)

            rag_ready = rag_assistant is not None
            if rag_ready:
                logger.info("RAG assistant ready")
            else:
                last_error = index_manager.get_last_error()
                logger.warning(f"RAG not available: {last_error}")

            return TaskResult.success(
                outputs={
                    "rag_ready": rag_ready,
                    "files_indexed": index_manager.tracker.get_indexed_count(),
                    "needs_update": needs_update,
                    "workflow_id": workflow_id,
                    "last_error": index_manager.get_last_error() if not rag_ready else None,
                }
            )

        except ImportError as e:
            # ragit or other dependency not available
            logger.warning(f"RAG dependencies not available: {e}")
            return TaskResult.success(
                outputs={
                    "rag_ready": False,
                    "files_indexed": 0,
                    "needs_update": False,
                    "warning": f"RAG dependencies not available: {e}",
                }
            )
        except Exception as e:
            # Log error but don't fail workflow - RAG is optional
            logger.exception(f"Index setup failed: {e}")
            return TaskResult.success(
                outputs={
                    "rag_ready": False,
                    "files_indexed": 0,
                    "needs_update": False,
                    "warning": f"Index setup failed: {e}",
                }
            )
