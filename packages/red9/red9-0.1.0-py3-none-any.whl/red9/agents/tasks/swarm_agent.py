"""Single Agent Task - Individual agent execution as a Stabilize stage.

Each agent runs as its own Stabilize stage. Stabilize's DAG naturally runs
stages with the same dependencies in parallel.

Benefits:
- Native parallelism via Stabilize's orchestrator
- Per-agent retry with exponential backoff
- Per-agent observability and state tracking
- Better fault isolation
- Resume capability from specific failed agent
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from stabilize import Task, TaskResult
from stabilize.models.stage import StageExecution

from red9.agents.error_handler import handle_transient_error
from red9.agents.loop import AgentLoop
from red9.errors import is_transient_error
from red9.logging import get_logger
from red9.workflows.models import SwarmAgentConfig, SwarmAgentResult

if TYPE_CHECKING:
    from red9.providers.base import LLMProvider
    from red9.tools.base import ToolRegistry

logger = get_logger(__name__)


class SwarmAgentTask(Task):
    """Single agent execution - designed to run as independent Stabilize stage.

    Each SwarmAgentTask instance runs one agent with a specific role/focus.
    Multiple SwarmAgentTask stages with the same dependencies run in parallel
    automatically via Stabilize's DAG execution.

    Expected context:
        - agent_config: SwarmAgentConfig dict with role, focus, model, etc.
        - request: The user's original request
        - project_root: Project root path
        - upstream_context: Context from upstream stages (optional)

    Outputs:
        - agent_result: Full SwarmAgentResult dict
        - {output_key}: The agent's output text (keyed by config.output_key)
    """

    def __init__(
        self,
        providers: dict[str, LLMProvider],
        tool_registry: ToolRegistry,
    ) -> None:
        """Initialize swarm agent task.

        Args:
            providers: Dictionary of providers by model name.
            tool_registry: Tool registry for agent execution.
        """
        self.providers = providers
        self.tools = tool_registry
        # Use default provider as fallback if available
        self.fallback_provider = providers.get("agent_model") or providers.get("default")

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute single agent.

        Args:
            stage: Stage execution context.

        Returns:
            TaskResult with agent output.
        """
        # Extract context
        agent_config_data = stage.context.get("agent_config")
        if not agent_config_data:
            return TaskResult.terminal(error="agent_config is required")

        request = stage.context.get("request", "")
        project_root = stage.context.get("project_root")
        upstream_context = stage.context.get("upstream_context", {})

        if not project_root:
            return TaskResult.terminal(error="project_root is required")

        # Parse agent config
        if isinstance(agent_config_data, dict):
            agent_config = SwarmAgentConfig.from_dict(agent_config_data)
        elif isinstance(agent_config_data, SwarmAgentConfig):
            agent_config = agent_config_data
        else:
            return TaskResult.terminal(error="Invalid agent_config format")

        root_path = Path(project_root)

        logger.info(
            f"Starting agent: role={agent_config.role.value}, focus={agent_config.focus[:50]}..."
        )

        # Get streaming callback from context or module-level registry
        from red9.workflows.runner import get_stream_callback, get_ui_event_callback

        on_token = stage.context.get("on_token") or get_stream_callback()
        on_ui_event = stage.context.get("on_ui_event") or get_ui_event_callback()

        try:
            # Execute the agent
            result = self._execute_agent(
                agent_config=agent_config,
                request=request,
                upstream_context=upstream_context,
                project_root=root_path,
                on_token=on_token,
                on_ui_event=on_ui_event,
            )

            if not result.success:
                # Agent failed but not due to infrastructure error
                # Use failed_continue to allow aggregator to run with partial results
                logger.warning(
                    f"Agent {agent_config.role.value} failed: {result.error}. "
                    "Continuing workflow with partial results."
                )
                return TaskResult.failed_continue(
                    error=result.error or f"Agent {agent_config.role.value} failed",
                    outputs={
                        "agent_result": None,
                        "role": agent_config.role.value,
                        "success": False,
                        "error": result.error,
                    },
                )

            # Build outputs
            outputs: dict[str, Any] = {
                "agent_result": result.to_dict(),
                agent_config.output_key: result.output,
                "role": agent_config.role.value,
                "success": True,
            }

            logger.info(f"Agent {agent_config.role.value} completed successfully")
            return TaskResult.success(outputs=outputs)

        except Exception as e:
            if is_transient_error(e):
                return handle_transient_error(
                    e, [], agent_name=f"SwarmAgent:{agent_config.role.value}"
                )

            # Fallback attempt if provider is available and different from current
            logger.exception(f"Agent {agent_config.role.value} crashed: {e}")

            return TaskResult.failed_continue(
                error=f"Agent crashed: {e}",
                outputs={
                    "agent_result": None,
                    "role": agent_config.role.value,
                    "success": False,
                    "error": str(e),
                },
            )

    def _execute_agent(
        self,
        agent_config: SwarmAgentConfig,
        request: str,
        upstream_context: dict[str, str],
        project_root: Path,
        on_token: Any = None,
        on_ui_event: Any = None,
    ) -> SwarmAgentResult:
        """Run the agent with its specific configuration.

        Args:
            agent_config: Configuration for this agent.
            request: User's original request.
            upstream_context: Context from upstream stages.
            project_root: Project root path.
            on_token: Optional callback for streaming tokens.
            on_ui_event: Optional callback for UI events.

        Returns:
            SwarmAgentResult with the agent's output.
        """
        # Get the appropriate provider for this agent's model
        model = agent_config.get_model()
        provider = self.providers.get(model) or self.providers.get("default")

        if not provider:
            return SwarmAgentResult(
                agent_config=agent_config,
                output="",
                success=False,
                error=f"No provider available for model: {model}",
            )

        # Build system prompt
        system_prompt = self._build_system_prompt(agent_config, upstream_context)

        # Build user message with context substitution
        user_message = self._build_user_message(agent_config, request, upstream_context)

        # Create agent loop
        agent_loop = AgentLoop(
            provider=provider,
            tool_registry=self.tools,
            max_iterations=agent_config.max_iterations,
            parallel_tool_execution=True,
            max_parallel_tools=4,
            enable_loop_detection=True,
            enable_compression=True,
        )

        # Run the agent
        result = agent_loop.run(
            system_prompt=system_prompt,
            user_message=user_message,
            on_token=on_token,
            on_ui_event=on_ui_event,
        )

        return SwarmAgentResult(
            agent_config=agent_config,
            output=result.final_message,
            success=result.success,
            error=result.error,
            files_modified=result.files_modified,
            files_read=[],
            confidence=0.0,
        )

    def _build_system_prompt(
        self,
        agent_config: SwarmAgentConfig,
        upstream_context: dict[str, str],
    ) -> str:
        """Build system prompt for an agent based on its role.

        Args:
            agent_config: Agent configuration with role and extensions.
            upstream_context: Context from upstream stages.

        Returns:
            Complete system prompt for the agent.
        """
        from red9.agents.swarm_prompts import get_role_prompt

        base_prompt = get_role_prompt(agent_config.role)

        # Add focus area
        prompt = f"{base_prompt}\n\n## Your Focus Area\n\n{agent_config.focus}"

        # Add custom extension if provided
        if agent_config.system_prompt_extension:
            prompt += f"\n\n## Additional Guidance\n\n{agent_config.system_prompt_extension}"

        # Add upstream context summary
        if upstream_context:
            context_summary = "\n".join(
                f"- **{k}**: {v[:500]}..." if len(v) > 500 else f"- **{k}**: {v}"
                for k, v in upstream_context.items()
            )
            prompt += f"\n\n## Context from Previous Phases\n\n{context_summary}"

        return prompt

    def _build_user_message(
        self,
        agent_config: SwarmAgentConfig,
        request: str,
        upstream_context: dict[str, str],
    ) -> str:
        """Build user message with context template substitution.

        Args:
            agent_config: Agent configuration.
            request: User's original request.
            upstream_context: Context for template substitution.

        Returns:
            User message with templates substituted.
        """
        message = f"""# Request

{request}

## Your Task

Analyze this request from the perspective of a {agent_config.role.value.replace("_", " ")}.

Focus on: {agent_config.focus}

Provide your analysis and recommendations. Be specific and actionable.
"""

        # Apply template substitution for {key} patterns
        for key, value in upstream_context.items():
            placeholder = "{" + key + "}"
            if placeholder in message:
                message = message.replace(placeholder, value)

        return message
