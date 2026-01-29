"""Edit file tool implementation with fuzzy matching fallback."""

from __future__ import annotations

from typing import Any

from red9.files.diff import generate_unified_diff
from red9.files.fuzzy_match import find_best_match
from red9.files.lock import FileLockTimeoutError, get_file_manager
from red9.logging import get_logger
from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult, validate_path

logger = get_logger(__name__)

# Fuzzy matching configuration
FUZZY_MATCH_THRESHOLD = 0.8  # Minimum similarity for auto-match
HIGH_CONFIDENCE_THRESHOLD = 0.9  # Threshold for high confidence match


class EditFileTool(Tool):
    """Replace text in a file with fuzzy matching fallback."""

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return """Replace text in a file.

CRITICAL REQUIREMENTS:
1. old_string should match the text to replace (including whitespace)
2. The text must appear exactly once (unless replace_all=true)
3. Use read_file first to see current content

The tool supports:
- Exact matching (preferred, fastest)
- Fuzzy matching fallback when exact match fails due to minor
  whitespace/indentation differences

The tool will fail if:
- old_string is not found (even with fuzzy matching)
- Multiple matches found (unless replace_all=true)
- old_string equals new_string (no change)"""

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
                    "old_string": {
                        "type": "string",
                        "description": "Exact text to find and replace",
                    },
                    "new_string": {
                        "type": "string",
                        "description": "Replacement text",
                    },
                    "replace_all": {
                        "type": "boolean",
                        "description": "Replace all occurrences (default: false)",
                    },
                },
                "required": ["file_path", "old_string", "new_string"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        raw_path = params.get("file_path", "")
        old_string = params.get("old_string", "")
        new_string = params.get("new_string", "")
        replace_all = params.get("replace_all", False)

        if not raw_path:
            return ToolResult.fail(
                "file_path is required",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        # Validate path for security (don't require existence for new files)
        file_path, error = validate_path(raw_path, must_exist=False)
        if error:
            return ToolResult.fail(error, error_type=ToolErrorType.PERMISSION_DENIED)

        # Acquire file lock for thread-safe editing
        file_manager = get_file_manager()

        try:
            with file_manager.locked(file_path, timeout=30.0):
                # Handle file creation (old_string empty)
                if old_string == "" and not file_path.exists():
                    try:
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(new_string)
                        diff = generate_unified_diff("", new_string, str(file_path))
                        return ToolResult.ok(
                            {
                                "file_path": str(file_path),
                                "is_new_file": True,
                                "occurrences_replaced": 0,
                            },
                            diff=diff,
                        )
                    except Exception as e:
                        return ToolResult.fail(
                            f"Failed to create file: {e}",
                            error_type=ToolErrorType.FILE_WRITE_FAILURE,
                        )

                if not file_path.exists():
                    return ToolResult.fail(
                        f"File not found: {file_path}",
                        error_type=ToolErrorType.FILE_NOT_FOUND,
                    )

                try:
                    original_content = file_path.read_text()
                    # Normalize line endings
                    original_content = original_content.replace("\r\n", "\n")
                    old_string = old_string.replace("\r\n", "\n")
                    new_string = new_string.replace("\r\n", "\n")

                except PermissionError:
                    return ToolResult.fail(
                        f"Permission denied: {file_path}",
                        error_type=ToolErrorType.PERMISSION_DENIED,
                    )
                except Exception as e:
                    return ToolResult.fail(f"Failed to read file: {e}")

                # Check for no-change case first
                if old_string == new_string:
                    return ToolResult.fail(
                        "old_string and new_string are identical - no change needed",
                        error_type=ToolErrorType.EDIT_NO_CHANGE,
                    )

                # Try exact match first
                occurrences = original_content.count(old_string)
                match_type = "exact"
                actual_old_string = old_string
                fuzzy_info: dict[str, Any] | None = None

                if occurrences == 0:
                    # Try fuzzy matching as fallback
                    match = find_best_match(
                        original_content,  # Source first
                        old_string,  # Block to find
                        threshold=FUZZY_MATCH_THRESHOLD,
                    )

                    if match:
                        # Use the fuzzy match
                        actual_old_string = match.matched_text
                        occurrences = original_content.count(actual_old_string)
                        match_type = "fuzzy"

                        fuzzy_info = {
                            "fuzzy_match": True,
                            "similarity": round(match.confidence, 3),
                            "match_type": match_type,
                            "confidence": match.confidence,
                        }

                        logger.info(f"Fuzzy match found with {match.confidence:.0%} confidence")
                    else:
                        return ToolResult.fail(
                            "old_string not found in file. "
                            "Ensure exact match including whitespace.",
                            error_type=ToolErrorType.EDIT_NO_OCCURRENCE_FOUND,
                        )

                if occurrences > 1 and not replace_all:
                    return ToolResult.fail(
                        f"Found {occurrences} occurrences. "
                        "Use replace_all=true or provide more context.",
                        error_type=ToolErrorType.EDIT_MULTIPLE_OCCURRENCES,
                    )

                # Apply replacement using the matched string
                if replace_all:
                    new_content = original_content.replace(actual_old_string, new_string)
                    replaced_count = occurrences
                else:
                    new_content = original_content.replace(actual_old_string, new_string, 1)
                    replaced_count = 1

                # Generate diff
                diff = generate_unified_diff(original_content, new_content, str(file_path))

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
                            f"Please fix your edit - the old_string or new_string "
                            f"is incorrect.",
                            error_type=ToolErrorType.EDIT_VALIDATION_FAILED,
                        )

                # Write file
                try:
                    file_path.write_text(new_content)
                except Exception as e:
                    return ToolResult.fail(
                        f"Failed to write file: {e}",
                        error_type=ToolErrorType.FILE_WRITE_FAILURE,
                    )

                result_output: dict[str, Any] = {
                    "file_path": str(file_path),
                    "occurrences_replaced": replaced_count,
                    "is_new_file": False,
                    "match_type": match_type,
                }
                if fuzzy_info:
                    result_output.update(fuzzy_info)

                return ToolResult.ok(result_output, diff=diff)

        except FileLockTimeoutError as e:
            return ToolResult.fail(
                f"Could not acquire file lock: {e}",
                error_type=ToolErrorType.FILE_WRITE_FAILURE,
            )
