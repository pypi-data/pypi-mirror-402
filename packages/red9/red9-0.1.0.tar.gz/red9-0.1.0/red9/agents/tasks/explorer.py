"""Explorer Agent Task - Codebase exploration for the enterprise workflow.

Explorers analyze the codebase to find relevant files, trace code flow,
and understand architecture patterns. Multiple explorers run in parallel
with different focus areas (architecture, UX, tests).

This is a Stabilize Task that can be executed as an independent stage.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from stabilize import Task, TaskResult
from stabilize.models.stage import StageExecution

from red9.agents.error_handler import handle_transient_error
from red9.agents.loop import AgentLoop
from red9.agents.personas.explorer import get_explorer_persona
from red9.errors import is_transient_error
from red9.logging import get_logger
from red9.workflows.schemas import EXPLORATION_OUTPUT_SCHEMA, validate_output

if TYPE_CHECKING:
    from red9.providers.base import LLMProvider
    from red9.tools.base import ToolRegistry

logger = get_logger(__name__)


class ExplorerAgentTask(Task):
    """Explorer agent task for codebase analysis.

    Explorers are read-only agents that find relevant files and patterns.
    They run in parallel during the exploration phase.

    Expected context:
        - project_root: Project root path
        - request: User's original request
        - focus: Explorer focus area ("architecture", "ux", "tests")
        - workflow_id: Workflow identifier

    Outputs:
        - essential_files: List of {path, reason} dicts
        - patterns_found: Design patterns observed
        - summary: Analysis summary
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
    ) -> None:
        """Initialize explorer task.

        Args:
            provider: LLM provider for generation.
            tool_registry: Tool registry (will be filtered to read-only).
        """
        self.provider = provider
        self.tools = tool_registry

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute explorer analysis.

        Args:
            stage: Stage execution context.

        Returns:
            TaskResult with exploration findings.
        """
        from red9.workflows.runner import emit_phase_start

        # Emit phase start for UI
        emit_phase_start(stage)

        # Extract context
        project_root = stage.context.get("project_root")
        request = stage.context.get("request", "")
        focus = stage.context.get("focus", "architecture")

        if not project_root:
            return TaskResult.terminal(error="project_root is required")

        # Get the explorer persona for this focus area
        try:
            persona = get_explorer_persona(focus)
        except ValueError as e:
            return TaskResult.terminal(error=str(e))

        logger.info(f"Explorer ({focus}) starting analysis for: {request[:50]}...")

        # Get callbacks for UI events
        from red9.workflows.runner import get_stream_callback, get_ui_event_callback

        on_token = stage.context.get("on_token") or get_stream_callback()
        on_ui_event = stage.context.get("on_ui_event") or get_ui_event_callback()

        # Emit agent start event
        if on_ui_event:
            on_ui_event(
                {
                    "type": "agent_start",
                    "agent_id": f"explorer_{focus}",
                    "role": f"Explorer ({focus})",
                    "focus": focus,
                }
            )

        try:
            # Build user message
            user_message = f"""# Task Request

{request}

## Your Assignment

Explore the codebase from a {focus} perspective.

Find and document:
1. **Essential Files**: Files directly relevant to this task
2. **Related Files**: Supporting files that may need attention
3. **Patterns Found**: Design patterns and conventions observed
4. **Risks**: Potential issues or complications

Output your findings as JSON with this structure:
```json
{{
  "essential_files": [
    {{"path": "path/to/file.py", "reason": "Why this file is essential"}}
  ],
  "patterns_found": ["pattern1", "pattern2"],
  "summary": "Overall analysis summary"
}}
```
"""

            # Create agent loop with limited tools
            agent_loop = AgentLoop(
                provider=self.provider,
                tool_registry=self._get_filtered_registry(persona.allowed_tools),
                max_iterations=persona.max_iterations,
                parallel_tool_execution=True,
                max_parallel_tools=4,
                enable_loop_detection=True,
            )

            # Run the agent
            result = agent_loop.run(
                system_prompt=persona.system_prompt,
                user_message=user_message,
                on_token=on_token,
                on_ui_event=on_ui_event,
            )

            # Parse the result
            output = self._parse_explorer_output(result.final_message)

            # Validate against schema
            is_valid, errors = validate_output(output, EXPLORATION_OUTPUT_SCHEMA)
            if not is_valid:
                logger.warning(f"Explorer output validation failed: {errors}")
                # Continue anyway with partial output

            # Emit agent end event
            if on_ui_event:
                on_ui_event(
                    {
                        "type": "agent_end",
                        "agent_id": f"explorer_{focus}",
                        "success": result.success,
                    }
                )

                # Emit essential files event
                if output.get("essential_files"):
                    on_ui_event(
                        {
                            "type": "essential_files",
                            "files": output["essential_files"],
                        }
                    )

            files_count = len(output.get("essential_files", []))
            logger.info(f"Explorer ({focus}) completed: found {files_count} files")

            # Build output compatible with swarm_aggregator
            # The aggregator expects agent_result with SwarmAgentResult format
            role_map = {
                "architecture": "explorer_architecture",
                "ux": "explorer_ux",
                "tests": "explorer_tests",
            }
            agent_result = {
                "agent_config": {
                    "role": role_map.get(focus, f"explorer_{focus}"),
                    "focus": f"Explore codebase from {focus} perspective",
                    "system_prompt_extension": "",
                },
                "output": json.dumps(output),
                "success": result.success,
                "error": None,
                "files_modified": [],
                "files_read": [
                    f.get("path", f) if isinstance(f, dict) else f
                    for f in output.get("essential_files", [])
                ],
                "confidence": 80.0,
            }

            return TaskResult.success(
                outputs={
                    "focus": focus,
                    "essential_files": output.get("essential_files", []),
                    "patterns_found": output.get("patterns_found", []),
                    "summary": output.get("summary", ""),
                    "success": result.success,
                    "agent_result": agent_result,  # For swarm_aggregator compatibility
                }
            )

        except Exception as e:
            if is_transient_error(e):
                return handle_transient_error(e, [], agent_name=f"Explorer:{focus}")

            logger.exception(f"Explorer ({focus}) crashed: {e}")

            # Emit failure event
            if on_ui_event:
                on_ui_event(
                    {
                        "type": "agent_end",
                        "agent_id": f"explorer_{focus}",
                        "success": False,
                    }
                )

            return TaskResult.failed_continue(
                error=f"Explorer ({focus}) crashed: {e}",
                outputs={
                    "focus": focus,
                    "essential_files": [],
                    "patterns_found": [],
                    "summary": "",
                    "success": False,
                    "error": str(e),
                },
            )

    def _get_filtered_registry(self, allowed_tools: list[str]) -> ToolRegistry:
        """Get a filtered tool registry with only allowed tools.

        Args:
            allowed_tools: List of allowed tool names.

        Returns:
            Filtered tool registry.
        """
        return self.tools.filter(allowed_tools)

    def _parse_explorer_output(self, message: str) -> dict[str, Any]:
        """Parse explorer output to extract structured data.

        Args:
            message: Raw message from the explorer agent.

        Returns:
            Structured output dictionary.
        """
        # Try to extract JSON from the message
        try:
            # Look for JSON in code blocks
            if "```json" in message:
                json_str = message.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in message:
                # Try any code block
                json_str = message.split("```")[1].split("```")[0].strip()
                if json_str.startswith("{"):
                    return json.loads(json_str)
            # Try parsing the whole message as JSON
            if message.strip().startswith("{"):
                return json.loads(message.strip())
        except (json.JSONDecodeError, IndexError):
            pass

        # Fallback: extract files mentioned in the message
        essential_files = []
        for line in message.split("\n"):
            # Look for file paths
            if "/" in line or ".py" in line or ".ts" in line or ".js" in line:
                # Simple heuristic to extract file paths
                parts = line.split()
                for part in parts:
                    is_path = "/" in part or part.endswith((".py", ".ts", ".js", ".tsx", ".jsx"))
                    if is_path and not part.startswith("http"):
                        # Clean up the path
                        path = part.strip("`,\"'()[]")
                        if path and not path.startswith("#"):
                            file_info = {"path": path, "reason": "Mentioned in analysis"}
                            essential_files.append(file_info)

        return {
            "essential_files": essential_files[:20],  # Limit to 20 files
            "patterns_found": [],
            "summary": message[:500] if message else "",
        }
