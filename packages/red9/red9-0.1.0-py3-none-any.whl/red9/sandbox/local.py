"""Local 'sandbox' implementation (runs on host machine)."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from red9.logging import get_logger
from red9.sandbox.base import Sandbox, SandboxResult

logger = get_logger(__name__)


class LocalSandbox(Sandbox):
    """Local execution environment (not actually sandboxed).

    Executes commands directly on the host machine.
    Used for local development and when full trust is assumed.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize local sandbox.

        Args:
            project_root: Root directory for relative paths.
        """
        self.project_root = project_root.resolve()

    def run_command(
        self,
        command: str,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
        background: bool = False,
    ) -> SandboxResult:
        """Run a shell command on the host.

        Args:
            command: Command to run.
            cwd: Working directory.
            env: Environment variables.
            timeout: Timeout in seconds.
            background: If True, starts process and returns immediately (fake success).
        """
        start_time = time.time()

        # Resolve working directory
        if cwd:
            work_dir = Path(cwd)
            if not work_dir.is_absolute():
                work_dir = self.project_root / work_dir
        else:
            work_dir = self.project_root

        # Merge environment
        run_env = os.environ.copy()
        if env:
            run_env.update(env)

        try:
            if background:
                # For background processes, we just start Popen and don't wait
                subprocess.Popen(
                    command,
                    shell=True,
                    cwd=work_dir,
                    env=run_env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return SandboxResult(0, "(background process started)", "", 0.0)

            # Synchronous execution
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                env=run_env,
                capture_output=True,
                text=True,
                timeout=timeout,
                stdin=subprocess.DEVNULL,  # Prevent hanging on stdin
            )

            duration = time.time() - start_time
            return SandboxResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return SandboxResult(
                exit_code=124,  # Standard timeout exit code
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                duration=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            return SandboxResult(
                exit_code=1,
                stdout="",
                stderr=str(e),
                duration=duration,
            )

    def read_file(self, path: str | Path) -> str:
        """Read file from host filesystem."""
        target = self._resolve_path(path)
        return target.read_text(encoding="utf-8")

    def write_file(self, path: str | Path, content: str) -> None:
        """Write file to host filesystem."""
        target = self._resolve_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def file_exists(self, path: str | Path) -> bool:
        """Check file existence on host."""
        target = self._resolve_path(path)
        return target.exists()

    def cleanup(self) -> None:
        """Nothing to clean up for local sandbox."""
        pass

    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve path relative to project root."""
        p = Path(path)
        if p.is_absolute():
            return p
        return self.project_root / p
