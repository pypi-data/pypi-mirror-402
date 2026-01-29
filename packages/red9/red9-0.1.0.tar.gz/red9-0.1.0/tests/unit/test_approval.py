"""Unit tests for RED9 approval system."""

from __future__ import annotations

from red9.approval import (
    ApprovalManager,
    ApprovalMode,
    ApprovalRequest,
    ApprovalStatus,
    AutoApproveHandler,
    AutoRejectHandler,
    CallbackApprovalHandler,
    OperationType,
    configure_approval,
    get_approval_manager,
    set_approval_manager,
)


class TestApprovalRequest:
    """Tests for ApprovalRequest."""

    def test_approve_request(self) -> None:
        """Test approving a request."""
        request = ApprovalRequest(
            id="test-1",
            operation_type=OperationType.FILE_WRITE,
            description="Write file: test.py",
            details={"file_path": "test.py"},
        )

        assert request.status == ApprovalStatus.PENDING
        request.approve(reason="Test approval")
        assert request.status == ApprovalStatus.APPROVED
        assert request.decided_at is not None
        assert request.decision_reason == "Test approval"

    def test_reject_request(self) -> None:
        """Test rejecting a request."""
        request = ApprovalRequest(
            id="test-2",
            operation_type=OperationType.SHELL_COMMAND,
            description="Execute: rm -rf /tmp/test",
            details={"command": "rm -rf /tmp/test"},
        )

        request.reject(reason="Too dangerous")
        assert request.status == ApprovalStatus.REJECTED
        assert request.decision_reason == "Too dangerous"

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        request = ApprovalRequest(
            id="test-3",
            operation_type=OperationType.FILE_WRITE,
            description="Write file",
            details={"path": "/tmp/test"},
            workflow_id="wf-123",
            stage_name="code",
        )
        request.approve()

        data = request.to_dict()
        assert data["id"] == "test-3"
        assert data["operation_type"] == "file_write"
        assert data["status"] == "approved"
        assert data["workflow_id"] == "wf-123"


class TestApprovalHandlers:
    """Tests for approval handlers."""

    def test_auto_approve_handler(self) -> None:
        """Test auto-approve handler."""
        handler = AutoApproveHandler()
        request = ApprovalRequest(
            id="test-1",
            operation_type=OperationType.FILE_WRITE,
            description="Test",
            details={},
        )

        status = handler.request_approval(request)
        assert status == ApprovalStatus.APPROVED
        assert request.status == ApprovalStatus.APPROVED

    def test_auto_reject_handler(self) -> None:
        """Test auto-reject handler."""
        handler = AutoRejectHandler()
        request = ApprovalRequest(
            id="test-2",
            operation_type=OperationType.SHELL_COMMAND,
            description="Test",
            details={},
        )

        status = handler.request_approval(request)
        assert status == ApprovalStatus.REJECTED
        assert request.status == ApprovalStatus.REJECTED

    def test_callback_handler_approve(self) -> None:
        """Test callback handler with approval."""
        handler = CallbackApprovalHandler(callback=lambda r: True)
        request = ApprovalRequest(
            id="test-3",
            operation_type=OperationType.FILE_WRITE,
            description="Test",
            details={},
        )

        status = handler.request_approval(request)
        assert status == ApprovalStatus.APPROVED

    def test_callback_handler_reject(self) -> None:
        """Test callback handler with rejection."""
        handler = CallbackApprovalHandler(callback=lambda r: False)
        request = ApprovalRequest(
            id="test-4",
            operation_type=OperationType.FILE_WRITE,
            description="Test",
            details={},
        )

        status = handler.request_approval(request)
        assert status == ApprovalStatus.REJECTED


class TestApprovalManager:
    """Tests for ApprovalManager."""

    def test_yolo_mode_no_approval_required(self) -> None:
        """Test YOLO mode doesn't require approval."""
        manager = ApprovalManager(mode=ApprovalMode.YOLO)

        # No operation type requires approval in YOLO mode
        assert not manager.requires_approval(OperationType.FILE_WRITE)
        assert not manager.requires_approval(OperationType.SHELL_COMMAND)
        assert not manager.requires_approval(OperationType.FILE_DELETE)

    def test_auto_mode_no_approval_required(self) -> None:
        """Test AUTO mode doesn't require approval."""
        manager = ApprovalManager(mode=ApprovalMode.AUTO)

        assert not manager.requires_approval(OperationType.FILE_WRITE)
        assert not manager.requires_approval(OperationType.SHELL_COMMAND)

    def test_default_mode_requires_approval(self) -> None:
        """Test DEFAULT mode requires approval for destructive ops."""
        manager = ApprovalManager(mode=ApprovalMode.DEFAULT)

        # Destructive operations require approval
        assert manager.requires_approval(OperationType.FILE_WRITE)
        assert manager.requires_approval(OperationType.FILE_DELETE)
        assert manager.requires_approval(OperationType.SHELL_COMMAND)
        assert manager.requires_approval(OperationType.PLAN_EXECUTION)

        # External API doesn't require approval by default
        assert not manager.requires_approval(OperationType.EXTERNAL_API)

    def test_plan_mode_before_approval(self) -> None:
        """Test PLAN mode before plan is approved."""
        manager = ApprovalManager(mode=ApprovalMode.PLAN)

        # Only plan execution needs approval before plan is approved
        assert manager.requires_approval(OperationType.PLAN_EXECUTION)
        assert not manager.requires_approval(OperationType.FILE_WRITE)
        assert not manager.requires_approval(OperationType.SHELL_COMMAND)

    def test_plan_mode_after_approval(self) -> None:
        """Test PLAN mode after plan is approved."""
        manager = ApprovalManager(mode=ApprovalMode.PLAN)
        manager.mark_plan_approved()

        # After plan approval, nothing needs approval
        assert not manager.requires_approval(OperationType.PLAN_EXECUTION)
        assert not manager.requires_approval(OperationType.FILE_WRITE)

    def test_request_approval_auto_mode(self) -> None:
        """Test requesting approval in AUTO mode."""
        manager = ApprovalManager(mode=ApprovalMode.AUTO)

        status = manager.request_approval(
            operation_type=OperationType.FILE_WRITE,
            description="Write test.py",
            details={"file_path": "test.py"},
        )

        assert status == ApprovalStatus.APPROVED
        assert len(manager.get_history()) == 1

    def test_request_approval_default_mode_with_handler(self) -> None:
        """Test requesting approval with custom handler."""
        handler = AutoRejectHandler()
        manager = ApprovalManager(mode=ApprovalMode.DEFAULT, handler=handler)

        status = manager.request_approval(
            operation_type=OperationType.FILE_WRITE,
            description="Write test.py",
            details={"file_path": "test.py"},
        )

        assert status == ApprovalStatus.REJECTED

    def test_check_tool_approval_read_only(self) -> None:
        """Test that read-only tools don't need approval."""
        manager = ApprovalManager(mode=ApprovalMode.DEFAULT)

        # Read-only tools return None for operation type
        approved, reason = manager.check_tool_approval(
            tool_name="read_file",
            params={"file_path": "test.py"},
        )

        assert approved
        assert reason is None

    def test_check_tool_approval_write_tool(self) -> None:
        """Test approval check for write tools."""
        handler = AutoApproveHandler()
        manager = ApprovalManager(mode=ApprovalMode.DEFAULT, handler=handler)

        approved, reason = manager.check_tool_approval(
            tool_name="write_file",
            params={"file_path": "test.py", "content": "test"},
        )

        assert approved
        assert reason is None

    def test_check_tool_approval_rejected(self) -> None:
        """Test rejection for write tools."""
        handler = AutoRejectHandler()
        manager = ApprovalManager(mode=ApprovalMode.DEFAULT, handler=handler)

        approved, reason = manager.check_tool_approval(
            tool_name="edit_file",
            params={"file_path": "test.py"},
        )

        assert not approved
        assert reason is not None

    def test_history_tracking(self) -> None:
        """Test that approval history is tracked."""
        manager = ApprovalManager(mode=ApprovalMode.AUTO)

        manager.request_approval(
            operation_type=OperationType.FILE_WRITE,
            description="Write 1",
            details={},
        )
        manager.request_approval(
            operation_type=OperationType.SHELL_COMMAND,
            description="Run command",
            details={},
        )

        history = manager.get_history()
        assert len(history) == 2
        assert history[0]["description"] == "Write 1"
        assert history[1]["operation_type"] == "shell_command"

    def test_clear_history(self) -> None:
        """Test clearing approval history."""
        manager = ApprovalManager(mode=ApprovalMode.AUTO)
        manager.request_approval(
            operation_type=OperationType.FILE_WRITE,
            description="Test",
            details={},
        )

        assert len(manager.get_history()) == 1
        manager.clear_history()
        assert len(manager.get_history()) == 0


class TestGlobalManager:
    """Tests for global approval manager functions."""

    def test_configure_approval(self) -> None:
        """Test configuring global approval manager."""
        manager = configure_approval(mode="auto")

        assert get_approval_manager() is manager
        assert manager.mode == ApprovalMode.AUTO

    def test_set_approval_manager(self) -> None:
        """Test setting custom approval manager."""
        custom_manager = ApprovalManager(mode=ApprovalMode.YOLO)
        set_approval_manager(custom_manager)

        assert get_approval_manager() is custom_manager
