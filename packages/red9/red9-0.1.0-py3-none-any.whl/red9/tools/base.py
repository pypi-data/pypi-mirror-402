"""Base tool interface and registry."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from red9.security.hooks import SecurityHookRunner

logger = logging.getLogger(__name__)

# Default project root - can be overridden
_project_root: Path | None = None


def set_project_root(path: Path) -> None:
    """Set the project root for path validation."""
    global _project_root
    _project_root = path.resolve()
    logger.info(f"Project root set to: {_project_root}")


def get_project_root() -> Path:
    """Get the project root, defaulting to cwd."""
    return _project_root or Path.cwd()


def validate_path(
    path: str | Path,
    must_exist: bool = False,
    allow_outside_project: bool = False,
) -> tuple[Path | None, str | None]:
    """
    Validate a file path for security.

    Args:
        path: Path to validate
        must_exist: If True, the path must exist
        allow_outside_project: If True, allow paths outside project root

    Returns:
        Tuple of (resolved_path, error_message)
        If valid: (path, None)
        If invalid: (None, error_message)
    """
    try:
        # Convert to Path and resolve to absolute
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = get_project_root() / file_path
        file_path = file_path.resolve()

        # Check for path traversal attempts
        project_root = get_project_root().resolve()

        if not allow_outside_project:
            try:
                file_path.relative_to(project_root)
            except ValueError:
                logger.warning(
                    f"Path traversal attempt blocked: {path} -> {file_path} "
                    f"(outside project root: {project_root})"
                )
                return None, "Access denied: path is outside project directory"

        # Check for suspicious patterns
        path_str = str(file_path)
        suspicious_patterns = [
            "/etc/passwd",
            "/etc/shadow",
            "/etc/sudoers",
            "/.ssh/",
            "/.gnupg/",
            "/.aws/",
            "/proc/",
            "/sys/",
            "/dev/",
        ]
        for pattern in suspicious_patterns:
            if pattern in path_str:
                logger.warning(f"Access to sensitive path blocked: {path_str}")
                return None, "Access denied: sensitive system path"

        # Check if file must exist
        if must_exist and not file_path.exists():
            return None, f"File not found: {path}"

        return file_path, None

    except Exception as e:
        logger.error(f"Path validation error for {path}: {e}")
        return None, f"Invalid path: {e}"


class ToolErrorType(Enum):
    """Error types for tool execution."""

    # File System
    FILE_NOT_FOUND = "file_not_found"
    FILE_WRITE_FAILURE = "file_write_failure"
    PERMISSION_DENIED = "permission_denied"
    NO_SPACE_LEFT = "no_space_left"

    # Edit-specific
    EDIT_NO_OCCURRENCE_FOUND = "edit_no_occurrence_found"
    EDIT_MULTIPLE_OCCURRENCES = "edit_multiple_occurrences"
    EDIT_NO_CHANGE = "edit_no_change"
    EDIT_VALIDATION_FAILED = "edit_validation_failed"  # Syntax validation failed

    # Search
    GREP_EXECUTION_ERROR = "grep_execution_error"
    GLOB_EXECUTION_ERROR = "glob_execution_error"

    # Shell
    SHELL_EXECUTE_ERROR = "shell_execute_error"
    SHELL_TIMEOUT = "shell_timeout"

    # Approval
    APPROVAL_DENIED = "approval_denied"

    # General
    INVALID_PARAMS = "invalid_params"
    NOT_INITIALIZED = "not_initialized"
    EXECUTION_ERROR = "execution_error"

    # Network
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"

    # Security
    SECURITY_VIOLATION = "security_violation"


@dataclass
class ToolResult:
    """Result of a tool execution."""

    success: bool
    output: Any
    error: str | None = None
    error_type: ToolErrorType | None = None
    diff: str | None = None  # Unified diff for file operations

    @classmethod
    def ok(cls, output: Any, diff: str | None = None) -> ToolResult:
        """Create a successful result."""
        return cls(success=True, output=output, diff=diff)

    @classmethod
    def fail(
        cls,
        error: str,
        error_type: ToolErrorType | None = None,
        output: Any = None,
    ) -> ToolResult:
        """Create a failure result."""
        return cls(
            success=False,
            output=output,
            error=error,
            error_type=error_type,
        )


@dataclass
class ToolDefinition:
    """OpenAI function calling compatible definition."""

    name: str
    description: str
    parameters: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to OpenAI function format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class Tool(ABC):
    """Abstract base class for tools.

    Tools are atomic operations that agents can perform.
    Each tool has a name, description, and execute method.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for identification."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM context."""
        pass

    @property
    def read_only(self) -> bool:
        """Whether this tool only reads data (no side effects)."""
        return True

    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """Get the OpenAI function calling compatible definition."""
        pass

    @abstractmethod
    def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            params: Tool parameters.

        Returns:
            Tool execution result.
        """
        pass


class ToolRegistry:
    """Registry for available tools."""

    def __init__(
        self,
        require_approval: bool = False,
        workflow_id: str | None = None,
        stage_name: str | None = None,
        security_hooks: SecurityHookRunner | None = None,
    ) -> None:
        """Initialize an empty registry.

        Args:
            require_approval: Whether to check approval for write operations.
            workflow_id: Optional workflow ID for approval tracking.
            stage_name: Optional stage name for approval tracking.
            security_hooks: Optional SecurityHookRunner for pre-execution checks.
        """
        self._tools: dict[str, Tool] = {}
        self._require_approval = require_approval
        self._workflow_id = workflow_id
        self._stage_name = stage_name
        self._security_hooks = security_hooks

    def register(self, tool: Tool) -> None:
        """Register a tool.

        Args:
            tool: Tool instance to register.
        """
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Get a tool by name.

        Args:
            name: Tool name.

        Returns:
            Tool instance or None.
        """
        return self._tools.get(name)

    def get_all(self) -> list[Tool]:
        """Get all registered tools.

        Returns:
            List of all tools.
        """
        return list(self._tools.values())

    def get_read_only(self) -> list[Tool]:
        """Get all read-only tools.

        Returns:
            List of read-only tools.
        """
        return [t for t in self._tools.values() if t.read_only]

    def get_write_tools(self) -> list[Tool]:
        """Get all tools that can modify state.

        Returns:
            List of write tools.
        """
        return [t for t in self._tools.values() if not t.read_only]

    def get_definitions(self) -> list[dict[str, Any]]:
        """Get OpenAI function calling definitions for all tools.

        Returns:
            List of tool definitions in OpenAI format.
        """
        return [tool.get_definition().to_dict() for tool in self._tools.values()]

    def set_security_hooks(self, hooks: SecurityHookRunner) -> None:
        """Set security hooks for pre-execution checks.

        Args:
            hooks: SecurityHookRunner instance.
        """
        self._security_hooks = hooks

    def filter(self, allowed_tools: list[str]) -> ToolRegistry:
        """Create a filtered registry with only specified tools.

        Args:
            allowed_tools: List of tool names to include.

        Returns:
            New ToolRegistry with only allowed tools.
        """
        filtered = ToolRegistry(
            require_approval=self._require_approval,
            workflow_id=self._workflow_id,
            stage_name=self._stage_name,
            security_hooks=self._security_hooks,
        )
        for name in allowed_tools:
            if name in self._tools:
                filtered._tools[name] = self._tools[name]
        return filtered

    def execute(self, name: str, params: dict[str, Any]) -> ToolResult:
        """Execute a tool by name.

        Args:
            name: Tool name.
            params: Tool parameters.

        Returns:
            Tool execution result.
        """
        tool = self.get(name)
        if not tool:
            # Include available tools in error message for LLM feedback loop
            available = sorted(self._tools.keys())
            available_str = ", ".join(available[:15])  # Limit to avoid huge messages
            if len(available) > 15:
                available_str += f" ... and {len(available) - 15} more"
            return ToolResult.fail(
                f"Unknown tool '{name}'. Available tools: {available_str}",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        # [1] Check approval for non-read-only tools
        if self._require_approval and not tool.read_only:
            from red9.approval import get_approval_manager

            manager = get_approval_manager()
            approved, reason = manager.check_tool_approval(
                tool_name=name,
                params=params,
                workflow_id=self._workflow_id,
                stage_name=self._stage_name,
            )
            if not approved:
                logger.warning(f"Tool execution denied: {name} - {reason}")
                return ToolResult.fail(
                    reason or "Operation not approved",
                    error_type=ToolErrorType.APPROVAL_DENIED,
                )

        # [2] Run security hooks before execution
        if self._security_hooks:
            from red9.security.hooks import SecurityAction

            security_result = self._security_hooks.run_pre_hooks(name, params)
            if security_result.action == SecurityAction.BLOCK:
                logger.error(f"Security hook blocked {name}: {security_result.reason}")
                return ToolResult.fail(
                    f"Security violation: {security_result.reason}",
                    error_type=ToolErrorType.SECURITY_VIOLATION,
                )

        # [3] Execute tool
        return tool.execute(params)


def create_default_registry() -> ToolRegistry:
    """Create a registry with all default tools.

    Returns:
        ToolRegistry with all tools registered.
    """
    from red9.tools.apply_diff import ApplyDiffTool
    from red9.tools.complete_task import CompleteTaskTool
    from red9.tools.edit_file import EditFileTool
    from red9.tools.glob import GlobTool
    from red9.tools.grep import GrepTool
    from red9.tools.list_dir import ListDirTool
    from red9.tools.memory import MemoryTool
    from red9.tools.read_file import ReadFileTool
    from red9.tools.read_many_files import ReadManyFilesTool
    from red9.tools.semantic_search import SemanticSearchTool
    from red9.tools.shell import ShellTool
    from red9.tools.web_fetch import WebFetchTool
    from red9.tools.write_file import WriteFileTool

    registry = ToolRegistry()
    # Read tools
    registry.register(ReadFileTool())
    registry.register(ReadManyFilesTool())
    registry.register(ListDirTool())
    registry.register(GrepTool())
    registry.register(GlobTool())
    registry.register(SemanticSearchTool())
    registry.register(WebFetchTool())
    # Write tools
    registry.register(WriteFileTool())
    registry.register(EditFileTool())
    registry.register(ApplyDiffTool())
    registry.register(ShellTool())
    registry.register(MemoryTool())
    # Control tools
    registry.register(CompleteTaskTool())

    return registry
