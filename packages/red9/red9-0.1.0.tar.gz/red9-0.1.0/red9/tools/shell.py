"""Shell command execution tool with security controls."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from red9.logging import get_logger
from red9.sandbox import LocalSandbox, Sandbox
from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult

logger = get_logger(__name__)

# Dangerous command patterns that should be blocked
DANGEROUS_PATTERNS: list[re.Pattern[str]] = [
    # Destructive file operations
    re.compile(r"\brm\s+(-[rfRF]+\s+)?(/|~|\$HOME|\.\.|/etc|/usr|/var|/bin|/sbin)", re.I),
    re.compile(r"\brm\s+-[rfRF]*\s+\*", re.I),  # rm -rf *
    re.compile(r"\bdd\s+.*\bof=/dev/", re.I),  # dd to devices
    re.compile(r"\bmkfs\b", re.I),  # Format filesystems
    re.compile(r"\bfdisk\b", re.I),  # Partition tools
    re.compile(r"\bparted\b", re.I),
    # Privilege escalation
    re.compile(r"\bsudo\s+", re.I),
    re.compile(r"\bsu\s+", re.I),
    re.compile(r"\bdoas\s+", re.I),
    re.compile(r"\bchmod\s+[0-7]*777", re.I),  # World-writable
    re.compile(r"\bchown\s+root", re.I),
    # Network exfiltration
    re.compile(r"\bcurl\s+.*\|\s*(ba)?sh", re.I),  # curl | sh
    re.compile(r"\bwget\s+.*\|\s*(ba)?sh", re.I),  # wget | sh
    re.compile(r"\bnc\s+-[el]", re.I),  # netcat listeners
    re.compile(r"\bncat\s+-[el]", re.I),
    # System modification
    re.compile(r"\bsystemctl\s+(stop|disable|mask)", re.I),
    re.compile(r"\bservice\s+\S+\s+stop", re.I),
    re.compile(r"\bkillall\b", re.I),
    re.compile(r"\bpkill\s+-9", re.I),
    # Cron/scheduled tasks
    re.compile(r"\bcrontab\s+-[re]", re.I),
    # Shell bombs/forks
    re.compile(r":\(\)\s*\{\s*:\|:&\s*\}", re.I),  # Fork bomb
    re.compile(r"\bwhile\s+true.*done", re.I),  # Infinite loops
    # History/credential access
    re.compile(r"\bcat\s+.*\.(bash_history|ssh|gnupg|aws)", re.I),
    re.compile(r"\bcat\s+.*/etc/(passwd|shadow)", re.I),
    # Dangerous redirections
    re.compile(r">\s*/dev/sd[a-z]", re.I),  # Write to raw disk
    re.compile(r">\s*/etc/", re.I),  # Overwrite system configs
]

# Safe command prefixes (commands that are explicitly allowed)
SAFE_COMMAND_PREFIXES: list[str] = [
    # Git operations
    "git",
    # Testing
    "pytest",
    "python -m pytest",
    "python3 -m pytest",
    "unittest",
    "python -m unittest",
    "npm test",
    "npm run test",
    "yarn test",
    "cargo test",
    "go test",
    "mix test",
    "rspec",
    "bundle exec rspec",
    # Linting/formatting
    "ruff",
    "black",
    "isort",
    "flake8",
    "pylint",
    "mypy",
    "pyright",
    "eslint",
    "prettier",
    "tsc",
    "cargo fmt",
    "cargo clippy",
    "rustfmt",
    "go fmt",
    "gofmt",
    "golint",
    # Build tools
    "pip install",
    "pip3 install",
    "python -m pip",
    "npm install",
    "npm ci",
    "npm run build",
    "yarn",
    "cargo build",
    "cargo run",
    "go build",
    "go run",
    "go mod",
    "make",
    "cmake",
    "mvn",
    "gradle",
    # File inspection (read-only)
    "cat",
    "head",
    "tail",
    "less",
    "more",
    "ls",
    "find",
    "locate",
    "which",
    "whereis",
    "wc",
    "grep",
    "rg",
    "ag",
    "ack",
    "file",
    "stat",
    "du",
    "df",
    # Process inspection
    "ps",
    "top",
    "htop",
    "pgrep",
    # Python/Node execution
    "python",
    "python3",
    "node",
    "npx",
]


def is_command_safe(command: str) -> tuple[bool, str]:
    """
    Check if a command is safe to execute.

    Returns:
        Tuple of (is_safe, reason)
    """
    # Normalize command
    cmd_lower = command.lower().strip()

    # Check against dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return False, f"Command matches dangerous pattern: {pattern.pattern}"

    # Check for shell injection via special characters in suspicious contexts
    # RELAXED: Allow &&, ||, ; for command chaining in autonomous agents
    suspicious_chars = ["|", "`", "$(", "${"]
    for char in suspicious_chars:
        if char in command:
            # Allow pipes for safe commands like grep
            if char == "|":
                parts = command.split("|")
                # Check each part of the pipeline
                for part in parts:
                    part = part.strip()
                    if not any(part.startswith(prefix) for prefix in SAFE_COMMAND_PREFIXES):
                        # Allow common safe pipe targets
                        safe_pipe_targets = [
                            "grep",
                            "head",
                            "tail",
                            "wc",
                            "sort",
                            "uniq",
                            "awk",
                            "sed",
                            "cut",
                            "tr",
                            "tee",
                            "xargs",
                            "python",  # Allow piping to python
                            "python3",
                            "node",
                            "bash",  # Allow piping to bash (source is validated)
                            "sh",
                        ]
                        if not any(part.startswith(t) for t in safe_pipe_targets):
                            # Allow if source is a local script (./...)
                            if part.startswith("./") or part.startswith("python"):
                                continue
                            return False, f"Pipe to potentially unsafe command: {part[:50]}"
                continue
            # Log warning for command chaining
            logger.warning(f"Command contains shell metacharacter '{char}': {command[:100]}")

    # Check if command starts with a known safe prefix
    is_explicitly_safe = any(
        cmd_lower.startswith(prefix.lower()) for prefix in SAFE_COMMAND_PREFIXES
    )

    if is_explicitly_safe:
        return True, "Command matches safe prefix"

    # For unknown commands, allow but log
    logger.info(f"Executing unrecognized command (not in safe list): {command[:100]}")
    return True, "Command allowed (not in blocklist)"


class ShellTool(Tool):
    """Execute shell commands with security controls via sandbox."""

    def __init__(
        self,
        project_root: Path | None = None,
        strict_mode: bool = False,
        sandbox: Sandbox | None = None,
    ):
        """
        Initialize ShellTool.

        Args:
            project_root: Root directory for command execution.
            strict_mode: If True, only allow explicitly safe commands.
            sandbox: Sandbox execution environment.
        """
        self.project_root = project_root or Path.cwd()
        self.strict_mode = strict_mode
        self.sandbox = sandbox or LocalSandbox(self.project_root)

    @property
    def name(self) -> str:
        return "run_command"

    @property
    def description(self) -> str:
        return """Execute a shell command and return output.
Use for: running tests, installing dependencies, git operations, linting.

IMPORTANT:
- Commands run in the project directory
- Long-running commands will timeout (default: 120s)
- stdout and stderr are captured separately
- Dangerous commands (rm -rf /, sudo, etc.) are blocked
- Commands are logged for audit purposes"""

    @property
    def read_only(self) -> bool:
        return False

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (optional)",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 120, max: 600)",
                    },
                },
                "required": ["command"],
            },
        )

    def _validate_cwd(self, cwd: str | None) -> tuple[Path | None, str | None]:
        """Validate working directory is within project root."""
        if cwd is None:
            return None, None

        cwd_path = Path(cwd)
        # Handle absolute paths that might be inside project root
        if not cwd_path.is_absolute():
            cwd_path = (self.project_root / cwd_path).resolve()
        else:
            cwd_path = cwd_path.resolve()

        # Check if cwd is within project root
        try:
            cwd_path.relative_to(self.project_root.resolve())
            return cwd_path, None
        except ValueError:
            return None, f"Working directory must be within project root: {self.project_root}"

    def execute(self, params: dict[str, Any]) -> ToolResult:
        command = params.get("command", "")
        cwd = params.get("cwd")
        timeout = min(params.get("timeout", 120), 600)  # Max 10 minutes

        if not command:
            return ToolResult.fail(
                "command is required",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        # Security check: validate command
        is_safe, reason = is_command_safe(command)

        if not is_safe:
            logger.warning(f"Blocked dangerous command: {command[:200]} - Reason: {reason}")
            return ToolResult.fail(
                f"Command blocked for security reasons: {reason}",
                error_type=ToolErrorType.PERMISSION_DENIED,
            )

        # In strict mode, only allow explicitly safe commands
        if self.strict_mode and "not in blocklist" in reason:
            logger.warning(f"Strict mode: blocking non-allowlisted command: {command[:100]}")
            return ToolResult.fail(
                "Command not in allowlist (strict mode enabled)",
                error_type=ToolErrorType.PERMISSION_DENIED,
            )

        # Validate working directory
        validated_cwd, cwd_error = self._validate_cwd(cwd)
        if cwd_error:
            return ToolResult.fail(cwd_error, error_type=ToolErrorType.PERMISSION_DENIED)

        # Log command execution for audit
        logger.info(f"Executing command: {command[:200]}")

        try:
            # Execute in sandbox
            result = self.sandbox.run_command(
                command,
                cwd=validated_cwd or self.project_root,
                timeout=timeout,
            )

            # Log result summary
            logger.info(
                f"Command completed: return_code={result.exit_code}, "
                f"stdout_len={len(result.stdout)}, stderr_len={len(result.stderr)}"
            )

            if not result.success and result.stderr == f"Command timed out after {timeout}s":
                return ToolResult.fail(
                    result.stderr,
                    error_type=ToolErrorType.SHELL_TIMEOUT,
                )

            return ToolResult.ok(
                {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.exit_code,
                    "command": command,
                    "success": result.success,
                }
            )

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return ToolResult.fail(
                f"Command failed: {e}",
                error_type=ToolErrorType.SHELL_EXECUTE_ERROR,
            )
