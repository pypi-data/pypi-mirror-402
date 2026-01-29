"""Validation aggregation for RED9.

Combines multiple validation layers:
1. Path validation (exists, allowed)
2. Syntax validation (ast.parse)
3. Quality gates (coverage, size)
4. Behavior preservation (regressions)
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from red9.logging import get_logger
from red9.quality.gates import QualityGate, QualityResult

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Combined validation result."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    quality: QualityResult | None = None

    def merge(self, other: ValidationResult) -> None:
        """Merge another result into this one."""
        self.valid = self.valid and other.valid
        self.errors.extend(other.errors)
        if other.quality:
            self.quality = other.quality


class Validator:
    """Aggregates validation checks."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.quality_gate = QualityGate(project_root)

    def validate_file_content(self, path: str, content: str) -> ValidationResult:
        """Validate content for a specific file (syntax check)."""
        errors = []
        valid = True

        # Syntax Check (Python)
        if path.endswith(".py"):
            try:
                ast.parse(content)
            except SyntaxError as e:
                valid = False
                errors.append(f"SyntaxError in {path}: {e}")

        return ValidationResult(valid=valid, errors=errors)

    def validate_change_set(self, files: list[str]) -> ValidationResult:
        """Validate a set of changes against quality gates."""
        quality_result = self.quality_gate.check(files)

        valid = quality_result.passed
        errors = quality_result.blocking_issues

        return ValidationResult(
            valid=valid,
            errors=errors,
            quality=quality_result,
        )
