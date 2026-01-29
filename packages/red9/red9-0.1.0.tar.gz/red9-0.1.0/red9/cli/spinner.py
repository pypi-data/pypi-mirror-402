"""Background spinner with 0.5s visibility delay and daemon thread.

Inspired by Aider's waiting.py, this provides a non-blocking spinner
that only becomes visible after 0.5s (to avoid flicker for fast operations).
Uses pre-rendered animation frames for smooth display.
"""

from __future__ import annotations

import sys
import threading
import time
from collections.abc import Callable

from rich.console import Console


class Spinner:
    """Low-level spinner with pre-rendered animation frames.

    The animation is pre-rendered into frames that bounce a marker
    back and forth. Supports both ASCII and Unicode terminals.
    """

    # Class variable to persist frame position across instances
    _last_frame_idx = 0

    def __init__(self, text: str = "Thinking..."):
        """Initialize the spinner.

        Args:
            text: Text to display next to the spinner animation.
        """
        self.text = text
        self.start_time = time.time()
        self.last_update = 0.0
        self.visible = False
        self.is_tty = sys.stdout.isatty()
        self.console = Console()
        self.last_display_len = 0

        # Pre-render ASCII animation frames (bouncing scanner)
        ascii_frames = [
            "#=        ",
            "=#        ",
            " =#       ",
            "  =#      ",
            "   =#     ",
            "    =#    ",
            "     =#   ",
            "      =#  ",
            "       =# ",
            "        =#",
            "        #=",
            "       #= ",
            "      #=  ",
            "     #=   ",
            "    #=    ",
            "   #=     ",
            "  #=      ",
            " #=       ",
        ]

        # Use unicode glyphs if supported
        if self._supports_unicode():
            translation = str.maketrans("=#", "░█")
            self.frames = [f.translate(translation) for f in ascii_frames]
            self.scan_char = "█"
        else:
            self.frames = ascii_frames
            self.scan_char = "#"

        self.frame_idx = Spinner._last_frame_idx

    def _supports_unicode(self) -> bool:
        """Check if terminal supports unicode output."""
        if not self.is_tty:
            return False
        try:
            test_chars = "░█"
            sys.stdout.write(test_chars)
            sys.stdout.write("\b" * len(test_chars))
            sys.stdout.write(" " * len(test_chars))
            sys.stdout.write("\b" * len(test_chars))
            sys.stdout.flush()
            return True
        except (UnicodeEncodeError, OSError):
            return False

    def _next_frame(self) -> str:
        """Get the next animation frame."""
        frame = self.frames[self.frame_idx]
        self.frame_idx = (self.frame_idx + 1) % len(self.frames)
        Spinner._last_frame_idx = self.frame_idx
        return frame

    def step(self, text: str | None = None) -> None:
        """Advance the spinner animation by one frame.

        Args:
            text: Optional new text to display.
        """
        if text is not None:
            self.text = text

        if not self.is_tty:
            return

        now = time.time()

        # Delay visibility for 0.5s to avoid flicker on fast operations
        if not self.visible and now - self.start_time >= 0.5:
            self.visible = True
            self.last_update = 0.0
            self.console.show_cursor(False)

        # Throttle updates to ~10fps (0.1s between frames)
        if not self.visible or now - self.last_update < 0.1:
            return

        self.last_update = now
        frame_str = self._next_frame()

        # Build the display line
        max_width = self.console.width - 2
        if max_width < 0:
            max_width = 0

        line = f"{frame_str} {self.text}"
        if len(line) > max_width:
            line = line[:max_width]

        # Calculate padding to clear previous content
        padding = " " * max(0, self.last_display_len - len(line))

        # Write and position cursor
        sys.stdout.write(f"\r{line}{padding}")
        self.last_display_len = len(line)

        # Position cursor at the scan character
        scan_pos = frame_str.find(self.scan_char)
        total_written = len(line) + len(padding)
        backspaces = total_written - scan_pos
        sys.stdout.write("\b" * backspaces)
        sys.stdout.flush()

    def end(self) -> None:
        """Clear the spinner and restore cursor."""
        if self.visible and self.is_tty:
            clear_line = "\r" + " " * self.last_display_len + "\r"
            sys.stdout.write(clear_line)
            sys.stdout.flush()
            self.console.show_cursor(True)
        self.visible = False


class WaitingSpinner:
    """Background spinner that runs in a daemon thread.

    Provides a non-blocking spinner that can be started/stopped safely.
    The spinner only becomes visible after 0.5s delay to avoid flicker
    for fast operations.

    Example:
        spinner = WaitingSpinner("Analyzing codebase...")
        spinner.start()
        # ... long operation ...
        spinner.stop()

    Or as a context manager:
        with WaitingSpinner("Processing...") as spinner:
            # ... long operation ...
    """

    def __init__(
        self,
        text: str = "Thinking...",
        delay: float = 0.15,
        on_visible: Callable[[], None] | None = None,
    ):
        """Initialize the waiting spinner.

        Args:
            text: Text to display next to the animation.
            delay: Time between animation frames (default 0.15s = ~6.7fps).
            on_visible: Optional callback when spinner becomes visible.
        """
        self.spinner = Spinner(text)
        self.delay = delay
        self.on_visible = on_visible
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._started = False

    def _spin(self) -> None:
        """Background animation loop."""
        was_visible = False
        while not self._stop_event.is_set():
            self.spinner.step()

            # Fire callback when first becoming visible
            if not was_visible and self.spinner.visible:
                was_visible = True
                if self.on_visible:
                    try:
                        self.on_visible()
                    except Exception:
                        pass

            time.sleep(self.delay)

        self.spinner.end()

    def start(self) -> None:
        """Start the spinner in a background thread."""
        if not self._started and not self._thread.is_alive():
            self._started = True
            self._thread.start()

    def stop(self) -> None:
        """Stop the spinner and wait for thread to exit."""
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=self.delay * 2)
        self.spinner.end()

    def update_text(self, text: str) -> None:
        """Update the spinner text while running.

        Args:
            text: New text to display.
        """
        self.spinner.text = text

    def is_visible(self) -> bool:
        """Check if the spinner is currently visible."""
        return self.spinner.visible

    def __enter__(self) -> WaitingSpinner:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


class ProgressSpinner(WaitingSpinner):
    """Spinner with phase progress tracking.

    Extends WaitingSpinner to show progress through multi-phase operations.

    Example:
        spinner = ProgressSpinner(total_phases=5)
        spinner.start()
        spinner.set_phase(1, "Analyzing")
        # ...
        spinner.set_phase(2, "Planning")
        # ...
        spinner.stop()
    """

    def __init__(self, total_phases: int = 5, **kwargs):
        """Initialize the progress spinner.

        Args:
            total_phases: Total number of phases in the operation.
            **kwargs: Additional arguments for WaitingSpinner.
        """
        super().__init__(**kwargs)
        self.total_phases = total_phases
        self.current_phase = 0
        self.phase_name = ""

    def set_phase(self, phase: int, name: str) -> None:
        """Update the current phase.

        Args:
            phase: Current phase number (1-indexed).
            name: Name of the current phase.
        """
        self.current_phase = phase
        self.phase_name = name

        # Update spinner text with progress
        filled = "█" * phase
        empty = "░" * (self.total_phases - phase)
        progress = f"[{filled}{empty}]"
        self.update_text(f"{progress} {name}")


def demo() -> None:
    """Demo the spinner functionality."""
    print("Starting spinner demo...")

    # Basic spinner
    spinner = WaitingSpinner("Loading data...")
    spinner.start()
    time.sleep(3)
    spinner.stop()
    print("Basic spinner done.")

    # Progress spinner
    progress = ProgressSpinner(total_phases=4)
    progress.start()

    phases = [
        (1, "Analyzing"),
        (2, "Planning"),
        (3, "Implementing"),
        (4, "Verifying"),
    ]

    for phase_num, phase_name in phases:
        progress.set_phase(phase_num, phase_name)
        time.sleep(1.5)

    progress.stop()
    print("Progress spinner done.")


if __name__ == "__main__":
    demo()
