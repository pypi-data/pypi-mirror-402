"""Reviewer Agent Task - Code review for the enterprise workflow.

Reviewers analyze implemented code to find issues with confidence scoring.
Multiple reviewers run in parallel with different focus areas (simplicity,
bugs, conventions). Only issues with confidence >= 80 are surfaced.

This is a Stabilize Task that can be executed as an independent stage.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from stabilize import Task, TaskResult
from stabilize.models.stage import StageExecution

from red9.agents.error_handler import handle_transient_error
from red9.agents.loop import AgentLoop
from red9.agents.personas.reviewer import get_reviewer_persona
from red9.errors import is_transient_error
from red9.logging import get_logger
from red9.workflows.schemas import (
    REVIEW_OUTPUT_SCHEMA,
    filter_high_confidence_issues,
    validate_output,
)

if TYPE_CHECKING:
    from red9.providers.base import LLMProvider
    from red9.tools.base import ToolRegistry

logger = get_logger(__name__)


class ReviewerAgentTask(Task):
    """Reviewer agent task for code analysis.

    Reviewers find issues in code with confidence scoring. Only high-confidence
    issues (>=80) are reported to reduce noise and false positives.

    Expected context:
        - project_root: Project root path
        - request: User's original request
        - focus: Reviewer focus area ("simplicity", "bugs", "conventions")
        - files_modified: List of files that were changed
        - workflow_id: Workflow identifier

    Outputs:
        - issues: List of {description, location, confidence, severity} dicts
        - summary: Review summary
        - approved: Whether the code is approved
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        min_confidence: int = 80,
    ) -> None:
        """Initialize reviewer task.

        Args:
            provider: LLM provider for generation (code model recommended).
            tool_registry: Tool registry.
            min_confidence: Minimum confidence threshold (default 80).
        """
        self.provider = provider
        self.tools = tool_registry
        self.min_confidence = min_confidence

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute code review.

        Args:
            stage: Stage execution context.

        Returns:
            TaskResult with review findings.
        """
        # Extract context
        project_root = stage.context.get("project_root")
        request = stage.context.get("request", "")
        focus = stage.context.get("focus", "bugs")
        files_modified = stage.context.get("files_modified", [])

        if not project_root:
            return TaskResult.terminal(error="project_root is required")

        # Get the reviewer persona for this focus area
        try:
            persona = get_reviewer_persona(focus)
        except ValueError as e:
            return TaskResult.terminal(error=str(e))

        logger.info(f"Reviewer ({focus}) starting analysis for: {request[:50]}...")

        # Get callbacks for UI events
        from red9.workflows.runner import get_stream_callback, get_ui_event_callback

        on_token = stage.context.get("on_token") or get_stream_callback()
        on_ui_event = stage.context.get("on_ui_event") or get_ui_event_callback()

        # Emit agent start event
        if on_ui_event:
            on_ui_event(
                {
                    "type": "agent_start",
                    "agent_id": f"reviewer_{focus}",
                    "role": f"Reviewer ({focus})",
                    "focus": focus,
                }
            )

        try:
            # Load spec content for verification (Spec-First compliance)
            spec_content = stage.context.get("spec_content")
            if not spec_content and project_root and workflow_id:
                # Try to load from disk if not in context
                # Use suffix matching to be robust or standard ID format
                spec_id_suffix = workflow_id[-6:] if len(workflow_id) >= 6 else workflow_id
                spec_path = Path(project_root) / ".red9" / "specs" / f"SPEC-{spec_id_suffix}.md"
                if spec_path.exists():
                    try:
                        spec_content = spec_path.read_text(encoding="utf-8")
                        logger.info(f"Reviewer ({focus}): Loaded spec from {spec_path}")
                    except Exception as e:
                        logger.warning(f"Failed to read spec: {e}")

            # Build file list for review
            files_context = ""
            if files_modified:
                files_list = "\n".join([f"- {f}" for f in files_modified[:20]])
                files_context = f"\n## Files to Review\n{files_list}\n"
            else:
                files_context = "\n## Note: No specific files provided. Review recent changes.\n"

            # Build user message
            user_message = f"""# Task Request

{request}

## Technical Specification (Reference)
{spec_content or "No formal spec available."}

{files_context}

## Your Assignment

Review the implementation from a {focus.upper()} perspective.
Verify that the code matches the requirements in the Technical Specification.

**CRITICAL: Assign a confidence score (0-100) to EVERY issue you find.**
Only report issues with confidence >= 80.

Provide your review as JSON with this structure:
```json
{{
  "issues": [
    {{
      "description": "Clear description of the issue",
      "location": "path/to/file.py:42",
      "confidence": 85,
      "severity": "medium",
      "suggestion": "How to fix (optional)"
    }}
  ],
  "summary": "Overall review summary",
  "approved": true
}}
```

Remember: Only report issues you are CONFIDENT about (score >= 80).
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
            output = self._parse_reviewer_output(result.final_message, focus)

            # Filter to high-confidence issues
            all_issues = output.get("issues", [])
            high_confidence_issues = filter_high_confidence_issues(all_issues, self.min_confidence)

            logger.info(
                f"Reviewer ({focus}): {len(all_issues)} issues found, "
                f"{len(high_confidence_issues)} with confidence >= {self.min_confidence}"
            )

            # Validate against schema (with filtered issues)
            output["issues"] = high_confidence_issues
            is_valid, errors = validate_output(output, REVIEW_OUTPUT_SCHEMA)
            if not is_valid:
                logger.warning(f"Reviewer output validation failed: {errors}")

            # Emit agent end event
            if on_ui_event:
                on_ui_event(
                    {
                        "type": "agent_end",
                        "agent_id": f"reviewer_{focus}",
                        "success": result.success,
                    }
                )

                # Emit review issues event if any high-confidence issues found
                if high_confidence_issues:
                    on_ui_event(
                        {
                            "type": "review_issues",
                            "issues": high_confidence_issues,
                        }
                    )

            # Code is approved if no high-confidence issues found
            approved = len(high_confidence_issues) == 0

            # Build output compatible with swarm_aggregator
            role_map = {
                "simplicity": "reviewer_simplicity",
                "bugs": "reviewer_bugs",
                "conventions": "reviewer_conventions",
            }
            agent_result = {
                "agent_config": {
                    "role": role_map.get(focus, f"reviewer_{focus}"),
                    "focus": f"Review code for {focus}",
                    "system_prompt_extension": "",
                },
                "output": json.dumps(output),
                "success": result.success,
                "error": None,
                "files_modified": [],
                "files_read": files_modified[:10] if files_modified else [],
                "confidence": 80.0,
            }

            outputs = {
                "focus": focus,
                "issues": high_confidence_issues,
                "all_issues_count": len(all_issues),
                "high_confidence_count": len(high_confidence_issues),
                "summary": output.get("summary", ""),
                "approved": approved,
                "success": result.success,
                "agent_result": agent_result,  # For swarm_aggregator compatibility
            }

            # Check for critical/high severity issues - these block completion
            critical_high_issues = [
                i for i in high_confidence_issues if i.get("severity") in ("critical", "high")
            ]

            if critical_high_issues:
                # Return failed_continue to trigger iteration
                logger.warning(
                    f"Reviewer ({focus}): Found {len(critical_high_issues)} "
                    "critical/high severity issues - blocking completion"
                )
                return TaskResult.failed_continue(
                    error=f"Review found {len(critical_high_issues)} critical/high issues",
                    outputs=outputs,
                )

            return TaskResult.success(outputs=outputs)

        except Exception as e:
            if is_transient_error(e):
                return handle_transient_error(e, [], agent_name=f"Reviewer:{focus}")

            logger.exception(f"Reviewer ({focus}) crashed: {e}")

            # Emit failure event
            if on_ui_event:
                on_ui_event(
                    {
                        "type": "agent_end",
                        "agent_id": f"reviewer_{focus}",
                        "success": False,
                    }
                )

            return TaskResult.failed_continue(
                error=f"Reviewer ({focus}) crashed: {e}",
                outputs={
                    "focus": focus,
                    "issues": [],
                    "summary": "",
                    "approved": False,
                    "success": False,
                    "error": str(e),
                },
            )

    def _parse_reviewer_output(self, message: str, focus: str) -> dict[str, Any]:
        """Parse reviewer output to extract structured data.

        Args:
            message: Raw message from the reviewer agent.
            focus: The focus area being reviewed.

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

        # Fallback: try to extract issues from text
        issues = []

        # Look for patterns like "Issue:", "Problem:", "Bug:", etc.
        issue_patterns = [
            r"(?:Issue|Problem|Bug|Warning|Error|Concern):\s*(.+?)(?=\n(?:Issue|Problem|Bug|Warning|Error|Concern|$))",
            r"\*\*Issue\*\*:\s*(.+?)(?=\n\*\*|$)",
            r"[-*]\s+(.+?(?:line|Line|\d+).*?)(?=\n[-*]|$)",
        ]

        for pattern in issue_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Try to extract location
                location_match = re.search(r"([\w/]+\.[a-z]+):?(\d+)?", match)
                location = location_match.group(0) if location_match else "unknown"

                # Try to extract confidence (default to 75 - below threshold)
                confidence_match = re.search(r"confidence[:\s]+(\d+)", match, re.IGNORECASE)
                confidence = int(confidence_match.group(1)) if confidence_match else 75

                # Try to extract severity
                severity = "medium"
                if re.search(r"critical|severe|security", match, re.IGNORECASE):
                    severity = "critical"
                elif re.search(r"high|important|major", match, re.IGNORECASE):
                    severity = "high"
                elif re.search(r"low|minor|nitpick", match, re.IGNORECASE):
                    severity = "low"

                issues.append(
                    {
                        "description": match.strip()[:200],
                        "location": location,
                        "confidence": confidence,
                        "severity": severity,
                    }
                )

        return {
            "issues": issues,
            "summary": message[:500] if message else "",
            "approved": len(issues) == 0,
        }
