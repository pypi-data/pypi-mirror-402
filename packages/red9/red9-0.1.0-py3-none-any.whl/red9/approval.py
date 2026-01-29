"""Approval system for RED9 operations.

Provides configurable approval gates for destructive operations.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal

from red9.logging import get_logger

logger = get_logger(__name__)


class ApprovalMode(str, Enum):
    """Approval mode settings."""

    DEFAULT = "default"  # Require approval for destructive operations
    PLAN = "plan"  # Only approve the plan, then auto-execute
    AUTO = "auto"  # Auto-approve everything in workflows
    YOLO = "yolo"  # No approvals ever (use with caution)


class ApprovalStatus(str, Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OperationType(str, Enum):
    """Types of operations that may require approval."""

    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    SHELL_COMMAND = "shell_command"
    PLAN_EXECUTION = "plan_execution"
    EXTERNAL_API = "external_api"


@dataclass
class ApprovalRequest:
    """A request for user approval."""

    id: str
    operation_type: OperationType
    description: str
    details: dict[str, Any]
    workflow_id: str | None = None
    stage_name: str | None = None
    tool_name: str | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    decided_at: datetime | None = None
    decision_reason: str | None = None

    def approve(self, reason: str | None = None) -> None:
        """Mark this request as approved."""
        self.status = ApprovalStatus.APPROVED
        self.decided_at = datetime.now(UTC)
        self.decision_reason = reason
        logger.info(f"Approval granted: {self.id} - {self.description}")

    def reject(self, reason: str | None = None) -> None:
        """Mark this request as rejected."""
        self.status = ApprovalStatus.REJECTED
        self.decided_at = datetime.now(UTC)
        self.decision_reason = reason
        logger.warning(f"Approval rejected: {self.id} - {self.description}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "operation_type": self.operation_type.value,
            "description": self.description,
            "details": self.details,
            "workflow_id": self.workflow_id,
            "stage_name": self.stage_name,
            "tool_name": self.tool_name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "decision_reason": self.decision_reason,
        }


class ApprovalHandler(ABC):
    """Abstract handler for approval requests."""

    @abstractmethod
    def request_approval(self, request: ApprovalRequest) -> ApprovalStatus:
        """Request approval for an operation.

        Args:
            request: The approval request.

        Returns:
            The approval status after handling.
        """
        pass


class AutoApproveHandler(ApprovalHandler):
    """Handler that auto-approves everything."""

    def request_approval(self, request: ApprovalRequest) -> ApprovalStatus:
        """Auto-approve the request."""
        request.approve(reason="Auto-approved")
        return ApprovalStatus.APPROVED


class AutoRejectHandler(ApprovalHandler):
    """Handler that auto-rejects everything (for testing)."""

    def request_approval(self, request: ApprovalRequest) -> ApprovalStatus:
        """Auto-reject the request."""
        request.reject(reason="Auto-rejected")
        return ApprovalStatus.REJECTED


class ConsoleApprovalHandler(ApprovalHandler):
    """Handler that prompts for approval via console."""

    def __init__(self, timeout: int = 300) -> None:
        """Initialize with optional timeout.

        Args:
            timeout: Timeout in seconds for approval (default: 5 minutes).
        """
        self.timeout = timeout

    def request_approval(self, request: ApprovalRequest) -> ApprovalStatus:
        """Prompt for approval via console."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Confirm

        console = Console()

        # Build approval panel
        details_str = json.dumps(request.details, indent=2, default=str)

        panel_content = f"""[bold]Operation:[/bold] {request.operation_type.value}
[bold]Description:[/bold] {request.description}
[bold]Tool:[/bold] {request.tool_name or "N/A"}
[bold]Workflow:[/bold] {request.workflow_id or "N/A"}
[bold]Stage:[/bold] {request.stage_name or "N/A"}

[bold]Details:[/bold]
{details_str}"""

        console.print(
            Panel(
                panel_content,
                title="[yellow]⚠️ Approval Required[/yellow]",
                border_style="yellow",
            )
        )

        try:
            approved = Confirm.ask("[yellow]Approve this operation?[/yellow]")
            if approved:
                request.approve(reason="User approved via console")
                return ApprovalStatus.APPROVED
            else:
                request.reject(reason="User rejected via console")
                return ApprovalStatus.REJECTED
        except KeyboardInterrupt:
            request.reject(reason="Interrupted by user")
            return ApprovalStatus.REJECTED


class CallbackApprovalHandler(ApprovalHandler):
    """Handler that uses a callback function for approval."""

    def __init__(self, callback: Callable[[ApprovalRequest], bool]) -> None:
        """Initialize with callback function.

        Args:
            callback: Function that takes ApprovalRequest and returns True/False.
        """
        self.callback = callback

    def request_approval(self, request: ApprovalRequest) -> ApprovalStatus:
        """Call the callback for approval decision."""
        try:
            if self.callback(request):
                request.approve(reason="Approved via callback")
                return ApprovalStatus.APPROVED
            else:
                request.reject(reason="Rejected via callback")
                return ApprovalStatus.REJECTED
        except Exception as e:
            logger.error(f"Approval callback error: {e}")
            request.reject(reason=f"Callback error: {e}")
            return ApprovalStatus.REJECTED


class ApprovalManager:
    """Manages approval workflow for RED9 operations.

    Provides configurable approval gates based on operation type and mode.
    """

    def __init__(
        self,
        mode: ApprovalMode = ApprovalMode.DEFAULT,
        handler: ApprovalHandler | None = None,
        tool_registry: Any = None,
    ) -> None:
        """Initialize approval manager.

        Args:
            mode: The approval mode to use.
            handler: Custom approval handler (uses ConsoleApprovalHandler by default).
            tool_registry: Optional ToolRegistry for dynamic tool discovery.
        """
        self.mode = mode
        self._handler = handler
        self._history: list[ApprovalRequest] = []
        self._auto_approved_operations: set[str] = set()
        self._plan_approved = False
        self._tool_registry = tool_registry

        # Default handler based on mode
        if self._handler is None:
            if mode in (ApprovalMode.AUTO, ApprovalMode.YOLO):
                self._handler = AutoApproveHandler()
            else:
                self._handler = ConsoleApprovalHandler()

    def set_tool_registry(self, registry: Any) -> None:
        """Set the tool registry for dynamic tool discovery.

        Args:
            registry: ToolRegistry instance.
        """
        self._tool_registry = registry

    @property
    def handler(self) -> ApprovalHandler:
        """Get the approval handler."""
        return self._handler or ConsoleApprovalHandler()

    def requires_approval(self, operation_type: OperationType) -> bool:
        """Check if an operation type requires approval.

        Args:
            operation_type: The type of operation.

        Returns:
            True if approval is required.
        """
        if self.mode == ApprovalMode.YOLO:
            return False

        if self.mode == ApprovalMode.AUTO:
            return False

        if self.mode == ApprovalMode.PLAN:
            # Only plan execution needs approval, rest auto-approved after
            return operation_type == OperationType.PLAN_EXECUTION and not self._plan_approved

        # DEFAULT mode - all destructive operations need approval
        destructive_ops = {
            OperationType.FILE_WRITE,
            OperationType.FILE_DELETE,
            OperationType.SHELL_COMMAND,
            OperationType.PLAN_EXECUTION,
        }
        return operation_type in destructive_ops

    def mark_plan_approved(self) -> None:
        """Mark that the plan has been approved.

        In PLAN mode, this allows subsequent operations to auto-execute.
        """
        self._plan_approved = True
        logger.info("Plan approved - subsequent operations will auto-execute")

    def request_approval(
        self,
        operation_type: OperationType,
        description: str,
        details: dict[str, Any],
        workflow_id: str | None = None,
        stage_name: str | None = None,
        tool_name: str | None = None,
    ) -> ApprovalStatus:
        """Request approval for an operation.

        Args:
            operation_type: Type of operation.
            description: Human-readable description.
            details: Operation details (params, paths, etc.).
            workflow_id: Optional workflow ID.
            stage_name: Optional stage name.
            tool_name: Optional tool name.

        Returns:
            The approval status.
        """
        import uuid

        request = ApprovalRequest(
            id=str(uuid.uuid4())[:8],
            operation_type=operation_type,
            description=description,
            details=details,
            workflow_id=workflow_id,
            stage_name=stage_name,
            tool_name=tool_name,
        )

        # Check if approval is required
        if not self.requires_approval(operation_type):
            request.approve(reason=f"Auto-approved (mode={self.mode.value})")
            self._history.append(request)
            return ApprovalStatus.APPROVED

        # Request approval from handler
        status = self.handler.request_approval(request)
        self._history.append(request)

        # If plan was approved, mark it
        if status == ApprovalStatus.APPROVED and operation_type == OperationType.PLAN_EXECUTION:
            self.mark_plan_approved()

        return status

    def check_tool_approval(
        self,
        tool_name: str,
        params: dict[str, Any],
        workflow_id: str | None = None,
        stage_name: str | None = None,
    ) -> tuple[bool, str | None]:
        """Check if a tool execution is approved.

        Args:
            tool_name: Name of the tool.
            params: Tool parameters.
            workflow_id: Optional workflow ID.
            stage_name: Optional stage name.

        Returns:
            Tuple of (is_approved, rejection_reason).
        """
        # Determine operation type from tool
        operation_type = self._get_tool_operation_type(tool_name)

        if operation_type is None:
            # Read-only tool, no approval needed
            return True, None

        # Build description
        description = self._build_tool_description(tool_name, params)

        # Request approval
        status = self.request_approval(
            operation_type=operation_type,
            description=description,
            details={"tool": tool_name, "params": params},
            workflow_id=workflow_id,
            stage_name=stage_name,
            tool_name=tool_name,
        )

        if status == ApprovalStatus.APPROVED:
            return True, None
        else:
            return False, f"Operation not approved: {description}"

    def _get_tool_operation_type(self, tool_name: str) -> OperationType | None:
        """Map tool name to operation type.

        Uses dynamic discovery if tool_registry is available, otherwise falls
        back to hardcoded mappings for known tools.

        Args:
            tool_name: Name of the tool.

        Returns:
            Operation type or None for read-only tools.
        """
        # Try dynamic discovery from tool registry first
        if self._tool_registry is not None:
            tool = self._tool_registry.get(tool_name)
            if tool is not None:
                # Use the tool's read_only property for discovery
                if getattr(tool, "read_only", False):
                    return None  # Read-only tools don't need approval

                # Determine operation type based on tool name patterns
                tool_name_lower = tool_name.lower()

                # Shell/command execution tools
                if any(kw in tool_name_lower for kw in ["shell", "command", "exec", "run", "bash"]):
                    return OperationType.SHELL_COMMAND

                # File deletion tools
                if any(kw in tool_name_lower for kw in ["delete", "remove", "rm"]):
                    return OperationType.FILE_DELETE

                # External API tools
                if any(kw in tool_name_lower for kw in ["api", "http", "request", "fetch"]):
                    return OperationType.EXTERNAL_API

                # Default to file write for non-read-only tools
                return OperationType.FILE_WRITE

        # Fallback to hardcoded mappings for known tools
        # (used when tool_registry is not available)
        write_tools = {
            "write_file": OperationType.FILE_WRITE,
            "edit_file": OperationType.FILE_WRITE,
        }
        shell_tools = {
            "shell": OperationType.SHELL_COMMAND,
        }

        if tool_name in write_tools:
            return write_tools[tool_name]
        if tool_name in shell_tools:
            return shell_tools[tool_name]

        # Read-only tools don't need approval
        return None

    def _build_tool_description(self, tool_name: str, params: dict[str, Any]) -> str:
        """Build human-readable description of tool operation.

        Args:
            tool_name: Name of the tool.
            params: Tool parameters.

        Returns:
            Description string.
        """
        if tool_name == "write_file":
            path = params.get("file_path", "unknown")
            return f"Write file: {path}"

        if tool_name == "edit_file":
            path = params.get("file_path", "unknown")
            old = params.get("old_string", "")[:50]
            return f"Edit file: {path} (replace '{old}...')"

        if tool_name == "shell":
            cmd = params.get("command", "unknown")
            return f"Execute command: {cmd}"

        return f"Execute {tool_name}"

    def get_history(self) -> list[dict[str, Any]]:
        """Get approval history.

        Returns:
            List of approval requests as dictionaries.
        """
        return [r.to_dict() for r in self._history]

    def clear_history(self) -> None:
        """Clear approval history."""
        self._history.clear()


# Global approval manager instance
_approval_manager: ApprovalManager | None = None


def get_approval_manager() -> ApprovalManager:
    """Get the global approval manager.

    Returns:
        The global ApprovalManager instance.
    """
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManager()
    return _approval_manager


def set_approval_manager(manager: ApprovalManager) -> None:
    """Set the global approval manager.

    Args:
        manager: The ApprovalManager to use globally.
    """
    global _approval_manager
    _approval_manager = manager


def configure_approval(
    mode: Literal["default", "plan", "auto", "yolo"] = "default",
    handler: ApprovalHandler | None = None,
    tool_registry: Any = None,
) -> ApprovalManager:
    """Configure the global approval manager.

    Args:
        mode: Approval mode string.
        handler: Optional custom handler.
        tool_registry: Optional ToolRegistry for dynamic tool discovery.

    Returns:
        The configured ApprovalManager.
    """
    manager = ApprovalManager(
        mode=ApprovalMode(mode),
        handler=handler,
        tool_registry=tool_registry,
    )
    set_approval_manager(manager)
    return manager
