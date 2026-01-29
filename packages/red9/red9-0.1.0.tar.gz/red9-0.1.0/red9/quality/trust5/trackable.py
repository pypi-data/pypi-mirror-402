"""TRUST 5 - T (Trackable) Dimension.

Checks version control and documentation practices:
- Commit message quality
- Changelog presence and updates
- Git best practices
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from red9.logging import get_logger

from .validator import DimensionResult

logger = get_logger(__name__)


# Conventional commit prefixes
CONVENTIONAL_PREFIXES = {
    "feat",  # New feature
    "fix",  # Bug fix
    "docs",  # Documentation
    "style",  # Code style
    "refactor",  # Refactoring
    "perf",  # Performance
    "test",  # Tests
    "build",  # Build system
    "ci",  # CI/CD
    "chore",  # Chores
    "revert",  # Revert
}


def check_trackable(
    project_root: Path,
    files: list[str],
) -> DimensionResult:
    """Check T (Trackable) dimension.

    Args:
        project_root: Project root directory.
        files: List of modified file paths.

    Returns:
        DimensionResult with trackability score.
    """
    issues: list[str] = []
    details: dict[str, Any] = {}
    scores: list[float] = []

    # Check if in git repository
    is_git_repo = (project_root / ".git").exists()
    details["is_git_repo"] = is_git_repo

    if not is_git_repo:
        issues.append("Not a git repository")
        return DimensionResult(
            name="trackable",
            passed=False,
            score=0.5,
            issues=issues,
            details=details,
        )

    # Check commit message quality (recent commits)
    commit_score, commit_issues = _check_commit_messages(project_root)
    scores.append(commit_score)
    issues.extend(commit_issues)
    details["commit_quality"] = {
        "score": commit_score,
        "issues_count": len(commit_issues),
    }

    # Check changelog
    changelog_score, changelog_issues = _check_changelog(project_root)
    scores.append(changelog_score)
    issues.extend(changelog_issues)
    details["changelog"] = {
        "score": changelog_score,
        "exists": changelog_score > 0,
    }

    # Check git practices
    practices_score, practices_issues = _check_git_practices(project_root)
    scores.append(practices_score)
    issues.extend(practices_issues)
    details["git_practices"] = {
        "score": practices_score,
    }

    # Calculate overall score (weighted average)
    # Commit quality: 50%, changelog: 25%, practices: 25%
    overall_score = commit_score * 0.50 + changelog_score * 0.25 + practices_score * 0.25

    passed = overall_score >= 0.70 and len(issues) == 0

    return DimensionResult(
        name="trackable",
        passed=passed,
        score=overall_score,
        issues=issues,
        details=details,
    )


def _check_commit_messages(
    project_root: Path,
    num_commits: int = 10,
) -> tuple[float, list[str]]:
    """Check quality of recent commit messages.

    Args:
        project_root: Project root directory.
        num_commits: Number of recent commits to check.

    Returns:
        Tuple of (score, list of issues).
    """
    issues: list[str] = []

    try:
        # Get recent commit messages
        result = subprocess.run(
            ["git", "log", f"-{num_commits}", "--format=%s"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(project_root),
        )

        if result.returncode != 0:
            return 0.5, ["Could not retrieve commit history"]

        messages = result.stdout.strip().split("\n")
        if not messages or messages == [""]:
            return 1.0, []  # No commits yet is OK

        good_commits = 0
        total_commits = len(messages)

        for msg in messages:
            msg = msg.strip()
            if not msg:
                continue

            quality = _evaluate_commit_message(msg)

            if quality >= 0.7:
                good_commits += 1
            else:
                if len(issues) < 3:
                    issues.append(f"Poor commit message: '{msg[:50]}...'")

        score = good_commits / total_commits if total_commits > 0 else 1.0
        return score, issues

    except Exception as e:
        logger.debug(f"Failed to check commit messages: {e}")
        return 0.5, ["Could not check commit messages"]


def _evaluate_commit_message(message: str) -> float:
    """Evaluate quality of a single commit message.

    Checks for:
    - Conventional commit format (feat:, fix:, etc.)
    - Reasonable length (>10 chars, <100 chars)
    - Capitalization
    - No trailing period

    Args:
        message: The commit message.

    Returns:
        Quality score from 0.0 to 1.0.
    """
    score = 0.0
    message = message.strip()

    # Length check
    if 10 <= len(message) <= 100:
        score += 0.3
    elif len(message) > 5:
        score += 0.1

    # Conventional commit check
    conventional_pattern = r"^(" + "|".join(CONVENTIONAL_PREFIXES) + r")(\(.+\))?!?:\s+"
    if re.match(conventional_pattern, message):
        score += 0.4
    elif ":" in message[:20]:
        # Has some kind of prefix
        score += 0.2

    # Starts with capital or conventional prefix
    if message[0].isupper() or re.match(r"^[a-z]+:", message):
        score += 0.15

    # Doesn't end with period (conventional style)
    if not message.endswith("."):
        score += 0.15

    return min(1.0, score)


def _check_changelog(project_root: Path) -> tuple[float, list[str]]:
    """Check for changelog presence and quality.

    Args:
        project_root: Project root directory.

    Returns:
        Tuple of (score, list of issues).
    """
    issues: list[str] = []

    # Common changelog filenames
    changelog_names = [
        "CHANGELOG.md",
        "CHANGELOG",
        "CHANGELOG.txt",
        "CHANGES.md",
        "CHANGES",
        "HISTORY.md",
        "HISTORY",
        "NEWS.md",
        "NEWS",
    ]

    changelog_path = None
    for name in changelog_names:
        path = project_root / name
        if path.exists():
            changelog_path = path
            break

    if not changelog_path:
        issues.append("No CHANGELOG file found")
        return 0.0, issues

    # Check changelog quality
    try:
        content = changelog_path.read_text(encoding="utf-8", errors="ignore")

        # Check for reasonable content
        if len(content) < 100:
            issues.append("CHANGELOG is too short")
            return 0.3, issues

        # Check for version entries
        version_pattern = r"(v?\d+\.\d+\.?\d*|##\s+\[?\d+\.\d+)"
        versions = re.findall(version_pattern, content)

        if len(versions) < 1:
            issues.append("CHANGELOG has no version entries")
            return 0.5, issues

        return 1.0, []

    except Exception as e:
        logger.debug(f"Failed to read changelog: {e}")
        return 0.3, ["Could not read CHANGELOG"]


def _check_git_practices(project_root: Path) -> tuple[float, list[str]]:
    """Check git best practices.

    Args:
        project_root: Project root directory.

    Returns:
        Tuple of (score, list of issues).
    """
    issues: list[str] = []
    score = 1.0

    # Check for .gitignore
    if not (project_root / ".gitignore").exists():
        issues.append("No .gitignore file")
        score -= 0.2

    # Check for large files in history (simplified check)
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(project_root),
        )

        if result.returncode == 0:
            files = result.stdout.strip().split("\n")

            # Check for common bad patterns
            bad_patterns = [
                r"\.env$",  # Environment files
                r"\.pem$",  # Private keys
                r"\.key$",  # Private keys
                r"node_modules/",  # Dependencies
                r"__pycache__/",  # Python cache
                r"\.pyc$",  # Compiled Python
            ]

            for file in files:
                for pattern in bad_patterns:
                    if re.search(pattern, file):
                        if len(issues) < 3:
                            issues.append(f"Sensitive/unwanted file tracked: {file}")
                        score -= 0.1
                        break

    except Exception as e:
        logger.debug(f"Failed to check git files: {e}")

    # Check branch naming (current branch)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(project_root),
        )

        if result.returncode == 0:
            branch = result.stdout.strip()
            # Good branch names: main, master, develop, feature/*, fix/*, etc.
            good_branch_pattern = (
                r"^(main|master|develop|dev|staging|feature/|fix/|bugfix/|hotfix/|release/)"
            )
            if not re.match(good_branch_pattern, branch):
                # Not necessarily bad, but main branches are preferred
                pass

    except Exception:
        pass

    return max(0.0, score), issues
