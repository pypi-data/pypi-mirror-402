"""TRUST 5 - R (Readable) Dimension.

Checks code readability metrics:
- File size <= max_file_lines (default 300)
- Function size <= max_function_lines (default 50)
- Function parameters <= max_function_params (default 5)
- Cyclomatic complexity <= max_cyclomatic_complexity (default 10)
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from red9.logging import get_logger

from .validator import DimensionResult

logger = get_logger(__name__)


@dataclass
class FunctionMetrics:
    """Metrics for a single function."""

    name: str
    file: str
    line: int
    lines: int
    params: int
    complexity: int


@dataclass
class FileMetrics:
    """Metrics for a single file."""

    path: str
    lines: int
    functions: list[FunctionMetrics] = field(default_factory=list)


def check_readable(
    project_root: Path,
    files: list[str],
    max_file_lines: int = 300,
    max_function_lines: int = 50,
    max_function_params: int = 5,
    max_cyclomatic_complexity: int = 10,
) -> DimensionResult:
    """Check R (Readable) dimension.

    Args:
        project_root: Project root directory.
        files: List of modified file paths.
        max_file_lines: Maximum lines per file.
        max_function_lines: Maximum lines per function.
        max_function_params: Maximum parameters per function.
        max_cyclomatic_complexity: Maximum cyclomatic complexity.

    Returns:
        DimensionResult with readability score.
    """
    issues: list[str] = []
    details: dict[str, Any] = {}
    file_metrics: list[FileMetrics] = []

    # Analyze Python files
    python_files = [f for f in files if f.endswith(".py")]
    total_score = 0.0
    analyzed_count = 0

    for file_path in python_files:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        try:
            metrics = _analyze_python_file(full_path, file_path)
            file_metrics.append(metrics)

            # Calculate score for this file
            file_score = _calculate_file_score(
                metrics,
                max_file_lines,
                max_function_lines,
                max_function_params,
                max_cyclomatic_complexity,
                issues,
            )
            total_score += file_score
            analyzed_count += 1

        except Exception as e:
            logger.debug(f"Failed to analyze {file_path}: {e}")

    # Calculate overall score
    if analyzed_count > 0:
        score = total_score / analyzed_count
    else:
        # No files analyzed - assume good
        score = 1.0

    # Store details
    details["files_analyzed"] = analyzed_count
    details["max_file_lines"] = max_file_lines
    details["max_function_lines"] = max_function_lines
    details["max_function_params"] = max_function_params
    details["max_cyclomatic_complexity"] = max_cyclomatic_complexity
    details["file_metrics"] = [
        {
            "path": m.path,
            "lines": m.lines,
            "functions": [
                {
                    "name": f.name,
                    "line": f.line,
                    "lines": f.lines,
                    "params": f.params,
                    "complexity": f.complexity,
                }
                for f in m.functions
            ],
        }
        for m in file_metrics
    ]

    passed = score >= 0.80 and len(issues) == 0

    return DimensionResult(
        name="readable",
        passed=passed,
        score=score,
        issues=issues,
        details=details,
    )


def _analyze_python_file(full_path: Path, rel_path: str) -> FileMetrics:
    """Analyze a Python file for readability metrics.

    Args:
        full_path: Full path to the file.
        rel_path: Relative path for reporting.

    Returns:
        FileMetrics with analysis results.
    """
    content = full_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.split("\n")
    line_count = len(lines)

    # Parse AST
    tree = ast.parse(content, filename=str(full_path))

    # Extract function metrics
    functions: list[FunctionMetrics] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_metrics = _analyze_function(node, rel_path)
            functions.append(func_metrics)

    return FileMetrics(
        path=rel_path,
        lines=line_count,
        functions=functions,
    )


def _analyze_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str
) -> FunctionMetrics:
    """Analyze a function for metrics.

    Args:
        node: AST node for the function.
        file_path: Path to the file.

    Returns:
        FunctionMetrics for the function.
    """
    # Calculate line count
    start_line = node.lineno
    end_line = _get_end_line(node)
    line_count = end_line - start_line + 1

    # Count parameters
    param_count = len(node.args.args)
    if node.args.vararg:
        param_count += 1
    if node.args.kwarg:
        param_count += 1
    param_count += len(node.args.kwonlyargs)
    param_count += len(node.args.posonlyargs)

    # Calculate cyclomatic complexity
    complexity = _calculate_complexity(node)

    return FunctionMetrics(
        name=node.name,
        file=file_path,
        line=start_line,
        lines=line_count,
        params=param_count,
        complexity=complexity,
    )


def _get_end_line(node: ast.AST) -> int:
    """Get the end line of an AST node.

    Args:
        node: AST node.

    Returns:
        End line number.
    """
    if hasattr(node, "end_lineno") and node.end_lineno is not None:
        return node.end_lineno

    # Fallback: find max line in children
    max_line = getattr(node, "lineno", 1)
    for child in ast.walk(node):
        child_line = getattr(child, "lineno", 0)
        if child_line > max_line:
            max_line = child_line

    return max_line


def _calculate_complexity(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Calculate cyclomatic complexity of a function.

    Cyclomatic complexity = E - N + 2P
    For a function: 1 + number of decision points

    Decision points:
    - if, elif
    - for, while
    - except
    - and, or
    - ternary (IfExp)
    - comprehension conditions

    Args:
        node: AST node for the function.

    Returns:
        Cyclomatic complexity score.
    """
    complexity = 1  # Base complexity

    for child in ast.walk(node):
        # Control flow statements
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1

        # Exception handlers
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1

        # Boolean operators
        elif isinstance(child, ast.BoolOp):
            # Each 'and'/'or' adds complexity
            complexity += len(child.values) - 1

        # Ternary expressions
        elif isinstance(child, ast.IfExp):
            complexity += 1

        # Comprehensions with conditions
        elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for generator in child.generators:
                complexity += len(generator.ifs)

        # Assert statements
        elif isinstance(child, ast.Assert):
            complexity += 1

    return complexity


def _calculate_file_score(
    metrics: FileMetrics,
    max_file_lines: int,
    max_function_lines: int,
    max_function_params: int,
    max_cyclomatic_complexity: int,
    issues: list[str],
) -> float:
    """Calculate readability score for a file.

    Args:
        metrics: File metrics.
        max_file_lines: Maximum lines per file.
        max_function_lines: Maximum lines per function.
        max_function_params: Maximum parameters per function.
        max_cyclomatic_complexity: Maximum cyclomatic complexity.
        issues: List to append issues to.

    Returns:
        Score from 0.0 to 1.0.
    """
    penalties = 0.0
    total_checks = 1  # File size check

    # Check file size
    if metrics.lines > max_file_lines:
        penalty = min(0.3, (metrics.lines - max_file_lines) / max_file_lines * 0.3)
        penalties += penalty
        issues.append(f"{metrics.path}: {metrics.lines} lines exceeds max {max_file_lines}")

    # Check each function
    for func in metrics.functions:
        total_checks += 3  # lines, params, complexity

        # Function size
        if func.lines > max_function_lines:
            penalty = min(0.2, (func.lines - max_function_lines) / max_function_lines * 0.2)
            penalties += penalty
            issues.append(
                f"{metrics.path}:{func.line} {func.name}(): {func.lines} lines "
                f"exceeds max {max_function_lines}"
            )

        # Parameter count
        if func.params > max_function_params:
            penalty = min(0.1, (func.params - max_function_params) / max_function_params * 0.1)
            penalties += penalty
            issues.append(
                f"{metrics.path}:{func.line} {func.name}(): {func.params} params "
                f"exceeds max {max_function_params}"
            )

        # Cyclomatic complexity
        if func.complexity > max_cyclomatic_complexity:
            penalty = min(
                0.2, (func.complexity - max_cyclomatic_complexity) / max_cyclomatic_complexity * 0.2
            )
            penalties += penalty
            issues.append(
                f"{metrics.path}:{func.line} {func.name}(): complexity {func.complexity} "
                f"exceeds max {max_cyclomatic_complexity}"
            )

    # Calculate final score (1.0 - penalties, minimum 0.0)
    score = max(0.0, 1.0 - penalties)
    return score
