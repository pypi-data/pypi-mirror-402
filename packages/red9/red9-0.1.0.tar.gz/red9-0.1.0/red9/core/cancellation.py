"""Global cancellation handling for RED9 workflows.

Provides a thread-safe cancellation mechanism that allows graceful
interruption of workflows when the user presses Ctrl+C.
"""

from __future__ import annotations

import signal
import threading
from collections.abc import Callable


class CancellationToken:
    """Thread-safe cancellation token for workflow interruption.

    Usage:
        token = CancellationToken()

        # In main thread, install signal handler
        token.install_signal_handler()

        # In worker threads, check for cancellation
        if token.is_cancelled:
            return

        # Or use as callback
        agent = AgentLoop(cancellation_check=token.is_cancelled)
    """

    def __init__(self) -> None:
        self._cancelled = threading.Event()
        self._original_handler: Callable | None = None
        self._cancel_callbacks: list[Callable[[], None]] = []
        self._lock = threading.Lock()

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancelled.is_set()

    def cancel(self) -> None:
        """Request cancellation."""
        self._cancelled.set()
        # Notify all callbacks
        with self._lock:
            for callback in self._cancel_callbacks:
                try:
                    callback()
                except Exception:
                    pass  # Don't let callback errors propagate

    def reset(self) -> None:
        """Reset the cancellation token for reuse."""
        self._cancelled.clear()

    def add_callback(self, callback: Callable[[], None]) -> None:
        """Add a callback to be called when cancellation is requested."""
        with self._lock:
            self._cancel_callbacks.append(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove a cancellation callback."""
        with self._lock:
            try:
                self._cancel_callbacks.remove(callback)
            except ValueError:
                pass

    def install_signal_handler(self) -> None:
        """Install SIGINT handler to trigger cancellation on Ctrl+C.

        Must be called from the main thread.
        """

        def handler(signum: int, frame: object) -> None:
            self.cancel()
            # Re-raise KeyboardInterrupt for normal Python behavior
            raise KeyboardInterrupt()

        self._original_handler = signal.signal(signal.SIGINT, handler)

    def uninstall_signal_handler(self) -> None:
        """Restore the original SIGINT handler."""
        if self._original_handler is not None:
            signal.signal(signal.SIGINT, self._original_handler)
            self._original_handler = None

    def __enter__(self) -> CancellationToken:
        """Context manager entry - installs signal handler."""
        self.install_signal_handler()
        return self

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: object) -> bool:
        """Context manager exit - restores original handler."""
        self.uninstall_signal_handler()
        return False  # Don't suppress exceptions


# Global cancellation token for the current workflow
_current_token: CancellationToken | None = None
_token_lock = threading.Lock()


def get_cancellation_token() -> CancellationToken | None:
    """Get the current cancellation token if one is active."""
    return _current_token


def set_cancellation_token(token: CancellationToken | None) -> None:
    """Set the current cancellation token."""
    global _current_token
    with _token_lock:
        _current_token = token


def is_cancelled() -> bool:
    """Check if the current workflow is cancelled.

    This can be used as a cancellation_check callback for AgentLoop.
    """
    token = _current_token
    return token.is_cancelled if token else False


def request_cancellation() -> None:
    """Request cancellation of the current workflow."""
    token = _current_token
    if token:
        token.cancel()
