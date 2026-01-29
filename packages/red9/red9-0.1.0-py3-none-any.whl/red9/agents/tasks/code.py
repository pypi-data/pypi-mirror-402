"""Code agent task - implements code changes.

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
from red9.agents.prompts import get_agent_prompt
from red9.errors import is_transient_error
from red9.files.backup import BackupManager
from red9.logging import get_logger
from red9.providers.base import LLMProvider
from red9.tools.base import ToolRegistry

logger = get_logger(__name__)


class CodeAgentTask(Task):
    """Code agent that implements code changes.

    This is a Stabilize Task that:
    1. Creates backup of files before modification
    2. Loads project guidelines from IssueDB
    3. Runs the code agent loop with specialized persona
    4. Returns list of modified files
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        rag_assistant: Any | None = None,
    ) -> None:
        """Initialize code agent task.

        Args:
            provider: LLM provider for agent execution.
            tool_registry: Registry of available tools.
            rag_assistant: Optional Ragit RAGAssistant for semantic search.
        """
        self.provider = provider
        self.tools = tool_registry
        self.rag = rag_assistant

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the code agent.

        Args:
            stage: Stage execution context with file path and request.

        Returns:
            TaskResult with modified files or error.
        """
        request = stage.context.get("request", "")
        file_path = stage.context.get("file_path")
        issue_id = stage.context.get("issue_id")
        workflow_id = stage.context.get("workflow_id", "default")
        project_root = stage.context.get("project_root")

        # Persona selection (default to general)
        persona = stage.context.get("persona", "general")

        # Get error history for retry context
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

            # Create backup manager
            backup_manager = BackupManager(root, workflow_id)

            # Initialize Notepad
            notepad = Notepad(root, workflow_id)

            # Backup target file if it exists
            if file_path:
                target = Path(file_path)
                if target.exists():
                    backup_manager.backup(target)

            # Load project guidelines from IssueDB (ON-DEMAND)
            guidelines = load_agent_context(
                db_path,
                categories=["conventions", "architecture"],
            )
            guidelines_text = format_guidelines(guidelines)

            # Get Notepad Wisdom
            wisdom_text = notepad.get_summary()

            # Get relevant code context from RAG
            rag_context = ""
            if self.rag:
                try:
                    query = f"{request} {file_path}" if file_path else request
                    rag_context = self.rag.get_context(query, top_k=3)
                except Exception as e:
                    logger.warning(f"Failed to get RAG context: {e}")

            # Build full context
            context_parts = []
            if guidelines_text:
                context_parts.append(guidelines_text)
            if wisdom_text:
                context_parts.append(wisdom_text)
            if rag_context:
                context_parts.append(f"## Relevant Code\n\n{rag_context}")

            full_context = "\n\n".join(context_parts) if context_parts else None

            # Create agent loop
            agent = AgentLoop(
                provider=self.provider,
                tool_registry=self.tools,
                max_iterations=60,
            )

            # Build user message
            if file_path:
                user_message = f"Implement the following changes to {file_path}:\n\n{request}"
            else:
                user_message = f"Implement the following changes:\n\n{request}"

            # Run the agent with error history for retry awareness
            # Use dynamic prompt based on persona
            system_prompt = get_agent_prompt("code", persona=persona)

            # Get streaming callback from context or module-level registry
            from red9.workflows.runner import get_stream_callback

            on_token = stage.context.get("on_token") or get_stream_callback()

            result = agent.run(
                system_prompt=system_prompt,
                user_message=user_message,
                context=full_context,
                error_history=error_history if error_history else None,
                on_token=on_token,
            )

            if not result.success:
                # Restore from backup on failure
                backup_manager.restore_all()

                # Log failure to notepad
                notepad.add_entry(
                    "issue", f"Failed to implement {request}: {result.error}", "CodeAgent"
                )

                # Add comment to issue
                self._add_issue_comment(
                    db_path,
                    issue_id,
                    f"❌ Code agent failed on {file_path or 'task'}: {result.error}",
                )
                return TaskResult.terminal(error=result.error or "Code agent failed")

            # Capture learnings
            # In a real scenario, we'd ask the agent to output learnings explicitly.
            # For now, we just log success.
            notepad.add_entry("learning", f"Successfully implemented: {request}", "CodeAgent")

            # Add progress comment to issue
            files_list = (
                ", ".join(result.files_modified) if result.files_modified else "No files modified"
            )
            msg_preview = result.final_message[:300]
            comment = f"✅ Code changes complete:\n\n**Files:** {files_list}\n\n{msg_preview}..."
            self._add_issue_comment(db_path, issue_id, comment)

            return TaskResult.success(
                outputs={
                    "files_modified": result.files_modified,
                    "summary": result.final_message,
                    "tool_calls_made": result.tool_calls_made,
                    "backup_dir": str(backup_manager.backup_dir),
                }
            )

        except Exception as e:
            # Handle transient errors with error history for context-aware retries
            if is_transient_error(e):
                return handle_transient_error(e, error_history, agent_name="Code agent")

            # Permanent errors fail immediately
            raise PermanentError(f"Code agent error: {e}", cause=e)

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
