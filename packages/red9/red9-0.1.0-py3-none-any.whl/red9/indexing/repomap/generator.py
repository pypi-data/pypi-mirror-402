"""RepoMap Generator - Smart repository map generation.

Generates a sparse representation of the repository structure using:
- Tree-sitter AST parsing for accurate symbol extraction
- PageRank algorithm for intelligent file ranking
- Multi-level caching for fast subsequent generations

Based on aider's repomap.py implementation.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from red9.logging import get_logger

from .cache import MapCache, TagCache, TreeContextCache
from .ranker import RankedTag, TagRanker, select_tags_for_budget
from .tags import Tag, TagExtractor

logger = get_logger(__name__)


class RepoMap:
    """Generates a smart map of the repository structure.

    Features:
    - Tree-sitter based symbol extraction
    - PageRank file ranking with personalization
    - Multi-level caching (tags, tree context, full map)
    - Binary search for optimal token budget
    """

    # Default ignore patterns
    DEFAULT_IGNORE_PATTERNS = {
        ".git",
        ".venv",
        "venv",
        "env",
        ".env",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        "dist",
        "build",
        ".idea",
        ".vscode",
        "*.egg-info",
        ".red9",
        ".red9.tags.cache.*",
    }

    # Supported file extensions
    SUPPORTED_EXTENSIONS = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".rs",
        ".go",
        ".c",
        ".cpp",
        ".cc",
        ".h",
        ".hpp",
        ".java",
        ".rb",
        ".php",
        ".cs",
        ".swift",
        ".kt",
        ".scala",
        ".r",
        ".lua",
        ".sh",
    }

    def __init__(
        self,
        project_root: Path,
        max_tokens: int = 1024,
        cache_enabled: bool = True,
        use_pagerank: bool = True,
    ) -> None:
        """Initialize RepoMap.

        Args:
            project_root: Project root directory.
            max_tokens: Maximum tokens for generated map.
            cache_enabled: Whether to use caching.
            use_pagerank: Whether to use PageRank ranking.
        """
        self.project_root = project_root
        self.max_tokens = max_tokens
        self.cache_enabled = cache_enabled
        self.use_pagerank = use_pagerank

        # Initialize components
        self._tag_extractor = TagExtractor(project_root)

        if cache_enabled:
            self._tag_cache = TagCache(project_root)
            self._tree_cache = TreeContextCache()
            self._map_cache = MapCache()
        else:
            self._tag_cache = None
            self._tree_cache = None
            self._map_cache = None

        self._ignore_patterns = self.DEFAULT_IGNORE_PATTERNS.copy()

    def generate(
        self,
        max_tokens: int | None = None,
        chat_fnames: set[str] | None = None,
        mentioned_fnames: set[str] | None = None,
        mentioned_idents: set[str] | None = None,
        refresh: str = "auto",
    ) -> str:
        """Generate the repository map.

        Args:
            max_tokens: Maximum tokens (overrides default).
            chat_fnames: Files currently in chat context.
            mentioned_fnames: Files mentioned by user.
            mentioned_idents: Identifiers mentioned by user.
            refresh: Cache refresh strategy ("auto", "always", "files", "manual").

        Returns:
            Generated map string.
        """
        max_tokens = max_tokens or self.max_tokens
        chat_fnames = chat_fnames or set()
        mentioned_fnames = mentioned_fnames or set()
        mentioned_idents = mentioned_idents or set()

        # Check map cache
        if self._map_cache and refresh == "files":
            cached = self._map_cache.get(
                frozenset(chat_fnames),
                frozenset(mentioned_fnames | set(self._get_all_files())),
                max_tokens,
            )
            if cached:
                return cached

        start_time = time.time()

        # Collect all source files
        all_files = list(self._get_all_files())

        if not all_files:
            return "(No source files found)"

        # Extract tags from all files
        all_tags: list[Tag] = []
        for filepath in all_files:
            tags = self._get_tags_cached(filepath)
            all_tags.extend(tags)

        if not all_tags:
            # Fall back to simple tree if no tags extracted
            return self._generate_simple_tree(all_files)

        # Rank tags using PageRank
        if self.use_pagerank:
            ranker = TagRanker(
                chat_fnames=chat_fnames,
                mentioned_fnames=mentioned_fnames,
                mentioned_idents=mentioned_idents,
            )
            ranked_tags = ranker.rank_tags(all_tags)
        else:
            # Simple ranking by file order
            ranked_tags = [
                RankedTag(
                    name=t.name,
                    rel_fname=t.rel_fname,
                    line=t.line,
                    score=0.0,
                    kind=t.kind,
                    category=t.category,
                )
                for t in all_tags
                if t.kind == "def"
            ]

        # Select tags that fit within token budget
        selected_tags = select_tags_for_budget(ranked_tags, max_tokens)

        # Render the map
        map_string = self._render_map(selected_tags, all_files)

        generation_time = time.time() - start_time
        logger.debug(
            f"RepoMap generated in {generation_time:.2f}s "
            f"({len(selected_tags)} tags, {len(all_files)} files)"
        )

        # Cache the result
        if self._map_cache and refresh != "always":
            self._map_cache.set(
                frozenset(chat_fnames),
                frozenset(mentioned_fnames | set(str(f) for f in all_files)),
                max_tokens,
                map_string,
                generation_time,
            )

        return map_string

    def _get_tags_cached(self, filepath: Path) -> list[Tag]:
        """Get tags for a file, using cache if available.

        Args:
            filepath: Path to the source file.

        Returns:
            List of Tag objects.
        """
        # Check cache
        if self._tag_cache:
            cached = self._tag_cache.get(filepath)
            if cached is not None:
                return [Tag.from_dict(t) for t in cached]

        # Extract tags
        tags = self._tag_extractor.extract_tags(filepath)

        # Cache result
        if self._tag_cache and tags:
            self._tag_cache.set(filepath, [t.to_dict() for t in tags])

        return tags

    def _get_all_files(self) -> list[Path]:
        """Get all source files in the project.

        Returns:
            List of Path objects for source files.
        """
        files: list[Path] = []

        for root, dirs, filenames in os.walk(self.project_root):
            # Filter directories
            dirs[:] = [
                d
                for d in dirs
                if not self._should_ignore(d)
                and not any(d.startswith(p.rstrip("*")) for p in self._ignore_patterns)
            ]

            for filename in filenames:
                filepath = Path(root) / filename
                suffix = filepath.suffix.lower()

                if suffix in self.SUPPORTED_EXTENSIONS:
                    if not self._should_ignore(filepath.name):
                        files.append(filepath)

        return files

    def _should_ignore(self, name: str) -> bool:
        """Check if a file/directory should be ignored.

        Args:
            name: File or directory name.

        Returns:
            True if should be ignored.
        """
        for pattern in self._ignore_patterns:
            if pattern.endswith("*"):
                if name.startswith(pattern[:-1]):
                    return True
            elif name == pattern:
                return True
        return False

    def _render_map(self, tags: list[RankedTag], all_files: list[Path]) -> str:
        """Render the map from ranked tags.

        Args:
            tags: List of RankedTag objects.
            all_files: List of all source files.

        Returns:
            Rendered map string.
        """
        lines: list[str] = []

        # Group tags by file
        tags_by_file: dict[str, list[RankedTag]] = {}
        for tag in tags:
            if tag.rel_fname not in tags_by_file:
                tags_by_file[tag.rel_fname] = []
            tags_by_file[tag.rel_fname].append(tag)

        # Render each file's tags
        for rel_fname in sorted(tags_by_file.keys()):
            file_tags = tags_by_file[rel_fname]
            lines.append(f"\n{rel_fname}:")

            # Sort by line number
            file_tags.sort(key=lambda t: t.line)

            for tag in file_tags:
                # Format: line: [category] name
                category_str = f"[{tag.category}] " if tag.category else ""
                lines.append(f"  {tag.line}: {category_str}{tag.name}")

        if not lines:
            return self._generate_simple_tree(all_files)

        return "\n".join(lines)

    def _generate_simple_tree(self, files: list[Path]) -> str:
        """Generate a simple file tree (fallback).

        Args:
            files: List of file paths.

        Returns:
            Simple tree string.
        """
        tree_lines: list[str] = []

        for filepath in sorted(files)[:50]:  # Limit to 50 files
            try:
                rel_path = filepath.relative_to(self.project_root)
                tree_lines.append(str(rel_path))
            except ValueError:
                tree_lines.append(str(filepath))

        if len(files) > 50:
            tree_lines.append(f"... ({len(files) - 50} more files)")

        return "\n".join(tree_lines)

    def get_map(self) -> str:
        """Get the generated map (alias for generate).

        Returns:
            Generated map string.
        """
        return self.generate()

    def get_sparse_map(self) -> str:
        """Get the generated map (alias for generate).

        Returns:
            Generated map string.
        """
        return self.generate()

    def invalidate_file(self, filepath: Path) -> None:
        """Invalidate cache for a specific file.

        Args:
            filepath: Path to the file.
        """
        if self._tag_cache:
            self._tag_cache.invalidate(filepath)
        if self._map_cache:
            self._map_cache.clear()

    def clear_cache(self) -> None:
        """Clear all caches."""
        if self._tag_cache:
            self._tag_cache.clear()
        if self._tree_cache:
            self._tree_cache.clear()
        if self._map_cache:
            self._map_cache.clear()

    def close(self) -> None:
        """Close the cache (cleanup)."""
        if self._tag_cache:
            self._tag_cache.close()

    def __enter__(self) -> RepoMap:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def get_repo_map(
    project_root: Path,
    max_tokens: int = 1024,
    chat_fnames: set[str] | None = None,
    mentioned_idents: set[str] | None = None,
) -> str:
    """Convenience function to generate a repo map.

    Args:
        project_root: Project root directory.
        max_tokens: Maximum tokens.
        chat_fnames: Files in chat context.
        mentioned_idents: Mentioned identifiers.

    Returns:
        Generated map string.
    """
    with RepoMap(project_root, max_tokens=max_tokens) as repo_map:
        return repo_map.generate(
            chat_fnames=chat_fnames,
            mentioned_idents=mentioned_idents,
        )
