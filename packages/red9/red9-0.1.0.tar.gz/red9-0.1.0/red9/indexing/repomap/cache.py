"""RepoMap cache module - SQLite-backed caching for tag extraction.

Based on aider's caching pattern:
- Uses diskcache (SQLite-backed) for persistent per-file tag caching
- Cache key: filename, invalidation by mtime
- Graceful fallback to in-memory dict on SQLite errors
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from red9.logging import get_logger

if TYPE_CHECKING:
    from diskcache import Cache

logger = get_logger(__name__)

# Cache version - bump when tag format changes
CACHE_VERSION = 1
TAGS_CACHE_DIR = ".red9.tags.cache.v{version}"


class TagCache:
    """SQLite-backed cache for AST tags with mtime invalidation.

    Provides fast lookup of previously extracted tags, avoiding expensive
    tree-sitter parsing on unchanged files.
    """

    def __init__(self, project_root: Path, cache_dir: str | None = None) -> None:
        """Initialize tag cache.

        Args:
            project_root: Project root directory.
            cache_dir: Optional custom cache directory name.
        """
        self.project_root = project_root
        self._cache: Cache | dict[str, Any] | None = None
        self._use_disk_cache = True

        # Determine cache directory
        if cache_dir:
            self._cache_dir = project_root / cache_dir
        else:
            self._cache_dir = project_root / TAGS_CACHE_DIR.format(version=CACHE_VERSION)

        self._init_cache()

    def _init_cache(self) -> None:
        """Initialize the cache, falling back to memory dict on errors."""
        try:
            from diskcache import Cache

            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache = Cache(str(self._cache_dir))
            self._use_disk_cache = True
            logger.debug(f"TagCache initialized at {self._cache_dir}")
        except Exception as e:
            logger.warning(f"Failed to initialize diskcache, using memory dict: {e}")
            self._cache = {}
            self._use_disk_cache = False

    def get(self, filepath: Path) -> list[dict[str, Any]] | None:
        """Get cached tags for a file if valid.

        Args:
            filepath: Path to the file.

        Returns:
            List of tag dicts if cache is valid, None if miss or stale.
        """
        if self._cache is None:
            return None

        try:
            # Get current mtime
            current_mtime = filepath.stat().st_mtime
        except OSError:
            return None

        cache_key = self._make_key(filepath)

        try:
            if self._use_disk_cache:
                cached = self._cache.get(cache_key)
            else:
                cached = self._cache.get(cache_key)

            if cached is None:
                return None

            # Check if mtime matches
            cached_mtime = cached.get("mtime")
            if cached_mtime != current_mtime:
                # Stale cache entry
                return None

            return cached.get("tags")

        except Exception as e:
            logger.debug(f"Cache get failed for {filepath}: {e}")
            return None

    def set(self, filepath: Path, tags: list[dict[str, Any]]) -> None:
        """Cache tags for a file.

        Args:
            filepath: Path to the file.
            tags: List of tag dicts to cache.
        """
        if self._cache is None:
            return

        try:
            current_mtime = filepath.stat().st_mtime
        except OSError:
            return

        cache_key = self._make_key(filepath)
        cache_value = {
            "mtime": current_mtime,
            "tags": tags,
        }

        try:
            if self._use_disk_cache:
                self._cache.set(cache_key, cache_value)
            else:
                self._cache[cache_key] = cache_value
        except Exception as e:
            logger.debug(f"Cache set failed for {filepath}: {e}")

    def invalidate(self, filepath: Path) -> None:
        """Invalidate cache entry for a file.

        Args:
            filepath: Path to the file.
        """
        if self._cache is None:
            return

        cache_key = self._make_key(filepath)

        try:
            if self._use_disk_cache:
                self._cache.delete(cache_key)
            else:
                self._cache.pop(cache_key, None)
        except Exception as e:
            logger.debug(f"Cache invalidate failed for {filepath}: {e}")

    def clear(self) -> None:
        """Clear all cache entries."""
        if self._cache is None:
            return

        try:
            if self._use_disk_cache:
                self._cache.clear()
            else:
                self._cache.clear()
            logger.debug("TagCache cleared")
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")

    def _make_key(self, filepath: Path) -> str:
        """Create cache key from filepath.

        Uses relative path from project root for portability.

        Args:
            filepath: Path to the file.

        Returns:
            Cache key string.
        """
        try:
            rel_path = filepath.relative_to(self.project_root)
        except ValueError:
            rel_path = filepath

        return str(rel_path)

    def close(self) -> None:
        """Close the cache (for diskcache cleanup)."""
        if self._cache is not None and self._use_disk_cache:
            try:
                self._cache.close()
            except Exception:
                pass

    def __enter__(self) -> TagCache:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class TreeContextCache:
    """In-memory cache for rendered tree contexts.

    Caches TreeContext objects by (filename, lines_of_interest, mtime) to avoid
    re-rendering the same file multiple times.
    """

    def __init__(self) -> None:
        """Initialize tree context cache."""
        self._cache: dict[tuple[str, tuple[int, ...], float], Any] = {}

    def get(
        self,
        filepath: Path,
        lines_of_interest: tuple[int, ...],
    ) -> Any | None:
        """Get cached tree context.

        Args:
            filepath: Path to the file.
            lines_of_interest: Tuple of line numbers.

        Returns:
            Cached TreeContext or None.
        """
        try:
            mtime = filepath.stat().st_mtime
        except OSError:
            return None

        key = (str(filepath), lines_of_interest, mtime)
        return self._cache.get(key)

    def set(
        self,
        filepath: Path,
        lines_of_interest: tuple[int, ...],
        tree_context: Any,
    ) -> None:
        """Cache a tree context.

        Args:
            filepath: Path to the file.
            lines_of_interest: Tuple of line numbers.
            tree_context: TreeContext object to cache.
        """
        try:
            mtime = filepath.stat().st_mtime
        except OSError:
            return

        key = (str(filepath), lines_of_interest, mtime)
        self._cache[key] = tree_context

    def clear(self) -> None:
        """Clear all cached tree contexts."""
        self._cache.clear()


class MapCache:
    """In-memory cache for generated repo maps.

    Caches the final rendered map by (chat_files, other_files, max_tokens).
    """

    def __init__(self) -> None:
        """Initialize map cache."""
        self._cache: dict[str, tuple[str, float]] = {}

    def get(
        self,
        chat_fnames: frozenset[str],
        other_fnames: frozenset[str],
        max_tokens: int,
    ) -> str | None:
        """Get cached map.

        Args:
            chat_fnames: Frozenset of chat file names.
            other_fnames: Frozenset of other file names.
            max_tokens: Maximum tokens for the map.

        Returns:
            Cached map string or None.
        """
        key = self._make_key(chat_fnames, other_fnames, max_tokens)
        entry = self._cache.get(key)

        if entry is None:
            return None

        # Entry is (map_string, generation_time)
        return entry[0]

    def set(
        self,
        chat_fnames: frozenset[str],
        other_fnames: frozenset[str],
        max_tokens: int,
        map_string: str,
        generation_time: float,
    ) -> None:
        """Cache a generated map.

        Args:
            chat_fnames: Frozenset of chat file names.
            other_fnames: Frozenset of other file names.
            max_tokens: Maximum tokens for the map.
            map_string: The generated map string.
            generation_time: Time taken to generate (for auto-cache decisions).
        """
        key = self._make_key(chat_fnames, other_fnames, max_tokens)
        self._cache[key] = (map_string, generation_time)

    def should_use_cache(
        self,
        chat_fnames: frozenset[str],
        other_fnames: frozenset[str],
        max_tokens: int,
    ) -> bool:
        """Check if cache should be used (based on generation time).

        Uses cache if previous generation took > 1 second.

        Args:
            chat_fnames: Frozenset of chat file names.
            other_fnames: Frozenset of other file names.
            max_tokens: Maximum tokens for the map.

        Returns:
            True if cache should be used.
        """
        key = self._make_key(chat_fnames, other_fnames, max_tokens)
        entry = self._cache.get(key)

        if entry is None:
            return False

        # Use cache if generation took > 1 second
        return entry[1] > 1.0

    def clear(self) -> None:
        """Clear all cached maps."""
        self._cache.clear()

    def _make_key(
        self,
        chat_fnames: frozenset[str],
        other_fnames: frozenset[str],
        max_tokens: int,
    ) -> str:
        """Create cache key.

        Args:
            chat_fnames: Frozenset of chat file names.
            other_fnames: Frozenset of other file names.
            max_tokens: Maximum tokens.

        Returns:
            Cache key string.
        """
        # Sort for deterministic key
        chat_sorted = tuple(sorted(chat_fnames))
        other_sorted = tuple(sorted(other_fnames))
        return f"{hash((chat_sorted, other_sorted, max_tokens))}"
