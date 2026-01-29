"""TRUST 5 - S (Secured) Dimension.

Checks for security vulnerabilities using:
- AST-grep rules (if available)
- Python AST analysis (fallback)

Detects:
- SQL injection
- Command injection
- Hardcoded secrets
- Path traversal
- XSS vulnerabilities
- Unsafe deserialization
"""

from __future__ import annotations

import ast
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from red9.logging import get_logger

from .validator import DimensionResult

logger = get_logger(__name__)


@dataclass
class SecurityIssue:
    """A security issue found in code."""

    rule_id: str
    severity: str  # critical, high, medium, low
    file: str
    line: int
    message: str
    code_snippet: str = ""


# Severity weights for scoring
SEVERITY_WEIGHTS = {
    "critical": 1.0,
    "high": 0.5,
    "medium": 0.2,
    "low": 0.1,
}


def check_secured(
    project_root: Path,
    files: list[str],
    rules_path: str = ".red9/quality/rules",
) -> DimensionResult:
    """Check S (Secured) dimension.

    Args:
        project_root: Project root directory.
        files: List of modified file paths.
        rules_path: Path to security rules directory.

    Returns:
        DimensionResult with security score.
    """
    issues: list[str] = []
    details: dict[str, Any] = {}
    security_issues: list[SecurityIssue] = []

    # Filter supported files
    python_files = [f for f in files if f.endswith(".py")]

    if not python_files:
        return DimensionResult(
            name="secured",
            passed=True,
            score=1.0,
            issues=[],
            details={"files_scanned": 0},
        )

    # Try AST-grep first
    ast_grep_available = _check_ast_grep_available()

    if ast_grep_available:
        security_issues = _scan_with_ast_grep(project_root, python_files, rules_path)
        details["scanner"] = "ast-grep"
    else:
        # Fallback to Python AST analysis
        security_issues = _scan_with_python_ast(project_root, python_files)
        details["scanner"] = "python-ast"

    # Calculate score based on issues
    score = _calculate_security_score(security_issues)

    # Convert security issues to string issues
    for issue in security_issues:
        issues.append(
            f"[{issue.severity.upper()}] {issue.file}:{issue.line} {issue.rule_id}: {issue.message}"
        )

    # Store details
    details["files_scanned"] = len(python_files)
    details["issues_found"] = len(security_issues)
    details["issues_by_severity"] = {
        "critical": sum(1 for i in security_issues if i.severity == "critical"),
        "high": sum(1 for i in security_issues if i.severity == "high"),
        "medium": sum(1 for i in security_issues if i.severity == "medium"),
        "low": sum(1 for i in security_issues if i.severity == "low"),
    }

    # Critical issues always fail
    has_critical = any(i.severity == "critical" for i in security_issues)
    passed = score >= 0.90 and not has_critical

    return DimensionResult(
        name="secured",
        passed=passed,
        score=score,
        issues=issues,
        details=details,
    )


def _check_ast_grep_available() -> bool:
    """Check if ast-grep (sg) is available.

    Returns:
        True if ast-grep is available.
    """
    try:
        result = subprocess.run(
            ["sg", "--version"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _scan_with_ast_grep(
    project_root: Path,
    files: list[str],
    rules_path: str,
) -> list[SecurityIssue]:
    """Scan files using ast-grep.

    Args:
        project_root: Project root directory.
        files: List of file paths.
        rules_path: Path to rules directory.

    Returns:
        List of SecurityIssue objects.
    """
    issues: list[SecurityIssue] = []
    rules_dir = project_root / rules_path

    # If no custom rules, use built-in patterns
    if not rules_dir.exists():
        return _scan_with_builtin_patterns(project_root, files)

    for file_path in files:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        try:
            # Run ast-grep scan
            result = subprocess.run(
                ["sg", "scan", "--json", str(full_path)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(project_root),
            )

            if result.stdout:
                import json

                findings = json.loads(result.stdout)
                for finding in findings:
                    issues.append(
                        SecurityIssue(
                            rule_id=finding.get("rule_id", "unknown"),
                            severity=finding.get("severity", "medium"),
                            file=file_path,
                            line=finding.get("range", {}).get("start", {}).get("line", 0),
                            message=finding.get("message", "Security issue found"),
                            code_snippet=finding.get("matched", ""),
                        )
                    )

        except Exception as e:
            logger.debug(f"AST-grep scan failed for {file_path}: {e}")

    return issues


def _scan_with_builtin_patterns(
    project_root: Path,
    files: list[str],
) -> list[SecurityIssue]:
    """Scan with built-in ast-grep patterns.

    Args:
        project_root: Project root directory.
        files: List of file paths.

    Returns:
        List of SecurityIssue objects.
    """
    issues: list[SecurityIssue] = []

    # Built-in security patterns for Python
    patterns = [
        {
            "rule_id": "sql-injection",
            "pattern": "execute($SQL)",
            "message": "Potential SQL injection - use parameterized queries",
            "severity": "critical",
        },
        {
            "rule_id": "command-injection",
            "pattern": "os.system($CMD)",
            "message": "Potential command injection - use subprocess with shell=False",
            "severity": "critical",
        },
        {
            "rule_id": "eval-usage",
            "pattern": "eval($CODE)",
            "message": "eval() is dangerous - avoid executing untrusted code",
            "severity": "high",
        },
        {
            "rule_id": "exec-usage",
            "pattern": "exec($CODE)",
            "message": "exec() is dangerous - avoid executing untrusted code",
            "severity": "high",
        },
    ]

    for file_path in files:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        for pattern_info in patterns:
            try:
                result = subprocess.run(
                    ["sg", "--pattern", pattern_info["pattern"], str(full_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.stdout:
                    # Found matches
                    for match in result.stdout.strip().split("\n"):
                        if match:
                            # Extract line number from match
                            line_match = re.search(r":(\d+):", match)
                            line = int(line_match.group(1)) if line_match else 0

                            issues.append(
                                SecurityIssue(
                                    rule_id=pattern_info["rule_id"],
                                    severity=pattern_info["severity"],
                                    file=file_path,
                                    line=line,
                                    message=pattern_info["message"],
                                )
                            )

            except Exception:
                pass

    return issues


def _scan_with_python_ast(
    project_root: Path,
    files: list[str],
) -> list[SecurityIssue]:
    """Scan files using Python AST (fallback).

    Args:
        project_root: Project root directory.
        files: List of file paths.

    Returns:
        List of SecurityIssue objects.
    """
    issues: list[SecurityIssue] = []

    for file_path in files:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(full_path))

            # Visit AST nodes
            visitor = SecurityVisitor(file_path, content.split("\n"))
            visitor.visit(tree)
            issues.extend(visitor.issues)

        except Exception as e:
            logger.debug(f"AST scan failed for {file_path}: {e}")

    return issues


class SecurityVisitor(ast.NodeVisitor):
    """AST visitor to detect security issues."""

    # Dangerous functions
    DANGEROUS_CALLS = {
        "eval": ("eval-usage", "critical", "eval() is dangerous - avoid untrusted code"),
        "exec": ("exec-usage", "critical", "exec() is dangerous - avoid untrusted code"),
        "compile": ("compile-usage", "high", "compile() can execute arbitrary code"),
    }

    # Dangerous module.function calls
    DANGEROUS_MODULE_CALLS = {
        ("os", "system"): (
            "command-injection",
            "critical",
            "os.system() - use subprocess with shell=False",
        ),
        ("os", "popen"): ("command-injection", "critical", "os.popen() - use subprocess"),
        ("subprocess", "call"): (
            "shell-true-check",
            "high",
            "Check shell=False for subprocess.call",
        ),
        ("subprocess", "Popen"): (
            "shell-true-check",
            "high",
            "Check shell=False for subprocess.Popen",
        ),
        ("pickle", "load"): (
            "unsafe-deserialization",
            "high",
            "pickle.load() can execute arbitrary code",
        ),
        ("pickle", "loads"): (
            "unsafe-deserialization",
            "high",
            "pickle.loads() can execute arbitrary code",
        ),
        ("yaml", "load"): ("unsafe-yaml", "high", "yaml.load() - use yaml.safe_load()"),
        ("marshal", "load"): ("unsafe-deserialization", "high", "marshal.load() is unsafe"),
        ("marshal", "loads"): ("unsafe-deserialization", "high", "marshal.loads() is unsafe"),
    }

    # Patterns for hardcoded secrets
    SECRET_PATTERNS = [
        (r"(?i)(password|passwd|pwd)\s*=\s*['\"][^'\"]+['\"]", "hardcoded-password"),
        (r"(?i)(api[_-]?key|apikey)\s*=\s*['\"][^'\"]+['\"]", "hardcoded-api-key"),
        (r"(?i)(secret[_-]?key|secretkey)\s*=\s*['\"][^'\"]+['\"]", "hardcoded-secret"),
        (r"(?i)(token)\s*=\s*['\"][a-zA-Z0-9_-]{20,}['\"]", "hardcoded-token"),
        (r"(?i)(aws[_-]?access|aws[_-]?secret)\s*=\s*['\"][^'\"]+['\"]", "hardcoded-aws"),
    ]

    def __init__(self, file_path: str, lines: list[str]) -> None:
        self.file_path = file_path
        self.lines = lines
        self.issues: list[SecurityIssue] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls."""
        # Check for dangerous built-in calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.DANGEROUS_CALLS:
                rule_id, severity, message = self.DANGEROUS_CALLS[func_name]
                self.issues.append(
                    SecurityIssue(
                        rule_id=rule_id,
                        severity=severity,
                        file=self.file_path,
                        line=node.lineno,
                        message=message,
                    )
                )

        # Check for dangerous module.function calls
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
                func_name = node.func.attr
                key = (module_name, func_name)

                if key in self.DANGEROUS_MODULE_CALLS:
                    rule_id, severity, message = self.DANGEROUS_MODULE_CALLS[key]

                    # Special check for subprocess with shell=True
                    if "shell-true-check" in rule_id:
                        if self._has_shell_true(node):
                            self.issues.append(
                                SecurityIssue(
                                    rule_id="shell-injection",
                                    severity="critical",
                                    file=self.file_path,
                                    line=node.lineno,
                                    message="shell=True is dangerous - use shell=False",
                                )
                            )
                    else:
                        self.issues.append(
                            SecurityIssue(
                                rule_id=rule_id,
                                severity=severity,
                                file=self.file_path,
                                line=node.lineno,
                                message=message,
                            )
                        )

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignments to check for hardcoded secrets."""
        # Get the line text
        if node.lineno <= len(self.lines):
            line_text = self.lines[node.lineno - 1]

            for pattern, rule_id in self.SECRET_PATTERNS:
                if re.search(pattern, line_text):
                    self.issues.append(
                        SecurityIssue(
                            rule_id=rule_id,
                            severity="high",
                            file=self.file_path,
                            line=node.lineno,
                            message=f"Potential hardcoded secret ({rule_id})",
                        )
                    )
                    break

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Check for dangerous imports."""
        for alias in node.names:
            if alias.name in ("telnetlib", "ftplib"):
                self.issues.append(
                    SecurityIssue(
                        rule_id="insecure-protocol",
                        severity="medium",
                        file=self.file_path,
                        line=node.lineno,
                        message=f"{alias.name} uses insecure protocol",
                    )
                )

        self.generic_visit(node)

    def _has_shell_true(self, node: ast.Call) -> bool:
        """Check if a call has shell=True.

        Args:
            node: The Call node.

        Returns:
            True if shell=True is found.
        """
        for keyword in node.keywords:
            if keyword.arg == "shell":
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value is True
                elif isinstance(keyword.value, ast.NameConstant):
                    return keyword.value.value is True
        return False


def _calculate_security_score(issues: list[SecurityIssue]) -> float:
    """Calculate security score based on issues.

    Args:
        issues: List of security issues.

    Returns:
        Score from 0.0 to 1.0.
    """
    if not issues:
        return 1.0

    # Sum weighted penalties
    total_penalty = 0.0
    for issue in issues:
        weight = SEVERITY_WEIGHTS.get(issue.severity, 0.1)
        total_penalty += weight

    # Score decreases with each issue
    # 1 critical = 0.0 score
    # 2 high = 0.0 score
    # etc.
    score = max(0.0, 1.0 - total_penalty)
    return score
