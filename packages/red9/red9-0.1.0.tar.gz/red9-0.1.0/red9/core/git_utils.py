"""Git integration utilities."""

from __future__ import annotations

import subprocess
from pathlib import Path

from red9.logging import get_logger

logger = get_logger(__name__)


class GitRepository:
    """Simple wrapper around git CLI."""

    def __init__(self, root: Path):
        self.root = root

    def is_git_repo(self) -> bool:
        return (self.root / ".git").is_dir()

    def _run(self, args: list[str]) -> tuple[int, str, str]:
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            logger.error(f"Git command failed: {e}")
            return -1, "", str(e)

    def get_dirty_files(self) -> list[str]:
        """Get list of modified/untracked files."""
        code, stdout, _ = self._run(["status", "--porcelain"])
        if code != 0:
            return []

        files = []
        for line in stdout.splitlines():
            if len(line) > 3:
                files.append(line[3:])
        return files

    def add_all(self) -> bool:
        code, _, _ = self._run(["add", "."])
        return code == 0

    def commit(self, message: str) -> bool:
        code, _, err = self._run(["commit", "-m", message])
        if code != 0:
            logger.warning(f"Commit failed: {err}")
            return False
        return True

    def get_last_commit_hash(self) -> str | None:
        code, stdout, _ = self._run(["rev-parse", "HEAD"])
        if code == 0:
            return stdout.strip()
        return None
