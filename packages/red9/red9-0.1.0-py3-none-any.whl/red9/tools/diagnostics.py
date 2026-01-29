"""Diagnostics tool for project-wide verification.

Inspired by oh-my-opencode's lsp_diagnostics strategy.
Runs build/typecheck commands to catch cascading errors.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from red9.logging import get_logger
from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult

logger = get_logger(__name__)


class DiagnosticsTool(Tool):
    """Run project-wide diagnostics (type checking, build)."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    @property
    def name(self) -> str:
        return "run_diagnostics"

    @property
    def description(self) -> str:
        return """Run project-wide diagnostics to catch cascading errors.

Automatically detects and runs:
- Python: `mypy .` (if configured)
- Node/TS: `npm run typecheck` or `tsc --noEmit`
- Rust: `cargo check`
- Go: `go build ./...`

Use this AFTER applying changes to ensure you haven't broken other files.
"""

    @property
    def read_only(self) -> bool:
        return True

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "scope": {
                        "type": "string",
                        "description": "Scope of check (unused currently, reserved for future file-specific LSP)",
                        "default": "project",
                    }
                },
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        # 1. Detect project type
        commands = []

        # Python
        if (self.project_root / "pyproject.toml").exists() or list(self.project_root.glob("*.py")):
            # Type Check
            if (self.project_root / "mypy.ini").exists() or "mypy" in self._get_dev_deps():
                commands.append(("mypy .", "Type Check"))

            # Coverage
            if (self.project_root / ".coveragerc").exists() or "pytest-cov" in self._get_dev_deps():
                commands.append(("pytest --cov=.", "Test Coverage"))

        # Node/TS
        if (self.project_root / "package.json").exists():
            pkg = self._read_package_json()
            scripts = pkg.get("scripts", {})

            if "typecheck" in scripts:
                commands.append(("npm run typecheck", "Type Check"))
            elif (self.project_root / "tsconfig.json").exists():
                commands.append(("npx tsc --noEmit", "Type Check"))

            if "test:cov" in scripts:
                commands.append(("npm run test:cov", "Test Coverage"))

        # Rust
        if (self.project_root / "Cargo.toml").exists():
            commands.append(("cargo check", "Cargo Check"))
            commands.append(("cargo test", "Rust Tests"))

        # Go
        if (self.project_root / "go.mod").exists():
            commands.append(("go build ./...", "Go Build"))
            commands.append(("go test ./... -cover", "Go Coverage"))

        if not commands:
            return ToolResult.ok("No diagnostic commands detected for this project structure.")

        results = []
        all_passed = True

        for cmd, desc in commands:
            logger.info(f"Running diagnostic: {cmd}")
            try:
                # Use shell=True for flexibility with npm/npx
                proc = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                output = (proc.stdout + "\n" + proc.stderr).strip()
                if proc.returncode == 0:
                    results.append(f"✅ {desc}: PASSED")
                else:
                    all_passed = False
                    results.append(
                        f"❌ {desc}: FAILED\n{output[:2000]}"
                    )  # Truncate long error logs

            except Exception as e:
                all_passed = False
                results.append(f"❌ {desc}: EXECUTION ERROR: {e}")

        summary = "\n\n".join(results)

        if all_passed:
            return ToolResult.ok(f"All diagnostics passed.\n\n{summary}")
        else:
            return ToolResult.fail(
                f"Diagnostics failed.\n\n{summary}", error_type=ToolErrorType.EXECUTION_ERROR
            )

    def _read_package_json(self) -> dict:
        try:
            import json

            return json.loads((self.project_root / "package.json").read_text())
        except Exception:
            return {}

    def _get_dev_deps(self) -> str:
        # Heuristic for python deps
        try:
            return (self.project_root / "pyproject.toml").read_text()
        except Exception:
            return ""
