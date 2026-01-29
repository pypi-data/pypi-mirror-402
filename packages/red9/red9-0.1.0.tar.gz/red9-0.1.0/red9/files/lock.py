"""Thread-safe file access coordination for parallel agents.

Provides file-level locking to prevent race conditions when multiple
parallel agents attempt to write to the same file concurrently.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from red9.logging import get_logger

logger = get_logger(__name__)


class FileLockTimeoutError(Exception):
    """Raised when a file lock cannot be acquired within the timeout."""

    def __init__(self, file_path: Path, timeout: float) -> None:
        self.file_path = file_path
        self.timeout = timeout
        super().__init__(f"Could not acquire lock for {file_path} within {timeout}s")


class FileAccessManager:
    """Thread-safe file access coordination for parallel agents.

    Uses per-file RLocks to allow the same thread to acquire a lock
    multiple times (e.g., nested tool calls) while blocking other threads.

    This is a singleton - use get_file_manager() to get the global instance.
    """

    _instance: FileAccessManager | None = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize the file access manager."""
        self._locks: dict[Path, threading.RLock] = {}
        self._lock_metadata: dict[Path, dict] = {}
        self._lock_holders: dict[Path, int] = {}  # Maps file to holder thread id
        self._global_lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> FileAccessManager:
        """Get the singleton instance of FileAccessManager."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = FileAccessManager()
        return cls._instance

    def _get_or_create_lock(self, file_path: Path) -> threading.RLock:
        """Get or create a lock for the given file path.

        Args:
            file_path: The file path to get a lock for.

        Returns:
            The RLock for this file.
        """
        resolved = file_path.resolve()

        with self._global_lock:
            if resolved not in self._locks:
                self._locks[resolved] = threading.RLock()
                self._lock_metadata[resolved] = {
                    "created_at": threading.current_thread().name,
                    "acquire_count": 0,
                }
            return self._locks[resolved]

    def acquire(self, file_path: Path, timeout: float = 30.0) -> bool:
        """Acquire exclusive write access to a file.

        Args:
            file_path: The file to lock.
            timeout: Maximum time to wait for the lock (seconds).

        Returns:
            True if lock was acquired, False if timeout.

        Raises:
            FileLockTimeoutError: If the lock cannot be acquired within timeout.
        """
        resolved = file_path.resolve()
        lock = self._get_or_create_lock(resolved)

        acquired = lock.acquire(timeout=timeout)

        if acquired:
            with self._global_lock:
                self._lock_metadata[resolved]["acquire_count"] += 1
                self._lock_holders[resolved] = threading.current_thread().ident
            logger.debug(f"Acquired lock for {resolved}")
        else:
            logger.warning(f"Timeout acquiring lock for {resolved} after {timeout}s")
            raise FileLockTimeoutError(resolved, timeout)

        return acquired

    def release(self, file_path: Path) -> None:
        """Release the lock on a file.

        Args:
            file_path: The file to unlock.
        """
        resolved = file_path.resolve()

        with self._global_lock:
            if resolved in self._locks:
                try:
                    self._locks[resolved].release()
                    # Clear holder tracking
                    if resolved in self._lock_holders:
                        del self._lock_holders[resolved]
                    logger.debug(f"Released lock for {resolved}")
                except RuntimeError:
                    # Lock not held - ignore
                    pass

    @contextmanager
    def locked(self, file_path: Path, timeout: float = 30.0) -> Iterator[Path]:
        """Context manager for exclusive file access.

        Args:
            file_path: The file to lock.
            timeout: Maximum time to wait for the lock.

        Yields:
            The resolved file path.

        Raises:
            FileLockTimeoutError: If the lock cannot be acquired within timeout.

        Example:
            with file_manager.locked(Path("src/utils.py")):
                # Safe to write to the file
                file_path.write_text(content)
        """
        resolved = file_path.resolve()
        self.acquire(resolved, timeout=timeout)
        try:
            yield resolved
        finally:
            self.release(resolved)

    def is_locked(self, file_path: Path) -> bool:
        """Check if a file is currently locked.

        Note: This is a snapshot - the state may change immediately after.

        Args:
            file_path: The file to check.

        Returns:
            True if the file is locked by any thread.
        """
        resolved = file_path.resolve()

        with self._global_lock:
            # Use holder tracking for accurate status
            return resolved in self._lock_holders

    def get_stats(self) -> dict[str, int]:
        """Get statistics about file locks.

        Returns:
            Dictionary with lock statistics.
        """
        with self._global_lock:
            return {
                "total_files_tracked": len(self._locks),
                "currently_locked": len(self._lock_holders),
            }

    def clear(self) -> None:
        """Clear all locks. Use only for testing/cleanup.

        Warning: This does not release held locks, just clears the registry.
        """
        with self._global_lock:
            self._locks.clear()
            self._lock_metadata.clear()
            self._lock_holders.clear()


def get_file_manager() -> FileAccessManager:
    """Get the global FileAccessManager instance.

    Returns:
        The singleton FileAccessManager.
    """
    return FileAccessManager.get_instance()
