"""Documentation Sync Task - Phase 3 of the Workflow.

Responsible for:
1. Finalizing the task.
2. Reporting results.
"""

from __future__ import annotations

from stabilize import Task, TaskResult
from stabilize.models.stage import StageExecution

from red9.logging import get_logger
from red9.providers.base import LLMProvider
from red9.tools.base import ToolRegistry

logger = get_logger(__name__)

DOCS_AGENT_SYSTEM_PROMPT = """You are the Documentation Sync Agent.

Your goal is to finalize the task.

## Your Tasks
1. Summarize what was accomplished.
2. Call complete_task.
"""


class DocSyncTask(Task):
    """Phase 3: Sync & Commit."""

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
    ) -> None:
        self.provider = provider
        self.tools = tool_registry

    def execute(self, stage: StageExecution) -> TaskResult:
        logger.info("DocSyncTask: Finalizing task...")

        return TaskResult.success(outputs={"summary": "Task completed successfully."})
