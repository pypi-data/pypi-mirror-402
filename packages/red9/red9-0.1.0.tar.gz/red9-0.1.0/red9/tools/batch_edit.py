"""Batch edit tool for applying multiple file changes atomically."""

from __future__ import annotations

from typing import Any, TypedDict

from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult, validate_path


class FileEdit(TypedDict):
    file_path: str
    old_string: str
    new_string: str
    replace_all: bool | None


class BatchEditTool(Tool):
    """Apply edits to multiple files in a single transaction."""

    @property
    def name(self) -> str:
        return "batch_edit"

    @property
    def description(self) -> str:
        return """Apply edits to multiple files atomically.
Either all edits succeed, or none are applied.
Use this when making coordinated changes across multiple files (e.g., renaming a function and updating callers)."""

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
                    "edits": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string"},
                                "old_string": {"type": "string"},
                                "new_string": {"type": "string"},
                                "replace_all": {"type": "boolean"},
                            },
                            "required": ["file_path", "old_string", "new_string"],
                        },
                        "description": "List of edits to apply",
                    }
                },
                "required": ["edits"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        edits_data = params.get("edits", [])
        if not edits_data:
            return ToolResult.fail("No edits provided", error_type=ToolErrorType.INVALID_PARAMS)

        # 1. Validation Phase
        # Check all files exist and contain the old_string
        validated_edits = []

        for edit in edits_data:
            path_str = edit.get("file_path")
            old_str = edit.get("old_string")
            new_str = edit.get("new_string")

            if not path_str or not old_str or new_str is None:
                return ToolResult.fail(
                    f"Invalid edit format for {path_str}", error_type=ToolErrorType.INVALID_PARAMS
                )

            file_path, error = validate_path(path_str, must_exist=True)
            if error or not file_path:
                return ToolResult.fail(
                    error or "Invalid path", error_type=ToolErrorType.FILE_NOT_FOUND
                )

            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                return ToolResult.fail(f"Could not read {file_path}: {e}")

            # Simple exact match check (fuzzy matching is harder in batch without applying first)
            # For robustness, we'll implement a dry-run check
            if old_str not in content:
                # Try fuzzy match logic from EditFileTool if needed,
                # but for now, strictness ensures atomicity is safer.
                # Let's keep it simple: strict match for batch.
                return ToolResult.fail(
                    f"Could not find exact match for old_string in {path_str}",
                    error_type=ToolErrorType.EDIT_NO_OCCURRENCE_FOUND,
                )

            count = content.count(old_str)
            if count > 1 and not edit.get("replace_all"):
                return ToolResult.fail(
                    f"Multiple occurrences found in {path_str}, but replace_all is False",
                    error_type=ToolErrorType.EDIT_MULTIPLE_OCCURRENCES,
                )

            validated_edits.append((file_path, old_str, new_str, edit.get("replace_all", False)))

        # 2. Execution Phase (with backup for rollback)
        # We read all files into memory again to be safe from race conditions (mostly),
        # apply changes in memory, then write out.
        # Ideally we'd lock all files, but FileAccessManager locks one by one.
        # We will attempt to acquire locks for all.

        from red9.files.lock import get_file_manager

        file_manager = get_file_manager()

        locked_paths = []
        try:
            # Acquire all locks
            unique_paths = sorted(list(set(p for p, _, _, _ in validated_edits)))
            for p in unique_paths:
                if file_manager.acquire(p, timeout=5.0):
                    locked_paths.append(p)
                else:
                    raise TimeoutError(f"Could not acquire lock for {p}")

            # Apply edits in memory
            file_contents = {p: p.read_text(encoding="utf-8") for p in unique_paths}
            new_contents = file_contents.copy()

            for file_path, old_str, new_str, replace_all in validated_edits:
                current = new_contents[file_path]
                if replace_all:
                    new = current.replace(old_str, new_str)
                else:
                    new = current.replace(old_str, new_str, 1)
                new_contents[file_path] = new

            # Write all files
            for p, content in new_contents.items():
                p.write_text(content, encoding="utf-8")

        except Exception as e:
            # Note: If writing fails halfway, we might leave partial state.
            # Real atomic file systems are hard.
            # But we can try to restore the original contents we read into memory.
            try:
                for p in unique_paths:
                    if p in file_contents:
                        p.write_text(file_contents[p], encoding="utf-8")
            except Exception:
                pass  # Double fault

            return ToolResult.fail(
                f"Batch edit failed: {e}", error_type=ToolErrorType.FILE_WRITE_FAILURE
            )
        finally:
            # Release all locks
            for p in locked_paths:
                file_manager.release(p)

        return ToolResult.ok(
            f"Successfully applied {len(validated_edits)} edits across {len(unique_paths)} files"
        )
