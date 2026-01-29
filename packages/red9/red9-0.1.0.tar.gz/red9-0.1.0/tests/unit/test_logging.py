"""Unit tests for RED9 logging module."""

from __future__ import annotations

import json
import logging

import pytest

from red9.logging import (
    ConsoleFormatter,
    JSONFormatter,
    LogContext,
    configure_logging,
    get_correlation_id,
    get_logger,
    log_llm_call,
    log_tool_call,
    log_workflow_event,
    new_correlation_id,
    set_correlation_id,
)


class TestCorrelationId:
    """Tests for correlation ID functionality."""

    def test_set_and_get_correlation_id(self) -> None:
        """Test setting and getting correlation ID."""
        set_correlation_id("test-123")
        assert get_correlation_id() == "test-123"

        # Clean up
        set_correlation_id(None)

    def test_new_correlation_id(self) -> None:
        """Test generating a new correlation ID."""
        cid = new_correlation_id()

        assert cid is not None
        assert len(cid) == 8
        assert get_correlation_id() == cid

        # Clean up
        set_correlation_id(None)


class TestLogContext:
    """Tests for LogContext context manager."""

    def test_log_context_sets_ids(self) -> None:
        """Test that LogContext sets context IDs."""
        with LogContext(
            correlation_id="ctx-123",
            workflow_id="wf-456",
            stage_id="stage-789",
        ):
            assert get_correlation_id() == "ctx-123"

        # Should be restored after context
        assert get_correlation_id() is None

    def test_nested_log_contexts(self) -> None:
        """Test nested LogContext."""
        set_correlation_id("outer")

        with LogContext(correlation_id="inner"):
            assert get_correlation_id() == "inner"

            with LogContext(correlation_id="innermost"):
                assert get_correlation_id() == "innermost"

            assert get_correlation_id() == "inner"

        assert get_correlation_id() == "outer"

        # Clean up
        set_correlation_id(None)


class TestJSONFormatter:
    """Tests for JSON log formatter."""

    def test_json_format_basic(self) -> None:
        """Test basic JSON formatting."""
        formatter = JSONFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data
        assert "source" in data

    def test_json_format_with_correlation_id(self) -> None:
        """Test JSON formatting includes correlation ID."""
        formatter = JSONFormatter()
        set_correlation_id("json-test-123")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["correlation_id"] == "json-test-123"

        # Clean up
        set_correlation_id(None)


class TestConsoleFormatter:
    """Tests for console log formatter."""

    def test_console_format_basic(self) -> None:
        """Test basic console formatting."""
        formatter = ConsoleFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        assert "test.logger" in output
        assert "Test message" in output


class TestLogHelpers:
    """Tests for log helper functions."""

    def test_log_tool_call(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test log_tool_call helper."""
        logger = get_logger("test_tool")

        with caplog.at_level(logging.DEBUG, logger="red9.test_tool"):
            log_tool_call(
                logger,
                tool_name="read_file",
                params={"file_path": "/test.py"},
                result=True,
                duration_ms=50.5,
            )

        assert "read_file" in caplog.text

    def test_log_tool_call_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test log_tool_call with error."""
        logger = get_logger("test_tool_error")

        with caplog.at_level(logging.DEBUG, logger="red9.test_tool_error"):
            log_tool_call(
                logger,
                tool_name="write_file",
                params={"file_path": "/test.py"},
                error="Permission denied",
            )

        assert "write_file" in caplog.text
        assert "failed" in caplog.text.lower()

    def test_log_llm_call(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test log_llm_call helper."""
        logger = get_logger("test_llm")

        with caplog.at_level(logging.INFO, logger="red9.test_llm"):
            log_llm_call(
                logger,
                provider="ollama",
                model="llama3.1:8b",
                input_tokens=100,
                output_tokens=50,
                duration_ms=1500.0,
            )

        assert "ollama" in caplog.text

    def test_log_workflow_event(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test log_workflow_event helper."""
        logger = get_logger("test_workflow")

        with caplog.at_level(logging.INFO, logger="red9.test_workflow"):
            log_workflow_event(
                logger,
                event="started",
                workflow_id="wf-12345",
            )

        assert "wf-12345" in caplog.text


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_prefixes_red9(self) -> None:
        """Test that get_logger adds red9 prefix."""
        logger = get_logger("mymodule")
        assert logger.name == "red9.mymodule"

    def test_get_logger_keeps_red9_prefix(self) -> None:
        """Test that get_logger doesn't double-prefix."""
        logger = get_logger("red9.existing")
        assert logger.name == "red9.existing"


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_default(self) -> None:
        """Test default logging configuration."""
        configure_logging(level="DEBUG")

        logger = logging.getLogger("red9")
        # getEffectiveLevel returns the actual level considering parent inheritance
        assert logger.getEffectiveLevel() == logging.DEBUG
        # Handlers are on root logger, so check root
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) >= 1

    def test_configure_json_format(self) -> None:
        """Test JSON format configuration."""
        configure_logging(level="INFO", json_format=True)

        # Handlers are on root logger, not the "red9" logger
        root_logger = logging.getLogger()
        # Check that at least one handler uses JSONFormatter
        has_json = any(isinstance(h.formatter, JSONFormatter) for h in root_logger.handlers)
        assert has_json
