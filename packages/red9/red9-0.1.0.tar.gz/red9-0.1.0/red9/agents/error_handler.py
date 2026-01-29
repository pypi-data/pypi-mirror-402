"""Shared error handling utilities for agent tasks.

Provides context-aware retry handling that preserves error history
between retry attempts, enabling agents to learn from past failures.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from stabilize import TaskResult
from stabilize.models.status import WorkflowStatus

from red9.logging import get_logger

logger = get_logger(__name__)

# Default maximum retry attempts before failing permanently
DEFAULT_MAX_RETRY_ATTEMPTS = 5


def handle_transient_error(
    error: Exception,
    error_history: list[dict[str, Any]],
    agent_name: str = "Agent",
    max_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS,
) -> TaskResult:
    """Handle transient error with context-aware retry.

    Instead of raising TransientError (which doesn't store context),
    we return RUNNING status which triggers Stabilize to re-queue
    with the updated stage context preserved.

    Args:
        error: The transient error that occurred.
        error_history: Previous error history from stage.context.get("_error_history", []).
        agent_name: Name of the agent for logging.
        max_attempts: Maximum retry attempts before failing permanently.

    Returns:
        TaskResult with RUNNING status to trigger retry, or terminal if max attempts.
    """
    attempt = len(error_history) + 1

    if attempt >= max_attempts:
        logger.warning(f"{agent_name} exceeded max retries ({max_attempts})")
        return TaskResult.terminal(error=f"{agent_name} failed after {attempt} attempts: {error}")

    # Add error to history
    new_error = {
        "attempt": attempt,
        "error": str(error),
        "timestamp": datetime.now().isoformat(),
        "error_type": type(error).__name__,
    }
    updated_history = error_history + [new_error]

    logger.info(f"{agent_name} transient error (attempt {attempt}): {error}")

    # Return RUNNING status to trigger re-queue WITH stored context
    # This is the key difference from TransientError - context is persisted
    return TaskResult(
        status=WorkflowStatus.RUNNING,
        context={"_error_history": updated_history},
        outputs={},
    )


def get_error_history(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract error history from stage context.

    Args:
        context: Stage context dictionary.

    Returns:
        List of error history entries, empty if none.
    """
    return context.get("_error_history", [])
