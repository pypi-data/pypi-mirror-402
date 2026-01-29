"""AST-Grep tool for structural code analysis.

Finds code patterns based on AST structure rather than just text.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from red9.logging import get_logger
from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult

logger = get_logger(__name__)


class ASTGrepTool(Tool):
    """Run ast-grep to find structural patterns."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    @property
    def name(self) -> str:
        return "ast_grep"

    @property
    def description(self) -> str:
        return """Search for structural code patterns using ast-grep.
Finds code based on syntax tree rather than just text.

Examples:
- `ast_grep(pattern="print($$$)")` - Find all print calls
- `ast_grep(pattern="def $FUNC($$$): $$$", lang="python")` - Find all function definitions
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
                    "pattern": {
                        "type": "string",
                        "description": "The code pattern to search for (using ast-grep syntax)",
                    },
                    "lang": {
                        "type": "string",
                        "description": "Programming language (python, typescript, go, etc.)",
                    },
                    "path": {
                        "type": "string",
                        "description": "Subdirectory to search in",
                    },
                },
                "required": ["pattern"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        pattern = params.get("pattern", "")
        lang = params.get("lang")
        search_path = params.get("path", ".")

        if not pattern:
            return ToolResult.fail("pattern is required", error_type=ToolErrorType.INVALID_PARAMS)

        sg_cmd = shutil.which("sg") or shutil.which("ast-grep")
        if not sg_cmd:
            return ToolResult.fail(
                "ast-grep (sg) is not installed", error_type=ToolErrorType.EXECUTION_ERROR
            )

        cmd = [sg_cmd, "--pattern", pattern]
        if lang:
            cmd.extend(["--lang", lang])

        cmd.append(search_path)

        try:
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                output = result.stdout or "No matches found."
                return ToolResult.ok(output)
            else:
                return ToolResult.fail(
                    f"ast-grep failed: {result.stderr}", error_type=ToolErrorType.EXECUTION_ERROR
                )

        except Exception as e:
            return ToolResult.fail(
                f"Error running ast-grep: {e}", error_type=ToolErrorType.EXECUTION_ERROR
            )
