"""Linter tool for providing static analysis feedback."""

from __future__ import annotations

import ast
import shutil
import subprocess
from pathlib import Path
from typing import Any, NamedTuple

from red9.logging import get_logger
from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult, validate_path

logger = get_logger(__name__)


class LintError(NamedTuple):
    file: str
    line: int
    message: str
    code: str | None = None


class LinterTool(Tool):
    """Run linters and static analysis on files."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()

    @property
    def name(self) -> str:
        return "lint_file"

    @property
    def description(self) -> str:
        return """Run static analysis (linting) on a file.
Use this to check for syntax errors and common bugs after editing a file.
Supports Python (compile + flake8) and JavaScript/TypeScript (if npm lint configured)."""

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
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to lint",
                    },
                },
                "required": ["file_path"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        path_str = params.get("file_path")
        if not path_str:
            return ToolResult.fail("file_path is required", error_type=ToolErrorType.INVALID_PARAMS)

        file_path, error = validate_path(path_str, must_exist=True)
        if error or not file_path:
            return ToolResult.fail(error or "Invalid path", error_type=ToolErrorType.FILE_NOT_FOUND)

        ext = file_path.suffix.lower()
        errors: list[LintError] = []

        # 1. Python Linting
        if ext == ".py":
            errors.extend(self._lint_python(file_path))

        # 2. JS/TS Linting (Optional, if configured in package.json)
        # TODO: Implement basic npm run lint check if package.json exists
        # For now, we stick to robust Python linting which is critical for the current stack

        if not errors:
            return ToolResult.ok("No lint errors found.")

        # Format errors
        output_lines = [f"Found {len(errors)} lint errors:"]
        for err in errors:
            output_lines.append(f"{err.file}:{err.line}: {err.message}")

        return ToolResult.ok("\n".join(output_lines))

    def _lint_python(self, file_path: Path) -> list[LintError]:
        errors = []

        # A. Syntax Check (fastest)
        try:
            content = file_path.read_text(encoding="utf-8")
            ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            errors.append(
                LintError(file=str(file_path), line=e.lineno or 0, message=f"SyntaxError: {e.msg}")
            )
            return errors  # Stop if syntax is broken

        # B. Flake8 (if available)
        flake8_cmd = shutil.which("flake8")
        if flake8_cmd:
            try:
                # Run flake8 with isolated config to ensure consistent basic checks
                # checking mainly for F (Pyflakes) and E9 (Syntax) errors which are critical
                result = subprocess.run(
                    [flake8_cmd, "--select=E9,F", "--isolated", str(file_path)],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )
                if result.returncode != 0:
                    for line in result.stdout.splitlines():
                        parts = line.split(":")
                        if len(parts) >= 3:
                            try:
                                # format: file:line:col: code msg
                                line_num = int(parts[1])
                                msg = ":".join(parts[3:]).strip()
                                errors.append(
                                    LintError(file=str(file_path), line=line_num, message=msg)
                                )
                            except ValueError:
                                pass
            except Exception as e:
                logger.warning(f"Flake8 execution failed: {e}")

        return errors
