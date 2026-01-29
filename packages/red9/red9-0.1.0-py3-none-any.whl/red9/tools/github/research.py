"""GitHub integration tools for external research.

Enables agents to clone and search external repositories for reference implementations.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from red9.logging import get_logger
from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult

logger = get_logger(__name__)


class GitHubCloneTool(Tool):
    """Clone a GitHub repository to a temporary directory for analysis."""

    def __init__(self):
        self._temp_base = Path(tempfile.gettempdir()) / "red9_research"
        self._temp_base.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "github_clone"

    @property
    def description(self) -> str:
        return """Clone a public GitHub repository for reference.
Use this to read code from other projects to understand how to use libraries or implement features.
Returns the path to the cloned repository.
"""

    @property
    def read_only(self) -> bool:
        return False  # Writes to temp dir

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "repo_url": {
                        "type": "string",
                        "description": "GitHub URL (e.g., https://github.com/owner/repo) or owner/repo string",
                    },
                },
                "required": ["repo_url"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        repo_url = params.get("repo_url", "").strip()
        if not repo_url:
            return ToolResult.fail("repo_url is required", error_type=ToolErrorType.INVALID_PARAMS)

        # Normalize URL
        if not repo_url.startswith("http"):
            repo_url = f"https://github.com/{repo_url}"

        # Create safe directory name
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        owner = repo_url.split("/")[-2]
        dest_dir = self._temp_base / f"{owner}_{repo_name}"

        # Check if already cloned
        if dest_dir.exists():
            # Quick pull to update
            try:
                subprocess.run(["git", "pull"], cwd=dest_dir, capture_output=True, timeout=30)
                return ToolResult.ok(
                    {
                        "path": str(dest_dir),
                        "status": "updated",
                        "message": f"Repository already exists at {dest_dir}. Updated.",
                    }
                )
            except Exception:
                # If pull fails, re-clone might be safer, or just return existing
                pass

        try:
            # Clone shallowly for speed
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(dest_dir)],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                return ToolResult.fail(
                    f"Git clone failed: {result.stderr}", error_type=ToolErrorType.EXECUTION_ERROR
                )

            return ToolResult.ok(
                {
                    "path": str(dest_dir),
                    "status": "cloned",
                    "message": f"Cloned {repo_url} to {dest_dir}",
                }
            )

        except subprocess.TimeoutExpired:
            return ToolResult.fail("Git clone timed out", error_type=ToolErrorType.TIMEOUT)
        except Exception as e:
            return ToolResult.fail(
                f"Git clone error: {e}", error_type=ToolErrorType.EXECUTION_ERROR
            )


class GitHubRepoSearchTool(Tool):
    """Search for code patterns inside a cloned repository."""

    @property
    def name(self) -> str:
        return "github_search"

    @property
    def description(self) -> str:
        return """Search for code patterns in a CLONED external repository.
Use this AFTER calling github_clone to find usage examples.
Do NOT use this for the main project (use grep instead).
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
                    "repo_path": {
                        "type": "string",
                        "description": "Path to the cloned repository (returned by github_clone)",
                    },
                    "query": {
                        "type": "string",
                        "description": "Regex pattern to search for",
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "Glob pattern for file filtering (e.g., '*.ts')",
                    },
                },
                "required": ["repo_path", "query"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        repo_path = params.get("repo_path")
        query = params.get("query")
        file_pattern = params.get("file_pattern")

        if not repo_path or not query:
            return ToolResult.fail(
                "repo_path and query are required", error_type=ToolErrorType.INVALID_PARAMS
            )

        path = Path(repo_path)
        if not path.exists() or not path.is_dir():
            return ToolResult.fail(
                f"Repository path not found: {repo_path}", error_type=ToolErrorType.FILE_NOT_FOUND
            )

        # Check if it's likely a repo (safety check)
        if not (path / ".git").exists():
            return ToolResult.fail(
                f"Path is not a git repository: {repo_path}",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        # Use grep/ripgrep logic
        # We can reuse GrepTool logic or implement simple grep
        cmd = ["grep", "-r", "-n", "-I", query, "."]

        if file_pattern:
            cmd.extend(["--include", file_pattern])

        try:
            result = subprocess.run(cmd, cwd=path, capture_output=True, text=True, timeout=30)

            output = result.stdout
            if not output:
                return ToolResult.ok("No matches found.")

            # Limit output
            lines = output.splitlines()
            if len(lines) > 100:
                output = (
                    "\n".join(lines[:100]) + f"\n... ({len(lines) - 100} more matches truncated)"
                )

            return ToolResult.ok(output)

        except Exception as e:
            return ToolResult.fail(
                f"Search failed: {e}", error_type=ToolErrorType.GREP_EXECUTION_ERROR
            )
