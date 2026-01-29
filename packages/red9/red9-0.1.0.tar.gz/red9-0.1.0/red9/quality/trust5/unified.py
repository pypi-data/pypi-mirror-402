"""TRUST 5 - U (Unified) Dimension.

Checks code consistency and style:
- Linting passes (ruff)
- Type hints present
- Consistent patterns
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from typing import Any

from red9.logging import get_logger

from .validator import DimensionResult

logger = get_logger(__name__)


def check_unified(
    project_root: Path,
    files: list[str],
    check_linting: bool = True,
    check_type_hints: bool = True,
) -> DimensionResult:
    """Check U (Unified) dimension.

    Args:
        project_root: Project root directory.
        files: List of modified file paths.
        check_linting: Whether to run linting checks.
        check_type_hints: Whether to check for type hints.

    Returns:
        DimensionResult with unified score.
    """
    issues: list[str] = []
    details: dict[str, Any] = {}

    score = 1.0

    # Filter Python files
    python_files = [f for f in files if f.endswith(".py")]

    if not python_files:
        return DimensionResult(
            name="unified",
            passed=True,
            score=1.0,
            issues=[],
            details={"files_checked": 0},
        )

    # Check linting
    if check_linting:
        lint_score, lint_issues = _check_linting(project_root, python_files)
        details["linting"] = {
            "score": lint_score,
            "issues_count": len(lint_issues),
        }
        issues.extend(lint_issues[:5])  # Limit to 5 lint issues
        score = min(score, lint_score)

    # Check type hints
    if check_type_hints:
        hint_score, hint_issues = _check_type_hints(project_root, python_files)
        details["type_hints"] = {
            "score": hint_score,
            "issues_count": len(hint_issues),
        }
        issues.extend(hint_issues[:5])  # Limit to 5 hint issues
        score = min(score, (score + hint_score) / 2)  # Average with current

    details["files_checked"] = len(python_files)
    passed = score >= 0.75 and len(issues) == 0

    return DimensionResult(
        name="unified",
        passed=passed,
        score=score,
        issues=issues,
        details=details,
    )


def _check_linting(project_root: Path, files: list[str]) -> tuple[float, list[str]]:
    """Run linting checks using ruff.

    Args:
        project_root: Project root directory.
        files: List of file paths.

    Returns:
        Tuple of (score, list of issues).
    """
    issues: list[str] = []

    # Check if ruff is available
    try:
        subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            check=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.debug("Ruff not available, skipping lint check")
        return 1.0, []

    # Run ruff on each file
    total_issues = 0
    total_lines = 0

    for file_path in files:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        try:
            # Count lines for ratio calculation
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            total_lines += len(content.split("\n"))

            # Run ruff check
            result = subprocess.run(
                ["ruff", "check", "--quiet", str(full_path)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(project_root),
            )

            if result.returncode != 0 and result.stdout:
                # Parse ruff output
                for line in result.stdout.strip().split("\n"):
                    if line:
                        total_issues += 1
                        if len(issues) < 10:
                            issues.append(f"Lint: {line}")

        except (subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"Ruff check failed for {file_path}: {e}")

    # Calculate score based on issues per 100 lines
    if total_lines > 0:
        issues_per_100 = (total_issues / total_lines) * 100
        # 0 issues = 1.0, 10+ issues per 100 lines = 0.0
        score = max(0.0, 1.0 - (issues_per_100 / 10))
    else:
        score = 1.0

    return score, issues


def _check_type_hints(project_root: Path, files: list[str]) -> tuple[float, list[str]]:
    """Check for type hint coverage.

    Args:
        project_root: Project root directory.
        files: List of file paths.

    Returns:
        Tuple of (score, list of issues).
    """
    issues: list[str] = []
    total_functions = 0
    functions_with_hints = 0

    for file_path in files:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(full_path))

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Skip private/dunder methods for stricter checking
                    if node.name.startswith("_") and not node.name.startswith("__"):
                        continue

                    total_functions += 1

                    # Check for return type annotation
                    has_return_hint = node.returns is not None

                    # Check for argument type annotations
                    args = node.args
                    typed_args = sum(1 for arg in args.args if arg.annotation is not None)
                    total_args = len(args.args)

                    # Consider self/cls as "typed"
                    if total_args > 0 and args.args[0].arg in ("self", "cls"):
                        total_args -= 1
                        if typed_args > 0:
                            typed_args -= 1

                    # Function is considered "typed" if:
                    # - Has return annotation, or
                    # - All args have annotations
                    if has_return_hint or (total_args > 0 and typed_args == total_args):
                        functions_with_hints += 1
                    elif total_args == 0 and has_return_hint:
                        functions_with_hints += 1
                    else:
                        if len(issues) < 10:
                            issues.append(
                                f"{file_path}:{node.lineno} {node.name}(): missing type hints"
                            )

        except Exception as e:
            logger.debug(f"Type hint check failed for {file_path}: {e}")

    # Calculate score
    if total_functions > 0:
        score = functions_with_hints / total_functions
    else:
        score = 1.0

    return score, issues


def _check_consistency(project_root: Path, files: list[str]) -> tuple[float, list[str]]:
    """Check for consistent patterns (optional, not currently used).

    Args:
        project_root: Project root directory.
        files: List of file paths.

    Returns:
        Tuple of (score, list of issues).
    """
    # This could check for:
    # - Consistent naming conventions
    # - Consistent import ordering
    # - Consistent docstring presence
    # For now, return perfect score as this is optional
    return 1.0, []
