"""Unit tests for RED9 audit trail system."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from red9.audit import (
    AuditEvent,
    AuditEventType,
    AuditStore,
    AuditTrail,
    configure_audit,
    get_audit_trail,
    set_audit_trail,
)


class TestAuditEvent:
    """Tests for AuditEvent."""

    def test_create_event(self) -> None:
        """Test creating an audit event."""
        event = AuditEvent(
            event_type=AuditEventType.TOOL_CALL,
            timestamp=datetime.now(UTC),
            tool_name="read_file",
            parameters={"file_path": "/test.py"},
        )

        assert event.event_type == AuditEventType.TOOL_CALL
        assert event.tool_name == "read_file"
        assert event.success is True

    def test_to_dict(self) -> None:
        """Test event serialization."""
        now = datetime.now(UTC)
        event = AuditEvent(
            event_type=AuditEventType.TOOL_RESULT,
            timestamp=now,
            workflow_id="wf-123",
            tool_name="write_file",
            success=True,
            duration_ms=150.5,
        )

        data = event.to_dict()
        assert data["event_type"] == "tool_result"
        assert data["workflow_id"] == "wf-123"
        assert data["duration_ms"] == 150.5

    def test_from_dict(self) -> None:
        """Test event deserialization."""
        data = {
            "event_type": "tool_call",
            "timestamp": "2026-01-17T10:00:00+00:00",
            "tool_name": "shell",
            "parameters": {"command": "pytest"},
            "success": True,
        }

        event = AuditEvent.from_dict(data)
        assert event.event_type == AuditEventType.TOOL_CALL
        assert event.tool_name == "shell"


class TestAuditStore:
    """Tests for AuditStore."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> AuditStore:
        """Create a temporary audit store."""
        return AuditStore(tmp_path / "audit.db")

    def test_store_and_query(self, store: AuditStore) -> None:
        """Test storing and querying events."""
        event = AuditEvent(
            event_type=AuditEventType.TOOL_CALL,
            timestamp=datetime.now(UTC),
            workflow_id="wf-test",
            tool_name="read_file",
            parameters={"file_path": "/test.py"},
        )

        event_id = store.store(event)
        assert event_id > 0

        events = store.query(workflow_id="wf-test")
        assert len(events) == 1
        assert events[0].tool_name == "read_file"

    def test_query_by_event_type(self, store: AuditStore) -> None:
        """Test querying by event type."""
        store.store(
            AuditEvent(
                event_type=AuditEventType.TOOL_CALL,
                timestamp=datetime.now(UTC),
                tool_name="read_file",
            )
        )
        store.store(
            AuditEvent(
                event_type=AuditEventType.ERROR,
                timestamp=datetime.now(UTC),
                error="Test error",
            )
        )

        tool_calls = store.query(event_type=AuditEventType.TOOL_CALL)
        assert len(tool_calls) == 1
        assert tool_calls[0].tool_name == "read_file"

        errors = store.query(event_type=AuditEventType.ERROR)
        assert len(errors) == 1
        assert errors[0].error == "Test error"

    def test_get_workflow_events(self, store: AuditStore) -> None:
        """Test getting all events for a workflow."""
        for i in range(5):
            store.store(
                AuditEvent(
                    event_type=AuditEventType.TOOL_CALL,
                    timestamp=datetime.now(UTC),
                    workflow_id="wf-1",
                    tool_name=f"tool_{i}",
                )
            )
        store.store(
            AuditEvent(
                event_type=AuditEventType.TOOL_CALL,
                timestamp=datetime.now(UTC),
                workflow_id="wf-2",
                tool_name="other",
            )
        )

        events = store.get_workflow_events("wf-1")
        assert len(events) == 5

    def test_get_tool_stats(self, store: AuditStore) -> None:
        """Test getting tool statistics."""
        for i in range(3):
            store.store(
                AuditEvent(
                    event_type=AuditEventType.TOOL_CALL,
                    timestamp=datetime.now(UTC),
                    tool_name="read_file",
                    success=True,
                    duration_ms=100.0,
                )
            )
        store.store(
            AuditEvent(
                event_type=AuditEventType.TOOL_CALL,
                timestamp=datetime.now(UTC),
                tool_name="read_file",
                success=False,
                duration_ms=50.0,
            )
        )

        stats = store.get_tool_stats()
        assert "read_file" in stats
        assert stats["read_file"]["total_calls"] == 4
        assert stats["read_file"]["successful_calls"] == 3
        assert stats["read_file"]["failed_calls"] == 1


class TestAuditTrail:
    """Tests for AuditTrail."""

    @pytest.fixture
    def trail(self, tmp_path: Path) -> AuditTrail:
        """Create a temporary audit trail."""
        return AuditTrail(db_path=tmp_path / "audit.db", enabled=True)

    def test_disabled_trail(self) -> None:
        """Test that disabled trail doesn't log."""
        trail = AuditTrail(enabled=False)

        event = trail.log_tool_call(
            tool_name="test",
            parameters={},
        )

        assert event is None

    def test_log_tool_call(self, trail: AuditTrail) -> None:
        """Test logging tool calls."""
        event = trail.log_tool_call(
            tool_name="read_file",
            parameters={"file_path": "/test.py"},
            workflow_id="wf-123",
        )

        assert event is not None
        assert event.event_type == AuditEventType.TOOL_CALL
        assert event.tool_name == "read_file"

    def test_log_tool_result(self, trail: AuditTrail) -> None:
        """Test logging tool results."""
        event = trail.log_tool_result(
            tool_name="write_file",
            success=True,
            result={"bytes_written": 100},
            duration_ms=150.0,
        )

        assert event is not None
        assert event.success is True
        assert event.duration_ms == 150.0

    def test_log_workflow_events(self, trail: AuditTrail) -> None:
        """Test logging workflow start and end."""
        start = trail.log_workflow_start(
            workflow_id="wf-test",
            request="Fix the bug",
        )
        end = trail.log_workflow_end(
            workflow_id="wf-test",
            success=True,
            duration_ms=5000.0,
        )

        assert start is not None
        assert end is not None
        assert start.event_type == AuditEventType.WORKFLOW_START
        assert end.event_type == AuditEventType.WORKFLOW_END

    def test_log_file_modified(self, trail: AuditTrail) -> None:
        """Test logging file modifications."""
        event = trail.log_file_modified(
            file_path="/src/main.py",
            tool_name="edit_file",
            workflow_id="wf-123",
        )

        assert event is not None
        assert event.event_type == AuditEventType.FILE_MODIFIED
        assert event.parameters["file_path"] == "/src/main.py"

    def test_log_error(self, trail: AuditTrail) -> None:
        """Test logging errors."""
        event = trail.log_error(
            error="Connection refused",
            context={"host": "localhost"},
            workflow_id="wf-123",
        )

        assert event is not None
        assert event.event_type == AuditEventType.ERROR
        assert event.success is False

    def test_sanitize_params(self, trail: AuditTrail) -> None:
        """Test parameter sanitization."""
        event = trail.log_tool_call(
            tool_name="api_call",
            parameters={
                "url": "https://api.example.com",
                "api_key": "secret123",
                "password": "hunter2",
                "config": {"timeout": 30},
            },
        )

        assert event is not None
        params = event.parameters
        assert params["url"] == "https://api.example.com"
        assert params["api_key"] == "[REDACTED]"
        assert params["password"] == "[REDACTED]"
        # Non-sensitive nested dict is preserved
        assert params["config"]["timeout"] == 30


class TestGlobalAuditTrail:
    """Tests for global audit trail functions."""

    def test_configure_audit(self, tmp_path: Path) -> None:
        """Test configuring global audit trail."""
        trail = configure_audit(
            db_path=tmp_path / "audit.db",
            enabled=True,
        )

        assert get_audit_trail() is trail
        assert trail.enabled is True

    def test_set_audit_trail(self) -> None:
        """Test setting custom audit trail."""
        custom = AuditTrail(enabled=False)
        set_audit_trail(custom)

        assert get_audit_trail() is custom
