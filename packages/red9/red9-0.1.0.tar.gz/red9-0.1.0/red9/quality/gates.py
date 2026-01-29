"""Quality gates for RED9.

Enforces quality standards using TRUST 5 framework:
- T (Tested): Coverage >= 75%, test quality
- R (Readable): File/function size, complexity
- U (Unified): Linting, type hints, consistency
- S (Secured): Security scanning via AST-grep
- T (Trackable): Commit quality, changelog
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from red9.logging import get_logger
from red9.quality.trust5 import TRUST5Config, TRUST5Validator

logger = get_logger(__name__)


@dataclass
class QualityResult:
    """Result of a quality gate check."""

    passed: bool
    score: float  # 0.0 to 1.0
    failed_dimensions: list[str] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    # Backward compatibility properties
    @property
    def overall_score(self) -> float:
        return self.score

    @property
    def dimensions(self) -> list:
        # Stub for backward compatibility if code iterates over dimensions
        # This returns pseudo-objects that have .name and .details
        return [type("Dim", (), {"name": dim, "details": ""}) for dim in self.failed_dimensions]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "score": self.score,
            "failed_dimensions": self.failed_dimensions,
            "blocking_issues": self.blocking_issues,
            "details": self.details,
        }


class QualityGate:
    """Enforces quality standards using TRUST 5 framework.

    The TRUST 5 framework validates:
    - T (Tested): Coverage >= 75%, test quality
    - R (Readable): File/function size <= 300/50 LOC, complexity <= 10
    - U (Unified): Linting passes, type hints present
    - S (Secured): No security vulnerabilities
    - T (Trackable): Good commit practices
    """

    def __init__(
        self,
        project_root: Path,
        min_coverage: float = 75.0,
        max_file_lines: int = 300,
        config: TRUST5Config | None = None,
    ) -> None:
        self.project_root = project_root
        self.min_coverage = min_coverage
        self.max_file_lines = max_file_lines

        # Create TRUST 5 config
        if config:
            self.trust5_config = config
        else:
            self.trust5_config = TRUST5Config(
                min_coverage=min_coverage,
                max_file_lines=max_file_lines,
            )

        # Initialize TRUST 5 validator
        self.validator = TRUST5Validator(project_root, self.trust5_config)

    def check(
        self,
        files_modified: list[str] | None = None,
        coverage_percent: float | None = None,
    ) -> QualityResult:
        """Run all quality checks using TRUST 5.

        Args:
            files_modified: List of files modified.
            coverage_percent: Dynamic coverage percentage determined by LLM/Agent.

        Returns:
            QualityResult indicating pass/fail and details.
        """
        # Run TRUST 5 validation
        trust5_result = self.validator.validate(
            files_modified=files_modified,
            coverage_percent=coverage_percent,
        )

        # Convert TRUST5Result to QualityResult
        return QualityResult(
            passed=trust5_result.passed,
            score=trust5_result.overall_score,
            failed_dimensions=trust5_result.failed_dimensions,
            blocking_issues=trust5_result.blocking_issues,
            details=trust5_result.to_dict(),
        )

    def check_legacy(
        self,
        files_modified: list[str] | None = None,
        coverage_percent: float | None = None,
    ) -> QualityResult:
        """Legacy quality check (for backward compatibility).

        Args:
            files_modified: List of files modified.
            coverage_percent: Dynamic coverage percentage.

        Returns:
            QualityResult.
        """
        blocking_issues = []
        failed_dimensions = []
        total_score = 1.0

        # 1. Check File Size (Maintainability)
        size_passed, size_issues = self._check_file_sizes(files_modified)
        if not size_passed:
            blocking_issues.extend(size_issues)
            failed_dimensions.append("maintainability")
            total_score -= 0.2

        # 2. Check Coverage (Reliability)
        coverage_score = coverage_percent if coverage_percent is not None else 0.0

        if coverage_percent is not None:
            if coverage_percent < self.min_coverage:
                failed_dimensions.append("coverage")
                total_score -= 0.3
                blocking_issues.append(f"Coverage {coverage_score:.1f}% < {self.min_coverage}%")

        # Determine final pass/fail
        passed = len(blocking_issues) == 0 and total_score >= 0.7

        return QualityResult(
            passed=passed,
            score=max(0.0, total_score),
            failed_dimensions=failed_dimensions,
            blocking_issues=blocking_issues,
            details={
                "coverage_score": coverage_score,
                "size_issues": size_issues,
            },
        )

    def _check_file_sizes(self, files: list[str] | None) -> tuple[bool, list[str]]:
        """Check if any files exceed size limits."""
        issues = []
        files_to_check = []

        if files:
            for f in files:
                path = self.project_root / f
                if path.exists() and path.is_file():
                    files_to_check.append(path)

        for path in files_to_check:
            try:
                line_count = sum(1 for _ in path.open())
                if line_count > self.max_file_lines:
                    issues.append(
                        f"File {path.name} is too large "
                        f"({line_count} > {self.max_file_lines} lines)"
                    )
            except Exception:
                pass

        return len(issues) == 0, issues


def check_quality_gates(
    project_root: Path,
    files_modified: list[str] | None = None,
    review_issues: list[dict[str, Any]] | None = None,
    coverage_percent: float | None = None,
    config: TRUST5Config | None = None,
) -> QualityResult:
    """Run quality gates using TRUST 5 framework.

    The TRUST 5 framework validates code across 5 dimensions:
    - T (Tested): Coverage >= 75%, tests exist
    - R (Readable): File/function size, complexity <= 10
    - U (Unified): Linting passes, consistent patterns
    - S (Secured): No security vulnerabilities
    - T (Trackable): Good commit practices

    Args:
        project_root: Project root path.
        files_modified: List of modified files.
        review_issues: List of issues found by reviewer (optional).
        coverage_percent: Dynamic coverage percentage (optional).
        config: Optional TRUST5Config for customization.

    Returns:
        QualityResult with TRUST 5 scores.
    """
    gate = QualityGate(project_root, config=config)
    result = gate.check(files_modified, coverage_percent=coverage_percent)

    # If there are blocking review issues (critical/high), ensure result reflects failure
    if review_issues:
        has_blocking, issues = has_blocking_issues(review_issues)
        if has_blocking:
            result.passed = False
            result.blocking_issues.extend([i.get("description", "Critical issue") for i in issues])

    return result


def has_blocking_issues(issues: list[dict[str, Any]] | None) -> tuple[bool, list[dict[str, Any]]]:
    """Check if there are blocking (critical/high) issues.

    Args:
        issues: List of issues.

    Returns:
        Tuple of (has_blocking, blocking_issues_list).
    """
    if not issues:
        return False, []

    blocking = [
        i
        for i in issues
        if i.get("severity") in ("critical", "high") or i.get("confidence", 0) >= 90
    ]
    return len(blocking) > 0, blocking
