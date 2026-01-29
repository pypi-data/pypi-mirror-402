"""Behavior preservation for RED9.

Ensures that code changes do not break existing behavior by:
1. Snapshotting test results before changes
2. Verifying test results after changes
3. Detecting regressions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from red9.logging import get_logger
from red9.tools.base import ToolRegistry

logger = get_logger(__name__)


@dataclass
class TestSnapshot:
    """Snapshot of test execution results."""

    total: int
    passed: int
    failed: int
    errors: int
    failures: list[dict[str, Any]] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.failed == 0 and self.errors == 0


class BehaviorMonitor:
    """Monitors behavior preservation."""

    def __init__(self, project_root: Path, tool_registry: ToolRegistry) -> None:
        self.project_root = project_root
        self.tools = tool_registry
        self.baseline: TestSnapshot | None = None

    def capture_baseline(self) -> TestSnapshot:
        """Run tests and capture baseline results."""
        logger.info("Capturing behavior baseline...")
        # Use the test runner tool to get structured results
        # For now, we simulate this or rely on previous run
        # TODO: Integrate with actual test runner tool output
        return TestSnapshot(total=0, passed=0, failed=0, errors=0)

    def verify_preservation(self, current: TestSnapshot) -> bool:
        """Verify that behavior is preserved (no new regressions)."""
        if not self.baseline:
            return True  # No baseline to compare against

        # Check for regressions
        if current.failed > self.baseline.failed:
            logger.warning(
                f"Regression detected: Failures increased from {self.baseline.failed} to {current.failed}"
            )
            return False

        if current.errors > self.baseline.errors:
            logger.warning(
                f"Regression detected: Errors increased from {self.baseline.errors} to {current.errors}"
            )
            return False

        return True
