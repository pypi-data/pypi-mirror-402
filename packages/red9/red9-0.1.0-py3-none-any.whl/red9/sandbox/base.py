"""Sandbox environment for executing code and commands safely."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SandboxResult:
    """Result of a sandbox execution."""

    exit_code: int
    stdout: str
    stderr: str
    duration: float = 0.0

    @property
    def success(self) -> bool:
        """Check if execution was successful."""
        return self.exit_code == 0


class Sandbox(ABC):
    """Abstract base class for execution sandboxes.

    A sandbox provides an isolated environment for:
    1. Running shell commands
    2. Reading/Writing files (optionally mapped)
    3. Executing tests
    """

    @abstractmethod
    def run_command(
        self,
        command: str,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
        background: bool = False,
    ) -> SandboxResult:
        """Run a shell command in the sandbox.

        Args:
            command: Command string to execute.
            cwd: Working directory inside sandbox.
            env: Environment variables.
            timeout: Execution timeout in seconds.
            background: Whether to run in background (not awaited).

        Returns:
            SandboxResult with output and exit code.
        """
        pass

    @abstractmethod
    def read_file(self, path: str | Path) -> str:
        """Read a file from the sandbox.

        Args:
            path: Path to file inside sandbox.

        Returns:
            File content.
        """
        pass

    @abstractmethod
    def write_file(self, path: str | Path, content: str) -> None:
        """Write content to a file in the sandbox.

        Args:
            path: Path to file inside sandbox.
            content: Content to write.
        """
        pass

    @abstractmethod
    def file_exists(self, path: str | Path) -> bool:
        """Check if file exists in sandbox.

        Args:
            path: Path to check.

        Returns:
            True if exists.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up sandbox resources."""
        pass
