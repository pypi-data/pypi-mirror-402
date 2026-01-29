"""Mention extraction utilities."""

from __future__ import annotations

import re
from pathlib import Path


def extract_mentions(message: str, project_root: Path) -> list[str]:
    """Extract file paths mentioned in the message that exist in the project."""
    # Matches common file extensions and paths
    # e.g., src/main.py, ./tests/test_foo.py, file.txt
    pattern = r"(?:[\w./-]+\.(?:py|js|ts|tsx|jsx|md|html|css|rs|go|c|cpp|h|json|yaml|toml|txt))"

    matches = re.findall(pattern, message)
    valid_files = []

    for match in matches:
        # Clean up match
        path_str = match.strip("`'\"")

        try:
            # Resolve path relative to project root
            path = (project_root / path_str).resolve()

            # Check if it exists and is within project root
            if path.exists() and path.is_file() and str(path).startswith(str(project_root)):
                # Return relative path
                valid_files.append(str(path.relative_to(project_root)))
        except Exception:
            continue

    return sorted(list(set(valid_files)))
