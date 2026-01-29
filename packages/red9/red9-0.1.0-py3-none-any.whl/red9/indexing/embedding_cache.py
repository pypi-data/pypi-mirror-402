"""Embedding cache for RAG assistant with incremental updates."""

from __future__ import annotations

import hashlib
import json
import pickle
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from red9.logging import get_logger

if TYPE_CHECKING:
    from red9.indexing.tracker import IndexTracker

logger = get_logger(__name__)

# Cache version - increment when cache format changes
CACHE_VERSION = 1


@dataclass
class CacheMetadata:
    """Metadata about the cached embeddings."""

    version: int = CACHE_VERSION
    embedding_model: str = ""
    chunk_size: int = 512
    chunk_overlap: int = 50
    file_hashes: dict[str, str] = field(default_factory=dict)  # file_path -> content_hash

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CacheMetadata:
        return cls(
            version=data.get("version", 0),
            embedding_model=data.get("embedding_model", ""),
            chunk_size=data.get("chunk_size", 512),
            chunk_overlap=data.get("chunk_overlap", 50),
            file_hashes=data.get("file_hashes", {}),
        )


class EmbeddingCache:
    """Disk-based cache for RAG assistant with incremental updates.

    Stores the pickled RAGAssistant object along with metadata for validation.
    Cache is invalidated when:
    - Cache version changes
    - Embedding model changes
    - Chunk size or overlap changes
    - Any source file is added, modified, or deleted
    """

    def __init__(
        self,
        cache_dir: Path,
        embedding_model: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        """Initialize embedding cache.

        Args:
            cache_dir: Directory to store cache files.
            embedding_model: Name of the embedding model.
            chunk_size: Size of text chunks.
            chunk_overlap: Overlap between chunks.
        """
        self.cache_dir = cache_dir
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Cache file paths
        self.meta_path = cache_dir / "cache_meta.json"
        self.assistant_path = cache_dir / "rag_assistant.pkl"

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_metadata(self) -> CacheMetadata | None:
        """Load cache metadata from disk."""
        if not self.meta_path.exists():
            return None

        try:
            with open(self.meta_path) as f:
                data = json.load(f)
            return CacheMetadata.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to load cache metadata: {e}")
            return None

    def _save_metadata(self, metadata: CacheMetadata) -> None:
        """Save cache metadata to disk."""
        with open(self.meta_path, "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)

    def is_valid(self) -> bool:
        """Check if cache exists and settings match."""
        metadata = self._load_metadata()
        if metadata is None:
            return False

        # Check version
        if metadata.version != CACHE_VERSION:
            logger.info(f"Cache version mismatch: {metadata.version} != {CACHE_VERSION}")
            return False

        # Check settings
        if metadata.embedding_model != self.embedding_model:
            old, new = metadata.embedding_model, self.embedding_model
            logger.info(f"Embedding model changed: {old} -> {new}")
            return False

        if metadata.chunk_size != self.chunk_size:
            logger.info(f"Chunk size changed: {metadata.chunk_size} -> {self.chunk_size}")
            return False

        if metadata.chunk_overlap != self.chunk_overlap:
            logger.info(f"Chunk overlap changed: {metadata.chunk_overlap} -> {self.chunk_overlap}")
            return False

        # Check if assistant file exists
        if not self.assistant_path.exists():
            logger.info("Assistant cache file missing")
            return False

        return True

    def needs_update(
        self, tracker: IndexTracker
    ) -> tuple[bool, list[Path], list[Path], list[Path]]:
        """Check if cache needs update based on file changes.

        Args:
            tracker: IndexTracker with current file state.

        Returns:
            Tuple of (needs_update, added, modified, deleted).
        """
        metadata = self._load_metadata()
        if metadata is None:
            # No cache - need full index
            return True, [], [], []

        # Compare file hashes
        added: list[Path] = []
        modified: list[Path] = []
        deleted: list[Path] = []

        current_files = tracker.get_current_files()
        cached_hashes = metadata.file_hashes

        for file_path, content_hash in current_files.items():
            if file_path not in cached_hashes:
                added.append(Path(file_path))
            elif cached_hashes[file_path] != content_hash:
                modified.append(Path(file_path))

        for file_path in cached_hashes:
            if file_path not in current_files:
                deleted.append(Path(file_path))

        needs_update = bool(added or modified or deleted)
        return needs_update, added, modified, deleted

    def get_cached_assistant(self) -> Any | None:
        """Load cached RAGAssistant from disk.

        Returns:
            RAGAssistant or None if cache is invalid.
        """
        if not self.is_valid():
            return None

        try:
            with open(self.assistant_path, "rb") as f:
                assistant = pickle.load(f)
            logger.info("Loaded RAG assistant from cache")
            return assistant
        except Exception as e:
            logger.warning(f"Failed to load cached assistant: {e}")
            self.invalidate()
            return None

    def save_assistant(self, assistant: Any, file_hashes: dict[str, str]) -> None:
        """Save RAGAssistant to cache.

        Args:
            assistant: RAGAssistant instance to cache.
            file_hashes: Dict mapping file paths to content hashes.
        """
        try:
            # Save assistant
            with open(self.assistant_path, "wb") as f:
                pickle.dump(assistant, f)

            # Save metadata
            metadata = CacheMetadata(
                version=CACHE_VERSION,
                embedding_model=self.embedding_model,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                file_hashes=file_hashes,
            )
            self._save_metadata(metadata)

            logger.info(f"Saved RAG assistant to cache ({len(file_hashes)} files)")
        except Exception as e:
            logger.error(f"Failed to save assistant to cache: {e}")
            self.invalidate()

    def invalidate(self) -> None:
        """Clear the cache."""
        if self.meta_path.exists():
            self.meta_path.unlink()
        if self.assistant_path.exists():
            self.assistant_path.unlink()
        logger.info("Cache invalidated")

    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """Compute content hash for a file."""
        try:
            content = file_path.read_bytes()
            return hashlib.sha256(content).hexdigest()[:16]
        except Exception:
            return ""
