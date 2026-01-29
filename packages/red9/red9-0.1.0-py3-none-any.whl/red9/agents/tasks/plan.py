"""Plan agent task - analyzes request and creates implementation plan.

Uses error history context for intelligent retry behavior.
Outputs structured PlanOutput for downstream stages.
"""

from __future__ import annotations

import re
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
from red9.agents.notepad import Notepad
from red9.agents.prompts import PLAN_AGENT_SYSTEM_PROMPT, QUESTION_AGENT_SYSTEM_PROMPT
from red9.errors import is_transient_error
from red9.logging import get_logger
from red9.providers.base import LLMProvider
from red9.tools.base import ToolRegistry
from red9.workflows.models import PlanOutput, SubTask, SubTaskType

logger = get_logger(__name__)


class PlanAgentTask(Task):
    """Plan agent that analyzes requests and creates implementation plans.

    This is a Stabilize Task that:
    1. Loads project guidelines from IssueDB
    2. Gets relevant code context from RAG
    3. Runs the plan agent loop
    4. Returns structured plan for downstream tasks
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        rag_assistant: Any | None = None,
    ) -> None:
        """Initialize plan agent task.

        Args:
            provider: LLM provider for agent execution.
            tool_registry: Registry of available tools.
            rag_assistant: Optional Ragit RAGAssistant for semantic search.
        """
        self.provider = provider
        self.tools = tool_registry
        self.rag = rag_assistant

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the plan agent.

        Args:
            stage: Stage execution context with request and issue info.

        Returns:
            TaskResult with plan or error.
        """
        request = stage.context.get("request", "")
        issue_id = stage.context.get("issue_id")
        project_root = stage.context.get("project_root")
        workflow_id = stage.context.get("workflow_id", "default")
        is_question = stage.context.get("is_question", False)

        # Get error history for retry context
        error_history = get_error_history(stage.context)

        if not request:
            return TaskResult.terminal(error="request is required in stage context")

        try:
            # Determine database path for guidelines
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
                categories=["conventions", "architecture", "workflow"],
            )
            guidelines_text = format_guidelines(guidelines)

            # Get Notepad Wisdom
            wisdom_text = notepad.get_summary()

            # Get relevant code context from RAG
            rag_context = ""
            if self.rag:
                try:
                    rag_context = self.rag.get_context(request, top_k=5)
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

            # Create agent loop (reduced from 30 to 20 to prevent iteration explosion)
            agent = AgentLoop(
                provider=self.provider,
                tool_registry=self.tools,
                max_iterations=20,
            )

            # Adjust prompt and system prompt for questions vs tasks
            if is_question:
                system_prompt = QUESTION_AGENT_SYSTEM_PROMPT
                user_message = f"Answer this question about the codebase:\n\n{request}"
            else:
                system_prompt = PLAN_AGENT_SYSTEM_PROMPT
                user_message = f"Create an implementation plan for:\n\n{request}"

            # Get streaming callback from context or module-level registry
            from red9.workflows.runner import get_stream_callback

            on_token = stage.context.get("on_token") or get_stream_callback()

            # Run the agent with error history for retry awareness
            result = agent.run(
                system_prompt=system_prompt,
                user_message=user_message,
                context=full_context,
                error_history=error_history if error_history else None,
                on_token=on_token,
            )

            if not result.success:
                # Log failure to notepad
                notepad.add_entry("issue", f"Plan agent failed: {result.error}", "PlanAgent")

                # Add comment to issue if available
                self._add_issue_comment(
                    db_path,
                    issue_id,
                    f"❌ Plan agent failed: {result.error}",
                )
                return TaskResult.terminal(error=result.error or "Plan agent failed")

            # Extract structured plan from result
            plan_output = self._extract_plan(result)

            # Capture success
            notepad.add_entry("decision", f"Plan created: {plan_output.summary}", "PlanAgent")

            # Add progress comment to issue
            self._add_issue_comment(
                db_path,
                issue_id,
                f"📋 Plan created:\n\n{plan_output.summary[:500]}...",
            )

            # Return structured outputs for downstream stages
            return TaskResult.success(
                outputs={
                    "plan": plan_output.to_dict(),
                    "files_to_modify": plan_output.files_to_modify,
                    "files_to_create": plan_output.files_to_create,
                    "test_requirements": plan_output.test_requirements,
                    "sub_tasks": [t.to_dict() for t in plan_output.sub_tasks],
                    "has_parallel_potential": plan_output.has_parallel_potential(),
                    "estimated_complexity": plan_output.estimated_complexity,
                    "summary": plan_output.summary[:500],
                    "tool_calls_made": result.tool_calls_made,
                }
            )

        except Exception as e:
            # Handle transient errors with error history for context-aware retries
            if is_transient_error(e):
                return handle_transient_error(e, error_history, agent_name="Plan agent")

            # Permanent errors fail immediately
            raise PermanentError(f"Plan agent error: {e}", cause=e)

    def _extract_plan(self, result: AgentResult) -> PlanOutput:
        """Extract structured plan from agent result.

        Parses the agent's response to create a typed PlanOutput object
        that downstream stages can use directly.

        Args:
            result: Agent execution result.

        Returns:
            Structured PlanOutput object.
        """
        outputs = result.outputs.copy()
        message = result.final_message or ""

        # Extract file paths from message using patterns
        files_to_modify = outputs.get("files_to_modify", [])
        files_to_create = outputs.get("files_to_create", [])
        files_to_read = outputs.get("files_to_read", [])

        if not files_to_modify:
            files_to_modify = self._extract_file_paths(message, "modify")
        if not files_to_create:
            files_to_create = self._extract_file_paths(message, "create")
        if not files_to_read:
            files_to_read = self._extract_file_paths(message, "read")

        # Extract test requirements
        test_requirements = outputs.get("test_requirements", [])
        if not test_requirements:
            test_requirements = self._extract_test_requirements(message)

        # Determine complexity based on file count and message analysis
        total_files = len(set(files_to_modify + files_to_create))
        if total_files > 10 or "complex" in message.lower():
            complexity = "high"
        elif total_files > 3 or "multiple" in message.lower():
            complexity = "medium"
        else:
            complexity = "low"

        # Create sub-tasks from the plan if decomposition is possible
        sub_tasks = self._extract_sub_tasks(message, files_to_modify)

        return PlanOutput(
            summary=message[:2000] if message else "",
            files_to_modify=files_to_modify[:20],
            files_to_create=files_to_create[:20],
            files_to_read=files_to_read[:20],
            test_requirements=test_requirements[:10],
            sub_tasks=sub_tasks,
            parallel_groups=[],  # Will be populated by decomposition agent if needed
            estimated_complexity=complexity,
            requires_human_review=complexity == "high",
            notes=outputs.get("notes", ""),
        )

    def _extract_file_paths(self, message: str, action: str) -> list[str]:
        """Extract file paths from message text.

        Args:
            message: Message text to parse.
            action: Action type (modify, create, read) for context.

        Returns:
            List of extracted file paths.
        """
        files: list[str] = []

        # Pattern for file paths (with common extensions)
        extensions = r"py|ts|tsx|js|jsx|md|yaml|yml|json|toml|txt|html|css|sql"
        file_pattern = rf"[`'\"]?([a-zA-Z0-9_./-]+\.({extensions}))[`'\"]?"

        for match in re.finditer(file_pattern, message):
            path = match.group(1)
            # Skip common false positives
            if path and not path.startswith("http") and "/" in path:
                if path not in files:
                    files.append(path)

        return files[:20]  # Limit to 20 files

    def _extract_test_requirements(self, message: str) -> list[str]:
        """Extract test requirements from message.

        Args:
            message: Message text to parse.

        Returns:
            List of test requirements.
        """
        requirements: list[str] = []

        # Look for test-related patterns
        test_patterns = [
            r"test\s+(?:that\s+)?(.+?)(?:\.|$)",
            r"verify\s+(?:that\s+)?(.+?)(?:\.|$)",
            r"ensure\s+(?:that\s+)?(.+?)(?:\.|$)",
            r"should\s+(.+?)(?:\.|$)",
        ]

        for pattern in test_patterns:
            for match in re.finditer(pattern, message.lower()):
                req = match.group(1).strip()
                if req and len(req) > 10 and req not in requirements:
                    requirements.append(req[:200])

        return requirements[:10]

    def _extract_sub_tasks(self, message: str, files_to_modify: list[str]) -> list[SubTask]:
        """Extract sub-tasks from plan message.

        Creates individual sub-tasks for each file or logical group.

        Args:
            message: Plan message text.
            files_to_modify: Files that need modification.

        Returns:
            List of SubTask objects.
        """
        sub_tasks: list[SubTask] = []

        # Create a sub-task for each file to modify
        for i, file_path in enumerate(files_to_modify[:10]):
            task_id = f"task_{i + 1}"

            # Determine task type from file extension
            if file_path.endswith(("_test.py", ".test.ts", ".spec.ts", ".test.js")):
                task_type = SubTaskType.TEST_WRITE
            else:
                task_type = SubTaskType.CODE

            sub_tasks.append(
                SubTask(
                    id=task_id,
                    name=f"Modify {Path(file_path).name}",
                    description=f"Apply changes to {file_path}",
                    task_type=task_type,
                    files=[file_path],
                    dependencies=[],  # No dependencies by default
                    priority=len(files_to_modify) - i,  # Earlier files have higher priority
                )
            )

        return sub_tasks

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
