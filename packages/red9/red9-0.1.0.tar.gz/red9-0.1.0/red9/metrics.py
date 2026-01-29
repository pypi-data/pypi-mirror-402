"""Metrics collection system for RED9.

Provides performance, cost, and usage tracking for workflows and LLM calls.
"""

from __future__ import annotations

import json
import sqlite3
import time
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from red9.logging import get_logger

logger = get_logger(__name__)


class MetricType(str, Enum):
    """Types of metrics."""

    TIMER = "timer"  # Duration measurements
    COUNTER = "counter"  # Increment/decrement counts
    GAUGE = "gauge"  # Point-in-time values
    HISTOGRAM = "histogram"  # Distribution of values


@dataclass
class MetricValue:
    """A recorded metric value."""

    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    tags: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
        }


@dataclass
class LLMUsage:
    """LLM usage statistics."""

    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    requests: int = 0
    errors: int = 0
    total_duration_ms: float = 0.0
    estimated_cost_usd: float = 0.0

    def add_request(
        self,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
        success: bool = True,
        cost_usd: float = 0.0,
    ) -> None:
        """Record an LLM request."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += input_tokens + output_tokens
        self.requests += 1
        if not success:
            self.errors += 1
        self.total_duration_ms += duration_ms
        self.estimated_cost_usd += cost_usd

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "requests": self.requests,
            "errors": self.errors,
            "error_rate": self.errors / self.requests if self.requests > 0 else 0,
            "total_duration_ms": self.total_duration_ms,
            "avg_duration_ms": self.total_duration_ms / self.requests if self.requests > 0 else 0,
            "estimated_cost_usd": self.estimated_cost_usd,
        }


@dataclass
class WorkflowMetrics:
    """Metrics for a single workflow."""

    workflow_id: str
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None
    stages_completed: int = 0
    stages_failed: int = 0
    tool_calls: int = 0
    files_modified: int = 0
    llm_usage: dict[str, LLMUsage] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float | None:
        """Get workflow duration in milliseconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds() * 1000

    @property
    def success(self) -> bool:
        """Check if workflow completed successfully."""
        return self.end_time is not None and self.stages_failed == 0

    def record_llm_call(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
        success: bool = True,
        cost_usd: float = 0.0,
    ) -> None:
        """Record an LLM call."""
        key = f"{provider}:{model}"
        if key not in self.llm_usage:
            self.llm_usage[key] = LLMUsage(provider=provider, model=model)
        self.llm_usage[key].add_request(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            success=success,
            cost_usd=cost_usd,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "stages_completed": self.stages_completed,
            "stages_failed": self.stages_failed,
            "tool_calls": self.tool_calls,
            "files_modified": self.files_modified,
            "llm_usage": {k: v.to_dict() for k, v in self.llm_usage.items()},
        }


class MetricsStore:
    """SQLite-based metrics storage."""

    def __init__(self, db_path: str | Path) -> None:
        """Initialize metrics store.

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
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    tags TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL UNIQUE,
                    data TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_name
                ON metrics(name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
                ON metrics(timestamp)
            """)
            conn.commit()

    def record(self, metric: MetricValue) -> None:
        """Record a metric value.

        Args:
            metric: The metric to record.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO metrics (name, metric_type, value, timestamp, tags)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    metric.name,
                    metric.metric_type.value,
                    metric.value,
                    metric.timestamp.isoformat(),
                    json.dumps(metric.tags),
                ),
            )
            conn.commit()

    def record_workflow(self, metrics: WorkflowMetrics) -> None:
        """Record workflow metrics.

        Args:
            metrics: The workflow metrics to record.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO workflow_metrics
                (workflow_id, data, updated_at)
                VALUES (?, ?, ?)
                """,
                (
                    metrics.workflow_id,
                    json.dumps(metrics.to_dict(), default=str),
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.commit()

    def get_workflow(self, workflow_id: str) -> WorkflowMetrics | None:
        """Get workflow metrics.

        Args:
            workflow_id: The workflow ID.

        Returns:
            WorkflowMetrics or None if not found.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM workflow_metrics WHERE workflow_id = ?",
                (workflow_id,),
            )
            row = cursor.fetchone()
            if row:
                data = json.loads(row[0])
                metrics = WorkflowMetrics(
                    workflow_id=data["workflow_id"],
                    start_time=datetime.fromisoformat(data["start_time"]),
                    end_time=datetime.fromisoformat(data["end_time"]) if data["end_time"] else None,
                    stages_completed=data["stages_completed"],
                    stages_failed=data["stages_failed"],
                    tool_calls=data["tool_calls"],
                    files_modified=data["files_modified"],
                )
                return metrics
            return None

    def query(
        self,
        name: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 1000,
    ) -> list[MetricValue]:
        """Query metrics.

        Args:
            name: Filter by metric name.
            since: Filter metrics after this timestamp.
            until: Filter metrics before this timestamp.
            limit: Maximum number of metrics to return.

        Returns:
            List of matching metrics.
        """
        conditions = []
        params: list[Any] = []

        if name:
            conditions.append("name = ?")
            params.append(name)
        if since:
            conditions.append("timestamp >= ?")
            params.append(since.isoformat())
        if until:
            conditions.append("timestamp <= ?")
            params.append(until.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT name, metric_type, value, timestamp, tags
                FROM metrics
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                params,
            )
            metrics = []
            for row in cursor.fetchall():
                metrics.append(
                    MetricValue(
                        name=row[0],
                        metric_type=MetricType(row[1]),
                        value=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        tags=json.loads(row[4]) if row[4] else {},
                    )
                )
            return metrics

    def get_summary(
        self,
        name: str,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Get summary statistics for a metric.

        Args:
            name: Metric name.
            since: Only include metrics after this timestamp.

        Returns:
            Summary with count, sum, avg, min, max.
        """
        since_clause = ""
        params: list[Any] = [name]
        if since:
            since_clause = "AND timestamp >= ?"
            params.append(since.isoformat())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT
                    COUNT(*) as count,
                    SUM(value) as sum,
                    AVG(value) as avg,
                    MIN(value) as min,
                    MAX(value) as max
                FROM metrics
                WHERE name = ? {since_clause}
                """,
                params,
            )
            row = cursor.fetchone()
            return {
                "name": name,
                "count": row[0],
                "sum": row[1],
                "avg": row[2],
                "min": row[3],
                "max": row[4],
            }


class MetricsCollector:
    """High-level metrics collection interface."""

    def __init__(
        self,
        store: MetricsStore | None = None,
        db_path: str | Path | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize metrics collector.

        Args:
            store: Optional MetricsStore instance.
            db_path: Path to database (used if store not provided).
            enabled: Whether metrics collection is enabled.
        """
        self.enabled = enabled
        self._store = store
        self._in_memory_counters: dict[str, float] = defaultdict(float)
        self._active_workflows: dict[str, WorkflowMetrics] = {}

        if store is None and db_path:
            self._store = MetricsStore(db_path)

    @property
    def store(self) -> MetricsStore | None:
        """Get the metrics store."""
        return self._store

    def increment(
        self,
        name: str,
        value: float = 1.0,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Increment a counter.

        Args:
            name: Counter name.
            value: Amount to increment.
            tags: Optional tags.
        """
        self._in_memory_counters[name] += value

        if self.enabled and self._store:
            metric = MetricValue(
                name=name,
                metric_type=MetricType.COUNTER,
                value=value,
                tags=tags or {},
            )
            self._store.record(metric)

    def gauge(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Record a gauge value.

        Args:
            name: Gauge name.
            value: Current value.
            tags: Optional tags.
        """
        if self.enabled and self._store:
            metric = MetricValue(
                name=name,
                metric_type=MetricType.GAUGE,
                value=value,
                tags=tags or {},
            )
            self._store.record(metric)

    def timing(
        self,
        name: str,
        duration_ms: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Record a timing measurement.

        Args:
            name: Timer name.
            duration_ms: Duration in milliseconds.
            tags: Optional tags.
        """
        if self.enabled and self._store:
            metric = MetricValue(
                name=name,
                metric_type=MetricType.TIMER,
                value=duration_ms,
                tags=tags or {},
            )
            self._store.record(metric)

    @contextmanager
    def timer(
        self,
        name: str,
        tags: dict[str, str] | None = None,
    ) -> Iterator[None]:
        """Context manager for timing operations.

        Args:
            name: Timer name.
            tags: Optional tags.

        Yields:
            None
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self.timing(name, duration_ms, tags)

    def start_workflow(self, workflow_id: str) -> WorkflowMetrics:
        """Start tracking a workflow.

        Args:
            workflow_id: The workflow ID.

        Returns:
            WorkflowMetrics for the workflow.
        """
        metrics = WorkflowMetrics(workflow_id=workflow_id)
        self._active_workflows[workflow_id] = metrics
        logger.debug(f"Started tracking workflow {workflow_id}")
        return metrics

    def end_workflow(
        self,
        workflow_id: str,
        success: bool = True,
    ) -> WorkflowMetrics | None:
        """End workflow tracking.

        Args:
            workflow_id: The workflow ID.
            success: Whether the workflow succeeded.

        Returns:
            The workflow metrics or None if not found.
        """
        metrics = self._active_workflows.pop(workflow_id, None)
        if metrics:
            metrics.end_time = datetime.now(UTC)
            if not success:
                metrics.stages_failed += 1

            if self.enabled and self._store:
                self._store.record_workflow(metrics)
                # Also record summary metrics
                self.timing(
                    "workflow.duration",
                    metrics.duration_ms or 0,
                    {"workflow_id": workflow_id},
                )
                self.increment(
                    "workflow.completed" if success else "workflow.failed",
                    tags={"workflow_id": workflow_id},
                )

            logger.debug(f"Ended tracking workflow {workflow_id}")
        return metrics

    def record_tool_call(
        self,
        workflow_id: str | None,
        tool_name: str,
        duration_ms: float,
        success: bool = True,
    ) -> None:
        """Record a tool call.

        Args:
            workflow_id: Optional workflow ID.
            tool_name: Name of the tool.
            duration_ms: Duration in milliseconds.
            success: Whether the call succeeded.
        """
        if workflow_id and workflow_id in self._active_workflows:
            self._active_workflows[workflow_id].tool_calls += 1

        self.timing(
            f"tool.{tool_name}.duration",
            duration_ms,
            {"success": str(success)},
        )
        self.increment(
            f"tool.{tool_name}.calls" if success else f"tool.{tool_name}.errors",
        )

    def record_llm_call(
        self,
        workflow_id: str | None,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
        success: bool = True,
        cost_usd: float = 0.0,
    ) -> None:
        """Record an LLM call.

        Args:
            workflow_id: Optional workflow ID.
            provider: LLM provider name.
            model: Model name.
            input_tokens: Input token count.
            output_tokens: Output token count.
            duration_ms: Duration in milliseconds.
            success: Whether the call succeeded.
            cost_usd: Estimated cost in USD.
        """
        if workflow_id and workflow_id in self._active_workflows:
            self._active_workflows[workflow_id].record_llm_call(
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
                success=success,
                cost_usd=cost_usd,
            )

        self.timing(
            f"llm.{provider}.duration",
            duration_ms,
            {"model": model, "success": str(success)},
        )
        self.increment(f"llm.{provider}.input_tokens", input_tokens)
        self.increment(f"llm.{provider}.output_tokens", output_tokens)
        if cost_usd > 0:
            self.increment(f"llm.{provider}.cost_usd", cost_usd)

    def record_file_modified(
        self,
        workflow_id: str | None,
        file_path: str,
    ) -> None:
        """Record a file modification.

        Args:
            workflow_id: Optional workflow ID.
            file_path: Path to the modified file.
        """
        if workflow_id and workflow_id in self._active_workflows:
            self._active_workflows[workflow_id].files_modified += 1

        self.increment("files.modified")

    def get_counter(self, name: str) -> float:
        """Get in-memory counter value.

        Args:
            name: Counter name.

        Returns:
            Current counter value.
        """
        return self._in_memory_counters.get(name, 0.0)

    def get_summary(self, name: str, since: datetime | None = None) -> dict[str, Any]:
        """Get metric summary.

        Args:
            name: Metric name.
            since: Only include metrics after this timestamp.

        Returns:
            Summary statistics.
        """
        if self._store:
            return self._store.get_summary(name, since)
        return {"name": name, "count": 0}


# Global metrics collector instance
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector.

    Returns:
        The global MetricsCollector instance.
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(enabled=False)
    return _metrics_collector


def set_metrics_collector(collector: MetricsCollector) -> None:
    """Set the global metrics collector.

    Args:
        collector: The MetricsCollector to use globally.
    """
    global _metrics_collector
    _metrics_collector = collector


def configure_metrics(
    db_path: str | Path | None = None,
    enabled: bool = True,
) -> MetricsCollector:
    """Configure the global metrics collector.

    Args:
        db_path: Path to database file.
        enabled: Whether metrics collection is enabled.

    Returns:
        The configured MetricsCollector.
    """
    collector = MetricsCollector(db_path=db_path, enabled=enabled)
    set_metrics_collector(collector)
    return collector
