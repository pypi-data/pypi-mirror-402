"""Audit trail system for RED9 operations.

Provides comprehensive logging of all agent actions for compliance and debugging.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from red9.logging import get_logger

logger = get_logger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events."""

    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"
    STAGE_START = "stage_start"
    STAGE_END = "stage_end"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_DECISION = "approval_decision"
    ERROR = "error"
    FILE_MODIFIED = "file_modified"


@dataclass
class AuditEvent:
    """An audit event record."""

    event_type: AuditEventType
    timestamp: datetime
    workflow_id: str | None = None
    stage_name: str | None = None
    tool_name: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None
    duration_ms: float | None = None
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "workflow_id": self.workflow_id,
            "stage_name": self.stage_name,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "result": self.result,
            "success": self.success,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEvent:
        """Create from dictionary."""
        return cls(
            event_type=AuditEventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            workflow_id=data.get("workflow_id"),
            stage_name=data.get("stage_name"),
            tool_name=data.get("tool_name"),
            parameters=data.get("parameters", {}),
            result=data.get("result", {}),
            success=data.get("success", True),
            error=data.get("error"),
            duration_ms=data.get("duration_ms"),
            correlation_id=data.get("correlation_id"),
        )


class AuditStore:
    """SQLite-based audit event storage."""

    def __init__(self, db_path: str | Path) -> None:
        """Initialize audit store.

        Args:
            db_path: Path to SQLite database.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    workflow_id TEXT,
                    stage_name TEXT,
                    tool_name TEXT,
                    parameters TEXT,
                    result TEXT,
                    success INTEGER NOT NULL DEFAULT 1,
                    error TEXT,
                    duration_ms REAL,
                    correlation_id TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_workflow
                ON audit_events(workflow_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_type
                ON audit_events(event_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_events(timestamp)
            """)
            conn.commit()

    def store(self, event: AuditEvent) -> int:
        """Store an audit event.

        Args:
            event: The audit event to store.

        Returns:
            The event ID.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO audit_events
                (event_type, timestamp, workflow_id, stage_name, tool_name,
                 parameters, result, success, error, duration_ms, correlation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_type.value,
                    event.timestamp.isoformat(),
                    event.workflow_id,
                    event.stage_name,
                    event.tool_name,
                    json.dumps(event.parameters, default=str),
                    json.dumps(event.result, default=str),
                    1 if event.success else 0,
                    event.error,
                    event.duration_ms,
                    event.correlation_id,
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def query(
        self,
        workflow_id: str | None = None,
        event_type: AuditEventType | None = None,
        tool_name: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query audit events.

        Args:
            workflow_id: Filter by workflow ID.
            event_type: Filter by event type.
            tool_name: Filter by tool name.
            since: Filter events after this timestamp.
            limit: Maximum number of events to return.

        Returns:
            List of matching audit events.
        """
        conditions = []
        params: list[Any] = []

        if workflow_id:
            conditions.append("workflow_id = ?")
            params.append(workflow_id)
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type.value)
        if tool_name:
            conditions.append("tool_name = ?")
            params.append(tool_name)
        if since:
            conditions.append("timestamp >= ?")
            params.append(since.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                f"""
                SELECT * FROM audit_events
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                params,
            )
            events = []
            for row in cursor.fetchall():
                events.append(
                    AuditEvent(
                        event_type=AuditEventType(row["event_type"]),
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        workflow_id=row["workflow_id"],
                        stage_name=row["stage_name"],
                        tool_name=row["tool_name"],
                        parameters=json.loads(row["parameters"] or "{}"),
                        result=json.loads(row["result"] or "{}"),
                        success=bool(row["success"]),
                        error=row["error"],
                        duration_ms=row["duration_ms"],
                        correlation_id=row["correlation_id"],
                    )
                )
            return events

    def get_workflow_events(self, workflow_id: str) -> list[AuditEvent]:
        """Get all events for a workflow.

        Args:
            workflow_id: The workflow ID.

        Returns:
            List of audit events for the workflow.
        """
        return self.query(workflow_id=workflow_id, limit=1000)

    def get_tool_stats(
        self,
        since: datetime | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Get tool usage statistics.

        Args:
            since: Count events after this timestamp.

        Returns:
            Dictionary of tool stats (calls, successes, avg_duration).
        """
        since_clause = ""
        params: list[Any] = []
        if since:
            since_clause = "AND timestamp >= ?"
            params.append(since.isoformat())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT
                    tool_name,
                    COUNT(*) as total_calls,
                    SUM(success) as successful_calls,
                    AVG(duration_ms) as avg_duration_ms
                FROM audit_events
                WHERE event_type = 'tool_call' AND tool_name IS NOT NULL
                {since_clause}
                GROUP BY tool_name
                """,
                params,
            )
            stats = {}
            for row in cursor.fetchall():
                tool_name = row[0]
                stats[tool_name] = {
                    "total_calls": row[1],
                    "successful_calls": row[2],
                    "failed_calls": row[1] - row[2],
                    "success_rate": row[2] / row[1] if row[1] > 0 else 0,
                    "avg_duration_ms": row[3],
                }
            return stats


class AuditTrail:
    """High-level audit trail interface."""

    def __init__(
        self,
        store: AuditStore | None = None,
        db_path: str | Path | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize audit trail.

        Args:
            store: Optional AuditStore instance.
            db_path: Path to database (used if store not provided).
            enabled: Whether audit logging is enabled.
        """
        self.enabled = enabled
        self._store = store

        if store is None and db_path:
            self._store = AuditStore(db_path)

    @property
    def store(self) -> AuditStore | None:
        """Get the audit store."""
        return self._store

    def log_tool_call(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        workflow_id: str | None = None,
        stage_name: str | None = None,
        correlation_id: str | None = None,
    ) -> AuditEvent | None:
        """Log a tool call event.

        Args:
            tool_name: Name of the tool.
            parameters: Tool parameters.
            workflow_id: Optional workflow ID.
            stage_name: Optional stage name.
            correlation_id: Optional correlation ID.

        Returns:
            The audit event if stored, None if disabled.
        """
        if not self.enabled or not self._store:
            return None

        event = AuditEvent(
            event_type=AuditEventType.TOOL_CALL,
            timestamp=datetime.now(UTC),
            workflow_id=workflow_id,
            stage_name=stage_name,
            tool_name=tool_name,
            parameters=self._sanitize_params(parameters),
            correlation_id=correlation_id,
        )
        self._store.store(event)
        logger.debug(f"Audit: tool_call {tool_name}")
        return event

    def log_tool_result(
        self,
        tool_name: str,
        success: bool,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        duration_ms: float | None = None,
        workflow_id: str | None = None,
        stage_name: str | None = None,
        correlation_id: str | None = None,
    ) -> AuditEvent | None:
        """Log a tool result event.

        Args:
            tool_name: Name of the tool.
            success: Whether the tool succeeded.
            result: Tool result output.
            error: Error message if failed.
            duration_ms: Duration in milliseconds.
            workflow_id: Optional workflow ID.
            stage_name: Optional stage name.
            correlation_id: Optional correlation ID.

        Returns:
            The audit event if stored.
        """
        if not self.enabled or not self._store:
            return None

        event = AuditEvent(
            event_type=AuditEventType.TOOL_RESULT,
            timestamp=datetime.now(UTC),
            workflow_id=workflow_id,
            stage_name=stage_name,
            tool_name=tool_name,
            result=result or {},
            success=success,
            error=error,
            duration_ms=duration_ms,
            correlation_id=correlation_id,
        )
        self._store.store(event)
        logger.debug(f"Audit: tool_result {tool_name} success={success}")
        return event

    def log_workflow_start(
        self,
        workflow_id: str,
        request: str | None = None,
        correlation_id: str | None = None,
    ) -> AuditEvent | None:
        """Log workflow start event.

        Args:
            workflow_id: The workflow ID.
            request: The original request.
            correlation_id: Optional correlation ID.

        Returns:
            The audit event if stored.
        """
        if not self.enabled or not self._store:
            return None

        event = AuditEvent(
            event_type=AuditEventType.WORKFLOW_START,
            timestamp=datetime.now(UTC),
            workflow_id=workflow_id,
            parameters={"request": request} if request else {},
            correlation_id=correlation_id,
        )
        self._store.store(event)
        logger.info(f"Audit: workflow_start {workflow_id}")
        return event

    def log_workflow_end(
        self,
        workflow_id: str,
        success: bool,
        error: str | None = None,
        duration_ms: float | None = None,
        correlation_id: str | None = None,
    ) -> AuditEvent | None:
        """Log workflow end event.

        Args:
            workflow_id: The workflow ID.
            success: Whether the workflow succeeded.
            error: Error message if failed.
            duration_ms: Total duration.
            correlation_id: Optional correlation ID.

        Returns:
            The audit event if stored.
        """
        if not self.enabled or not self._store:
            return None

        event = AuditEvent(
            event_type=AuditEventType.WORKFLOW_END,
            timestamp=datetime.now(UTC),
            workflow_id=workflow_id,
            success=success,
            error=error,
            duration_ms=duration_ms,
            correlation_id=correlation_id,
        )
        self._store.store(event)
        logger.info(f"Audit: workflow_end {workflow_id} success={success}")
        return event

    def log_file_modified(
        self,
        file_path: str,
        tool_name: str | None = None,
        workflow_id: str | None = None,
        stage_name: str | None = None,
        correlation_id: str | None = None,
    ) -> AuditEvent | None:
        """Log a file modification event.

        Args:
            file_path: Path to the modified file.
            tool_name: Tool that made the modification.
            workflow_id: Optional workflow ID.
            stage_name: Optional stage name.
            correlation_id: Optional correlation ID.

        Returns:
            The audit event if stored.
        """
        if not self.enabled or not self._store:
            return None

        event = AuditEvent(
            event_type=AuditEventType.FILE_MODIFIED,
            timestamp=datetime.now(UTC),
            workflow_id=workflow_id,
            stage_name=stage_name,
            tool_name=tool_name,
            parameters={"file_path": file_path},
            correlation_id=correlation_id,
        )
        self._store.store(event)
        logger.debug(f"Audit: file_modified {file_path}")
        return event

    def log_error(
        self,
        error: str,
        context: dict[str, Any] | None = None,
        workflow_id: str | None = None,
        stage_name: str | None = None,
        correlation_id: str | None = None,
    ) -> AuditEvent | None:
        """Log an error event.

        Args:
            error: Error message.
            context: Additional context.
            workflow_id: Optional workflow ID.
            stage_name: Optional stage name.
            correlation_id: Optional correlation ID.

        Returns:
            The audit event if stored.
        """
        if not self.enabled or not self._store:
            return None

        event = AuditEvent(
            event_type=AuditEventType.ERROR,
            timestamp=datetime.now(UTC),
            workflow_id=workflow_id,
            stage_name=stage_name,
            error=error,
            parameters=context or {},
            success=False,
            correlation_id=correlation_id,
        )
        self._store.store(event)
        logger.warning(f"Audit: error - {error}")
        return event

    def _sanitize_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Sanitize parameters for audit logging.

        Removes sensitive information like passwords and tokens.

        Args:
            params: Original parameters.

        Returns:
            Sanitized parameters.
        """
        sensitive_keys = {
            "password",
            "token",
            "secret",
            "api_key",
            "apikey",
            "auth",
            "credential",
        }
        sanitized = {}
        for key, value in params.items():
            lower_key = key.lower()
            if any(s in lower_key for s in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_params(value)
            else:
                sanitized[key] = value
        return sanitized


# Global audit trail instance
_audit_trail: AuditTrail | None = None


def get_audit_trail() -> AuditTrail:
    """Get the global audit trail.

    Returns:
        The global AuditTrail instance.
    """
    global _audit_trail
    if _audit_trail is None:
        _audit_trail = AuditTrail(enabled=False)
    return _audit_trail


def set_audit_trail(trail: AuditTrail) -> None:
    """Set the global audit trail.

    Args:
        trail: The AuditTrail to use globally.
    """
    global _audit_trail
    _audit_trail = trail


def configure_audit(
    db_path: str | Path | None = None,
    enabled: bool = True,
) -> AuditTrail:
    """Configure the global audit trail.

    Args:
        db_path: Path to database file.
        enabled: Whether audit is enabled.

    Returns:
        The configured AuditTrail.
    """
    trail = AuditTrail(db_path=db_path, enabled=enabled)
    set_audit_trail(trail)
    return trail
