"""Structured logging for RED9.

Provides JSON-formatted logging with correlation IDs for tracing
agent executions and workflow stages.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Context variable for correlation ID (thread-safe)
_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)
_workflow_id: ContextVar[str | None] = ContextVar("workflow_id", default=None)
_stage_id: ContextVar[str | None] = ContextVar("stage_id", default=None)


def get_correlation_id() -> str | None:
    """Get current correlation ID."""
    return _correlation_id.get()


def set_correlation_id(cid: str | None) -> None:
    """Set correlation ID for current context."""
    _correlation_id.set(cid)


def new_correlation_id() -> str:
    """Generate and set a new correlation ID."""
    cid = str(uuid.uuid4())[:8]
    _correlation_id.set(cid)
    return cid


def set_workflow_context(workflow_id: str | None, stage_id: str | None = None) -> None:
    """Set workflow context for logging."""
    _workflow_id.set(workflow_id)
    _stage_id.set(stage_id)


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context IDs if available
        if cid := _correlation_id.get():
            log_data["correlation_id"] = cid
        if wid := _workflow_id.get():
            log_data["workflow_id"] = wid
        if sid := _stage_id.get():
            log_data["stage_id"] = sid

        # Add source location
        log_data["source"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "asctime",
            ):
                continue
            log_data[key] = value

        return json.dumps(log_data, default=str)


class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter with colors."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console."""
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET if color else ""

        # Build prefix with context
        parts = []
        if cid := _correlation_id.get():
            parts.append(f"[{cid}]")
        if wid := _workflow_id.get():
            parts.append(f"wf:{wid[:8]}")

        prefix = " ".join(parts)
        if prefix:
            prefix = f"{prefix} "

        timestamp = datetime.now().strftime("%H:%M:%S")
        level = record.levelname[0]  # First letter only

        msg = f"{timestamp} {color}{level}{reset} {prefix}{record.name}: {record.getMessage()}"

        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)

        return msg


def configure_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: str | None = None,
) -> None:
    """Configure RED9 logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON format for console output
        log_file: Optional file path for JSON logs
    """
    # Configure root logger to capture everything (including stabilize)
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ConsoleFormatter())
    root_logger.addHandler(console_handler)

    # File handler (always JSON)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    # Set level for noisy third-party loggers
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    # Ensure stabilize logs are visible but not debug noise unless requested
    logging.getLogger("stabilize").setLevel(getattr(logging, level.upper(), logging.INFO))


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    if not name.startswith("red9"):
        name = f"red9.{name}"
    return logging.getLogger(name)


class LogContext:
    """Context manager for setting log context."""

    def __init__(
        self,
        correlation_id: str | None = None,
        workflow_id: str | None = None,
        stage_id: str | None = None,
    ):
        self.correlation_id = correlation_id
        self.workflow_id = workflow_id
        self.stage_id = stage_id
        self._old_cid: str | None = None
        self._old_wid: str | None = None
        self._old_sid: str | None = None

    def __enter__(self) -> LogContext:
        self._old_cid = _correlation_id.get()
        self._old_wid = _workflow_id.get()
        self._old_sid = _stage_id.get()

        if self.correlation_id:
            _correlation_id.set(self.correlation_id)
        if self.workflow_id:
            _workflow_id.set(self.workflow_id)
        if self.stage_id:
            _stage_id.set(self.stage_id)

        return self

    def __exit__(self, *args: Any) -> None:
        _correlation_id.set(self._old_cid)
        _workflow_id.set(self._old_wid)
        _stage_id.set(self._old_sid)


# Convenience functions for structured logging
def log_tool_call(
    logger: logging.Logger,
    tool_name: str,
    params: dict[str, Any],
    result: Any = None,
    error: str | None = None,
    duration_ms: float | None = None,
) -> None:
    """Log a tool call with structured data."""
    extra = {
        "event": "tool_call",
        "tool": tool_name,
        "params": params,
    }
    if result is not None:
        extra["result"] = result
    if error:
        extra["error"] = error
    if duration_ms is not None:
        extra["duration_ms"] = duration_ms

    if error:
        # Use debug level - errors are shown in UI via tool_end event
        logger.debug(f"Tool {tool_name} failed: {error}", extra=extra)
    else:
        logger.debug(f"Tool {tool_name} executed", extra=extra)


def log_llm_call(
    logger: logging.Logger,
    provider: str,
    model: str,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    duration_ms: float | None = None,
    error: str | None = None,
) -> None:
    """Log an LLM API call with structured data."""
    extra = {
        "event": "llm_call",
        "provider": provider,
        "model": model,
    }
    if input_tokens is not None:
        extra["input_tokens"] = input_tokens
    if output_tokens is not None:
        extra["output_tokens"] = output_tokens
    if duration_ms is not None:
        extra["duration_ms"] = duration_ms
    if error:
        extra["error"] = error

    if error:
        logger.error(f"LLM call to {provider}/{model} failed: {error}", extra=extra)
    else:
        logger.info(f"LLM call to {provider}/{model}", extra=extra)


def log_workflow_event(
    logger: logging.Logger,
    event: str,
    workflow_id: str,
    stage_id: str | None = None,
    **kwargs: Any,
) -> None:
    """Log a workflow event."""
    extra = {
        "event": f"workflow_{event}",
        "workflow_id": workflow_id,
        **kwargs,
    }
    if stage_id:
        extra["stage_id"] = stage_id

    logger.info(f"Workflow {event}: {workflow_id}", extra=extra)
