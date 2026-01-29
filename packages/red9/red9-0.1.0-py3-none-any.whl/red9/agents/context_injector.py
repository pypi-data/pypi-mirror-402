"""Context Injection Middleware.

Detects and injects directory-specific context into agent prompts.
Supports AGENTS.md, CLAUDE.md, README.md, and .context.md files.

This middleware allows projects to provide directory-specific guidance
that agents will automatically incorporate into their prompts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from red9.logging import get_logger

logger = get_logger(__name__)


# Priority order for context files (first found wins)
CONTEXT_FILES = [
    "AGENTS.md",  # Agent-specific instructions (highest priority)
    "CLAUDE.md",  # Claude Code style instructions
    ".context.md",  # Hidden context file
    "README.md",  # Fallback to README
]

# Maximum content size to inject (to avoid token bloat)
MAX_CONTEXT_SIZE = 4000


class ContextInjector:
    """Detects and injects directory-specific context into agent prompts.

    Scans directories for context files and incorporates their content
    into agent system prompts for better project-aware behavior.
    """

    def __init__(
        self,
        project_root: Path,
        context_files: list[str] | None = None,
        max_context_size: int = MAX_CONTEXT_SIZE,
    ) -> None:
        """Initialize the context injector.

        Args:
            project_root: Root directory of the project.
            context_files: List of context file names to search for.
            max_context_size: Maximum size of context to inject.
        """
        self.project_root = project_root.resolve()
        self.context_files = context_files or CONTEXT_FILES
        self.max_context_size = max_context_size
        self._cache: dict[str, str] = {}

    def get_context_for_directory(self, directory: Path) -> str:
        """Get context content for a specific directory.

        Searches for context files in the directory and returns the content
        of the first one found.

        Args:
            directory: Directory to search for context files.

        Returns:
            Content of the context file, or empty string if none found.
        """
        # Normalize path
        if not directory.is_absolute():
            directory = self.project_root / directory

        # Check cache
        cache_key = str(directory)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Search for context files
        for filename in self.context_files:
            context_path = directory / filename
            if context_path.exists() and context_path.is_file():
                try:
                    content = context_path.read_text(encoding="utf-8")
                    # Truncate if necessary
                    if len(content) > self.max_context_size:
                        content = content[: self.max_context_size] + "\n\n[Truncated...]"
                    self._cache[cache_key] = content
                    logger.debug(f"Found context file: {context_path}")
                    return content
                except Exception as e:
                    logger.warning(f"Failed to read context file {context_path}: {e}")

        # No context file found
        self._cache[cache_key] = ""
        return ""

    def get_context_chain(self, directory: Path) -> list[tuple[Path, str]]:
        """Get context from a directory and all its parents up to project root.

        Returns context files from most specific (directory) to least specific
        (project root), allowing for layered context injection.

        Args:
            directory: Starting directory.

        Returns:
            List of (path, content) tuples for each directory with context.
        """
        contexts: list[tuple[Path, str]] = []

        # Normalize path
        if not directory.is_absolute():
            directory = self.project_root / directory

        # Walk up from directory to project root
        current = directory
        while current >= self.project_root:
            content = self.get_context_for_directory(current)
            if content:
                contexts.append((current, content))

            # Move up one level
            parent = current.parent
            if parent == current:
                break
            current = parent

        # Return in order from root to most specific
        return list(reversed(contexts))

    def inject_into_prompt(
        self,
        prompt: str,
        current_dir: Path | None = None,
        include_chain: bool = False,
    ) -> str:
        """Inject directory context into an agent prompt.

        Args:
            prompt: Original system prompt.
            current_dir: Current working directory (defaults to project root).
            include_chain: If True, include context from all parent directories.

        Returns:
            Modified prompt with context injected.
        """
        if current_dir is None:
            current_dir = self.project_root

        if include_chain:
            # Get context chain from root to current directory
            chain = self.get_context_chain(current_dir)
            if not chain:
                return prompt

            # Build combined context
            context_parts = []
            for path, content in chain:
                rel_path = path.relative_to(self.project_root)
                if rel_path == Path("."):
                    header = "Project Root"
                else:
                    header = str(rel_path)
                context_parts.append(f"### {header}\n\n{content}")

            combined_context = "\n\n---\n\n".join(context_parts)
        else:
            # Just get context for the current directory
            combined_context = self.get_context_for_directory(current_dir)
            if not combined_context:
                return prompt

        # Inject into prompt
        return f"{prompt}\n\n## Directory-Specific Context\n\n{combined_context}"

    def get_relevant_context_for_files(
        self,
        file_paths: list[str | Path],
    ) -> dict[str, str]:
        """Get relevant context for a set of files.

        Groups files by their containing directories and returns context
        for each unique directory.

        Args:
            file_paths: List of file paths to analyze.

        Returns:
            Dictionary mapping directory paths to their context content.
        """
        contexts: dict[str, str] = {}

        # Collect unique directories
        directories: set[Path] = set()
        for file_path in file_paths:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            if not file_path.is_absolute():
                file_path = self.project_root / file_path
            directories.add(file_path.parent)

        # Get context for each directory
        for directory in directories:
            content = self.get_context_for_directory(directory)
            if content:
                rel_path = directory.relative_to(self.project_root)
                contexts[str(rel_path)] = content

        return contexts

    def clear_cache(self) -> None:
        """Clear the context cache."""
        self._cache.clear()

    def to_dict(self) -> dict[str, Any]:
        """Get diagnostic information about cached contexts.

        Returns:
            Dictionary with cache statistics.
        """
        return {
            "project_root": str(self.project_root),
            "context_files": self.context_files,
            "max_context_size": self.max_context_size,
            "cached_directories": len(self._cache),
            "directories_with_context": sum(1 for v in self._cache.values() if v),
        }


def create_context_injector(project_root: Path) -> ContextInjector:
    """Factory function to create a context injector.

    Args:
        project_root: Project root directory.

    Returns:
        Configured ContextInjector instance.
    """
    return ContextInjector(project_root)
