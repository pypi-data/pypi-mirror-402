"""Architect Agent Task - Design decisions for the enterprise workflow.

Architects analyze exploration findings and design implementation approaches.
Multiple architects run in parallel with different philosophies (minimal,
clean, pragmatic), and results are aggregated via voting.

This is a Stabilize Task that can be executed as an independent stage.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from stabilize import Task, TaskResult
from stabilize.models.stage import StageExecution

from red9.agents.error_handler import handle_transient_error
from red9.agents.loop import AgentLoop
from red9.agents.personas.architect import get_architect_persona
from red9.errors import is_transient_error
from red9.logging import get_logger
from red9.workflows.schemas import ARCHITECTURE_OUTPUT_SCHEMA, validate_output

if TYPE_CHECKING:
    from red9.providers.base import LLMProvider
    from red9.tools.base import ToolRegistry

logger = get_logger(__name__)


class ArchitectAgentTask(Task):
    """Architect agent task for design decisions.

    Architects design implementation approaches based on exploration findings.
    They run in parallel with different philosophies and results are aggregated.

    Expected context:
        - project_root: Project root path
        - request: User's original request
        - approach: Architect approach ("minimal", "clean", "pragmatic")
        - exploration_summary: Combined exploration findings
        - workflow_id: Workflow identifier

    Outputs:
        - approach: The approach used ("minimal", "clean", "pragmatic")
        - rationale: Explanation of the design
        - files_to_modify: List of files to change
        - files_to_create: List of files to create
        - estimated_impact: "few", "moderate", or "extensive"
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
    ) -> None:
        """Initialize architect task.

        Args:
            provider: LLM provider for generation (reasoning model recommended).
            tool_registry: Tool registry.
        """
        self.provider = provider
        self.tools = tool_registry

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute architecture design.

        Args:
            stage: Stage execution context.

        Returns:
            TaskResult with architecture proposal.
        """
        from red9.workflows.runner import emit_phase_start

        # Emit phase start for UI
        emit_phase_start(stage)

        # Extract context
        project_root = stage.context.get("project_root")
        request = stage.context.get("request", "")
        approach = stage.context.get("approach", "pragmatic")
        exploration_summary = stage.context.get("exploration_summary", "")
        essential_files = stage.context.get("essential_files", [])

        if not project_root:
            return TaskResult.terminal(error="project_root is required")

        # Get the architect persona for this approach
        try:
            persona = get_architect_persona(approach)
        except ValueError as e:
            return TaskResult.terminal(error=str(e))

        logger.info(f"Architect ({approach}) starting design for: {request[:50]}...")

        # Get callbacks for UI events
        from red9.workflows.runner import get_stream_callback, get_ui_event_callback

        on_token = stage.context.get("on_token") or get_stream_callback()
        on_ui_event = stage.context.get("on_ui_event") or get_ui_event_callback()

        # Emit agent start event
        if on_ui_event:
            on_ui_event(
                {
                    "type": "agent_start",
                    "agent_id": f"architect_{approach}",
                    "role": f"Architect ({approach})",
                    "focus": approach,
                }
            )

        try:
            # Build context from exploration
            files_context = ""
            if essential_files:
                files_list = "\n".join(
                    [
                        f"- {f.get('path', f)}: {f.get('reason', '')}"
                        if isinstance(f, dict)
                        else f"- {f}"
                        for f in essential_files[:20]
                    ]
                )
                files_context = f"\n## Essential Files Identified\n{files_list}\n"

            # Build user message
            user_message = f"""# Task Request

{request}

## Exploration Findings

{exploration_summary or "No exploration summary available."}
{files_context}

## Your Assignment

Design an implementation approach following the {approach.upper()} philosophy.

Provide your design as JSON with this structure:
```json
{{
  "approach": "{approach}",
  "rationale": "Detailed explanation of your design decisions",
  "files_to_modify": ["path/to/existing/file.py"],
  "files_to_create": ["path/to/new/file.py"],
  "key_decisions": ["Decision 1", "Decision 2"],
  "risks": ["Risk 1 with mitigation"],
  "estimated_impact": "few|moderate|extensive"
}}
```

Remember your {approach.upper()} philosophy when making design choices.
"""

            # Create agent loop
            agent_loop = AgentLoop(
                provider=self.provider,
                tool_registry=self.tools,
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
            output = self._parse_architect_output(result.final_message, approach)

            # Validate against schema
            is_valid, errors = validate_output(output, ARCHITECTURE_OUTPUT_SCHEMA)
            if not is_valid:
                logger.warning(f"Architect output validation failed: {errors}")

            # Emit agent end event
            if on_ui_event:
                on_ui_event(
                    {
                        "type": "agent_end",
                        "agent_id": f"architect_{approach}",
                        "success": result.success,
                    }
                )

            logger.info(
                f"Architect ({approach}) completed: "
                f"{len(output.get('files_to_modify', []))} files to modify, "
                f"{len(output.get('files_to_create', []))} files to create"
            )

            # Build output compatible with swarm_aggregator
            role_map = {
                "minimal": "architect_minimal",
                "clean": "architect_clean",
                "pragmatic": "architect_pragmatic",
            }
            agent_result = {
                "agent_config": {
                    "role": role_map.get(approach, f"architect_{approach}"),
                    "focus": f"Design from {approach} perspective",
                    "system_prompt_extension": "",
                },
                "output": json.dumps(output),
                "success": result.success,
                "error": None,
                "files_modified": output.get("files_to_create", []),
                "files_read": output.get("files_to_modify", []),
                "confidence": 80.0,
            }

            return TaskResult.success(
                outputs={
                    "approach": approach,
                    "rationale": output.get("rationale", ""),
                    "files_to_modify": output.get("files_to_modify", []),
                    "files_to_create": output.get("files_to_create", []),
                    "key_decisions": output.get("key_decisions", []),
                    "risks": output.get("risks", []),
                    "estimated_impact": output.get("estimated_impact", "moderate"),
                    "success": result.success,
                    "agent_result": agent_result,  # For swarm_aggregator compatibility
                }
            )

        except Exception as e:
            if is_transient_error(e):
                return handle_transient_error(e, [], agent_name=f"Architect:{approach}")

            logger.exception(f"Architect ({approach}) crashed: {e}")

            # Emit failure event
            if on_ui_event:
                on_ui_event(
                    {
                        "type": "agent_end",
                        "agent_id": f"architect_{approach}",
                        "success": False,
                    }
                )

            return TaskResult.failed_continue(
                error=f"Architect ({approach}) crashed: {e}",
                outputs={
                    "approach": approach,
                    "rationale": "",
                    "files_to_modify": [],
                    "files_to_create": [],
                    "success": False,
                    "error": str(e),
                },
            )

    def _parse_architect_output(self, message: str, approach: str) -> dict[str, Any]:
        """Parse architect output to extract structured data.

        Args:
            message: Raw message from the architect agent.
            approach: The approach being used.

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
                json_str = message.split("```")[1].split("```")[0].strip()
                if json_str.startswith("{"):
                    return json.loads(json_str)
            # Try parsing the whole message as JSON
            if message.strip().startswith("{"):
                return json.loads(message.strip())
        except (json.JSONDecodeError, IndexError):
            pass

        # Fallback: extract information from text
        files_to_modify = []
        files_to_create = []

        for line in message.split("\n"):
            line_lower = line.lower()
            if "modify" in line_lower or "change" in line_lower or "update" in line_lower:
                # Look for file paths
                parts = line.split()
                for part in parts:
                    if "/" in part or part.endswith((".py", ".ts", ".js", ".tsx", ".jsx")):
                        path = part.strip("`,\"'()[]")
                        if path and not path.startswith(("#", "http")):
                            files_to_modify.append(path)
            elif "create" in line_lower or "new" in line_lower or "add" in line_lower:
                parts = line.split()
                for part in parts:
                    if "/" in part or part.endswith((".py", ".ts", ".js", ".tsx", ".jsx")):
                        path = part.strip("`,\"'()[]")
                        if path and not path.startswith(("#", "http")):
                            files_to_create.append(path)

        return {
            "approach": approach,
            "rationale": message[:1000] if message else "",
            "files_to_modify": list(set(files_to_modify))[:20],
            "files_to_create": list(set(files_to_create))[:20],
            "key_decisions": [],
            "risks": [],
            "estimated_impact": "moderate",
        }
