"""Secret detection hook.

This hook detects secrets in file content and git commits:
- API keys (OpenAI, GitHub, AWS, etc.)
- Private keys (RSA, EC, PGP)
- Passwords and tokens
- Database connection strings with credentials
"""

from __future__ import annotations

import re
from typing import Any

from red9.security.hooks import SecurityAction, SecurityCheckResult, SecurityHook

# Secret patterns with descriptions
# Format: (regex_pattern, description, severity)
# NOTE: Order matters - more specific patterns should come before generic ones
SECRET_PATTERNS: list[tuple[str, str, str]] = [
    # ============================================
    # SPECIFIC PROVIDER PATTERNS (check first)
    # ============================================
    # OpenAI (check before generic api_key pattern)
    (
        r"sk-proj-[a-zA-Z0-9\-_]{48,}",
        "OpenAI project API key",
        "critical",
    ),
    (
        r"sk-[a-zA-Z0-9]{48}",
        "OpenAI API key",
        "critical",
    ),
    # Anthropic
    (
        r"sk-ant-[a-zA-Z0-9\-_]{40,}",
        "Anthropic API key",
        "critical",
    ),
    # GitHub (check before generic token pattern)
    (
        r"ghp_[a-zA-Z0-9]{36}",
        "GitHub personal access token",
        "critical",
    ),
    (
        r"gho_[a-zA-Z0-9]{36}",
        "GitHub OAuth token",
        "critical",
    ),
    (
        r"ghs_[a-zA-Z0-9]{36}",
        "GitHub server token",
        "critical",
    ),
    (
        r"ghr_[a-zA-Z0-9]{36}",
        "GitHub refresh token",
        "critical",
    ),
    (
        r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}",
        "GitHub fine-grained PAT",
        "critical",
    ),
    # GitLab
    (
        r"glpat-[a-zA-Z0-9\-]{20,}",
        "GitLab personal access token",
        "critical",
    ),
    # AWS
    (
        r"AKIA[0-9A-Z]{16}",
        "AWS access key ID",
        "critical",
    ),
    (
        r"(?:aws[_-]?secret[_-]?(?:access)?[_-]?key|secret[_-]?key)\s*[:=]\s*['\"]?[a-zA-Z0-9/+]{40}['\"]?",
        "AWS secret access key",
        "critical",
    ),
    # Google Cloud
    (
        r"AIza[0-9A-Za-z\-_]{35}",
        "Google API key",
        "critical",
    ),
    # Stripe
    (
        r"sk_live_[a-zA-Z0-9]{24,}",
        "Stripe live secret key",
        "critical",
    ),
    (
        r"rk_live_[a-zA-Z0-9]{24,}",
        "Stripe restricted key",
        "critical",
    ),
    # Slack
    (
        r"xox[baprs]-[a-zA-Z0-9\-]{10,}",
        "Slack token",
        "critical",
    ),
    # Private keys
    (
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "Private key",
        "critical",
    ),
    (
        r"-----BEGIN PGP PRIVATE KEY BLOCK-----",
        "PGP private key",
        "critical",
    ),
    (
        r"-----BEGIN DSA PRIVATE KEY-----",
        "DSA private key",
        "critical",
    ),
    # Database connection strings
    (
        r"(?:mysql|postgres|postgresql|mongodb|redis)://[^:]+:[^@]+@",
        "Database connection string with credentials",
        "critical",
    ),
    (
        r"mongodb\+srv://[^:]+:[^@]+@",
        "MongoDB Atlas connection string with credentials",
        "critical",
    ),
    # JWT secrets
    (
        r"(?:jwt[_-]?secret|jwt[_-]?key)\s*[:=]\s*['\"][^'\"]{32,}['\"]",
        "JWT secret key",
        "high",
    ),
    # Terraform (be specific to avoid false positives)
    (
        r"tf_(?:var_)?(?:secret|password|token)\s*=\s*['\"][^'\"]+['\"]",
        "Terraform secret",
        "high",
    ),
    (
        r"var\.(?:secret|password|token)\s*=\s*['\"][^'\"]+['\"]",
        "Terraform variable secret",
        "high",
    ),
    # SSH private key content
    (
        r"ssh-rsa\s+AAAA[a-zA-Z0-9+/=]{100,}",
        "SSH public key in file (may contain associated private key)",
        "medium",
    ),
    # ============================================
    # GENERIC PATTERNS (check last, as fallback)
    # ============================================
    # Generic secrets/passwords
    (
        r"(?:password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
        "Hardcoded password",
        "high",
    ),
    (
        r"(?:secret|token|auth[_-]?token)\s*[:=]\s*['\"][^'\"]{16,}['\"]",
        "Hardcoded secret/token",
        "high",
    ),
    (
        r"(?:api[_-]?key|apikey)\s*[:=]\s*['\"]?[a-zA-Z0-9\-_]{20,}['\"]?",
        "Generic API key",
        "high",
    ),
]


class SecretDetectionHook(SecurityHook):
    """Detects secrets in file content and git commits.

    This hook inspects content being written to files for patterns
    that indicate secrets such as API keys, passwords, and tokens.
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
        return "secret_detection"

    @property
    def enabled(self) -> bool:
        """Whether this hook is enabled."""
        return self._enabled

    @property
    def applies_to_tools(self) -> list[str]:
        """Tools this hook applies to."""
        return ["write_file", "edit_file", "shell", "run_command"]

    def check(self, tool_name: str, params: dict[str, Any]) -> SecurityCheckResult:
        """Check content for secrets.

        Args:
            tool_name: Name of the tool being called.
            params: Tool parameters.

        Returns:
            SecurityCheckResult indicating whether to block.
        """
        content = self._extract_content(tool_name, params)
        if not content:
            return SecurityCheckResult(
                action=SecurityAction.ALLOW,
                reason="No content to check",
            )

        # Skip checking if content is very long (performance)
        # and likely auto-generated/minified
        if len(content) > 500_000:
            return SecurityCheckResult(
                action=SecurityAction.ALLOW,
                reason="Content too large for secret scanning",
            )

        # Check all patterns
        all_patterns = SECRET_PATTERNS + self._extra_patterns

        for pattern, description, severity in all_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # Redact the actual secret for logging
                matched_text = match.group(0)
                if len(matched_text) > 14:
                    redacted = matched_text[:10] + "..." + matched_text[-4:]
                else:
                    redacted = matched_text[:4] + "..." + matched_text[-2:]

                return SecurityCheckResult(
                    action=SecurityAction.BLOCK,
                    reason=f"Secret detected: {description}",
                    details={
                        "type": description,
                        "redacted_match": redacted,
                        "tool": tool_name,
                    },
                    severity=severity,
                )

        return SecurityCheckResult(
            action=SecurityAction.ALLOW,
            reason="No secrets detected",
        )

    def _extract_content(self, tool_name: str, params: dict[str, Any]) -> str:
        """Extract content to scan based on tool type.

        Args:
            tool_name: Name of the tool.
            params: Tool parameters.

        Returns:
            Content string to scan for secrets.
        """
        if tool_name in ("write_file",):
            return params.get("content", "")

        if tool_name in ("edit_file",):
            # Only check new_string since old_string is already in the file
            return params.get("new_string", "")

        if tool_name in ("shell", "run_command"):
            command = params.get("command", "")
            # Check if it's a git operation that might commit secrets
            if "git commit" in command or "git add" in command:
                return command
            # Also check for echo/cat commands that might contain secrets
            if "echo" in command or "cat >" in command or "cat <<" in command:
                return command
            return ""

        return ""
