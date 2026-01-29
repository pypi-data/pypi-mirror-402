"""Swarm Aggregator Task - Synthesizes results from parallel agents.

Takes the outputs from SwarmAgentTask stages and aggregates them using one of:
- CONSENSUS: Synthesize common themes and reconcile differences
- UNION: Combine all unique insights
- VOTING: Select the approach with most support
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from stabilize import Task, TaskResult
from stabilize.errors import PermanentError
from stabilize.models.stage import StageExecution

from red9.agents.notepad import Notepad
from red9.logging import get_logger
from red9.providers.base import GenerationConfig
from red9.workflows.models import (
    AggregationStrategy,
    SwarmAgentResult,
)

if TYPE_CHECKING:
    from red9.providers.base import LLMProvider

logger = get_logger(__name__)


class SwarmAggregatorTask(Task):
    """Aggregate results from a swarm of agents.

    Takes multiple SwarmAgentResult objects and synthesizes them into
    a unified output based on the aggregation strategy.
    """

    def __init__(self, provider: LLMProvider) -> None:
        """Initialize aggregator task.

        Args:
            provider: LLM provider for synthesis (should be agentic model).
        """
        self.provider = provider

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the aggregation.

        Expected context:
            - swarm_results: List of SwarmAgentResult dicts from upstream swarm
            - aggregation_strategy: "consensus", "union", or "voting"
            - aggregation_focus: What aspect to focus on during aggregation
            - project_root: Project root path
            - workflow_id: Current workflow ID
            - output_key: Key for storing the aggregated output

        Returns:
            TaskResult with aggregated_output and chosen_approach (for voting).
        """
        project_root = stage.context.get("project_root")
        workflow_id = stage.context.get("workflow_id", "default")
        output_key = stage.context.get("output_key", "aggregated_output")

        # Get swarm results from upstream
        swarm_results_data = stage.context.get("swarm_results")
        if not swarm_results_data:
            # Try to get from upstream stage outputs
            swarm_results_data = self._get_swarm_results_from_upstream(stage)

        if not swarm_results_data:
            return TaskResult.terminal(error="swarm_results is required")

        # Parse results
        swarm_results = [
            SwarmAgentResult.from_dict(r) if isinstance(r, dict) else r for r in swarm_results_data
        ]

        # Filter out None values (e.g. from timed out tasks)
        swarm_results = [r for r in swarm_results if r is not None]

        # Filter to successful results only
        successful_results = [r for r in swarm_results if r.success]
        if not successful_results:
            return TaskResult.terminal(error="No successful swarm results to aggregate")

        # Get aggregation strategy
        strategy_str = stage.context.get("aggregation_strategy", "consensus")
        try:
            strategy = AggregationStrategy(strategy_str)
        except ValueError:
            strategy = AggregationStrategy.CONSENSUS

        aggregation_focus = stage.context.get("aggregation_focus", "")

        root_path = Path(project_root) if project_root else Path.cwd()
        notepad = Notepad(root_path, workflow_id)

        logger.info(
            f"Aggregating {len(successful_results)} results using strategy: {strategy.value}"
        )

        try:
            if strategy == AggregationStrategy.CONSENSUS:
                result = self._aggregate_consensus(successful_results, aggregation_focus)
            elif strategy == AggregationStrategy.UNION:
                result = self._aggregate_union(successful_results, aggregation_focus)
            elif strategy == AggregationStrategy.VOTING:
                result = self._aggregate_voting(successful_results, aggregation_focus)
            else:
                result = self._aggregate_consensus(successful_results, aggregation_focus)

            notepad.add_entry(
                "learning",
                f"Aggregated {len(successful_results)} agent outputs using {strategy.value}",
                "SwarmAggregator",
            )

            # Build outputs
            outputs = {
                output_key: result["aggregated_output"],
                "aggregation_strategy": strategy.value,
                "agents_aggregated": len(successful_results),
            }

            # Add strategy-specific outputs
            if strategy == AggregationStrategy.VOTING and "chosen_approach" in result:
                outputs["chosen_approach"] = result["chosen_approach"]
                outputs["vote_rationale"] = result.get("vote_rationale", "")

            return TaskResult.success(outputs=outputs)

        except Exception as e:
            logger.exception(f"Aggregation failed: {e}")
            raise PermanentError(f"Aggregation failed: {e}", cause=e)

    def _get_swarm_results_from_upstream(
        self, stage: StageExecution
    ) -> list[dict[str, Any]] | None:
        """Extract swarm results from upstream stage outputs.

        With the native Stabilize parallelism approach, each upstream stage is a
        SwarmAgentTask with agent_result in its outputs. This method collects
        all agent_result values from the parallel upstream stages.

        RESILIENCE: This method tolerates failed upstream stages - it collects
        results from whatever stages succeeded. The aggregation can proceed
        with partial results rather than failing entirely.

        Args:
            stage: Current stage execution.

        Returns:
            List of swarm result dicts or None.
        """
        results = []
        failed_stages = []

        for upstream in stage.upstream_stages():
            # Check if stage succeeded and has outputs
            if upstream.outputs:
                # Each upstream SwarmAgentTask has agent_result
                if "agent_result" in upstream.outputs:
                    results.append(upstream.outputs["agent_result"])
            else:
                # Track failed/incomplete stages for logging
                failed_stages.append(upstream.ref_id)

        if failed_stages:
            logger.warning(
                f"Aggregating with partial results: {len(results)} succeeded, "
                f"{len(failed_stages)} failed ({failed_stages})"
            )

        return results if results else None

    def _aggregate_consensus(
        self,
        results: list[SwarmAgentResult],
        focus: str,
    ) -> dict[str, Any]:
        """Synthesize common themes and reconcile differences.

        Args:
            results: List of agent results.
            focus: What to focus on during synthesis.

        Returns:
            Dict with aggregated_output.
        """
        # Build prompt with all agent outputs
        agent_outputs = "\n\n---\n\n".join(
            f"## {r.agent_config.role.value.upper()}\n\n{r.output}" for r in results
        )

        prompt = f"""You are synthesizing outputs from {len(results)} expert agents.

## Agent Outputs

{agent_outputs}

## Your Task

Synthesize these perspectives into a unified analysis:
1. Find COMMON THEMES that multiple agents identified
2. Reconcile any CONFLICTING viewpoints
3. Prioritize findings by importance and confidence
4. Create a unified RECOMMENDATION

{f"Focus specifically on: {focus}" if focus else ""}

## Output Format

Provide your synthesis as structured JSON:
```json
{{
  "consensus_points": ["Points most agents agree on"],
  "reconciled_conflicts": [
    {{
      "topic": "Area of disagreement",
      "resolution": "Your synthesized view"
    }}
  ],
  "prioritized_findings": [
    {{
      "priority": 1,
      "finding": "Key insight",
      "supporting_agents": ["agent roles that mentioned this"]
    }}
  ],
  "unified_recommendation": "Your overall recommendation",
  "summary": "2-3 sentence executive summary"
}}
```
"""

        config = GenerationConfig(max_tokens=4096, temperature=0.3)
        response = self.provider.generate(
            prompt,
            system_prompt="You are a Technical Synthesizer combining expert analyses.",
            config=config,
        )

        return {
            "aggregated_output": response,
            "raw_json": self._extract_json(response),
        }

    def _aggregate_union(
        self,
        results: list[SwarmAgentResult],
        focus: str,
    ) -> dict[str, Any]:
        """Combine all unique insights from agents.

        Args:
            results: List of agent results.
            focus: What to focus on during combination.

        Returns:
            Dict with aggregated_output.
        """
        # Build prompt for union aggregation
        agent_outputs = "\n\n---\n\n".join(
            f"## {r.agent_config.role.value.upper()}\n\n{r.output}" for r in results
        )

        prompt = f"""You are combining insights from {len(results)} expert agents.

## Agent Outputs

{agent_outputs}

## Your Task

Combine all unique insights into a comprehensive view:
1. Extract ALL unique findings from each agent
2. Remove duplicates but preserve unique perspectives
3. Organize by category/theme
4. Include attribution (which agent found what)

{f"Focus specifically on: {focus}" if focus else ""}

## Output Format

Provide the combined insights as structured JSON:
```json
{{
  "categories": [
    {{
      "category": "Category name",
      "insights": [
        {{
          "insight": "The finding",
          "source_agents": ["which agents found this"],
          "confidence": 85
        }}
      ]
    }}
  ],
  "unique_highlights": ["Most important unique findings"],
  "coverage_gaps": ["What wasn't covered"],
  "summary": "2-3 sentence comprehensive summary"
}}
```
"""

        config = GenerationConfig(max_tokens=4096, temperature=0.3)
        response = self.provider.generate(
            prompt,
            system_prompt="You are a Technical Synthesizer combining expert analyses.",
            config=config,
        )

        return {
            "aggregated_output": response,
            "raw_json": self._extract_json(response),
        }

    def _aggregate_voting(
        self,
        results: list[SwarmAgentResult],
        focus: str,
    ) -> dict[str, Any]:
        """Select the approach with most support.

        Used primarily for architecture decisions where agents propose
        different approaches.

        Args:
            results: List of agent results.
            focus: What to focus on during voting.

        Returns:
            Dict with aggregated_output and chosen_approach.
        """
        # Build prompt for voting
        agent_outputs = "\n\n---\n\n".join(
            f"## {r.agent_config.role.value.upper()}\n\n{r.output}" for r in results
        )

        prompt = f"""You are evaluating architectural proposals from {len(results)} architects.

## Architect Proposals

{agent_outputs}

## Your Task

Evaluate the proposals and select the BEST approach:
1. Compare the TRADE-OFFS of each approach
2. Consider the CONTEXT (existing codebase, team, requirements)
3. Select the approach with the best BALANCE of factors
4. Explain your decision clearly

{f"Focus specifically on: {focus}" if focus else ""}

## Output Format

Provide your decision as structured JSON:
```json
{{
  "chosen_approach": "minimal|clean|pragmatic",
  "vote_rationale": "Why this approach was selected",
  "comparison": [
    {{
      "approach": "approach name",
      "pros": ["advantages"],
      "cons": ["disadvantages"],
      "score": 85
    }}
  ],
  "implementation_recommendation": "Specific guidance for implementing the chosen approach",
  "incorporated_ideas": ["Good ideas from non-chosen approaches to consider"],
  "summary": "2-3 sentence decision summary"
}}
```
"""

        config = GenerationConfig(max_tokens=4096, temperature=0.3)
        response = self.provider.generate(
            prompt,
            system_prompt="You are an Architecture Decision Maker evaluating proposals.",
            config=config,
        )

        # Try to extract the chosen approach
        json_data = self._extract_json(response)
        chosen_approach = None
        vote_rationale = ""

        if json_data:
            chosen_approach = json_data.get("chosen_approach")
            vote_rationale = json_data.get("vote_rationale", "")

        return {
            "aggregated_output": response,
            "raw_json": json_data,
            "chosen_approach": chosen_approach,
            "vote_rationale": vote_rationale,
        }

    def _extract_json(self, response: str) -> dict[str, Any] | None:
        """Extract JSON from response text.

        Args:
            response: Response text potentially containing JSON.

        Returns:
            Parsed JSON dict or None.
        """
        # Try to find JSON in markdown code blocks
        if "```json" in response:
            match = re.search(r"```json\s*\n?(.*?)\n?```", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    pass

        # Try to find JSON object directly
        if "```" in response:
            match = re.search(r"```\s*\n?(.*?)\n?```", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    pass

        # Try to parse the whole response as JSON
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # Try to find any JSON object in the response
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None
