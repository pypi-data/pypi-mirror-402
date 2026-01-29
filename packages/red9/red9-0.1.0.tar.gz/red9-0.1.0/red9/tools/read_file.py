"""Read file tool implementation with caching."""

from __future__ import annotations

import os
import threading
from collections import OrderedDict
from typing import Any

from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult, validate_path

# Global file read cache with LRU eviction
# Key: (file_path, mtime) -> Value: file content
_file_cache: OrderedDict[tuple[str, float], str] = OrderedDict()
_cache_lock = threading.Lock()
_MAX_CACHE_SIZE = 100  # Max cached files
_MAX_FILE_SIZE = 1024 * 1024  # Don't cache files > 1MB


def _get_cached_content(file_path: str) -> str | None:
    """Get cached file content if still valid.

    Args:
        file_path: Absolute path to the file.

    Returns:
        Cached content if valid, None otherwise.
    """
    try:
        mtime = os.path.getmtime(file_path)
        cache_key = (file_path, mtime)

        with _cache_lock:
            if cache_key in _file_cache:
                # Move to end (most recently used)
                _file_cache.move_to_end(cache_key)
                return _file_cache[cache_key]
    except (OSError, KeyError):
        pass
    return None


def _cache_content(file_path: str, content: str) -> None:
    """Cache file content.

    Args:
        file_path: Absolute path to the file.
        content: File content to cache.
    """
    # Don't cache large files
    if len(content) > _MAX_FILE_SIZE:
        return

    try:
        mtime = os.path.getmtime(file_path)
        cache_key = (file_path, mtime)

        with _cache_lock:
            # Evict oldest entries if at capacity
            while len(_file_cache) >= _MAX_CACHE_SIZE:
                _file_cache.popitem(last=False)

            _file_cache[cache_key] = content
    except OSError:
        pass


def clear_file_cache() -> None:
    """Clear the file read cache."""
    with _cache_lock:
        _file_cache.clear()


class ReadFileTool(Tool):
    """Read file contents with line numbers and caching."""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return """Read the contents of a file at the given path.
Returns file content with line numbers for reference.
Use this BEFORE edit_file to see current content."""

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
                        "description": "Path to the file to read",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Starting line number (1-indexed, optional)",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Ending line number (inclusive, optional)",
                    },
                },
                "required": ["file_path"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        raw_path = params.get("file_path", "")
        start_line = params.get("start_line", 1)
        end_line = params.get("end_line")

        if not raw_path:
            return ToolResult.fail(
                "file_path is required",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        # Validate path for security
        file_path, error = validate_path(raw_path, must_exist=True)
        if error:
            error_type = ToolErrorType.PERMISSION_DENIED
            if "not found" in error.lower():
                error_type = ToolErrorType.FILE_NOT_FOUND
            return ToolResult.fail(error, error_type=error_type)

        if not file_path.is_file():
            return ToolResult.fail(
                f"Not a file: {file_path}",
                error_type=ToolErrorType.FILE_NOT_FOUND,
            )

        try:
            # Try cache first
            file_path_str = str(file_path)
            content = _get_cached_content(file_path_str)

            if content is None:
                # Read from disk and cache
                content = file_path.read_text()
                _cache_content(file_path_str, content)

            lines = content.splitlines()
            total_lines = len(lines)

            # Validate line numbers
            start_line = max(1, start_line)
            if end_line is None:
                end_line = total_lines
            else:
                end_line = min(end_line, total_lines)

            # Extract requested lines
            selected_lines = lines[start_line - 1 : end_line]

            # Add line numbers
            numbered_lines = [
                f"{i + start_line:4d} | {line}" for i, line in enumerate(selected_lines)
            ]

            return ToolResult.ok(
                {
                    "content": "\n".join(numbered_lines),
                    "raw_content": "\n".join(selected_lines),
                    "total_lines": total_lines,
                    "shown_lines": len(selected_lines),
                    "start_line": start_line,
                    "end_line": end_line,
                    "file_path": file_path_str,
                }
            )

        except PermissionError:
            return ToolResult.fail(
                f"Permission denied: {file_path}",
                error_type=ToolErrorType.PERMISSION_DENIED,
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to read file: {e}")
