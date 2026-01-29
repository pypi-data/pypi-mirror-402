"""Code Review Tool for use within AgentLoop.

This tool enables code review as part of an agent's tool arsenal, allowing
review to happen inline during DDD iteration loops without spawning separate
Stabilize stages. This maintains proper architectural separation where tools
are blackbox to Stabilize.

Key difference from ReviewerAgentTask:
- ReviewerAgentTask: A Stabilize Task that runs review as a separate stage
- ReviewCodeTool: A tool that can be called within any AgentLoop iteration
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from red9.logging import get_logger
from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult

if TYPE_CHECKING:
    from red9.providers.base import LLMProvider

logger = get_logger(__name__)


class ReviewCodeTool(Tool):
    """Tool for reviewing code files within an AgentLoop.

    This tool performs targeted code review on specified files, returning
    structured issue findings with confidence scores. It uses an LLM provider
    to analyze code for bugs, simplicity issues, or convention violations.

    Unlike ReviewerAgentTask, this runs synchronously as a tool call,
    enabling inline review during iteration loops.
    """

    def __init__(
        self,
        provider: LLMProvider | None = None,
        project_root: Path | None = None,
        min_confidence: int = 80,
    ) -> None:
        """Initialize the review code tool.

        Args:
            provider: LLM provider for review analysis. If None, tool will
                return an error when executed.
            project_root: Project root for file path resolution.
            min_confidence: Minimum confidence threshold for reported issues.
        """
        self._provider = provider
        self._project_root = project_root or Path.cwd()
        self._min_confidence = min_confidence

    @property
    def name(self) -> str:
        return "review_code"

    @property
    def description(self) -> str:
        return """Review code files for issues (bugs, simplicity, conventions).

Use this tool to perform code review on modified files during implementation.
Returns a list of issues found, each with confidence score and severity.

Focus areas:
- bugs: Logic errors, edge cases, potential runtime errors
- simplicity: Over-engineering, unnecessary complexity, dead code
- conventions: Style violations, naming inconsistencies, missing docs

Only issues with confidence >= 80 are returned to reduce noise.

Example:
    review_code(files=["src/main.py", "src/utils.py"], focus="bugs")

Returns:
    {
        "issues": [{"description": "...", "location": "file:line", "confidence": 85}],
        "summary": "Review summary",
        "approved": true/false
    }
"""

    @property
    def read_only(self) -> bool:
        return True

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to review",
                    },
                    "focus": {
                        "type": "string",
                        "enum": ["bugs", "simplicity", "conventions"],
                        "description": "Focus area for review",
                        "default": "bugs",
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional context about the changes being reviewed",
                    },
                },
                "required": ["files"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute code review on specified files.

        Args:
            params: Tool parameters containing files, focus, and optional context.

        Returns:
            ToolResult with review findings or error.
        """
        if not self._provider:
            return ToolResult.fail(
                "ReviewCodeTool requires an LLM provider",
                error_type=ToolErrorType.NOT_INITIALIZED,
            )

        files = params.get("files", [])
        focus = params.get("focus", "bugs")
        context = params.get("context", "")

        if not files:
            return ToolResult.fail(
                "At least one file must be specified for review",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        # Read file contents for review
        file_contents: dict[str, str] = {}
        for file_path in files[:10]:  # Limit to 10 files
            try:
                path = Path(file_path)
                if not path.is_absolute():
                    path = self._project_root / path

                if path.exists() and path.is_file():
                    content = path.read_text(encoding="utf-8")
                    # Truncate large files
                    if len(content) > 10000:
                        content = content[:10000] + "\n... (truncated)"
                    file_contents[file_path] = content
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")
                file_contents[file_path] = f"(Error reading file: {e})"

        if not file_contents:
            return ToolResult.ok(
                {
                    "issues": [],
                    "summary": "No files could be read for review",
                    "approved": True,
                }
            )

        # Build review prompt
        files_section = "\n\n".join(
            f"### {path}\n```\n{content}\n```" for path, content in file_contents.items()
        )

        prompt = f"""You are a code reviewer focused on {focus.upper()}.

Review the following files and identify issues.

{f"Context: {context}" if context else ""}

{files_section}

For each issue found, provide:
- description: Clear explanation of the issue
- location: file:line_number
- confidence: Your confidence (0-100) that this is a real issue
- severity: critical, high, medium, or low

IMPORTANT:
- Only report issues with confidence >= 80
- Be specific about the location
- Provide actionable suggestions

Return your findings as JSON:
```json
{{
  "issues": [
    {{"description": "...", "location": "file.py:42", "confidence": 85, "severity": "medium"}}
  ],
  "summary": "Overall assessment",
  "approved": true/false
}}
```
"""

        try:
            from red9.providers.base import Message

            response = self._provider.chat(
                messages=[
                    Message(role="user", content=prompt),
                ],
                tools=None,
            )

            # Parse the response
            output = self._parse_review_output(response.message.content or "")

            # Filter to high-confidence issues
            all_issues = output.get("issues", [])
            high_confidence = [
                i for i in all_issues if i.get("confidence", 0) >= self._min_confidence
            ]

            output["issues"] = high_confidence
            output["approved"] = len(high_confidence) == 0

            logger.info(
                f"ReviewCodeTool ({focus}): {len(all_issues)} issues found, "
                f"{len(high_confidence)} with confidence >= {self._min_confidence}"
            )

            return ToolResult.ok(output)

        except Exception as e:
            logger.exception(f"ReviewCodeTool failed: {e}")
            return ToolResult.fail(
                f"Review failed: {e}",
                error_type=ToolErrorType.EXECUTION_ERROR,
            )

    def _parse_review_output(self, message: str) -> dict[str, Any]:
        """Parse review output from LLM response.

        Args:
            message: Raw message from the LLM.

        Returns:
            Structured review output.
        """
        import json
        import re

        # Try to extract JSON from code blocks
        try:
            if "```json" in message:
                json_str = message.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in message:
                json_str = message.split("```")[1].split("```")[0].strip()
                if json_str.startswith("{"):
                    return json.loads(json_str)
            if message.strip().startswith("{"):
                return json.loads(message.strip())
        except (json.JSONDecodeError, IndexError):
            pass

        # Fallback: extract issues from text
        issues = []
        issue_patterns = [
            r"(?:Issue|Problem|Bug|Warning):\s*(.+?)(?=\n(?:Issue|Problem|Bug|Warning|$))",
        ]

        for pattern in issue_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE | re.DOTALL)
            for match in matches:
                location_match = re.search(r"([\w/]+\.[a-z]+):?(\d+)?", match)
                location = location_match.group(0) if location_match else "unknown"

                confidence_match = re.search(r"confidence[:\s]+(\d+)", match, re.IGNORECASE)
                confidence = int(confidence_match.group(1)) if confidence_match else 75

                severity = "medium"
                if re.search(r"critical|severe|security", match, re.IGNORECASE):
                    severity = "critical"
                elif re.search(r"high|important", match, re.IGNORECASE):
                    severity = "high"
                elif re.search(r"low|minor", match, re.IGNORECASE):
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
