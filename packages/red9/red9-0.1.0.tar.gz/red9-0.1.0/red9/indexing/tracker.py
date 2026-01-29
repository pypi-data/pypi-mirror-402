"""File change tracking for incremental indexing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class FileState:
    """State of a tracked file."""

    path: str
    mtime: float
    size: int
    content_hash: str

    def to_dict(self) -> dict[str, str | float | int]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str | float | int]) -> FileState:
        """Create from dictionary."""
        return cls(
            path=data["path"],
            mtime=data["mtime"],
            size=data["size"],
            content_hash=data["content_hash"],
        )

    @classmethod
    def from_file(cls, file_path: Path, project_root: Path) -> FileState:
        """Create FileState from an actual file."""
        stat = file_path.stat()
        content = file_path.read_bytes()
        content_hash = hashlib.md5(content).hexdigest()

        return cls(
            path=str(file_path.relative_to(project_root)),
            mtime=stat.st_mtime,
            size=stat.st_size,
            content_hash=content_hash,
        )


@dataclass
class IndexState:
    """Full index state - tracks all indexed files."""

    version: int = 1
    last_indexed: str = ""
    files: dict[str, FileState] = field(default_factory=dict)

    def to_dict(self) -> dict[str, int | str | dict[str, dict[str, str | float | int]]]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "last_indexed": self.last_indexed,
            "files": {path: state.to_dict() for path, state in self.files.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> IndexState:
        """Create from dictionary."""
        return cls(
            version=data.get("version", 1),
            last_indexed=data.get("last_indexed", ""),
            files={
                path: FileState.from_dict(state_data)
                for path, state_data in data.get("files", {}).items()
            },
        )


class IndexTracker:
    """Tracks file modifications for incremental indexing."""

    def __init__(self, project_root: Path, state_path: Path) -> None:
        """Initialize the index tracker.

        Args:
            project_root: Root directory of the project.
            state_path: Path to store index state (e.g., .red9/index_state.json).
        """
        self.project_root = project_root
        self.state_path = state_path
        self._state = self._load_state()

    def _load_state(self) -> IndexState:
        """Load state from disk."""
        if not self.state_path.exists():
            return IndexState()

        try:
            data = json.loads(self.state_path.read_text())
            return IndexState.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return IndexState()

    def save(self) -> None:
        """Persist state to disk."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self._state.to_dict(), indent=2))

    def get_changed_files(
        self,
        patterns: list[str],
        excludes: list[str] | None = None,
    ) -> tuple[list[Path], list[Path], list[Path]]:
        """Get files that have changed since last scan.

        Args:
            patterns: Glob patterns to include (e.g., ["**/*.py"]).
            excludes: Glob patterns to exclude.

        Returns:
            Tuple of (added, modified, deleted) file paths.
        """
        excludes = excludes or []

        # Collect current files
        current_files: dict[str, Path] = {}
        for pattern in patterns:
            for file_path in self.project_root.glob(pattern):
                if not file_path.is_file():
                    continue

                # Check excludes
                rel_path = str(file_path.relative_to(self.project_root))
                excluded = False
                for exclude_pattern in excludes:
                    if file_path.match(exclude_pattern):
                        excluded = True
                        break

                if not excluded:
                    current_files[rel_path] = file_path

        added: list[Path] = []
        modified: list[Path] = []
        deleted: list[Path] = []

        # Find added and modified files
        for rel_path, file_path in current_files.items():
            if rel_path not in self._state.files:
                added.append(file_path)
            else:
                # Check if modified
                old_state = self._state.files[rel_path]
                try:
                    new_state = FileState.from_file(file_path, self.project_root)
                    # Use content hash for accurate change detection
                    if new_state.content_hash != old_state.content_hash:
                        modified.append(file_path)
                except OSError:
                    # File became inaccessible, treat as deleted
                    deleted.append(file_path)

        # Find deleted files
        for rel_path in self._state.files:
            if rel_path not in current_files:
                deleted.append(self.project_root / rel_path)

        return added, modified, deleted

    def update_state(self, files: list[Path]) -> None:
        """Update tracked state for the given files.

        Args:
            files: Files that have been (re)indexed.
        """
        for file_path in files:
            try:
                state = FileState.from_file(file_path, self.project_root)
                self._state.files[state.path] = state
            except OSError:
                # File no longer exists, remove from state
                rel_path = str(file_path.relative_to(self.project_root))
                self._state.files.pop(rel_path, None)

        self._state.last_indexed = datetime.now().isoformat()

    def remove_from_state(self, files: list[Path]) -> None:
        """Remove files from tracked state (for deleted files).

        Args:
            files: Files that have been deleted.
        """
        for file_path in files:
            rel_path = str(file_path.relative_to(self.project_root))
            self._state.files.pop(rel_path, None)

    def has_indexed_files(self) -> bool:
        """Check if we have any indexed files."""
        return bool(self._state.files)

    def get_indexed_count(self) -> int:
        """Get the number of indexed files."""
        return len(self._state.files)

    def clear(self) -> None:
        """Clear all tracked state."""
        self._state = IndexState()
        if self.state_path.exists():
            self.state_path.unlink()

    def get_file_hashes(self) -> dict[str, str]:
        """Get content hashes for all tracked files.

        Returns:
            Dict mapping relative file paths to content hashes.
        """
        return {path: state.content_hash for path, state in self._state.files.items()}
