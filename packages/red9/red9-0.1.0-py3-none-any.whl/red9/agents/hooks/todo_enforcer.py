"""Todo Continuation Enforcer Hook.

Forces agents to complete all todos before finishing.
Detects incomplete todo markers in agent output and prevents
premature completion.

Supported todo patterns:
- [ ] Markdown checkboxes
- TODO: Comments
- FIXME: Comments
- XXX: Comments
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from red9.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TodoCheckResult:
    """Result of checking for incomplete todos."""

    has_incomplete_todos: bool
    todo_count: int
    todos: list[str]
    warning_message: str


class TodoEnforcer:
    """Enforces completion of all todos before agent finishes.

    Scans agent output for incomplete todo markers and generates
    warning messages to force the agent to continue working.
    """

    # Patterns for detecting incomplete todos
    DEFAULT_PATTERNS = [
        # Markdown checkboxes (unchecked)
        r"\[\s?\]",  # [ ] or []
        # Code comments
        r"#\s*TODO[:\s]",  # # TODO: or # TODO
        r"//\s*TODO[:\s]",  # // TODO: or // TODO
        r"\*\s*TODO[:\s]",  # * TODO: or * TODO (JSDoc style)
        r"#\s*FIXME[:\s]",
        r"//\s*FIXME[:\s]",
        r"#\s*XXX[:\s]",
        r"//\s*XXX[:\s]",
        # Plain text
        r"TODO:",
        r"FIXME:",
        r"XXX:",
    ]

    def __init__(
        self,
        patterns: list[str] | None = None,
        case_sensitive: bool = False,
        max_todos_to_show: int = 5,
    ) -> None:
        """Initialize the todo enforcer.

        Args:
            patterns: List of regex patterns to match todos.
            case_sensitive: Whether patterns are case-sensitive.
            max_todos_to_show: Maximum number of todos to show in warning.
        """
        self.patterns = patterns or self.DEFAULT_PATTERNS
        self.case_sensitive = case_sensitive
        self.max_todos_to_show = max_todos_to_show

        # Compile patterns
        flags = 0 if case_sensitive else re.IGNORECASE
        self._compiled_patterns = [re.compile(pattern, flags) for pattern in self.patterns]

    def check_output(self, output: str) -> TodoCheckResult:
        """Check agent output for incomplete todos.

        Args:
            output: Agent's output text.

        Returns:
            TodoCheckResult with findings.
        """
        todos: list[str] = []

        # Search for todos line by line for better context
        lines = output.split("\n")
        for i, line in enumerate(lines):
            for pattern in self._compiled_patterns:
                if pattern.search(line):
                    # Get context (the line containing the todo)
                    todo_context = line.strip()[:100]
                    todos.append(f"Line {i + 1}: {todo_context}")
                    break  # One match per line is enough

        has_todos = len(todos) > 0

        # Build warning message
        if has_todos:
            shown_todos = todos[: self.max_todos_to_show]
            todo_list = "\n".join(f"  - {t}" for t in shown_todos)

            if len(todos) > self.max_todos_to_show:
                remaining = len(todos) - self.max_todos_to_show
                todo_list += f"\n  ... and {remaining} more"

            warning = f"""⚠️ INCOMPLETE TODOS DETECTED

Found {len(todos)} incomplete todo(s) in your output:
{todo_list}

You MUST complete these todos before calling `complete_task`.
Continue working to address each item."""
        else:
            warning = ""

        return TodoCheckResult(
            has_incomplete_todos=has_todos,
            todo_count=len(todos),
            todos=todos,
            warning_message=warning,
        )

    def check_files(self, file_contents: dict[str, str]) -> TodoCheckResult:
        """Check multiple file contents for incomplete todos.

        Args:
            file_contents: Dictionary mapping file paths to their contents.

        Returns:
            TodoCheckResult with findings from all files.
        """
        all_todos: list[str] = []

        for file_path, content in file_contents.items():
            lines = content.split("\n")
            for i, line in enumerate(lines):
                for pattern in self._compiled_patterns:
                    if pattern.search(line):
                        todo_context = line.strip()[:80]
                        all_todos.append(f"{file_path}:{i + 1}: {todo_context}")
                        break

        has_todos = len(all_todos) > 0

        if has_todos:
            shown_todos = all_todos[: self.max_todos_to_show]
            todo_list = "\n".join(f"  - {t}" for t in shown_todos)

            if len(all_todos) > self.max_todos_to_show:
                remaining = len(all_todos) - self.max_todos_to_show
                todo_list += f"\n  ... and {remaining} more"

            warning = f"""⚠️ INCOMPLETE TODOS IN FILES

Found {len(all_todos)} incomplete todo(s) in modified files:
{todo_list}

These todos must be addressed before completion."""
        else:
            warning = ""

        return TodoCheckResult(
            has_incomplete_todos=has_todos,
            todo_count=len(all_todos),
            todos=all_todos,
            warning_message=warning,
        )

    def should_block_completion(
        self,
        output: str,
        called_complete_task: bool = False,
    ) -> tuple[bool, str]:
        """Determine if completion should be blocked due to todos.

        Args:
            output: Agent's output text.
            called_complete_task: Whether agent is trying to call complete_task.

        Returns:
            Tuple of (should_block, warning_message).
        """
        if not called_complete_task:
            return False, ""

        result = self.check_output(output)

        if result.has_incomplete_todos:
            logger.warning(f"Blocking completion: {result.todo_count} incomplete todos found")
            return True, result.warning_message

        return False, ""

    def to_dict(self) -> dict[str, Any]:
        """Get configuration as dictionary.

        Returns:
            Dictionary with enforcer configuration.
        """
        return {
            "patterns": self.patterns,
            "case_sensitive": self.case_sensitive,
            "max_todos_to_show": self.max_todos_to_show,
        }


def create_todo_enforcer(
    strict: bool = False,
    custom_patterns: list[str] | None = None,
) -> TodoEnforcer:
    """Factory function to create a todo enforcer.

    Args:
        strict: If True, use case-sensitive matching.
        custom_patterns: Additional patterns to match.

    Returns:
        Configured TodoEnforcer instance.
    """
    patterns = TodoEnforcer.DEFAULT_PATTERNS.copy()
    if custom_patterns:
        patterns.extend(custom_patterns)

    return TodoEnforcer(
        patterns=patterns,
        case_sensitive=strict,
    )
