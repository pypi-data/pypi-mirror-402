"""RAG tuner using RagitExperiment for hyperparameter optimization.

Automatically optimizes RAG settings for the codebase using LLM-as-judge
evaluation.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from red9.logging import get_logger

if TYPE_CHECKING:
    from red9.config.schema import Red9Config

logger = get_logger(__name__)


@dataclass
class TuningResult:
    """Result from RAG tuning optimization."""

    chunk_size: int
    chunk_overlap: int
    num_chunks: int
    embedding_model: str
    llm_model: str
    final_score: float
    scores: dict[str, float] = field(default_factory=dict)
    execution_time: float = 0.0
    tuned_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TuningResult:
        """Create from dictionary."""
        return cls(
            chunk_size=data["chunk_size"],
            chunk_overlap=data["chunk_overlap"],
            num_chunks=data["num_chunks"],
            embedding_model=data["embedding_model"],
            llm_model=data["llm_model"],
            final_score=data["final_score"],
            scores=data.get("scores", {}),
            execution_time=data.get("execution_time", 0.0),
            tuned_at=data.get("tuned_at", ""),
        )


@dataclass
class TuningState:
    """Persistent tuning state."""

    version: int = 1
    best_result: TuningResult | None = None
    all_results: list[TuningResult] = field(default_factory=list)
    benchmark_questions: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "best_result": self.best_result.to_dict() if self.best_result else None,
            "all_results": [r.to_dict() for r in self.all_results],
            "benchmark_questions": self.benchmark_questions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TuningState:
        """Create from dictionary."""
        best_result = None
        if data.get("best_result"):
            best_result = TuningResult.from_dict(data["best_result"])

        return cls(
            version=data.get("version", 1),
            best_result=best_result,
            all_results=[TuningResult.from_dict(r) for r in data.get("all_results", [])],
            benchmark_questions=data.get("benchmark_questions", []),
        )


class RAGTuner:
    """Optimizes RAG hyperparameters using RagitExperiment.

    Automatically generates benchmark questions from the codebase and
    uses LLM-as-judge to find optimal settings for:
    - chunk_size
    - chunk_overlap
    - num_chunks (top_k for retrieval)
    """

    def __init__(self, project_root: Path, config: Red9Config) -> None:
        """Initialize the RAG tuner.

        Args:
            project_root: Root directory of the project.
            config: RED9 configuration.
        """
        self.project_root = project_root
        self.config = config
        self.red9_dir = project_root / ".red9"
        self.state_path = self.red9_dir / "tuning_state.json"
        self._state: TuningState | None = None

    def _load_state(self) -> TuningState:
        """Load tuning state from disk."""
        if not self.state_path.exists():
            return TuningState()

        try:
            data = json.loads(self.state_path.read_text())
            return TuningState.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to load tuning state: {e}")
            return TuningState()

    def _save_state(self) -> None:
        """Persist tuning state to disk."""
        if self._state is None:
            return

        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self._state.to_dict(), indent=2))

    def get_best_result(self) -> TuningResult | None:
        """Get the best tuning result if available.

        Returns:
            Best TuningResult or None if not tuned.
        """
        if self._state is None:
            self._state = self._load_state()
        return self._state.best_result

    def has_tuning(self) -> bool:
        """Check if tuning has been performed.

        Returns:
            True if tuning results exist.
        """
        return self.get_best_result() is not None

    def _collect_documents(self) -> list[Any]:
        """Collect documents from the codebase.

        Returns:
            List of ragit Document objects.
        """
        from ragit import Document

        documents: list[Document] = []

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

                if excluded:
                    continue

                try:
                    content = file_path.read_text(errors="ignore")
                    if content.strip():
                        rel_path = str(file_path.relative_to(self.project_root))
                        documents.append(
                            Document(
                                id=rel_path,
                                content=content,
                                metadata={"source": rel_path},
                            )
                        )
                except Exception as e:
                    logger.debug(f"Failed to read {file_path}: {e}")
                    continue

        return documents

    def _generate_benchmark(
        self,
        documents: list[Any],
        num_questions: int = 5,
    ) -> list[Any]:
        """Generate benchmark questions from the codebase using LLM.

        Args:
            documents: List of ragit Document objects.
            num_questions: Number of benchmark questions to generate.

        Returns:
            List of ragit BenchmarkQuestion objects.
        """
        from ragit import BenchmarkQuestion
        from ragit.providers import OllamaProvider

        if not documents:
            return []

        provider = OllamaProvider(base_url=self.config.provider.base_url)

        # Sample documents for benchmark generation (limit to avoid token overflow)
        sample_docs = documents[:10]
        doc_summaries = []
        for doc in sample_docs:
            # Take first 500 chars of each doc
            content_preview = doc.content[:500]
            doc_summaries.append(f"File: {doc.id}\n{content_preview}")

        context = "\n\n---\n\n".join(doc_summaries)

        prompt = f"""Analyze this codebase and generate {num_questions} technical questions
that could be answered by searching the code. For each question, provide:
1. A natural language question about the code
2. A ground truth answer based on the code content

Format your response as JSON array:
[
  {{"question": "...", "ground_truth": "...", "relevant_files": ["file1.py"]}},
  ...
]

Codebase sample:
{context}

Generate questions about:
- Function implementations
- Class structures
- Configuration patterns
- Error handling
- API usage

JSON response:"""

        try:
            response = provider.generate(
                prompt=prompt,
                model=self.config.provider.model,
                temperature=0.7,
            )

            # Parse JSON from response
            text = response.text.strip()
            # Find JSON array in response
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                questions_data = json.loads(json_str)

                benchmarks = []
                for q in questions_data[:num_questions]:
                    benchmarks.append(
                        BenchmarkQuestion(
                            question=q["question"],
                            ground_truth=q["ground_truth"],
                            relevant_doc_ids=q.get("relevant_files", []),
                        )
                    )
                return benchmarks

        except Exception as e:
            logger.warning(f"Failed to generate benchmarks via LLM: {e}")

        # Fallback: generate simple benchmarks from doc names
        return self._generate_fallback_benchmarks(documents, num_questions)

    def _generate_fallback_benchmarks(
        self,
        documents: list[Any],
        num_questions: int,
    ) -> list[Any]:
        """Generate simple fallback benchmarks without LLM.

        Args:
            documents: List of ragit Document objects.
            num_questions: Number of benchmark questions to generate.

        Returns:
            List of ragit BenchmarkQuestion objects.
        """
        from ragit import BenchmarkQuestion

        benchmarks = []

        for doc in documents[:num_questions]:
            # Extract first function or class from Python files
            content = doc.content
            if doc.id.endswith(".py"):
                # Simple extraction of first function/class
                for line in content.split("\n"):
                    if line.startswith("def ") or line.startswith("class "):
                        name = line.split("(")[0].split()[1] if "(" in line else ""
                        if name:
                            benchmarks.append(
                                BenchmarkQuestion(
                                    question=f"What does {name} do in {doc.id}?",
                                    ground_truth=f"{name} is defined in {doc.id}",
                                    relevant_doc_ids=[doc.id],
                                )
                            )
                            break
            else:
                # Generic question for non-Python files
                benchmarks.append(
                    BenchmarkQuestion(
                        question=f"What is the purpose of {doc.id}?",
                        ground_truth=f"{doc.id} contains project code",
                        relevant_doc_ids=[doc.id],
                    )
                )

            if len(benchmarks) >= num_questions:
                break

        return benchmarks

    def tune(
        self,
        chunk_sizes: list[int] | None = None,
        chunk_overlaps: list[int] | None = None,
        num_chunks_options: list[int] | None = None,
        num_questions: int = 5,
        max_configs: int | None = None,
        verbose: bool = True,
    ) -> TuningResult | None:
        """Run RAG hyperparameter optimization.

        Args:
            chunk_sizes: Chunk sizes to test (default: [256, 512, 1024]).
            chunk_overlaps: Chunk overlaps to test (default: [50, 100]).
            num_chunks_options: Number of chunks/top_k to test (default: [3, 5, 7]).
            num_questions: Number of benchmark questions to generate.
            max_configs: Maximum number of configurations to test.
            verbose: Print progress information.

        Returns:
            Best TuningResult or None if tuning failed.
        """
        from ragit import RagitExperiment
        from ragit.providers import OllamaProvider

        # Initialize state
        self._state = self._load_state()

        # Default search space optimized for code
        chunk_sizes = chunk_sizes or [256, 512, 1024]
        chunk_overlaps = chunk_overlaps or [50, 100]
        num_chunks_options = num_chunks_options or [3, 5, 7]

        # Collect documents
        if verbose:
            logger.info("Collecting documents from codebase...")
        documents = self._collect_documents()

        if not documents:
            logger.error("No documents found to tune on")
            return None

        if verbose:
            logger.info(f"Found {len(documents)} documents")

        # Limit documents for faster tuning
        if len(documents) > 50:
            documents = documents[:50]
            if verbose:
                logger.info(f"Limited to {len(documents)} documents for tuning")

        # Generate or reuse benchmarks
        if self._state.benchmark_questions:
            if verbose:
                logger.info(f"Reusing {len(self._state.benchmark_questions)} cached benchmarks")
            from ragit import BenchmarkQuestion

            benchmarks = [
                BenchmarkQuestion(
                    question=q["question"],
                    ground_truth=q["ground_truth"],
                    relevant_doc_ids=q.get("relevant_doc_ids", []),
                )
                for q in self._state.benchmark_questions
            ]
        else:
            if verbose:
                logger.info(f"Generating {num_questions} benchmark questions...")
            benchmarks = self._generate_benchmark(documents, num_questions)
            # Cache benchmarks
            self._state.benchmark_questions = [
                {
                    "question": b.question,
                    "ground_truth": b.ground_truth,
                    "relevant_doc_ids": b.relevant_doc_ids,
                }
                for b in benchmarks
            ]

        if not benchmarks:
            logger.error("Failed to generate benchmarks")
            return None

        if verbose:
            logger.info(f"Using {len(benchmarks)} benchmark questions")

        # Create experiment
        try:
            provider = OllamaProvider(base_url=self.config.provider.base_url)

            experiment = RagitExperiment(
                documents=documents,
                benchmark=benchmarks,
                provider=provider,
            )

            # Define search space
            configs = experiment.define_search_space(
                chunk_sizes=chunk_sizes,
                chunk_overlaps=chunk_overlaps,
                num_chunks_options=num_chunks_options,
                embedding_models=[self.config.provider.embedding_model],
                llm_models=[self.config.provider.model],
            )

            if verbose:
                logger.info(f"Testing {len(configs)} configurations...")

            # Run optimization
            results = experiment.run(
                configs=configs,
                max_configs=max_configs,
                verbose=verbose,
            )

            if not results:
                logger.error("No results from tuning")
                return None

            # Get best result
            best = results[0]
            best_tuning = TuningResult(
                chunk_size=best.indexing_params["chunk_size"],
                chunk_overlap=best.indexing_params["chunk_overlap"],
                num_chunks=best.inference_params["num_chunks"],
                embedding_model=best.indexing_params["embedding_model"],
                llm_model=best.inference_params["llm_model"],
                final_score=best.final_score,
                scores={
                    "answer_correctness": best.scores["answer_correctness"]["mean"],
                    "context_relevance": best.scores["context_relevance"]["mean"],
                    "faithfulness": best.scores["faithfulness"]["mean"],
                },
                execution_time=best.execution_time,
                tuned_at=datetime.now().isoformat(),
            )

            # Store all results
            all_tuning_results = []
            for r in results:
                all_tuning_results.append(
                    TuningResult(
                        chunk_size=r.indexing_params["chunk_size"],
                        chunk_overlap=r.indexing_params["chunk_overlap"],
                        num_chunks=r.inference_params["num_chunks"],
                        embedding_model=r.indexing_params["embedding_model"],
                        llm_model=r.inference_params["llm_model"],
                        final_score=r.final_score,
                        scores={
                            "answer_correctness": r.scores["answer_correctness"]["mean"],
                            "context_relevance": r.scores["context_relevance"]["mean"],
                            "faithfulness": r.scores["faithfulness"]["mean"],
                        },
                        execution_time=r.execution_time,
                        tuned_at=datetime.now().isoformat(),
                    )
                )

            # Update state
            self._state.best_result = best_tuning
            self._state.all_results = all_tuning_results
            self._save_state()

            if verbose:
                logger.info(f"Best configuration: score={best_tuning.final_score:.3f}")
                logger.info(
                    f"  chunk_size={best_tuning.chunk_size}, "
                    f"overlap={best_tuning.chunk_overlap}, "
                    f"num_chunks={best_tuning.num_chunks}"
                )

            return best_tuning

        except ImportError as e:
            logger.error(f"ragit not installed: {e}")
            return None
        except Exception as e:
            logger.error(f"Tuning failed: {e}")
            return None

    def apply_to_config(self, result: TuningResult | None = None) -> bool:
        """Apply tuning result to the RED9 config file.

        Args:
            result: TuningResult to apply (uses best if None).

        Returns:
            True if config was updated.
        """
        import yaml

        if result is None:
            result = self.get_best_result()

        if result is None:
            logger.warning("No tuning result to apply")
            return False

        config_path = self.red9_dir / "config.yaml"

        if not config_path.exists():
            logger.error("Config file not found")
            return False

        try:
            config_data = yaml.safe_load(config_path.read_text())

            # Update indexing settings
            if "indexing" not in config_data:
                config_data["indexing"] = {}

            config_data["indexing"]["chunk_size"] = result.chunk_size
            config_data["indexing"]["chunk_overlap"] = result.chunk_overlap
            config_data["indexing"]["num_chunks"] = result.num_chunks

            # Write back
            config_path.write_text(yaml.dump(config_data, default_flow_style=False))

            logger.info("Applied tuning result to config.yaml")
            return True

        except Exception as e:
            logger.error(f"Failed to apply tuning to config: {e}")
            return False

    def clear(self) -> None:
        """Clear all tuning state."""
        self._state = TuningState()
        if self.state_path.exists():
            self.state_path.unlink()
