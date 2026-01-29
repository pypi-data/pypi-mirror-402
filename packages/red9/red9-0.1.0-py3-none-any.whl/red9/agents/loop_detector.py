"""Loop detection for agent execution.

Prevents agents from getting stuck in repetitive tool call patterns.
"""

from __future__ import annotations

import hashlib
import json
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from red9.logging import get_logger

logger = get_logger(__name__)


# Configuration
DEFAULT_WINDOW_SIZE = 20  # Number of recent calls to track
DEFAULT_REPEAT_THRESHOLD = 3  # Same call repeated this many times = loop
DEFAULT_PATTERN_THRESHOLD = 2  # Pattern repeated this many times = loop


@dataclass
class ToolCall:
    """Represents a tool call for loop detection."""

    name: str
    args_hash: str
    sequence_num: int

    @classmethod
    def from_call(cls, name: str, args: dict[str, Any], sequence_num: int) -> ToolCall:
        """Create from tool name and arguments.

        Args:
            name: Tool name.
            args: Tool arguments.
            sequence_num: Call sequence number.

        Returns:
            ToolCall instance.
        """
        # Create deterministic hash of arguments
        args_str = json.dumps(args, sort_keys=True, default=str)
        args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
        return cls(name=name, args_hash=args_hash, sequence_num=sequence_num)

    @property
    def signature(self) -> str:
        """Get unique signature for this call."""
        return f"{self.name}:{self.args_hash}"


@dataclass
class LoopDetectionResult:
    """Result of loop detection check."""

    is_loop: bool
    loop_type: str | None = None  # "exact_repeat", "pattern", None
    message: str | None = None
    repeated_call: str | None = None
    repeat_count: int = 0
    suggestion: str | None = None


@dataclass
class LoopDetector:
    """Detects repetitive tool call patterns.

    Tracks recent tool calls in a sliding window and detects:
    1. Exact repeats: Same tool with same args called repeatedly
    2. Patterns: Sequences of calls that repeat (A->B->A->B)
    """

    window_size: int = DEFAULT_WINDOW_SIZE
    repeat_threshold: int = DEFAULT_REPEAT_THRESHOLD
    pattern_threshold: int = DEFAULT_PATTERN_THRESHOLD
    _history: deque[ToolCall] = field(default_factory=lambda: deque(maxlen=20))
    _sequence_num: int = 0

    def __post_init__(self) -> None:
        """Initialize with proper maxlen."""
        self._history = deque(maxlen=self.window_size)

    def record_call(self, tool_name: str, args: dict[str, Any]) -> LoopDetectionResult:
        """Record a tool call and check for loops.

        Args:
            tool_name: Name of the tool.
            args: Tool arguments.

        Returns:
            LoopDetectionResult indicating if a loop was detected.
        """
        self._sequence_num += 1
        call = ToolCall.from_call(tool_name, args, self._sequence_num)

        # Check for loops before adding
        result = self._check_for_loop(call)

        # Add to history
        self._history.append(call)

        if result.is_loop:
            logger.debug(f"Loop detected: {result.loop_type} - {result.message}")

        return result

    def _check_for_loop(self, new_call: ToolCall) -> LoopDetectionResult:
        """Check if adding this call would indicate a loop.

        Args:
            new_call: The new tool call to check.

        Returns:
            LoopDetectionResult.
        """
        if len(self._history) < 2:
            return LoopDetectionResult(is_loop=False)

        # Check 1: Exact repeat detection
        exact_result = self._check_exact_repeat(new_call)
        if exact_result.is_loop:
            return exact_result

        # Check 2: Pattern detection
        pattern_result = self._check_pattern(new_call)
        if pattern_result.is_loop:
            return pattern_result

        return LoopDetectionResult(is_loop=False)

    def _check_exact_repeat(self, new_call: ToolCall) -> LoopDetectionResult:
        """Check for exact repeated calls.

        Args:
            new_call: The new tool call.

        Returns:
            LoopDetectionResult.
        """
        signature = new_call.signature
        recent_matches = sum(1 for call in self._history if call.signature == signature)

        if recent_matches >= self.repeat_threshold - 1:
            return LoopDetectionResult(
                is_loop=True,
                loop_type="exact_repeat",
                message=(
                    f"Tool '{new_call.name}' called {recent_matches + 1} times "
                    f"with identical arguments"
                ),
                repeated_call=new_call.name,
                repeat_count=recent_matches + 1,
                suggestion=self._get_suggestion_for_repeat(new_call.name),
            )

        return LoopDetectionResult(is_loop=False)

    def _check_pattern(self, new_call: ToolCall) -> LoopDetectionResult:
        """Check for repeating patterns of calls.

        Args:
            new_call: The new tool call.

        Returns:
            LoopDetectionResult.
        """
        if len(self._history) < 4:
            return LoopDetectionResult(is_loop=False)

        # Get signatures including new call
        signatures = [c.signature for c in self._history] + [new_call.signature]

        # Check for patterns of length 2-4
        for pattern_len in range(2, min(5, len(signatures) // 2 + 1)):
            if self._has_repeating_pattern(signatures, pattern_len):
                pattern_calls = [
                    self._history[-(pattern_len - 1) + i].name
                    if i < pattern_len - 1
                    else new_call.name
                    for i in range(pattern_len)
                ]
                return LoopDetectionResult(
                    is_loop=True,
                    loop_type="pattern",
                    message=(f"Repeating pattern detected: {' -> '.join(pattern_calls)}"),
                    repeated_call=" -> ".join(pattern_calls),
                    repeat_count=self.pattern_threshold,
                    suggestion=(
                        "Try a different approach. The current sequence of "
                        "tool calls is repeating without making progress."
                    ),
                )

        return LoopDetectionResult(is_loop=False)

    def _has_repeating_pattern(
        self,
        signatures: list[str],
        pattern_len: int,
    ) -> bool:
        """Check if the last N elements form a repeating pattern.

        Args:
            signatures: List of call signatures.
            pattern_len: Length of pattern to check.

        Returns:
            True if pattern repeats threshold times.
        """
        if len(signatures) < pattern_len * self.pattern_threshold:
            return False

        # Get the last pattern_len signatures as the pattern
        pattern = signatures[-pattern_len:]

        # Check how many times this pattern appears at the end
        repeats = 0
        for i in range(self.pattern_threshold):
            start_idx = len(signatures) - pattern_len * (i + 1)
            if start_idx < 0:
                break
            window = signatures[start_idx : start_idx + pattern_len]
            if window == pattern:
                repeats += 1
            else:
                break

        return repeats >= self.pattern_threshold

    def _get_suggestion_for_repeat(self, tool_name: str) -> str:
        """Get a suggestion based on the repeated tool.

        Args:
            tool_name: Name of the repeated tool.

        Returns:
            Suggestion string.
        """
        suggestions = {
            "edit_file": (
                "The edit may not be matching. Try reading the file first "
                "to see its current content, or use a more specific old_string."
            ),
            "grep": (
                "The search pattern may not be finding what you expect. "
                "Try a different search term or check if the file exists."
            ),
            "read_file": (
                "You've read this file multiple times. Consider using "
                "the content you already have instead of re-reading."
            ),
            "shell": ("The command may be failing. Check the output and try a different approach."),
        }
        return suggestions.get(
            tool_name,
            f"Tool '{tool_name}' is being called repeatedly. Consider trying a different approach.",
        )

    def reset(self) -> None:
        """Clear the call history."""
        self._history.clear()
        self._sequence_num = 0

    def get_recent_calls(self, n: int = 5) -> list[str]:
        """Get the last N tool calls as strings.

        Args:
            n: Number of recent calls to return.

        Returns:
            List of tool call descriptions.
        """
        recent = list(self._history)[-n:]
        return [f"{c.name}({c.args_hash})" for c in recent]

    def inject_loop_warning(self, result: LoopDetectionResult) -> str:
        """Generate a warning message to inject into agent context.

        Args:
            result: The loop detection result.

        Returns:
            Warning message string.
        """
        if not result.is_loop:
            return ""

        warning = f"""
⚠️ LOOP DETECTED: {result.message}

{result.suggestion}

Recent tool calls:
{chr(10).join(f"  - {c}" for c in self.get_recent_calls(10))}

Please try a different approach to solve this problem. If you're stuck,
consider:
1. Reading files to understand the current state
2. Using a different tool or strategy
3. Asking for clarification if the task is unclear
"""
        return warning.strip()
