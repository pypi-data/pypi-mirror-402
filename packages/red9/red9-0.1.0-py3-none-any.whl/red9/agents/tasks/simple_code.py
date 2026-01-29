"""Simple code agent task - minimal overhead for simple tasks.

This agent is optimized for tasks like:
- "write a simple fibonacci python app"
- "create hello world"
- "fix typo in file X"

No exploration, no architecture analysis, no reviews.
Just: read request → write code → verify → done.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from stabilize import Task, TaskResult
from stabilize.errors import PermanentError
from stabilize.models.stage import StageExecution

from red9.agents.loop import AgentLoop
from red9.errors import is_transient_error
from red9.indexing.repomap.generator import RepoMap
from red9.logging import get_logger
from red9.providers.base import LLMProvider
from red9.tools.base import ToolRegistry

logger = get_logger(__name__)

# Direct, action-oriented prompt for simple tasks
SIMPLE_CODE_AGENT_PROMPT = """You are a coding assistant. Your job is to write code directly.

## Context
{context}

## Rules

1. **NO TALK**: Do not explain, analyze, or discuss. Just write code.
2. **NO PREAMBLE**: Do not say "Let me...", "I will...", "Here's my approach...". Just act.
3. **MINIMAL**: Write the simplest code that works. No over-engineering.
4. **SINGLE FILE**: Unless explicitly asked, create ONE file with the complete solution.
5. **RUN IT**: After writing code, run it to verify it works.

## Tools Available

- `write_file`: Create new files
- `read_file`: Read existing files (only if you need to modify something)
- `run_command`: Execute shell commands (CHECK OUTPUT FOR ERRORS!)
- `complete_task`: Call this when done with a summary of what you created

## CRITICAL: Error Handling (MANDATORY)

- **CHECK TOOL RESULTS**: After every tool call, examine the result for "Error:" or failure
- If you see "Error:" in any tool result, DO NOT call complete_task
- Instead, investigate and fix the error
- If a command times out, try a different approach:
  - Use shorter timeout: `timeout 5 cmd || echo "failed"`
  - Run as background: `cmd &` then verify file/output exists
  - Skip long-running servers - just verify the code is syntactically correct
- **NEVER claim success if tools failed** - this is a hard requirement
- The system will BLOCK your complete_task call if there are unresolved errors

## Timeouts

- Default command timeout is 30 seconds
- For web servers, DON'T start them - just verify code with: `python3 -m py_compile app.py`
- For long commands, use: `timeout 5 cmd || true`

## Example Workflow

For "write a fibonacci program":
1. write_file("fibonacci.py", "def fib(n): ...")
2. run_command("python3 fibonacci.py 10") → CHECK OUTPUT
3. If success → complete_task(summary="Created fibonacci.py")
4. If error → fix it, re-run, then complete_task

For "write a Flask/Falcon web app":
1. write_file("app.py", "...")
2. run_command("python3 -m py_compile app.py") → verify syntax
3. complete_task(summary="Created app.py - run with: python3 app.py")

## Current Task

Implement the request below. Be direct. Be minimal. Be fast.
"""


class SimpleCodeAgentTask(Task):
    """Simple code agent that implements changes with minimal overhead.

    Optimized for:
    - Single-file tasks
    - Clear, simple requirements
    - No need for exploration or analysis
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        rag_assistant: Any | None = None,
    ) -> None:
        """Initialize simple code agent task.

        Args:
            provider: LLM provider for agent execution.
            tool_registry: Registry of available tools.
            rag_assistant: Optional Ragit RAGAssistant (usually not needed for simple tasks).
        """
        self.provider = provider
        self.tools = tool_registry
        self.rag = rag_assistant

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the simple code agent.

        Args:
            stage: Stage execution context with request.

        Returns:
            TaskResult with created files or error.
        """
        from red9.workflows.runner import emit_phase_start

        # Emit phase start for UI
        emit_phase_start(stage)

        request = stage.context.get("request", "")
        project_root = stage.context.get("project_root")
        mentioned_files = stage.context.get("mentioned_files", [])

        if not request:
            return TaskResult.terminal(error="request is required in stage context")

        try:
            # Build Context
            context_str = ""
            project_path = Path(project_root) if project_root else Path.cwd()

            if mentioned_files:
                # 1. Read explicitly mentioned files
                context_parts = []
                for file_path in mentioned_files:
                    try:
                        full_path = project_path / file_path
                        if full_path.exists() and full_path.is_file():
                            content = full_path.read_text()
                            context_parts.append(f"File: {file_path}\n```\n{content}\n```")
                    except Exception as e:
                        logger.warning(f"Failed to read mentioned file {file_path}: {e}")

                if context_parts:
                    context_str = "\n".join(context_parts)
                    logger.info(f"Loaded {len(context_parts)} mentioned files into context")

            if not context_str:
                # 2. Fallback to sparse repo map
                try:
                    repo_map = RepoMap(project_path, max_tokens=2048).generate()
                    context_str = f"Repository Structure:\n{repo_map}"
                    logger.info("Generated sparse repo map for context")
                except Exception as e:
                    logger.warning(f"Failed to generate repo map: {e}")
                    context_str = "No repository context available."

            # Format system prompt
            system_prompt = SIMPLE_CODE_AGENT_PROMPT.format(context=context_str)

            # Get streaming callback
            from red9.workflows.runner import get_stream_callback, get_ui_event_callback

            on_token = stage.context.get("on_token") or get_stream_callback()
            on_ui_event = stage.context.get("on_ui_event") or get_ui_event_callback()

            # Create minimal agent loop
            agent = AgentLoop(
                provider=self.provider,
                tool_registry=self.tools,
                max_iterations=15,  # Lower limit for simple tasks
                enable_loop_detection=True,
                enable_compression=False,  # No compression needed for short tasks
            )

            # Run the agent with direct prompt
            result = agent.run(
                system_prompt=system_prompt,
                user_message=request,
                context=None,  # Already injected into system prompt
                error_history=None,
                on_token=on_token,
                on_ui_event=on_ui_event,
            )

            if not result.success:
                return TaskResult.terminal(error=result.error or "Simple code agent failed")

            logger.info(
                f"Simple task completed: {len(result.files_modified)} files, "
                f"{result.tool_calls_made} tool calls"
            )

            return TaskResult.success(
                outputs={
                    "files_modified": result.files_modified,
                    "summary": result.final_message,
                    "tool_calls_made": result.tool_calls_made,
                }
            )

        except Exception as e:
            if is_transient_error(e):
                from stabilize.errors import TransientError

                raise TransientError(
                    f"Simple code agent transient error: {e}",
                    retry_after=5,
                    cause=e,
                ) from e

            raise PermanentError(f"Simple code agent error: {e}", cause=e) from e
