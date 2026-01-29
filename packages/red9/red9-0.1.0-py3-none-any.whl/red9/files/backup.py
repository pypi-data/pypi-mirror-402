"""File backup management with copy-on-write."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


class BackupManager:
    """Manages file backups with copy-on-write semantics.

    Backups are stored in .red9/backups/{workflow_id}/ to allow
    per-workflow rollback.
    """

    def __init__(self, project_root: Path, workflow_id: str | None = None) -> None:
        """Initialize backup manager.

        Args:
            project_root: Root directory of the project.
            workflow_id: Optional workflow ID for organizing backups.
        """
        self.project_root = project_root
        self.workflow_id = workflow_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = project_root / ".red9" / "backups" / self.workflow_id
        self._backed_up: dict[str, Path] = {}

    def backup(self, file_path: Path) -> Path | None:
        """Create a backup of a file before modification.

        Args:
            file_path: Path to the file to backup.

        Returns:
            Path to the backup file, or None if file doesn't exist.
        """
        if not file_path.exists():
            return None

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Create backup path preserving relative structure
        try:
            relative = file_path.relative_to(self.project_root)
        except ValueError:
            relative = Path(file_path.name)

        backup_path = self.backup_dir / relative
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(file_path, backup_path)
        self._backed_up[str(file_path)] = backup_path

        return backup_path

    def restore(self, file_path: Path) -> bool:
        """Restore a file from backup.

        Args:
            file_path: Path to the file to restore.

        Returns:
            True if restored, False if no backup exists.
        """
        backup_path = self._backed_up.get(str(file_path))
        if not backup_path or not backup_path.exists():
            return False

        shutil.copy2(backup_path, file_path)
        return True

    def restore_all(self) -> int:
        """Restore all backed up files.

        Returns:
            Number of files restored.
        """
        restored = 0
        for file_path_str, backup_path in self._backed_up.items():
            if backup_path.exists():
                shutil.copy2(backup_path, file_path_str)
                restored += 1
        return restored

    def get_backed_up_files(self) -> list[str]:
        """Get list of files that have been backed up.

        Returns:
            List of file paths.
        """
        return list(self._backed_up.keys())

    def cleanup(self) -> None:
        """Remove all backups for this workflow."""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        self._backed_up.clear()

    @classmethod
    def list_backups(cls, project_root: Path) -> list[dict[str, Any]]:
        """List all available backups.

        Args:
            project_root: Project root directory.

        Returns:
            List of backup info dictionaries.
        """
        backup_root = project_root / ".red9" / "backups"
        if not backup_root.exists():
            return []

        backups = []
        for backup_dir in backup_root.iterdir():
            if backup_dir.is_dir():
                files = list(backup_dir.rglob("*"))
                files = [f for f in files if f.is_file()]
                backups.append(
                    {
                        "workflow_id": backup_dir.name,
                        "path": str(backup_dir),
                        "file_count": len(files),
                        "created": datetime.fromtimestamp(backup_dir.stat().st_mtime),
                    }
                )

        # Sort by creation time, newest first
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups
