"""Telemetry system for observability."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TelemetryEvent:
    """A single telemetry event."""

    event_type: str
    timestamp: float = field(default_factory=time.time)
    properties: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self))


class TelemetryService:
    """Service to collect and store telemetry data."""

    _instance: TelemetryService | None = None

    def __init__(self, log_dir: Path | None = None) -> None:
        self.enabled = False
        self.log_file: Path | None = None

        if log_dir:
            self.enable(log_dir)

    @classmethod
    def get_instance(cls) -> TelemetryService:
        if cls._instance is None:
            cls._instance = TelemetryService()
        return cls._instance

    def enable(self, log_dir: Path) -> None:
        """Enable telemetry logging to the specified directory."""
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = log_dir / "telemetry.jsonl"
            self.enabled = True
        except Exception as e:
            logger.warning(f"Failed to enable telemetry: {e}")

    def track(self, event_type: str, **properties: Any) -> None:
        """Track an event."""
        if not self.enabled or not self.log_file:
            return

        try:
            event = TelemetryEvent(event_type=event_type, properties=properties)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception:
            # Telemetry should never crash the app
            pass

    def track_tool_usage(self, tool_name: str, success: bool, duration: float) -> None:
        self.track(
            "tool_usage",
            tool_name=tool_name,
            success=success,
            duration=duration,
        )

    def track_workflow_start(self, workflow_id: str, request_length: int) -> None:
        self.track(
            "workflow_start",
            workflow_id=workflow_id,
            request_length=request_length,
        )

    def track_workflow_end(self, workflow_id: str, status: str, duration: float) -> None:
        self.track(
            "workflow_end",
            workflow_id=workflow_id,
            status=status,
            duration=duration,
        )

    def track_llm_call(self, model: str, duration_ms: float) -> None:
        self.track(
            "llm_call",
            model=model,
            duration_ms=duration_ms,
        )


def get_telemetry() -> TelemetryService:
    return TelemetryService.get_instance()
