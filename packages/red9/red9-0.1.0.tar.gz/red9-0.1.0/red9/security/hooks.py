"""Core security hook infrastructure.

This module provides the base classes and runner for security hooks that
inspect tool calls before execution and can block dangerous operations.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SecurityAction(Enum):
    """Actions that a security hook can take."""

    ALLOW = "allow"  # Let the tool execute
    BLOCK = "block"  # Block execution with error
    WARN = "warn"  # Log warning but allow


@dataclass
class SecurityCheckResult:
    """Result of a security check."""

    action: SecurityAction
    reason: str
    details: dict[str, Any] | None = None
    severity: str = "medium"  # low, medium, high, critical


class SecurityHook(ABC):
    """Abstract base class for security hooks.

    Security hooks are executed before tool calls to detect and block
    potentially dangerous operations like:
    - Destructive shell commands (rm -rf /, dd of=/dev/)
    - Secrets in file content (API keys, passwords, tokens)
    - Access to protected system paths
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Hook identifier."""
        pass

    @property
    def enabled(self) -> bool:
        """Whether this hook is enabled."""
        return True

    @property
    def applies_to_tools(self) -> list[str] | None:
        """List of tool names this hook applies to, or None for all tools."""
        return None

    @abstractmethod
    def check(self, tool_name: str, params: dict[str, Any]) -> SecurityCheckResult:
        """Check tool call for security issues.

        Args:
            tool_name: Name of the tool being called.
            params: Parameters passed to the tool.

        Returns:
            SecurityCheckResult indicating the action to take.
        """
        pass


@dataclass
class SecurityHookRunner:
    """Runs security hooks before tool execution.

    The runner executes all applicable hooks and returns the first BLOCK
    result, or aggregates WARN results if no blocking issues are found.
    """

    _hooks: list[SecurityHook] = field(default_factory=list)

    def add_hook(self, hook: SecurityHook) -> None:
        """Add a security hook to the runner.

        Args:
            hook: Security hook to add.
        """
        self._hooks.append(hook)

    def remove_hook(self, hook_name: str) -> bool:
        """Remove a security hook by name.

        Args:
            hook_name: Name of the hook to remove.

        Returns:
            True if hook was found and removed.
        """
        for i, hook in enumerate(self._hooks):
            if hook.name == hook_name:
                del self._hooks[i]
                return True
        return False

    def get_hooks(self) -> list[SecurityHook]:
        """Get all registered hooks."""
        return self._hooks.copy()

    def run_pre_hooks(self, tool_name: str, params: dict[str, Any]) -> SecurityCheckResult:
        """Run all applicable hooks before tool execution.

        Args:
            tool_name: Name of the tool being called.
            params: Parameters passed to the tool.

        Returns:
            SecurityCheckResult - BLOCK on first violation, ALLOW with
            aggregated warnings otherwise.
        """
        warnings: list[SecurityCheckResult] = []

        for hook in self._hooks:
            # Skip disabled hooks
            if not hook.enabled:
                continue

            # Check if hook applies to this tool
            applicable_tools = hook.applies_to_tools
            if applicable_tools and tool_name not in applicable_tools:
                continue

            try:
                result = hook.check(tool_name, params)

                if result.action == SecurityAction.BLOCK:
                    logger.warning(
                        f"Security hook '{hook.name}' blocked {tool_name}: {result.reason}"
                    )
                    return result

                if result.action == SecurityAction.WARN:
                    warnings.append(result)
                    logger.warning(
                        f"Security hook '{hook.name}' warning for {tool_name}: {result.reason}"
                    )

            except Exception as e:
                # Log hook errors but don't block execution
                logger.error(f"Security hook '{hook.name}' error: {e}")

        if warnings:
            # Aggregate warnings into a single result
            warning_reasons = [w.reason for w in warnings]
            logger.warning(f"Security warnings for {tool_name}: {warning_reasons}")

        return SecurityCheckResult(
            action=SecurityAction.ALLOW,
            reason="All security checks passed",
        )


def create_default_security_hooks(
    config: dict[str, bool] | None = None,
) -> SecurityHookRunner:
    """Create a SecurityHookRunner with default hooks.

    Args:
        config: Optional dict mapping hook names to enabled state.
            Defaults to all hooks enabled.

    Returns:
        Configured SecurityHookRunner.
    """
    from red9.security.dangerous_commands import DangerousCommandHook
    from red9.security.secrets import SecretDetectionHook

    config = config or {}

    runner = SecurityHookRunner()

    # Add hooks based on config (default: all enabled)
    if config.get("dangerous_commands", True):
        runner.add_hook(DangerousCommandHook())

    if config.get("secret_detection", True):
        runner.add_hook(SecretDetectionHook())

    return runner
