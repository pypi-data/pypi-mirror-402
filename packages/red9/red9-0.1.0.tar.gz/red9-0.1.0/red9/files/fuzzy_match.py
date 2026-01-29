"""Fuzzy matching for text replacement."""

from __future__ import annotations

import difflib
import textwrap
from typing import NamedTuple


class MatchResult(NamedTuple):
    start_index: int
    end_index: int
    confidence: float
    matched_text: str


def find_best_match(
    source_text: str, search_block: str, threshold: float = 0.85
) -> MatchResult | None:
    """Find the best match for search_block in source_text.

    Uses SequenceMatcher to find the most similar block of text.
    Handles minor whitespace/indentation differences.

    Args:
        source_text: The full text to search in.
        search_block: The text block to find.
        threshold: Minimum similarity ratio (0.0 to 1.0).

    Returns:
        MatchResult or None if no match found.
    """
    if not search_block:
        return None

    # 1. Exact match check (fast path)
    if search_block in source_text:
        start = source_text.index(search_block)
        return MatchResult(start, start + len(search_block), 1.0, search_block)

    # 2. Line-by-line fuzzy match
    source_lines = source_text.splitlines(keepends=True)
    search_lines = search_block.splitlines(keepends=True)

    if not search_lines:
        return None

    # Helper to strip whitespace for anchoring
    def normalize(s: str) -> str:
        return " ".join(s.split())

    # Helper to dedent a block of text
    def dedent_text(text: str) -> str:
        # We assume the first line defines the indentation for the block if it has content
        # But textwrap.dedent is safer
        return textwrap.dedent(text)

    search_text_dedented = dedent_text("".join(search_lines))

    # Sliding window search
    best_ratio = 0.0
    best_start_idx = -1
    best_end_idx = -1

    window_size = len(search_lines)

    # Heuristic: try to find the first line to anchor the search
    first_line_matches = []
    normalized_first = normalize(search_lines[0])

    for i, line in enumerate(source_lines):
        if normalize(line) == normalized_first:
            first_line_matches.append(i)

    # If no anchors found, fallback to scanning everything
    if not first_line_matches:
        scan_indices = range(len(source_lines) - window_size + 1)
    else:
        scan_indices = set()
        for anchor in first_line_matches:
            start = max(0, anchor - 2)
            end = min(len(source_lines) - window_size + 1, anchor + 2)
            for i in range(start, end + 1):
                scan_indices.add(i)
        scan_indices = sorted(list(scan_indices))

    for i in scan_indices:
        window = source_lines[i : i + window_size]
        window_text = "".join(window)

        # Strategy A: Raw comparison
        ratio_raw = difflib.SequenceMatcher(None, window_text, "".join(search_lines)).ratio()

        # Strategy B: Dedented comparison (handles indentation mismatch)
        window_text_dedented = dedent_text(window_text)
        ratio_dedented = difflib.SequenceMatcher(
            None, window_text_dedented, search_text_dedented
        ).ratio()

        # Take the best of both worlds
        ratio = max(ratio_raw, ratio_dedented)

        if ratio > best_ratio:
            best_ratio = ratio
            best_start_idx = i
            best_end_idx = i + window_size

    if best_ratio >= threshold:
        char_start = sum(len(line) for line in source_lines[:best_start_idx])
        char_end = sum(len(line) for line in source_lines[:best_end_idx])
        matched_text = "".join(source_lines[best_start_idx:best_end_idx])

        return MatchResult(char_start, char_end, best_ratio, matched_text)

    return None
