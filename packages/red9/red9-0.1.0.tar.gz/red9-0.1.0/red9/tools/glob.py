"""Glob file search tool implementation."""

from __future__ import annotations

import glob as glob_module
from pathlib import Path
from typing import Any

from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult


class GlobTool(Tool):
    """Find files matching a glob pattern."""

    @property
    def name(self) -> str:
        return "glob"

    @property
    def description(self) -> str:
        return """Find files matching a glob pattern.
Use this to discover files before reading/editing them.

Examples:
- "**/*.py" - All Python files
- "src/**/*.ts" - TypeScript files in src
- "**/test_*.py" - All test files"""

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
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern to match files",
                    },
                    "path": {
                        "type": "string",
                        "description": "Base directory to search from (default: current directory)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of files to return (default: 100)",
                    },
                },
                "required": ["pattern"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        pattern = params.get("pattern", "")
        base_path = Path(params.get("path", "."))
        limit = params.get("limit", 100)

        if not pattern:
            return ToolResult.fail(
                "pattern is required",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        # Make path absolute if relative
        if not base_path.is_absolute():
            from red9.tools.base import get_project_root

            base_path = get_project_root() / base_path

        try:
            full_pattern = str(base_path / pattern)
            files = glob_module.glob(full_pattern, recursive=True)

            # Sort by modification time (newest first)
            files_with_mtime: list[tuple[str, float]] = []
            for f in files:
                try:
                    mtime = Path(f).stat().st_mtime
                    files_with_mtime.append((f, mtime))
                except OSError:
                    files_with_mtime.append((f, 0))

            files_with_mtime.sort(key=lambda x: x[1], reverse=True)

            # Apply limit
            sorted_files = [f for f, _ in files_with_mtime[:limit]]

            # Make paths relative to base for cleaner output
            relative_files = []
            for f in sorted_files:
                try:
                    relative_files.append(str(Path(f).relative_to(base_path)))
                except ValueError:
                    relative_files.append(f)

            return ToolResult.ok(
                {
                    "files": relative_files,
                    "total_matches": len(files),
                    "shown": len(sorted_files),
                    "pattern": pattern,
                    "base_path": str(base_path),
                }
            )

        except Exception as e:
            return ToolResult.fail(
                f"Glob search failed: {e}",
                error_type=ToolErrorType.GLOB_EXECUTION_ERROR,
            )
