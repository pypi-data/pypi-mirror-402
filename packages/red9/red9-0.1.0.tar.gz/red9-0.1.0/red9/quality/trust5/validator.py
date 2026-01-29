"""TRUST 5 Validator - Main orchestrator for quality validation.

Implements the moai-adk TRUST 5 framework:
- T (Tested): Coverage and test quality
- R (Readable): Code readability metrics
- U (Unified): Consistency and linting
- S (Secured): Security scanning
- T (Trackable): Version control practices
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from red9.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TRUST5Config:
    """Configuration for TRUST 5 validation.

    Attributes:
        enabled: Whether TRUST 5 validation is enabled.
        thresholds: Score thresholds for each dimension (0.0-1.0).
        security_rules_path: Path to AST-grep security rules.
    """

    enabled: bool = True
    thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "overall": 0.75,
            "tested": 0.75,
            "readable": 0.80,
            "unified": 0.75,
            "secured": 0.90,
            "trackable": 0.70,
        }
    )
    security_rules_path: str = ".red9/quality/rules"

    # Readable dimension settings
    max_file_lines: int = 300
    max_function_lines: int = 50
    max_function_params: int = 5
    max_cyclomatic_complexity: int = 10

    # Tested dimension settings
    min_coverage: float = 75.0

    # Unified dimension settings
    check_linting: bool = True
    check_type_hints: bool = True


@dataclass
class DimensionResult:
    """Result from a single dimension check.

    Attributes:
        name: Dimension name (tested, readable, unified, secured, trackable).
        passed: Whether this dimension passed.
        score: Score from 0.0 to 1.0.
        issues: List of issue descriptions.
        details: Additional details.
    """

    name: str
    passed: bool
    score: float
    issues: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TRUST5Result:
    """Result from TRUST 5 validation.

    Attributes:
        passed: Whether all dimensions passed thresholds.
        overall_score: Average score across all dimensions.
        dimensions: Results for each dimension.
        failed_dimensions: Names of dimensions that failed.
        blocking_issues: Critical issues that block completion.
    """

    passed: bool
    overall_score: float
    dimensions: dict[str, DimensionResult]
    failed_dimensions: list[str] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "overall_score": self.overall_score,
            "dimensions": {
                name: {
                    "name": dim.name,
                    "passed": dim.passed,
                    "score": dim.score,
                    "issues": dim.issues,
                    "details": dim.details,
                }
                for name, dim in self.dimensions.items()
            },
            "failed_dimensions": self.failed_dimensions,
            "blocking_issues": self.blocking_issues,
        }


class TRUST5Validator:
    """TRUST 5 quality framework validator.

    Validates code quality across 5 dimensions:
    - T (Tested): Coverage >= 75%, tests exist
    - R (Readable): File/function size, complexity <= 10
    - U (Unified): Linting passes, consistent patterns
    - S (Secured): No security vulnerabilities
    - T (Trackable): Good commit practices
    """

    DIMENSIONS = ["tested", "readable", "unified", "secured", "trackable"]

    def __init__(
        self,
        project_root: Path,
        config: TRUST5Config | None = None,
    ) -> None:
        """Initialize TRUST 5 validator.

        Args:
            project_root: Project root directory.
            config: Optional configuration (uses defaults if None).
        """
        self.project_root = project_root
        self.config = config or TRUST5Config()

    def validate(
        self,
        files_modified: list[str] | None = None,
        coverage_percent: float | None = None,
    ) -> TRUST5Result:
        """Run TRUST 5 validation.

        Args:
            files_modified: List of modified file paths.
            coverage_percent: Optional coverage percentage (if already computed).

        Returns:
            TRUST5Result with scores for each dimension.
        """
        if not self.config.enabled:
            return TRUST5Result(
                passed=True,
                overall_score=1.0,
                dimensions={},
                failed_dimensions=[],
                blocking_issues=[],
            )

        files = files_modified or []
        thresholds = self.config.thresholds

        # Run each dimension check
        results: dict[str, DimensionResult] = {}

        results["tested"] = self._check_tested(files, coverage_percent)
        results["readable"] = self._check_readable(files)
        results["unified"] = self._check_unified(files)
        results["secured"] = self._check_secured(files)
        results["trackable"] = self._check_trackable(files)

        # Calculate overall score
        scores = [r.score for r in results.values()]
        overall_score = sum(scores) / len(scores) if scores else 0.0

        # Determine failed dimensions
        failed_dimensions = []
        for name, result in results.items():
            threshold = thresholds.get(name, 0.75)
            if result.score < threshold:
                failed_dimensions.append(name)

        # Collect blocking issues (from secured dimension primarily)
        blocking_issues = []
        if "secured" in results:
            blocking_issues.extend(results["secured"].issues)

        # Overall pass/fail
        overall_threshold = thresholds.get("overall", 0.75)
        passed = overall_score >= overall_threshold and len(blocking_issues) == 0

        logger.info(
            f"TRUST 5 validation: passed={passed}, score={overall_score:.0%}, "
            f"failed_dimensions={failed_dimensions}"
        )

        return TRUST5Result(
            passed=passed,
            overall_score=overall_score,
            dimensions=results,
            failed_dimensions=failed_dimensions,
            blocking_issues=blocking_issues,
        )

    def _check_tested(
        self,
        files: list[str],
        coverage_percent: float | None,
    ) -> DimensionResult:
        """Check T (Tested) dimension.

        Args:
            files: Modified files.
            coverage_percent: Optional coverage percentage.

        Returns:
            DimensionResult for tested dimension.
        """
        from .tested import check_tested

        return check_tested(
            self.project_root,
            files,
            coverage_percent=coverage_percent,
            min_coverage=self.config.min_coverage,
        )

    def _check_readable(self, files: list[str]) -> DimensionResult:
        """Check R (Readable) dimension.

        Args:
            files: Modified files.

        Returns:
            DimensionResult for readable dimension.
        """
        from .readable import check_readable

        return check_readable(
            self.project_root,
            files,
            max_file_lines=self.config.max_file_lines,
            max_function_lines=self.config.max_function_lines,
            max_function_params=self.config.max_function_params,
            max_cyclomatic_complexity=self.config.max_cyclomatic_complexity,
        )

    def _check_unified(self, files: list[str]) -> DimensionResult:
        """Check U (Unified) dimension.

        Args:
            files: Modified files.

        Returns:
            DimensionResult for unified dimension.
        """
        from .unified import check_unified

        return check_unified(
            self.project_root,
            files,
            check_linting=self.config.check_linting,
            check_type_hints=self.config.check_type_hints,
        )

    def _check_secured(self, files: list[str]) -> DimensionResult:
        """Check S (Secured) dimension.

        Args:
            files: Modified files.

        Returns:
            DimensionResult for secured dimension.
        """
        from .secured import check_secured

        return check_secured(
            self.project_root,
            files,
            rules_path=self.config.security_rules_path,
        )

    def _check_trackable(self, files: list[str]) -> DimensionResult:
        """Check T (Trackable) dimension.

        Args:
            files: Modified files.

        Returns:
            DimensionResult for trackable dimension.
        """
        from .trackable import check_trackable

        return check_trackable(self.project_root, files)
