"""Complete task tool for signaling task completion."""

from __future__ import annotations

from typing import Any

from red9.tools.base import Tool, ToolDefinition, ToolResult


class CompleteTaskTool(Tool):
    """Signal that the current task is complete."""

    @property
    def name(self) -> str:
        return "complete_task"

    @property
    def description(self) -> str:
        return """Signal that you have completed the current task.
Call this when you have finished all required work.
Provide a summary of what was accomplished and list modified files."""

    @property
    def read_only(self) -> bool:
        return False

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of what was accomplished",
                    },
                    "files_modified": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of files that were modified",
                    },
                    "tests_passed": {
                        "type": "boolean",
                        "description": "Whether tests passed (if applicable)",
                    },
                },
                "required": ["summary"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        summary = params.get("summary", "")
        files_modified = params.get("files_modified", [])
        tests_passed = params.get("tests_passed")

        if not summary:
            summary = "Task completed"

        return ToolResult.ok(
            {
                "summary": summary,
                "files_modified": files_modified,
                "tests_passed": tests_passed,
                "completed": True,
            }
        )
