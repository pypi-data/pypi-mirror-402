"""Streaming markdown renderer with 20fps throttling and dual-buffer pattern.

Inspired by Aider's mdstream.py, this provides smooth progressive rendering
by splitting output into stable lines (printed above) and a live window
(last few lines that may reflow as content streams in).
"""

from __future__ import annotations

import io
import time
from collections.abc import Callable

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text


class MarkdownStreamRenderer:
    """Streaming markdown renderer with dual-buffer pattern.

    Uses a dual-buffer approach:
    - Stable lines: Already rendered and printed above the Live window
    - Live window: Last N lines that may reflow as new content arrives

    This creates smooth scrolling while maintaining terminal scrollback
    compatibility.
    """

    MIN_DELAY_BASE = 1.0 / 20  # 20fps base refresh rate
    MIN_DELAY_MAX = 2.0  # Cap adaptive delay at 2 seconds
    LIVE_WINDOW_SIZE = 6  # Lines to keep in live window

    def __init__(
        self,
        console: Console | None = None,
        on_stable_line: Callable[[str], None] | None = None,
    ):
        """Initialize the stream renderer.

        Args:
            console: Rich Console instance for output. Creates new if None.
            on_stable_line: Optional callback for each stable line (for logging).
        """
        self.console = console or Console()
        self.on_stable_line = on_stable_line

        # State
        self.printed: list[str] = []  # Lines already printed above Live
        self.buffer = ""  # Accumulated markdown text
        self.when = 0.0  # Timestamp of last update
        self.min_delay = self.MIN_DELAY_BASE

        # Lazy-initialized Live display
        self.live: Live | None = None
        self._live_started = False

    def _ensure_live(self) -> Live:
        """Lazily initialize and start the Live display."""
        if not self._live_started:
            self.live = Live(
                Text(""),
                console=self.console,
                refresh_per_second=1.0 / self.min_delay,
                transient=False,  # Keep content in scrollback
            )
            self.live.start()
            self._live_started = True
        return self.live  # type: ignore

    def _render_to_lines(self, text: str) -> list[str]:
        """Render markdown text to a list of lines.

        Args:
            text: Markdown text to render.

        Returns:
            List of rendered lines with line endings preserved.
        """
        # Render markdown to a string buffer
        string_io = io.StringIO()
        render_console = Console(
            file=string_io,
            force_terminal=True,
            width=self.console.width,
        )
        markdown = Markdown(text, code_theme="monokai")
        render_console.print(markdown)
        output = string_io.getvalue()

        return output.splitlines(keepends=True)

    def update(self, token: str) -> None:
        """Accumulate a token and update the display.

        Tokens are accumulated into the buffer. Display is throttled
        to maintain 20fps (or adaptive rate based on render time).

        Args:
            token: New token to append to the buffer.
        """
        self.buffer += token

        now = time.time()
        if now - self.when < self.min_delay:
            return  # Throttle
        self.when = now

        self._render_update(final=False)

    def _render_update(self, final: bool = False) -> None:
        """Render the current buffer state to the display.

        Args:
            final: If True, this is the final render and we should clean up.
        """
        live = self._ensure_live()

        # Measure render time for adaptive throttling
        start = time.time()
        lines = self._render_to_lines(self.buffer)
        render_time = time.time() - start

        # Adaptive min_delay: slower renders get longer delays
        self.min_delay = min(
            max(render_time * 10, self.MIN_DELAY_BASE),
            self.MIN_DELAY_MAX,
        )

        num_lines = len(lines)

        # Calculate how many lines are now "stable" (left the live window)
        if not final:
            num_stable = max(0, num_lines - self.LIVE_WINDOW_SIZE)
        else:
            num_stable = num_lines  # All lines are stable on final

        # Print new stable lines above the Live window
        num_printed = len(self.printed)
        if num_stable > num_printed:
            new_stable = lines[num_printed:num_stable]
            new_stable_text = "".join(new_stable)
            ansi_text = Text.from_ansi(new_stable_text)
            live.console.print(ansi_text)

            # Notify callback of stable lines
            if self.on_stable_line:
                for line in new_stable:
                    self.on_stable_line(line.rstrip())

            self.printed = lines[:num_stable]

        # Handle final update
        if final:
            live.update(Text(""))
            live.stop()
            self.live = None
            self._live_started = False
            return

        # Update the live window with remaining unstable lines
        rest = lines[num_stable:]
        rest_text = "".join(rest)
        ansi_rest = Text.from_ansi(rest_text)
        live.update(ansi_rest)

    def finish(self) -> str:
        """Finish streaming and return the complete buffer.

        Returns:
            The complete accumulated markdown text.
        """
        if self._live_started:
            self._render_update(final=True)
        return self.buffer

    def reset(self) -> None:
        """Reset the renderer state for reuse."""
        if self.live and self._live_started:
            try:
                self.live.stop()
            except Exception:
                pass

        self.printed = []
        self.buffer = ""
        self.when = 0.0
        self.min_delay = self.MIN_DELAY_BASE
        self.live = None
        self._live_started = False

    def __del__(self) -> None:
        """Clean up Live display on destruction."""
        if self.live:
            try:
                self.live.stop()
            except Exception:
                pass


class PlainStreamRenderer:
    """Simple streaming renderer without markdown processing.

    For use cases where markdown rendering overhead is not desired,
    such as plain text or JSON output.
    """

    MIN_DELAY = 1.0 / 30  # 30fps for plain text (faster than markdown)

    def __init__(self, console: Console | None = None):
        """Initialize the plain stream renderer.

        Args:
            console: Rich Console instance for output.
        """
        self.console = console or Console()
        self.buffer = ""
        self.when = 0.0
        self._pending = ""

    def update(self, token: str) -> None:
        """Accumulate a token and flush when appropriate.

        Args:
            token: New token to append.
        """
        self.buffer += token
        self._pending += token

        now = time.time()
        if now - self.when < self.MIN_DELAY:
            return  # Throttle

        self.when = now
        self._flush()

    def _flush(self) -> None:
        """Flush pending content to console."""
        if self._pending:
            self.console.print(self._pending, end="", highlight=False)
            self._pending = ""

    def finish(self) -> str:
        """Finish streaming and return complete buffer."""
        self._flush()
        self.console.print()  # Final newline
        return self.buffer

    def reset(self) -> None:
        """Reset state for reuse."""
        self.buffer = ""
        self._pending = ""
        self.when = 0.0
