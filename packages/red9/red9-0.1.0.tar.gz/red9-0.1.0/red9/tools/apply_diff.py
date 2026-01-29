"""Apply Diff Tool.

Applies changes to a file using a SEARCH/REPLACE block strategy.
This is more robust than line numbers or raw overwrite.
"""

from __future__ import annotations

from typing import Any

from red9.files.diff import generate_unified_diff
from red9.files.fuzzy_match import find_best_match
from red9.files.lock import get_file_manager
from red9.logging import get_logger
from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult, validate_path

logger = get_logger(__name__)


class ApplyDiffTool(Tool):
    """Apply a SEARCH/REPLACE block to a file."""

    @property
    def name(self) -> str:
        return "apply_diff"

    @property
    def description(self) -> str:
        return """Apply a change to a file using a SEARCH/REPLACE block.

Provide the exact text to SEARCH for, and the REPLACE text to substitute it with.
The tool uses fuzzy matching to tolerate minor whitespace differences.
Use this for robust code editing.
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
                        "description": "Path to the file to edit",
                    },
                    "search": {
                        "type": "string",
                        "description": (
                            "The block of code to find and replace. "
                            "Must match existing code closely."
                        ),
                    },
                    "replace": {
                        "type": "string",
                        "description": "The new block of code to insert.",
                    },
                },
                "required": ["file_path", "search", "replace"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        file_path_str = params.get("file_path")
        search_block = params.get("search", "")
        replace_block = params.get("replace", "")

        if not file_path_str or not search_block:
            return ToolResult.fail(
                "file_path and search parameters are required",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        file_path, error = validate_path(file_path_str, must_exist=True)
        if error or not file_path:
            return ToolResult.fail(error or "Invalid path", error_type=ToolErrorType.FILE_NOT_FOUND)

        # Acquire lock
        file_manager = get_file_manager()
        try:
            with file_manager.locked(file_path):
                content = file_path.read_text(encoding="utf-8")
                original_content = content  # Store for diff generation

                # Helper to validate and write Python files
                def validate_and_write(new_content: str, match_type: str, confidence: float = 1.0):
                    # Validate syntax for Python files BEFORE writing
                    if file_path.suffix == ".py":
                        import ast

                        try:
                            ast.parse(new_content, filename=str(file_path))
                        except SyntaxError as e:
                            # Reject the edit - don't corrupt the file with invalid syntax
                            logger.warning(
                                f"Edit rejected: would create invalid Python syntax at "
                                f"line {e.lineno}: {e.msg}"
                            )
                            return ToolResult.fail(
                                f"Edit rejected: would create invalid Python syntax at "
                                f"line {e.lineno}: {e.msg}. "
                                f"Please fix your edit - the search or replace block "
                                f"is incorrect.",
                                error_type=ToolErrorType.EDIT_VALIDATION_FAILED,
                            )

                    file_path.write_text(new_content, encoding="utf-8")
                    diff = generate_unified_diff(original_content, new_content, str(file_path))

                    if match_type == "exact":
                        msg = "Successfully applied exact match replacement."
                    else:
                        msg = (
                            f"Successfully applied fuzzy match replacement "
                            f"(confidence: {confidence:.2f})."
                        )

                    return ToolResult.ok(
                        {"file_path": str(file_path), "message": msg},
                        diff=diff,
                    )

                # Try exact match first
                if search_block in content:
                    new_content = content.replace(search_block, replace_block, 1)
                    return validate_and_write(new_content, "exact")

                # Fallback to fuzzy match
                match = find_best_match(content, search_block)
                if match:
                    # Construct new content
                    new_content = (
                        content[: match.start_index] + replace_block + content[match.end_index :]
                    )
                    return validate_and_write(new_content, "fuzzy", match.confidence)

                return ToolResult.fail(
                    "Could not find the SEARCH block in the file. "
                    "Please verify the code exists and try again.",
                    error_type=ToolErrorType.EDIT_NO_OCCURRENCE_FOUND,
                )

        except Exception as e:
            return ToolResult.fail(
                f"Failed to apply diff: {e}", error_type=ToolErrorType.FILE_WRITE_FAILURE
            )
