"""File watcher for detecting external changes.

Monitors files for changes made outside of RED9 and warns before
overwriting them.
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from red9.logging import get_logger

logger = get_logger(__name__)

# Try to import watchdog, fall back to polling if not available
try:
    from watchdog.events import FileModifiedEvent, FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None  # type: ignore
    FileSystemEventHandler = object  # type: ignore
    FileModifiedEvent = None  # type: ignore


@dataclass
class FileState:
    """State of a tracked file."""

    path: Path
    content_hash: str
    modified_time: float
    size: int
    modified_externally: bool = False
    last_checked: float = field(default_factory=time.time)


class FileWatcher:
    """Watches files for external modifications.

    Tracks files that RED9 is working with and detects when they're
    modified by external processes. Uses watchdog if available,
    falls back to polling otherwise.
    """

    def __init__(
        self,
        use_polling: bool = False,
        poll_interval: float = 1.0,
    ) -> None:
        """Initialize file watcher.

        Args:
            use_polling: Force polling mode even if watchdog is available.
            poll_interval: Seconds between polls in polling mode.
        """
        self._tracked_files: dict[str, FileState] = {}
        self._lock = threading.Lock()
        self._use_polling = use_polling or not WATCHDOG_AVAILABLE
        self._poll_interval = poll_interval
        self._observer: Observer | None = None
        self._polling_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._change_callbacks: list[Callable[[Path], None]] = []

    def track_file(self, path: Path | str) -> None:
        """Start tracking a file.

        Args:
            path: Path to the file to track.
        """
        path = Path(path).resolve()

        with self._lock:
            if str(path) in self._tracked_files:
                return

            if not path.exists():
                logger.debug(f"File does not exist, will track when created: {path}")
                return

            state = self._create_file_state(path)
            self._tracked_files[str(path)] = state
            logger.debug(f"Now tracking file: {path}")

    def untrack_file(self, path: Path | str) -> None:
        """Stop tracking a file.

        Args:
            path: Path to the file to stop tracking.
        """
        path = Path(path).resolve()

        with self._lock:
            if str(path) in self._tracked_files:
                del self._tracked_files[str(path)]
                logger.debug(f"Stopped tracking file: {path}")

    def update_file_state(self, path: Path | str) -> None:
        """Update the tracked state of a file.

        Call this after RED9 modifies a file to update the baseline.

        Args:
            path: Path to the file.
        """
        path = Path(path).resolve()

        with self._lock:
            if str(path) in self._tracked_files:
                if path.exists():
                    self._tracked_files[str(path)] = self._create_file_state(path)

    def is_modified_externally(self, path: Path | str) -> bool:
        """Check if a file was modified externally.

        Args:
            path: Path to the file.

        Returns:
            True if the file was modified externally since last tracked.
        """
        path = Path(path).resolve()

        with self._lock:
            state = self._tracked_files.get(str(path))
            if state is None:
                return False

            if state.modified_externally:
                return True

            # Check current state
            if path.exists():
                current_hash = self._compute_hash(path)
                if current_hash != state.content_hash:
                    state.modified_externally = True
                    return True

            return False

    def get_external_changes(self) -> list[Path]:
        """Get list of files modified externally.

        Returns:
            List of paths that were modified externally.
        """
        changed: list[Path] = []

        with self._lock:
            for path_str, state in self._tracked_files.items():
                path = Path(path_str)
                if state.modified_externally:
                    changed.append(path)
                elif path.exists():
                    current_hash = self._compute_hash(path)
                    if current_hash != state.content_hash:
                        state.modified_externally = True
                        changed.append(path)

        return changed

    def clear_external_flag(self, path: Path | str) -> None:
        """Clear the externally modified flag for a file.

        Args:
            path: Path to the file.
        """
        path = Path(path).resolve()

        with self._lock:
            state = self._tracked_files.get(str(path))
            if state:
                state.modified_externally = False
                # Update state to current
                if path.exists():
                    self._tracked_files[str(path)] = self._create_file_state(path)

    def on_change(self, callback: Callable[[Path], None]) -> None:
        """Register a callback for file changes.

        Args:
            callback: Function to call when a tracked file changes.
        """
        self._change_callbacks.append(callback)

    def start(self) -> None:
        """Start watching for file changes."""
        if self._use_polling:
            self._start_polling()
        else:
            self._start_watchdog()

    def stop(self) -> None:
        """Stop watching for file changes."""
        self._stop_event.set()

        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5.0)
            self._observer = None

        if self._polling_thread:
            self._polling_thread.join(timeout=5.0)
            self._polling_thread = None

    def _create_file_state(self, path: Path) -> FileState:
        """Create a FileState for a file.

        Args:
            path: Path to the file.

        Returns:
            FileState instance.
        """
        stat = path.stat()
        return FileState(
            path=path,
            content_hash=self._compute_hash(path),
            modified_time=stat.st_mtime,
            size=stat.st_size,
        )

    def _compute_hash(self, path: Path) -> str:
        """Compute content hash of a file.

        Args:
            path: Path to the file.

        Returns:
            MD5 hash of content.
        """
        try:
            content = path.read_bytes()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return ""

    def _start_polling(self) -> None:
        """Start polling mode."""
        self._stop_event.clear()
        self._polling_thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
        )
        self._polling_thread.start()
        logger.debug("File watcher started (polling mode)")

    def _poll_loop(self) -> None:
        """Main polling loop."""
        while not self._stop_event.wait(self._poll_interval):
            self._check_all_files()

    def _check_all_files(self) -> None:
        """Check all tracked files for changes."""
        with self._lock:
            for path_str, state in list(self._tracked_files.items()):
                path = Path(path_str)
                if not path.exists():
                    continue

                current_hash = self._compute_hash(path)
                if current_hash != state.content_hash and not state.modified_externally:
                    state.modified_externally = True
                    self._notify_change(path)

    def _notify_change(self, path: Path) -> None:
        """Notify callbacks of a file change.

        Args:
            path: Path that changed.
        """
        for callback in self._change_callbacks:
            try:
                callback(path)
            except Exception as e:
                logger.error(f"Change callback error for {path}: {e}")

    def _start_watchdog(self) -> None:
        """Start watchdog mode."""
        if not WATCHDOG_AVAILABLE:
            logger.warning("Watchdog not available, falling back to polling")
            self._start_polling()
            return

        handler = _WatchdogHandler(self)
        self._observer = Observer()

        # Watch directories containing tracked files
        watched_dirs: set[str] = set()
        for path_str in self._tracked_files:
            dir_path = str(Path(path_str).parent)
            if dir_path not in watched_dirs:
                self._observer.schedule(handler, dir_path, recursive=False)
                watched_dirs.add(dir_path)

        self._observer.start()
        logger.debug("File watcher started (watchdog mode)")


class _WatchdogHandler(FileSystemEventHandler):  # type: ignore[misc]
    """Watchdog event handler for FileWatcher."""

    def __init__(self, watcher: FileWatcher) -> None:
        self._watcher = watcher

    def on_modified(self, event: FileModifiedEvent) -> None:  # type: ignore[override]
        """Handle file modification event."""
        if event.is_directory:
            return

        path = Path(event.src_path).resolve()

        with self._watcher._lock:
            state = self._watcher._tracked_files.get(str(path))
            if state and not state.modified_externally:
                current_hash = self._watcher._compute_hash(path)
                if current_hash != state.content_hash:
                    state.modified_externally = True
                    self._watcher._notify_change(path)


# Global watcher instance
_file_watcher: FileWatcher | None = None


def get_file_watcher() -> FileWatcher:
    """Get the global file watcher instance.

    Returns:
        FileWatcher instance.
    """
    global _file_watcher
    if _file_watcher is None:
        _file_watcher = FileWatcher()
    return _file_watcher


def set_file_watcher(watcher: FileWatcher) -> None:
    """Set the global file watcher instance.

    Args:
        watcher: FileWatcher to use globally.
    """
    global _file_watcher
    _file_watcher = watcher
