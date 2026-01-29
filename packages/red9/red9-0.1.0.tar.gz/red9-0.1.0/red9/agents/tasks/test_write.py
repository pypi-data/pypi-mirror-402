"""Test write agent task - writes tests FIRST following TDD.

Uses error history context for intelligent retry behavior.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from stabilize import Task, TaskResult
from stabilize.errors import PermanentError
from stabilize.models.stage import StageExecution

from red9.agents.error_handler import get_error_history, handle_transient_error
from red9.agents.loop import AgentLoop, format_guidelines, load_agent_context
from red9.agents.notepad import Notepad
from red9.agents.prompts import TEST_WRITE_AGENT_SYSTEM_PROMPT
from red9.errors import is_transient_error
from red9.logging import get_logger
from red9.providers.base import LLMProvider
from red9.tools.base import ToolRegistry

logger = get_logger(__name__)


class TestWriteAgentTask(Task):
    """Test write agent that creates tests FIRST (TDD approach).

    This is a Stabilize Task that:
    1. Analyzes the request and plan
    2. Determines appropriate test framework (pytest, jest, go test, etc.)
    3. Writes comprehensive tests BEFORE implementation
    4. Tests should initially fail (red phase of TDD)

    The goal is to define the expected behavior through tests,
    which the code agent will then implement to pass.
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        rag_assistant: Any | None = None,
    ) -> None:
        """Initialize test write agent task.

        Args:
            provider: LLM provider for agent execution.
            tool_registry: Registry of available tools.
            rag_assistant: Optional Ragit RAGAssistant for semantic search.
        """
        self.provider = provider
        self.tools = tool_registry
        self.rag = rag_assistant

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the test write agent.

        Args:
            stage: Stage execution context with request and plan.

        Returns:
            TaskResult with test files created or error.
        """
        request = stage.context.get("request", "")
        issue_id = stage.context.get("issue_id")
        workflow_id = stage.context.get("workflow_id", "default")
        project_root = stage.context.get("project_root")
        error_history = get_error_history(stage.context)

        if not request:
            return TaskResult.terminal(error="request is required in stage context")

        try:
            # Determine paths
            if project_root:
                root = Path(project_root)
                db_path = str(root / ".red9" / ".issue.db")
            else:
                root = Path.cwd()
                db_path = ".red9/.issue.db"

            # Initialize Notepad
            notepad = Notepad(root, workflow_id)

            # Load project guidelines from IssueDB (ON-DEMAND)
            guidelines = load_agent_context(
                db_path,
                categories=["conventions", "testing", "workflow"],
            )
            guidelines_text = format_guidelines(guidelines)

            # Get Notepad Wisdom
            wisdom_text = notepad.get_summary()

            # Get relevant code context from RAG
            rag_context = ""
            if self.rag:
                try:
                    rag_context = self.rag.get_context(f"tests for: {request}", top_k=5)
                except Exception as e:
                    logger.warning(f"Failed to get RAG context: {e}")

            # Build full context
            context_parts = []
            if guidelines_text:
                context_parts.append(guidelines_text)
            if wisdom_text:
                context_parts.append(wisdom_text)
            if rag_context:
                context_parts.append(f"## Existing Code Context\n\n{rag_context}")

            full_context = "\n\n".join(context_parts) if context_parts else None

            # Create agent loop
            agent = AgentLoop(
                provider=self.provider,
                tool_registry=self.tools,
                max_iterations=50,
            )

            # Build user message for test writing
            user_message = f"""Write tests FIRST for the following requirement (TDD approach):

{request}

IMPORTANT:
1. First, analyze the project to determine the appropriate test framework
   - For Python: use pytest
   - For JavaScript/TypeScript: use jest or vitest
   - For Go: use go test
   - For Rust: use cargo test
   - etc.

2. Create comprehensive test files that:
   - Test all expected functionality
   - Include edge cases
   - Test error conditions
   - Follow the project's existing test patterns if any

3. The tests should define the EXPECTED BEHAVIOR
   - They may fail initially (this is expected in TDD)
   - The code agent will implement code to make them pass

4. After writing tests, call complete_task with a summary of tests created."""

            # Get streaming callback from context or module-level registry
            from red9.workflows.runner import get_stream_callback

            on_token = stage.context.get("on_token") or get_stream_callback()

            # Run the agent
            result = agent.run(
                system_prompt=TEST_WRITE_AGENT_SYSTEM_PROMPT,
                user_message=user_message,
                context=full_context,
                error_history=error_history if error_history else None,
                on_token=on_token,
            )

            if not result.success:
                # Log failure to notepad
                notepad.add_entry("issue", f"Test write failed: {result.error}", "TestWriteAgent")

                self._add_issue_comment(
                    db_path,
                    issue_id,
                    f"❌ Test write agent failed: {result.error}",
                )
                return TaskResult.terminal(error=result.error or "Test write agent failed")

            # Capture success in notepad
            notepad.add_entry(
                "learning", f"Tests written: {', '.join(result.files_modified)}", "TestWriteAgent"
            )

            # Add progress comment to issue
            files_list = (
                ", ".join(result.files_modified)
                if result.files_modified
                else "No test files created"
            )
            msg_preview = result.final_message[:300]
            comment = f"✅ Tests written (TDD):\n\n**Test Files:** {files_list}\n\n{msg_preview}..."
            self._add_issue_comment(db_path, issue_id, comment)

            return TaskResult.success(
                outputs={
                    "test_files_created": result.files_modified,
                    "summary": result.final_message,
                    "tool_calls_made": result.tool_calls_made,
                }
            )

        except Exception as e:
            # Transient errors are retried with error history context
            if is_transient_error(e):
                return handle_transient_error(e, error_history, agent_name="TestWrite agent")
            # Permanent errors fail immediately
            raise PermanentError(f"Test write agent error: {e}", cause=e)

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
