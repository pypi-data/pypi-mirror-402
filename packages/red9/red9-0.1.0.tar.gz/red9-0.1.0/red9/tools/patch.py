"""Patch tool for applying unified diffs."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from red9.files.lock import get_file_manager
from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult, validate_path

logger = logging.getLogger(__name__)


class ApplyPatchTool(Tool):
    """Apply a standard unified diff (patch) to a file."""

    @property
    def name(self) -> str:
        return "apply_patch"

    @property
    def description(self) -> str:
        return """Apply a unified diff (patch) to a file.
Useful when the LLM generates a standard git-style diff.
Input should be the raw diff content.
"""

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
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to patch",
                    },
                    "patch": {
                        "type": "string",
                        "description": "The unified diff content to apply",
                    },
                },
                "required": ["file_path", "patch"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        file_path_str = params.get("file_path")
        patch_content = params.get("patch", "")

        if not file_path_str or not patch_content:
            return ToolResult.fail(
                "file_path and patch are required", error_type=ToolErrorType.INVALID_PARAMS
            )

        file_path, error = validate_path(file_path_str, must_exist=True)
        if error or not file_path:
            return ToolResult.fail(error or "Invalid path", error_type=ToolErrorType.FILE_NOT_FOUND)

        # Acquire lock
        file_manager = get_file_manager()
        try:
            with file_manager.locked(file_path):
                content = file_path.read_text(encoding="utf-8")
                content.splitlines(keepends=True)

                # Parse patch (basic implementation)
                # In a real scenario, we might use a library like `whatthepatch` or `patch` command
                # Here we use a simpler approach relying on python's difflib or manual parsing
                # But manual patching is error prone.
                # Let's try to use the `patch` command if available, otherwise fallback to simple replace?
                # Actually, `aider` does complex fuzzy patching.
                # For `red9`, let's stick to the robust `patch` utility if available, which is "superior" standard compliance.

                import shutil
                import subprocess
                import tempfile

                patch_cmd = shutil.which("patch")
                if patch_cmd:
                    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
                        tf.write(patch_content)
                        tf_path = tf.name

                    try:
                        # Try to apply patch
                        # -u: unified
                        # -N: ignore patches already applied
                        # -r -: reject file to stdout/stderr
                        cmd = [patch_cmd, "-u", "-N", str(file_path), tf_path]
                        result = subprocess.run(cmd, capture_output=True, text=True)

                        if result.returncode == 0:
                            return ToolResult.ok("Successfully applied patch.")
                        else:
                            # If patch failed, return error output
                            return ToolResult.fail(
                                f"Patch command failed:\n{result.stdout}\n{result.stderr}",
                                error_type=ToolErrorType.FILE_WRITE_FAILURE,
                            )
                    finally:
                        Path(tf_path).unlink()
                else:
                    return ToolResult.fail(
                        "The 'patch' command-line utility is not installed. Please install it or use apply_diff.",
                        error_type=ToolErrorType.EXECUTION_ERROR,
                    )

        except Exception as e:
            return ToolResult.fail(
                f"Failed to apply patch: {e}", error_type=ToolErrorType.FILE_WRITE_FAILURE
            )
