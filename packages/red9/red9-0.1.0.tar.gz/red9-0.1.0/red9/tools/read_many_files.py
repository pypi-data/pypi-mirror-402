"""Bulk file reading tool.

Reads multiple files in a single tool call to reduce token overhead.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from red9.tools.base import (
    Tool,
    ToolDefinition,
    ToolErrorType,
    ToolResult,
    get_project_root,
    validate_path,
)

# Limits to prevent context explosion
MAX_FILES = 50
MAX_LINES_PER_FILE = 500
MAX_TOTAL_CHARS = 100_000
DEFAULT_LINES_PER_FILE = 200


class ReadManyFilesTool(Tool):
    """Tool for reading multiple files in a single operation.

    More efficient than multiple read_file calls as it:
    - Reduces tool call overhead
    - Applies consistent limits across all files
    - Returns structured output with clear separators
    """

    @property
    def name(self) -> str:
        return "read_many_files"

    @property
    def description(self) -> str:
        return (
            "Read multiple files in a single operation. More efficient than "
            "multiple read_file calls. Returns structured output with file "
            "contents and metadata. Supports both explicit file paths and "
            "glob patterns."
        )

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
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "List of file paths to read. Relative paths are "
                            "resolved from project root."
                        ),
                    },
                    "pattern": {
                        "type": "string",
                        "description": (
                            "Optional glob pattern to find files (e.g., 'src/**/*.py'). "
                            "If provided, file_paths is ignored."
                        ),
                    },
                    "max_lines_per_file": {
                        "type": "integer",
                        "description": (
                            f"Maximum lines to read per file. Default: "
                            f"{DEFAULT_LINES_PER_FILE}, max: {MAX_LINES_PER_FILE}."
                        ),
                        "default": DEFAULT_LINES_PER_FILE,
                    },
                    "max_total_chars": {
                        "type": "integer",
                        "description": (
                            f"Maximum total characters across all files. "
                            f"Default/max: {MAX_TOTAL_CHARS}."
                        ),
                        "default": MAX_TOTAL_CHARS,
                    },
                },
                "required": [],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute bulk file reading.

        Args:
            params: Tool parameters.

        Returns:
            ToolResult with file contents.
        """
        file_paths = params.get("file_paths", [])
        pattern = params.get("pattern")
        max_lines = min(
            params.get("max_lines_per_file", DEFAULT_LINES_PER_FILE),
            MAX_LINES_PER_FILE,
        )
        max_chars = min(
            params.get("max_total_chars", MAX_TOTAL_CHARS),
            MAX_TOTAL_CHARS,
        )

        # Get files from pattern if provided
        if pattern:
            file_paths = self._glob_files(pattern)

        if not file_paths:
            return ToolResult.fail(
                "No files specified. Provide file_paths or pattern.",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        # Limit number of files
        if len(file_paths) > MAX_FILES:
            file_paths = file_paths[:MAX_FILES]

        # Read files
        results: list[dict[str, Any]] = []
        total_chars = 0
        files_read = 0
        files_skipped = 0
        truncated_files = 0

        for path_str in file_paths:
            # Check total character limit
            if total_chars >= max_chars:
                files_skipped += len(file_paths) - files_read
                break

            # Validate path
            validated_path, error = validate_path(path_str, must_exist=True)
            if error:
                results.append(
                    {
                        "path": path_str,
                        "error": error,
                        "content": None,
                    }
                )
                files_read += 1
                continue

            assert validated_path is not None

            if validated_path.is_dir():
                results.append(
                    {
                        "path": path_str,
                        "error": "Is a directory",
                        "content": None,
                    }
                )
                files_read += 1
                continue

            # Read file with limits
            try:
                content, was_truncated = self._read_file_limited(
                    validated_path,
                    max_lines=max_lines,
                    max_chars=max_chars - total_chars,
                )

                # Convert to relative path
                project_root = get_project_root()
                try:
                    rel_path = str(validated_path.relative_to(project_root))
                except ValueError:
                    rel_path = str(validated_path)

                results.append(
                    {
                        "path": rel_path,
                        "content": content,
                        "lines": content.count("\n") + 1 if content else 0,
                        "truncated": was_truncated,
                    }
                )

                total_chars += len(content)
                files_read += 1
                if was_truncated:
                    truncated_files += 1

            except PermissionError:
                results.append(
                    {
                        "path": path_str,
                        "error": "Permission denied",
                        "content": None,
                    }
                )
                files_read += 1
            except UnicodeDecodeError:
                results.append(
                    {
                        "path": path_str,
                        "error": "Binary or non-UTF-8 file",
                        "content": None,
                    }
                )
                files_read += 1
            except OSError as e:
                results.append(
                    {
                        "path": path_str,
                        "error": str(e),
                        "content": None,
                    }
                )
                files_read += 1

        return ToolResult.ok(
            {
                "files_read": files_read,
                "files_skipped": files_skipped,
                "truncated_files": truncated_files,
                "total_chars": total_chars,
                "files": results,
            }
        )

    def _glob_files(self, pattern: str) -> list[str]:
        """Find files matching glob pattern.

        Args:
            pattern: Glob pattern.

        Returns:
            List of matching file paths.
        """
        project_root = get_project_root()
        matches = list(project_root.glob(pattern))

        # Filter to files only, sort by path
        files = sorted(
            [str(m) for m in matches if m.is_file()],
            key=lambda p: p.lower(),
        )

        return files[:MAX_FILES]

    def _read_file_limited(
        self,
        path: Path,
        max_lines: int,
        max_chars: int,
    ) -> tuple[str, bool]:
        """Read file with line and character limits.

        Args:
            path: File to read.
            max_lines: Maximum lines to read.
            max_chars: Maximum characters to read.

        Returns:
            Tuple of (content, was_truncated).
        """
        lines: list[str] = []
        total_chars = 0
        truncated = False

        with path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    truncated = True
                    break

                if total_chars + len(line) > max_chars:
                    # Truncate this line if needed
                    remaining = max_chars - total_chars
                    if remaining > 0:
                        lines.append(line[:remaining])
                    truncated = True
                    break

                lines.append(line)
                total_chars += len(line)

        content = "".join(lines)
        return content, truncated
