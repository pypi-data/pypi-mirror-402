"""Test agent task - runs tests and validates changes.

Uses error history context for intelligent retry behavior.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from stabilize import Task, TaskResult
from stabilize.errors import PermanentError
from stabilize.models.stage import StageExecution

from red9.agents.error_handler import get_error_history, handle_transient_error
from red9.agents.loop import (
    AgentLoop,
    AgentResult,
    format_guidelines,
    load_agent_context,
)
from red9.agents.prompts import TEST_AGENT_SYSTEM_PROMPT
from red9.errors import is_transient_error
from red9.logging import get_logger
from red9.providers.base import LLMProvider
from red9.tools.base import ToolRegistry

logger = get_logger(__name__)


class TestAgentTask(Task):
    """Test agent that runs tests and validates changes.

    This is a Stabilize Task that:
    1. Identifies relevant test files
    2. Runs the test suite
    3. Analyzes and reports results
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        rag_assistant: Any | None = None,
    ) -> None:
        """Initialize test agent task.

        Args:
            provider: LLM provider for agent execution.
            tool_registry: Registry of available tools.
            rag_assistant: Optional Ragit RAGAssistant (not used for testing).
        """
        self.provider = provider
        self.tools = tool_registry
        self.rag = rag_assistant

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the test agent.

        Args:
            stage: Stage execution context with request info.

        Returns:
            TaskResult with test results or error.
        """
        _request = stage.context.get("request", "")  # noqa: F841 - may be used later
        issue_id = stage.context.get("issue_id")
        project_root = stage.context.get("project_root")
        error_history = get_error_history(stage.context)

        # Get files modified from upstream stages (via context propagation)
        files_modified = stage.context.get("files_modified", [])

        try:
            # Determine paths
            if project_root:
                root = Path(project_root)
                db_path = str(root / ".red9" / ".issue.db")
            else:
                root = Path.cwd()
                db_path = ".red9/.issue.db"

            # Load project guidelines (specifically testing requirements)
            guidelines = load_agent_context(
                db_path,
                categories=["workflow", "conventions"],
            )
            guidelines_text = format_guidelines(guidelines)

            # Build context
            context_parts = []
            if guidelines_text:
                context_parts.append(guidelines_text)
            if files_modified:
                files_list = "\n".join(f"- {f}" for f in files_modified)
                context_parts.append(f"## Files Modified\n\n{files_list}")

            full_context = "\n\n".join(context_parts) if context_parts else None

            # Create agent loop
            agent = AgentLoop(
                provider=self.provider,
                tool_registry=self.tools,
                max_iterations=20,
            )

            # Build user message
            user_message = "Run the test suite and report the results."
            if files_modified:
                user_message += "\n\nFocus on tests related to these modified files:\n"
                user_message += "\n".join(f"- {f}" for f in files_modified)

            # Get streaming callback from context or module-level registry
            from red9.workflows.runner import get_stream_callback

            on_token = stage.context.get("on_token") or get_stream_callback()

            # Run the agent
            result = agent.run(
                system_prompt=TEST_AGENT_SYSTEM_PROMPT,
                user_message=user_message,
                context=full_context,
                error_history=error_history if error_history else None,
                on_token=on_token,
            )

            # Extract test results
            tests_passed = self._extract_test_status(result)

            # Add progress comment to issue
            if tests_passed:
                comment = f"✅ Tests passed:\n\n{result.final_message[:300]}..."
            else:
                comment = f"❌ Tests failed:\n\n{result.final_message[:500]}..."

            self._add_issue_comment(db_path, issue_id, comment)

            if not result.success:
                return TaskResult.terminal(error=result.error or "Test agent failed")

            return TaskResult.success(
                outputs={
                    "tests_passed": tests_passed,
                    "summary": result.final_message,
                    "tool_calls_made": result.tool_calls_made,
                }
            )

        except Exception as e:
            # Transient errors are retried with error history context
            if is_transient_error(e):
                return handle_transient_error(e, error_history, agent_name="Test agent")
            # Permanent errors fail immediately
            raise PermanentError(f"Test agent error: {e}", cause=e)

    def _extract_test_status(self, result: AgentResult) -> bool:
        """Extract whether tests passed from agent result.

        Args:
            result: Agent execution result.

        Returns:
            True if tests passed, False otherwise.
        """
        # Check outputs first
        if "tests_passed" in result.outputs:
            return bool(result.outputs["tests_passed"])

        # Check final message for indicators
        message_lower = result.final_message.lower()

        # Positive indicators
        if any(
            phrase in message_lower
            for phrase in [
                "all tests pass",
                "tests passed",
                "100% pass",
                "no failures",
                "0 failed",
            ]
        ):
            return True

        # Negative indicators
        if any(
            phrase in message_lower
            for phrase in [
                "test failed",
                "tests failed",
                "failure",
                "error in test",
            ]
        ):
            return False

        # Default to success if agent completed without error
        return result.success

    def _add_issue_comment(
        self,
        db_path: str,
        issue_id: int | None,
        comment: str,
    ) -> None:
        """Add a comment to the issue.

        Args:
            db_path: Path to IssueDB database.
            issue_id: Issue ID (optional).
            comment: Comment text.
        """
        if not issue_id:
            return

        try:
            from issuedb.repository import IssueRepository

            repo = IssueRepository(db_path=db_path)
            repo.add_comment(issue_id, comment)
        except Exception as e:
            logger.warning(f"Failed to add issue comment to issue {issue_id}: {e}")
