"""Grep search tool implementation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult


class GrepTool(Tool):
    """Search for patterns in files using ripgrep."""

    @property
    def name(self) -> str:
        return "grep_search"

    @property
    def description(self) -> str:
        return """Search for a pattern in files using regex.
Uses ripgrep for fast, recursive search.

Examples:
- "function\\s+\\w+" - Find function declarations
- "import.*pandas" - Find pandas imports
- "TODO|FIXME" - Find todos and fixmes"""

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
                        "description": "Regex pattern to search for",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory or file to search (default: cwd)",
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "Glob pattern to filter files (e.g., '*.py')",
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Case sensitive search (default: false)",
                    },
                    "context_lines": {
                        "type": "integer",
                        "description": "Lines of context before/after match (default: 2)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                    },
                },
                "required": ["pattern"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        pattern = params.get("pattern", "")
        path = params.get("path", ".")
        file_pattern = params.get("file_pattern")
        case_sensitive = params.get("case_sensitive", False)
        context_lines = params.get("context_lines", 2)
        max_results = params.get("max_results", 50)

        if not pattern:
            return ToolResult.fail(
                "pattern is required",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        # Build ripgrep command
        cmd = ["rg", "--json", "-C", str(context_lines)]

        if not case_sensitive:
            cmd.append("-i")

        if file_pattern:
            cmd.extend(["-g", file_pattern])

        cmd.extend(["-m", str(max_results)])
        cmd.append(pattern)
        cmd.append(path)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Parse JSON lines output
            matches = []
            for line in result.stdout.splitlines():
                try:
                    data = json.loads(line)
                    if data.get("type") == "match":
                        match_data = data["data"]
                        matches.append(
                            {
                                "file": match_data["path"]["text"],
                                "line_number": match_data["line_number"],
                                "text": match_data["lines"]["text"].strip(),
                            }
                        )
                except json.JSONDecodeError:
                    continue

            return ToolResult.ok(
                {
                    "matches": matches,
                    "total_matches": len(matches),
                    "pattern": pattern,
                    "path": path,
                }
            )

        except subprocess.TimeoutExpired:
            return ToolResult.fail(
                "Search timed out after 30 seconds",
                error_type=ToolErrorType.GREP_EXECUTION_ERROR,
            )
        except FileNotFoundError:
            # ripgrep not installed, fall back to Python grep
            return self._python_grep(pattern, path, file_pattern, case_sensitive, max_results)
        except Exception as e:
            return ToolResult.fail(
                f"Search failed: {e}",
                error_type=ToolErrorType.GREP_EXECUTION_ERROR,
            )

    def _python_grep(
        self,
        pattern: str,
        path: str,
        file_pattern: str | None,
        case_sensitive: bool,
        max_results: int,
    ) -> ToolResult:
        """Fallback Python-based grep when ripgrep is not available."""
        import glob as glob_module
        import re

        base_path = Path(path)
        if not base_path.is_absolute():
            base_path = Path.cwd() / base_path

        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
        except re.error as e:
            return ToolResult.fail(
                f"Invalid regex pattern: {e}",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        matches = []
        search_pattern = file_pattern or "**/*"

        try:
            for file_path in glob_module.glob(str(base_path / search_pattern), recursive=True):
                if len(matches) >= max_results:
                    break

                path_obj = Path(file_path)
                if not path_obj.is_file():
                    continue

                try:
                    content = path_obj.read_text()
                    for i, line in enumerate(content.splitlines(), 1):
                        if regex.search(line):
                            matches.append(
                                {
                                    "file": str(path_obj),
                                    "line_number": i,
                                    "text": line.strip(),
                                }
                            )
                            if len(matches) >= max_results:
                                break
                except (UnicodeDecodeError, PermissionError):
                    continue

            return ToolResult.ok(
                {
                    "matches": matches,
                    "total_matches": len(matches),
                    "pattern": pattern,
                    "path": path,
                    "note": "Used Python fallback (ripgrep not available)",
                }
            )

        except Exception as e:
            return ToolResult.fail(
                f"Search failed: {e}",
                error_type=ToolErrorType.GREP_EXECUTION_ERROR,
            )
