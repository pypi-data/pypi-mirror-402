"""Dangerous command detection hook.

This hook blocks potentially destructive shell commands such as:
- Recursive deletion of root/home directories
- Direct device writes (dd, mkfs)
- Fork bombs
- Piping untrusted content to shell
- Force push/commit operations
"""

from __future__ import annotations

import re
from typing import Any

from red9.security.hooks import SecurityAction, SecurityCheckResult, SecurityHook

# Dangerous command patterns with descriptions
# Format: (regex_pattern, description, severity)
DANGEROUS_PATTERNS: list[tuple[str, str, str]] = [
    # Filesystem destruction
    (
        r"\brm\s+(-[rfRF]+\s+)?(/|~|\$HOME|\$\{HOME\}|\.\.)",
        "Recursive delete of root/home directory",
        "critical",
    ),
    (
        r"\brm\s+-[rfRF]*\s*\*",
        "Recursive delete with wildcard",
        "high",
    ),
    (
        r"\bmkfs\b",
        "Filesystem formatting command",
        "critical",
    ),
    (
        r"\bdd\s+.*\bof=/dev/",
        "Direct device write",
        "critical",
    ),
    (
        r">\s*/dev/sd[a-z]",
        "Redirect to block device",
        "critical",
    ),
    (
        r"\bshred\s+",
        "Secure file deletion",
        "high",
    ),
    # System compromise
    (
        r"\bchmod\s+777\s+/",
        "Insecure permissions on root",
        "critical",
    ),
    (
        r"\bchmod\s+-R\s+777",
        "Recursive insecure permissions",
        "high",
    ),
    (
        r"\bchown\s+-R\s+.*\s+/(?!home)",
        "Recursive ownership change on system directory",
        "critical",
    ),
    (
        r":\(\)\s*\{.*\|.*&",
        "Fork bomb pattern",
        "critical",
    ),
    (
        r"\bforkbomb\b",
        "Fork bomb reference",
        "critical",
    ),
    # Network exfiltration / RCE
    (
        r"\bcurl\s+.*\|\s*(ba)?sh",
        "Pipe curl output to shell",
        "critical",
    ),
    (
        r"\bwget\s+.*\|\s*(ba)?sh",
        "Pipe wget output to shell",
        "critical",
    ),
    (
        r"\bcurl\s+.*\|\s*python",
        "Pipe curl output to Python",
        "high",
    ),
    (
        r"\bwget\s+.*\|\s*python",
        "Pipe wget output to Python",
        "high",
    ),
    (
        r"\bnc\s+.*-e\s+/bin/(ba)?sh",
        "Netcat reverse shell",
        "critical",
    ),
    # Credential theft
    (
        r"\bcat\s+.*(/etc/passwd|/etc/shadow)",
        "Reading system credential files",
        "high",
    ),
    (
        r"\bcp\s+.*\.ssh/",
        "Copying SSH keys",
        "high",
    ),
    (
        r"\bscp\s+.*\.ssh/",
        "Transferring SSH keys",
        "high",
    ),
    # Git dangerous operations
    (
        r"\bgit\s+push\s+.*--force",
        "Force push to remote",
        "high",
    ),
    (
        r"\bgit\s+push\s+-f\b",
        "Force push to remote",
        "high",
    ),
    (
        r"\bgit\s+reset\s+--hard\s+origin/",
        "Hard reset to remote branch",
        "medium",
    ),
    # System services
    (
        r"\bsystemctl\s+(stop|disable|mask)\s+",
        "Stopping/disabling system services",
        "high",
    ),
    (
        r"\bservice\s+\w+\s+(stop|disable)",
        "Stopping system services",
        "high",
    ),
    # Kernel/boot
    (
        r"\brm\s+.*(/boot/|vmlinuz|initrd)",
        "Removing boot files",
        "critical",
    ),
    (
        r"\bsysctl\s+-w",
        "Modifying kernel parameters",
        "high",
    ),
    # History manipulation (potential for hiding malicious activity)
    (
        r"\bhistory\s+-c",
        "Clearing command history",
        "medium",
    ),
    (
        r"\bunset\s+HISTFILE",
        "Disabling history logging",
        "medium",
    ),
]


class DangerousCommandHook(SecurityHook):
    """Blocks dangerous shell commands.

    This hook inspects shell commands for dangerous patterns that could:
    - Destroy filesystems or data
    - Compromise system security
    - Steal credentials
    - Execute arbitrary remote code
    """

    def __init__(
        self,
        extra_patterns: list[tuple[str, str, str]] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize the hook.

        Args:
            extra_patterns: Additional (pattern, description, severity) tuples.
            enabled: Whether the hook is enabled.
        """
        self._enabled = enabled
        self._extra_patterns = extra_patterns or []

    @property
    def name(self) -> str:
        """Hook identifier."""
        return "dangerous_commands"

    @property
    def enabled(self) -> bool:
        """Whether this hook is enabled."""
        return self._enabled

    @property
    def applies_to_tools(self) -> list[str]:
        """Tools this hook applies to."""
        return ["shell", "run_command"]

    def check(self, tool_name: str, params: dict[str, Any]) -> SecurityCheckResult:
        """Check command for dangerous patterns.

        Args:
            tool_name: Name of the tool being called.
            params: Tool parameters (expects 'command' key).

        Returns:
            SecurityCheckResult indicating whether to block.
        """
        command = params.get("command", "")
        if not command:
            return SecurityCheckResult(
                action=SecurityAction.ALLOW,
                reason="No command to check",
            )

        # Check all patterns
        all_patterns = DANGEROUS_PATTERNS + self._extra_patterns

        for pattern, description, severity in all_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                # Truncate command for logging (don't expose full command)
                truncated_cmd = command[:200] + "..." if len(command) > 200 else command
                return SecurityCheckResult(
                    action=SecurityAction.BLOCK,
                    reason=f"Dangerous command blocked: {description}",
                    details={
                        "pattern": pattern,
                        "command_preview": truncated_cmd,
                    },
                    severity=severity,
                )

        return SecurityCheckResult(
            action=SecurityAction.ALLOW,
            reason="Command passed security checks",
        )
