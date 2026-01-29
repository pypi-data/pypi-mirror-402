"""Unit tests for RED9 metrics system."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from red9.metrics import (
    LLMUsage,
    MetricsCollector,
    MetricsStore,
    MetricType,
    MetricValue,
    WorkflowMetrics,
    configure_metrics,
    get_metrics_collector,
    set_metrics_collector,
)


class TestMetricValue:
    """Tests for MetricValue."""

    def test_create_metric(self) -> None:
        """Test creating a metric value."""
        metric = MetricValue(
            name="test.counter",
            metric_type=MetricType.COUNTER,
            value=1.0,
        )

        assert metric.name == "test.counter"
        assert metric.metric_type == MetricType.COUNTER
        assert metric.value == 1.0

    def test_to_dict(self) -> None:
        """Test metric serialization."""
        metric = MetricValue(
            name="test.timer",
            metric_type=MetricType.TIMER,
            value=150.5,
            tags={"operation": "read"},
        )

        data = metric.to_dict()
        assert data["name"] == "test.timer"
        assert data["type"] == "timer"
        assert data["value"] == 150.5
        assert data["tags"]["operation"] == "read"


class TestLLMUsage:
    """Tests for LLMUsage."""

    def test_create_usage(self) -> None:
        """Test creating LLM usage."""
        usage = LLMUsage(provider="ollama", model="llama3")
        assert usage.requests == 0
        assert usage.total_tokens == 0

    def test_add_request(self) -> None:
        """Test adding a request."""
        usage = LLMUsage(provider="ollama", model="llama3")
        usage.add_request(
            input_tokens=100,
            output_tokens=50,
            duration_ms=500.0,
            success=True,
            cost_usd=0.001,
        )

        assert usage.requests == 1
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150
        assert usage.total_duration_ms == 500.0
        assert usage.estimated_cost_usd == 0.001

    def test_add_multiple_requests(self) -> None:
        """Test adding multiple requests."""
        usage = LLMUsage(provider="ollama", model="llama3")
        for _ in range(3):
            usage.add_request(
                input_tokens=100,
                output_tokens=50,
                duration_ms=100.0,
            )

        assert usage.requests == 3
        assert usage.total_tokens == 450
        assert usage.total_duration_ms == 300.0

    def test_error_tracking(self) -> None:
        """Test error tracking."""
        usage = LLMUsage(provider="ollama", model="llama3")
        usage.add_request(100, 50, 100.0, success=True)
        usage.add_request(100, 0, 50.0, success=False)

        assert usage.requests == 2
        assert usage.errors == 1

        data = usage.to_dict()
        assert data["error_rate"] == 0.5


class TestWorkflowMetrics:
    """Tests for WorkflowMetrics."""

    def test_create_workflow_metrics(self) -> None:
        """Test creating workflow metrics."""
        metrics = WorkflowMetrics(workflow_id="wf-123")
        assert metrics.workflow_id == "wf-123"
        assert metrics.stages_completed == 0
        assert metrics.duration_ms is None

    def test_workflow_duration(self) -> None:
        """Test workflow duration calculation."""
        metrics = WorkflowMetrics(workflow_id="wf-123")
        time.sleep(0.01)  # 10ms
        metrics.end_time = datetime.now(UTC)

        assert metrics.duration_ms is not None
        assert metrics.duration_ms >= 10

    def test_record_llm_call(self) -> None:
        """Test recording LLM calls."""
        metrics = WorkflowMetrics(workflow_id="wf-123")
        metrics.record_llm_call(
            provider="ollama",
            model="llama3",
            input_tokens=100,
            output_tokens=50,
            duration_ms=200.0,
        )

        assert "ollama:llama3" in metrics.llm_usage
        assert metrics.llm_usage["ollama:llama3"].requests == 1


class TestMetricsStore:
    """Tests for MetricsStore."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> MetricsStore:
        """Create a temporary metrics store."""
        return MetricsStore(tmp_path / "metrics.db")

    def test_record_and_query(self, store: MetricsStore) -> None:
        """Test recording and querying metrics."""
        metric = MetricValue(
            name="test.counter",
            metric_type=MetricType.COUNTER,
            value=1.0,
        )
        store.record(metric)

        metrics = store.query(name="test.counter")
        assert len(metrics) == 1
        assert metrics[0].value == 1.0

    def test_record_workflow(self, store: MetricsStore) -> None:
        """Test recording workflow metrics."""
        wf_metrics = WorkflowMetrics(workflow_id="wf-test")
        wf_metrics.stages_completed = 5
        wf_metrics.end_time = datetime.now(UTC)

        store.record_workflow(wf_metrics)
        retrieved = store.get_workflow("wf-test")

        assert retrieved is not None
        assert retrieved.stages_completed == 5

    def test_get_summary(self, store: MetricsStore) -> None:
        """Test getting metric summary."""
        for i in range(5):
            store.record(
                MetricValue(
                    name="test.timer",
                    metric_type=MetricType.TIMER,
                    value=100.0 + i * 10,
                )
            )

        summary = store.get_summary("test.timer")
        assert summary["count"] == 5
        assert summary["min"] == 100.0
        assert summary["max"] == 140.0
        assert summary["avg"] == 120.0


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    @pytest.fixture
    def collector(self, tmp_path: Path) -> MetricsCollector:
        """Create a temporary metrics collector."""
        return MetricsCollector(db_path=tmp_path / "metrics.db", enabled=True)

    def test_disabled_collector(self) -> None:
        """Test that disabled collector doesn't store."""
        collector = MetricsCollector(enabled=False)
        collector.increment("test.counter")

        # In-memory counter is still updated
        assert collector.get_counter("test.counter") == 1.0
        # But no store operations
        assert collector.store is None

    def test_increment(self, collector: MetricsCollector) -> None:
        """Test incrementing counters."""
        collector.increment("test.counter")
        collector.increment("test.counter", 5)

        assert collector.get_counter("test.counter") == 6.0

    def test_timing(self, collector: MetricsCollector) -> None:
        """Test timing measurements."""
        collector.timing("test.operation", 150.5)

        metrics = collector.store.query(name="test.operation") if collector.store else []
        assert len(metrics) == 1
        assert metrics[0].value == 150.5
        assert metrics[0].metric_type == MetricType.TIMER

    def test_timer_context_manager(self, collector: MetricsCollector) -> None:
        """Test timer context manager."""
        with collector.timer("test.operation"):
            time.sleep(0.01)  # 10ms

        metrics = collector.store.query(name="test.operation") if collector.store else []
        assert len(metrics) == 1
        assert metrics[0].value >= 10  # At least 10ms

    def test_workflow_tracking(self, collector: MetricsCollector) -> None:
        """Test workflow tracking."""
        wf_metrics = collector.start_workflow("wf-123")
        wf_metrics.stages_completed = 3

        result = collector.end_workflow("wf-123", success=True)

        assert result is not None
        assert result.stages_completed == 3
        assert result.duration_ms is not None

    def test_record_tool_call(self, collector: MetricsCollector) -> None:
        """Test recording tool calls."""
        wf_metrics = collector.start_workflow("wf-123")
        collector.record_tool_call(
            workflow_id="wf-123",
            tool_name="read_file",
            duration_ms=50.0,
            success=True,
        )

        assert wf_metrics.tool_calls == 1
        assert collector.get_counter("tool.read_file.calls") == 1.0

    def test_record_llm_call(self, collector: MetricsCollector) -> None:
        """Test recording LLM calls."""
        wf_metrics = collector.start_workflow("wf-123")
        collector.record_llm_call(
            workflow_id="wf-123",
            provider="ollama",
            model="llama3",
            input_tokens=100,
            output_tokens=50,
            duration_ms=200.0,
            cost_usd=0.001,
        )

        assert "ollama:llama3" in wf_metrics.llm_usage
        assert collector.get_counter("llm.ollama.input_tokens") == 100
        assert collector.get_counter("llm.ollama.output_tokens") == 50

    def test_record_file_modified(self, collector: MetricsCollector) -> None:
        """Test recording file modifications."""
        wf_metrics = collector.start_workflow("wf-123")
        collector.record_file_modified("wf-123", "/src/main.py")

        assert wf_metrics.files_modified == 1
        assert collector.get_counter("files.modified") == 1.0


class TestGlobalMetricsCollector:
    """Tests for global metrics collector functions."""

    def test_configure_metrics(self, tmp_path: Path) -> None:
        """Test configuring global metrics collector."""
        collector = configure_metrics(
            db_path=tmp_path / "metrics.db",
            enabled=True,
        )

        assert get_metrics_collector() is collector
        assert collector.enabled is True

    def test_set_metrics_collector(self) -> None:
        """Test setting custom metrics collector."""
        custom = MetricsCollector(enabled=False)
        set_metrics_collector(custom)

        assert get_metrics_collector() is custom
