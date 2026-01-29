"""Unified diff generation utilities."""

from __future__ import annotations

import difflib


def generate_unified_diff(
    original: str,
    new: str,
    file_path: str,
    context_lines: int = 3,
) -> str:
    """Generate a unified diff between original and new content.

    Args:
        original: Original file content.
        new: New file content.
        file_path: Path to the file (for header).
        context_lines: Number of context lines to include.

    Returns:
        Unified diff string.
    """
    original_lines = original.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)

    # Ensure both end with newline for clean diff
    if original_lines and not original_lines[-1].endswith("\n"):
        original_lines[-1] += "\n"
    if new_lines and not new_lines[-1].endswith("\n"):
        new_lines[-1] += "\n"

    diff = difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        n=context_lines,
    )

    return "".join(diff)


def get_diff_stats(original: str, new: str) -> dict[str, int]:
    """Calculate diff statistics.

    Args:
        original: Original content.
        new: New content.

    Returns:
        Dictionary with lines_added, lines_removed, etc.
    """
    original_lines = original.splitlines()
    new_lines = new.splitlines()

    matcher = difflib.SequenceMatcher(None, original_lines, new_lines)

    added = 0
    removed = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert":
            added += j2 - j1
        elif tag == "delete":
            removed += i2 - i1
        elif tag == "replace":
            removed += i2 - i1
            added += j2 - j1

    return {
        "lines_added": added,
        "lines_removed": removed,
        "total_original": len(original_lines),
        "total_new": len(new_lines),
        "net_change": added - removed,
    }


def parse_unified_diff(diff_text: str) -> list[dict]:
    """Parse a unified diff into structured hunks.

    Args:
        diff_text: Unified diff string.

    Returns:
        List of hunk dictionaries with old_start, new_start, lines.
    """
    import re

    hunks = []
    current_hunk: dict | None = None

    for line in diff_text.splitlines():
        if line.startswith("@@"):
            # Parse hunk header: @@ -start,count +start,count @@
            match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            if match:
                current_hunk = {
                    "old_start": int(match.group(1)),
                    "old_count": int(match.group(2) or 1),
                    "new_start": int(match.group(3)),
                    "new_count": int(match.group(4) or 1),
                    "lines": [],
                }
                hunks.append(current_hunk)
        elif current_hunk is not None:
            if line.startswith("+") and not line.startswith("+++"):
                current_hunk["lines"].append({"type": "add", "content": line[1:]})
            elif line.startswith("-") and not line.startswith("---"):
                current_hunk["lines"].append({"type": "remove", "content": line[1:]})
            elif line.startswith(" "):
                current_hunk["lines"].append({"type": "context", "content": line[1:]})

    return hunks


def apply_unified_diff(
    original: str,
    diff_text: str,
    fuzz_factor: int = 0,
) -> tuple[str | None, str | None]:
    """Apply a unified diff to original content.

    Args:
        original: Original file content.
        diff_text: Unified diff to apply.
        fuzz_factor: Lines of fuzz allowed for matching (0 = exact).

    Returns:
        Tuple of (patched_content, error_message).
        If successful: (content, None)
        If failed: (None, error_message)
    """
    hunks = parse_unified_diff(diff_text)
    if not hunks:
        return None, "No hunks found in diff"

    lines = original.splitlines(keepends=True)
    # Ensure all lines have newlines for consistent processing
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    # Apply hunks in reverse order to maintain line numbers
    for hunk in reversed(hunks):
        result = _apply_hunk(lines, hunk, fuzz_factor)
        if result is None:
            return None, f"Failed to apply hunk at line {hunk['old_start']}"
        lines = result

    return "".join(lines), None


def _apply_hunk(
    lines: list[str],
    hunk: dict,
    fuzz_factor: int,
) -> list[str] | None:
    """Apply a single hunk to lines.

    Args:
        lines: Current file lines.
        hunk: Hunk dictionary from parse_unified_diff.
        fuzz_factor: Lines of fuzz allowed.

    Returns:
        Modified lines list, or None if hunk couldn't be applied.
    """
    old_start = hunk["old_start"] - 1  # Convert to 0-indexed
    hunk_lines = hunk["lines"]

    # Extract expected old lines (context + remove)
    expected_old: list[str] = []
    for line_info in hunk_lines:
        if line_info["type"] in ("context", "remove"):
            content = line_info["content"]
            if not content.endswith("\n"):
                content += "\n"
            expected_old.append(content)

    # Try to find a match with fuzz
    match_start = _find_hunk_match(lines, expected_old, old_start, fuzz_factor)
    if match_start is None:
        return None

    # Build new lines for this region
    new_lines: list[str] = []
    for line_info in hunk_lines:
        if line_info["type"] in ("context", "add"):
            content = line_info["content"]
            if not content.endswith("\n"):
                content += "\n"
            new_lines.append(content)

    # Replace the matched region
    result = lines[:match_start] + new_lines + lines[match_start + len(expected_old) :]
    return result


def _find_hunk_match(
    lines: list[str],
    expected: list[str],
    start_hint: int,
    fuzz_factor: int,
) -> int | None:
    """Find where the hunk matches in the file.

    Args:
        lines: File lines.
        expected: Expected lines to match.
        start_hint: Suggested start position.
        fuzz_factor: Lines of fuzz allowed.

    Returns:
        Start index of match, or None if not found.
    """
    if not expected:
        return start_hint

    # Try exact position first
    if _lines_match(lines, expected, start_hint):
        return start_hint

    # Try with fuzz (search around the hint position)
    for offset in range(1, fuzz_factor + 1):
        # Try before
        pos = start_hint - offset
        if pos >= 0 and _lines_match(lines, expected, pos):
            return pos
        # Try after
        pos = start_hint + offset
        if pos + len(expected) <= len(lines) and _lines_match(lines, expected, pos):
            return pos

    # If still not found and fuzz_factor > 0, search entire file
    if fuzz_factor > 0:
        for i in range(len(lines) - len(expected) + 1):
            if _lines_match(lines, expected, i):
                return i

    return None


def _lines_match(lines: list[str], expected: list[str], start: int) -> bool:
    """Check if lines match at position.

    Args:
        lines: File lines.
        expected: Expected lines.
        start: Start position.

    Returns:
        True if lines match.
    """
    if start < 0 or start + len(expected) > len(lines):
        return False

    for i, exp in enumerate(expected):
        actual = lines[start + i]
        # Normalize for comparison (strip trailing whitespace)
        if actual.rstrip() != exp.rstrip():
            return False

    return True
