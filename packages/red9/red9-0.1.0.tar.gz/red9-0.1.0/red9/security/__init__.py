"""Security hooks package for RED9.

This package provides security hooks that inspect tool calls before execution
and can block dangerous operations.

Usage:
    from red9.security import (
        SecurityHookRunner,
        create_default_security_hooks,
        DangerousCommandHook,
        SecretDetectionHook,
    )

    # Create runner with default hooks
    runner = create_default_security_hooks()

    # Or create custom runner
    runner = SecurityHookRunner()
    runner.add_hook(DangerousCommandHook())
    runner.add_hook(SecretDetectionHook())

    # Check a tool call
    result = runner.run_pre_hooks("shell", {"command": "rm -rf /"})
    if result.action == SecurityAction.BLOCK:
        print(f"Blocked: {result.reason}")
"""

from red9.security.dangerous_commands import DangerousCommandHook
from red9.security.hooks import (
    SecurityAction,
    SecurityCheckResult,
    SecurityHook,
    SecurityHookRunner,
    create_default_security_hooks,
)
from red9.security.secrets import SecretDetectionHook

__all__ = [
    # Core
    "SecurityAction",
    "SecurityCheckResult",
    "SecurityHook",
    "SecurityHookRunner",
    "create_default_security_hooks",
    # Hooks
    "DangerousCommandHook",
    "SecretDetectionHook",
]
