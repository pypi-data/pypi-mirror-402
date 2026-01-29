"""Index manager for embedding management with incremental updates."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from red9.indexing.embedding_cache import EmbeddingCache
from red9.indexing.tracker import IndexTracker
from red9.logging import get_logger

if TYPE_CHECKING:
    from red9.config.schema import Red9Config

logger = get_logger(__name__)


class IndexManager:
    """Manages embedding index with incremental updates.

    Features:
    - Incremental indexing with change tracking
    - Tuned RAG settings from RagitExperiment
    - Direct Q&A via RAGAssistant.ask()
    - Code generation via RAGAssistant.generate_code()
    """

    def __init__(self, project_root: Path, config: Red9Config) -> None:
        """Initialize the index manager.

        Args:
            project_root: Root directory of the project.
            config: RED9 configuration.
        """
        self.project_root = project_root
        self.config = config
        self.red9_dir = project_root / ".red9"
        self.state_path = self.red9_dir / "index_state.json"
        self.tracker = IndexTracker(project_root, self.state_path)
        self._rag_assistant: Any | None = None
        self._last_error: str | None = None  # Track last error for better messaging
        self._tuning_result: Any | None = None  # Cached tuning result

    def has_indexable_files(self) -> bool:
        """Check if project has any files matching index patterns.

        Returns:
            True if there are files to index.
        """
        for pattern in self.config.indexing.include:
            for file_path in self.project_root.glob(pattern):
                if not file_path.is_file():
                    continue
                # Check excludes
                excluded = False
                for exclude in self.config.indexing.exclude:
                    if file_path.match(exclude):
                        excluded = True
                        break
                if not excluded:
                    return True
        return False

    def needs_update(self) -> tuple[bool, int, int, int]:
        """Check if any files changed since last index.

        Returns:
            Tuple of (needs_update, added_count, modified_count, deleted_count).
        """
        added, modified, deleted = self.tracker.get_changed_files(
            patterns=self.config.indexing.include,
            excludes=self.config.indexing.exclude,
        )
        needs_update = bool(added or modified or deleted)
        return needs_update, len(added), len(modified), len(deleted)

    def update_index(self, provider: Any) -> int:
        """Incrementally update embeddings for changed files only.

        Args:
            provider: LLM provider for embeddings (must have embedding capability).

        Returns:
            Number of files updated.
        """
        added, modified, deleted = self.tracker.get_changed_files(
            patterns=self.config.indexing.include,
            excludes=self.config.indexing.exclude,
        )

        if not added and not modified and not deleted:
            return 0

        # Remove deleted files from state
        if deleted:
            self.tracker.remove_from_state(deleted)

        # Update state for added/modified files
        files_to_update = added + modified
        if files_to_update:
            self.tracker.update_state(files_to_update)

        # Save state
        self.tracker.save()

        # Clear cached assistant so it gets rebuilt with new files
        self._rag_assistant = None

        return len(files_to_update) + len(deleted)

    def _get_tuning_result(self) -> Any | None:
        """Get cached or load tuning result.

        Returns:
            TuningResult or None if not tuned.
        """
        if self._tuning_result is not None:
            return self._tuning_result

        try:
            from red9.indexing.tuner import RAGTuner

            tuner = RAGTuner(self.project_root, self.config)
            self._tuning_result = tuner.get_best_result()
            return self._tuning_result
        except Exception:
            return None

    def get_effective_settings(self) -> dict[str, Any]:
        """Get effective RAG settings (tuned or default).

        Returns:
            Dict with chunk_size, chunk_overlap, num_chunks.
        """
        tuning = self._get_tuning_result()

        if tuning:
            return {
                "chunk_size": tuning.chunk_size,
                "chunk_overlap": tuning.chunk_overlap,
                "num_chunks": tuning.num_chunks,
                "source": "tuned",
            }

        return {
            "chunk_size": self.config.indexing.chunk_size,
            "chunk_overlap": self.config.indexing.chunk_overlap,
            "num_chunks": self.config.indexing.num_chunks,
            "source": "config",
        }

    def get_rag_assistant(self, provider: Any) -> Any | None:
        """Get RAGAssistant with current embeddings.

        Uses disk cache for fast loading on subsequent runs.
        Cache is invalidated when files change or settings change.

        Args:
            provider: LLM provider for embeddings (unused, kept for compatibility).

        Returns:
            RAGAssistant or None if not available.
        """
        # Return in-memory cached assistant if available
        if self._rag_assistant is not None:
            return self._rag_assistant

        self._last_error = None  # Reset error state

        try:
            # Get effective settings (tuned or default)
            settings = self.get_effective_settings()
            chunk_size = settings["chunk_size"]
            chunk_overlap = settings["chunk_overlap"]

            # Initialize embedding cache
            cache = EmbeddingCache(
                cache_dir=self.red9_dir / "embeddings",
                embedding_model=self.config.provider.embedding_model,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            # Check if we can use cached assistant (FAST PATH)
            if cache.is_valid():
                # Check if any files changed
                added, modified, deleted = self.tracker.get_changed_files(
                    patterns=self.config.indexing.include,
                    excludes=self.config.indexing.exclude,
                )

                if not (added or modified or deleted):
                    # No changes - load from cache
                    cached_assistant = cache.get_cached_assistant()
                    if cached_assistant is not None:
                        # Inject LLM provider since it's not serializable
                        cached_assistant._llm_provider = self._create_llm_provider()
                        self._rag_assistant = cached_assistant
                        logger.info("RAG loaded from cache (fast path)")
                        return self._rag_assistant
                else:
                    logger.info(
                        f"Cache invalidated: +{len(added)} ~{len(modified)} -{len(deleted)} files"
                    )
                    cache.invalidate()

            # SLOW PATH: Build assistant from scratch
            logger.info("Building RAG assistant (slow path - embedding generation)")
            self._rag_assistant = self._build_rag_assistant(chunk_size, chunk_overlap)

            # Save to cache for next time (BEFORE injecting LLM provider which is not picklable)
            if self._rag_assistant is not None:
                # Update tracker state for all current files
                added, modified, deleted = self.tracker.get_changed_files(
                    patterns=self.config.indexing.include,
                    excludes=self.config.indexing.exclude,
                )
                files_to_track = added + modified
                if files_to_track:
                    self.tracker.update_state(files_to_track)
                if deleted:
                    self.tracker.remove_from_state(deleted)
                self.tracker.save()

                # Save assistant to cache
                cache.save_assistant(self._rag_assistant, self.tracker.get_file_hashes())

                # NOW inject LLM provider (after caching, since it's not picklable)
                self._rag_assistant._llm_provider = self._create_llm_provider()

            return self._rag_assistant

        except ImportError:
            self._last_error = "ragit_not_installed"
            return None
        except Exception as e:
            # Check for common Ollama connection errors
            error_str = str(e).lower()
            if "connection" in error_str or "refused" in error_str:
                self._last_error = "ollama_not_running"
            else:
                self._last_error = f"error: {e}"
            return None

    def _create_llm_provider(self) -> Any:
        """Create an LLM provider for RAGAssistant generation calls.

        Returns:
            A FunctionProvider that provides LLM generation using Ollama.
        """
        import requests
        from ragit.providers.function_adapter import FunctionProvider

        base_url = self.config.provider.base_url.rstrip("/")
        model = self.config.provider.model

        def generate_fn(
            prompt: str,
            system_prompt: str | None = None,
            temperature: float = 0.7,
        ) -> str:
            """Generate text using Ollama."""
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = requests.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")

        return FunctionProvider(generate_fn=generate_fn)

    def _build_rag_assistant(self, chunk_size: int, chunk_overlap: int) -> Any | None:
        """Build RAGAssistant from scratch (slow - generates embeddings).

        Args:
            chunk_size: Size of text chunks.
            chunk_overlap: Overlap between chunks.

        Returns:
            RAGAssistant or None if failed.
        """
        from ragit import RAGAssistant
        from ragit.loaders import chunk_by_separator, load_directory
        from ragit.providers.ollama import OllamaProvider as RagitOllamaProvider

        # Use ragit's OllamaProvider - has batch embedding and LRU cache
        # Use provider's base_url for embeddings (can be local or remote)
        embedding_url = self.config.provider.base_url
        rag_provider = RagitOllamaProvider(
            base_url=embedding_url,
            embedding_url=embedding_url,
        )

        logger.info(f"Using RAG settings: chunk_size={chunk_size}, overlap={chunk_overlap}")

        # Load all documents matching patterns
        logger.info("Loading documents...")
        documents = []
        load_errors = []
        for pattern in self.config.indexing.include:
            try:
                docs = load_directory(str(self.project_root), pattern)
                # Filter by excludes using metadata['source']
                filtered_docs = []
                for doc in docs:
                    source = doc.metadata.get("source", "")
                    excluded = False
                    for exclude in self.config.indexing.exclude:
                        if Path(source).match(exclude):
                            excluded = True
                            break
                    if not excluded:
                        filtered_docs.append(doc)
                documents.extend(filtered_docs)
            except Exception as e:
                load_errors.append(f"{pattern}: {e}")
                continue

        if not documents:
            if load_errors:
                self._last_error = f"load_failed: {'; '.join(load_errors)}"
            else:
                self._last_error = "no_documents"
            return None

        # Limit documents for performance
        if len(documents) > 200:
            logger.warning(f"Limiting to 200 documents (had {len(documents)})")
            documents = documents[:200]

        logger.info(f"Loaded {len(documents)} documents, generating embeddings...")

        # Use code-aware chunking if separator is configured
        chunks = None
        if self.config.indexing.chunk_separator:
            try:
                all_chunks = []
                for doc in documents:
                    doc_chunks = chunk_by_separator(
                        doc.content,
                        separator=self.config.indexing.chunk_separator,
                        max_chunk_size=chunk_size,
                    )
                    all_chunks.extend(doc_chunks)
                if all_chunks:
                    chunks = all_chunks
            except Exception as e:
                logger.warning(f"Code-aware chunking failed, using default: {e}")

        # Create assistant with effective settings
        # Try with chunks parameter first, fallback without it for older ragit versions
        try:
            if chunks is not None:
                assistant = RAGAssistant(
                    chunks=chunks,
                    provider=rag_provider,
                    embedding_model=self.config.provider.embedding_model,
                    llm_model=self.config.provider.model,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
            else:
                assistant = RAGAssistant(
                    documents=documents,
                    provider=rag_provider,
                    embedding_model=self.config.provider.embedding_model,
                    llm_model=self.config.provider.model,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
            # Note: LLM provider is injected by get_rag_assistant() AFTER caching
            return assistant
        except TypeError as e:
            # Fallback for older ragit versions that don't support chunks
            if "chunks" in str(e):
                logger.warning("Ragit doesn't support 'chunks' parameter, using documents only")
                assistant = RAGAssistant(
                    documents=documents,
                    provider=rag_provider,
                    embedding_model=self.config.provider.embedding_model,
                    llm_model=self.config.provider.model,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
                # Note: LLM provider is injected by get_rag_assistant() AFTER caching
                return assistant
            else:
                raise

    def ask(self, question: str, top_k: int | None = None) -> str | None:
        """Ask a question using RAG.

        Uses RAGAssistant.ask() for direct Q&A with retrieved context.

        Args:
            question: Question to ask about the codebase.
            top_k: Number of chunks to retrieve (uses tuned/config if None).

        Returns:
            Answer string or None if unavailable.
        """
        assistant = self.get_rag_assistant(provider=None)
        if assistant is None:
            return None

        if top_k is None:
            settings = self.get_effective_settings()
            top_k = settings["num_chunks"]

        try:
            return assistant.ask(question, top_k=top_k)
        except Exception as e:
            logger.error(f"RAG ask failed: {e}")
            return None

    def generate_code(
        self,
        prompt: str,
        language: str = "python",
        top_k: int | None = None,
    ) -> str | None:
        """Generate code using RAG context.

        Uses RAGAssistant.generate_code() for code generation with
        retrieved context from the codebase.

        Args:
            prompt: Code generation prompt.
            language: Target programming language.
            top_k: Number of chunks to retrieve (uses tuned/config if None).

        Returns:
            Generated code string or None if unavailable.
        """
        assistant = self.get_rag_assistant(provider=None)
        if assistant is None:
            return None

        if top_k is None:
            settings = self.get_effective_settings()
            top_k = settings["num_chunks"]

        try:
            return assistant.generate_code(prompt, language=language, top_k=top_k)
        except Exception as e:
            logger.error(f"RAG generate_code failed: {e}")
            return None

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[tuple[Any, float]]:
        """Retrieve relevant chunks for a query.

        Args:
            query: Search query.
            top_k: Number of results (uses tuned/config if None).

        Returns:
            List of (chunk, score) tuples.
        """
        assistant = self.get_rag_assistant(provider=None)
        if assistant is None:
            return []

        if top_k is None:
            settings = self.get_effective_settings()
            top_k = settings["num_chunks"]

        try:
            return assistant.retrieve(query, top_k=top_k)
        except Exception as e:
            logger.error(f"RAG retrieve failed: {e}")
            return []

    def get_context(self, query: str, top_k: int | None = None) -> str:
        """Get formatted context for a query.

        Args:
            query: Search query.
            top_k: Number of chunks to include (uses tuned/config if None).

        Returns:
            Formatted context string.
        """
        assistant = self.get_rag_assistant(provider=None)
        if assistant is None:
            return ""

        if top_k is None:
            settings = self.get_effective_settings()
            top_k = settings["num_chunks"]

        try:
            return assistant.get_context(query, top_k=top_k)
        except Exception as e:
            logger.error(f"RAG get_context failed: {e}")
            return ""

    def get_last_error(self) -> str | None:
        """Get the last error that occurred during RAG initialization.

        Returns:
            Error string or None if no error.
        """
        return self._last_error

    def full_reindex(self, provider: Any) -> int:
        """Perform a full reindex of all files.

        Args:
            provider: LLM provider for embeddings.

        Returns:
            Number of files indexed.
        """
        # Clear existing state
        self.tracker.clear()

        # Collect all matching files
        all_files: list[Path] = []
        for pattern in self.config.indexing.include:
            for file_path in self.project_root.glob(pattern):
                if not file_path.is_file():
                    continue
                excluded = False
                for exclude in self.config.indexing.exclude:
                    if file_path.match(exclude):
                        excluded = True
                        break
                if not excluded:
                    all_files.append(file_path)

        # Update tracker state
        if all_files:
            self.tracker.update_state(all_files)
            self.tracker.save()

        # Clear cached assistant
        self._rag_assistant = None

        return len(all_files)
