"""Directory listing tool.

Provides structured directory listing without relying on shell commands.
"""

from __future__ import annotations

import stat
from dataclasses import dataclass
from datetime import UTC, datetime
from fnmatch import fnmatch
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


@dataclass
class FileInfo:
    """Information about a file or directory."""

    name: str
    path: str
    is_dir: bool
    size: int | None = None
    modified: str | None = None
    permissions: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "name": self.name,
            "path": self.path,
            "type": "directory" if self.is_dir else "file",
        }
        if self.size is not None:
            result["size"] = self.size
        if self.modified is not None:
            result["modified"] = self.modified
        if self.permissions is not None:
            result["permissions"] = self.permissions
        return result


class ListDirTool(Tool):
    """Tool for listing directory contents.

    Provides structured output with optional metadata, filtering,
    and recursive depth control.
    """

    @property
    def name(self) -> str:
        return "list_dir"

    @property
    def description(self) -> str:
        return (
            "List files and directories in a path. Returns structured output with "
            "optional metadata (size, modification time, permissions). "
            "Supports pattern filtering and depth control for recursive listing."
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
                    "path": {
                        "type": "string",
                        "description": (
                            "Directory path to list. Relative paths are resolved from project root."
                        ),
                    },
                    "pattern": {
                        "type": "string",
                        "description": (
                            "Optional glob pattern to filter results (e.g., '*.py', "
                            "'test_*'). Applied to file/directory names."
                        ),
                    },
                    "depth": {
                        "type": "integer",
                        "description": (
                            "Maximum depth for recursive listing. 1 = current "
                            "directory only (default), 0 = unlimited."
                        ),
                        "default": 1,
                    },
                    "include_hidden": {
                        "type": "boolean",
                        "description": "Include hidden files (starting with '.').",
                        "default": False,
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "description": (
                            "Include file metadata (size, modification time, permissions)."
                        ),
                        "default": False,
                    },
                },
                "required": ["path"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute directory listing.

        Args:
            params: Tool parameters including path, pattern, depth, etc.

        Returns:
            ToolResult with list of files/directories.
        """
        path_str = params.get("path", ".")
        pattern = params.get("pattern")
        depth = params.get("depth", 1)
        include_hidden = params.get("include_hidden", False)
        include_metadata = params.get("include_metadata", False)

        # Validate path
        validated_path, error = validate_path(path_str, must_exist=True)
        if error:
            return ToolResult.fail(error, error_type=ToolErrorType.FILE_NOT_FOUND)

        assert validated_path is not None

        if not validated_path.is_dir():
            return ToolResult.fail(
                f"Not a directory: {path_str}",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        try:
            entries = self._list_directory(
                validated_path,
                pattern=pattern,
                depth=depth,
                current_depth=1,
                include_hidden=include_hidden,
                include_metadata=include_metadata,
            )

            # Convert to relative paths from project root
            project_root = get_project_root()
            for entry in entries:
                try:
                    rel_path = Path(entry["path"]).relative_to(project_root)
                    entry["path"] = str(rel_path)
                except ValueError:
                    pass  # Keep absolute if outside project

            return ToolResult.ok(
                {
                    "path": path_str,
                    "count": len(entries),
                    "entries": entries,
                }
            )

        except PermissionError as e:
            return ToolResult.fail(
                f"Permission denied: {e}",
                error_type=ToolErrorType.PERMISSION_DENIED,
            )
        except OSError as e:
            return ToolResult.fail(
                f"Error listing directory: {e}",
                error_type=ToolErrorType.EXECUTION_ERROR,
            )

    def _list_directory(
        self,
        path: Path,
        pattern: str | None,
        depth: int,
        current_depth: int,
        include_hidden: bool,
        include_metadata: bool,
    ) -> list[dict[str, Any]]:
        """Recursively list directory contents.

        Args:
            path: Directory to list.
            pattern: Optional glob pattern.
            depth: Maximum depth (0 = unlimited).
            current_depth: Current recursion depth.
            include_hidden: Include hidden files.
            include_metadata: Include file metadata.

        Returns:
            List of file info dictionaries.
        """
        entries: list[dict[str, Any]] = []

        try:
            items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return entries

        for item in items:
            # Skip hidden files if not included
            if not include_hidden and item.name.startswith("."):
                continue

            # Apply pattern filter
            if pattern and not fnmatch(item.name, pattern):
                # For directories, still recurse even if name doesn't match
                if not item.is_dir():
                    continue

            # Build file info
            info = FileInfo(
                name=item.name,
                path=str(item),
                is_dir=item.is_dir(),
            )

            if include_metadata:
                try:
                    stat_info = item.stat()
                    info.size = stat_info.st_size if not item.is_dir() else None
                    info.modified = datetime.fromtimestamp(stat_info.st_mtime, tz=UTC).isoformat()
                    info.permissions = stat.filemode(stat_info.st_mode)
                except OSError:
                    pass

            # Only add if matches pattern (or is directory we need to recurse)
            if not pattern or fnmatch(item.name, pattern):
                entries.append(info.to_dict())

            # Recurse into directories
            if item.is_dir() and (depth == 0 or current_depth < depth):
                sub_entries = self._list_directory(
                    item,
                    pattern=pattern,
                    depth=depth,
                    current_depth=current_depth + 1,
                    include_hidden=include_hidden,
                    include_metadata=include_metadata,
                )
                entries.extend(sub_entries)

        return entries
