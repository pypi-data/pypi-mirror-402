"""RED9 tune command for RAG hyperparameter optimization."""

from __future__ import annotations

from pathlib import Path

from red9.cli.output import (
    console,
    create_status,
    print_error,
    print_info,
    print_step,
    print_success,
    print_warning,
)
from red9.config import config_exists, load_config


def run_tune(
    apply: bool,
    questions: int,
    max_configs: int | None,
    quick: bool,
    verbose: bool,
) -> None:
    """Run RAG hyperparameter optimization.

    Args:
        apply: Apply best result to config.yaml.
        questions: Number of benchmark questions to generate.
        max_configs: Maximum configurations to test.
        quick: Use quick mode with fewer configurations.
        verbose: Show detailed progress.
    """
    project_root = Path.cwd()

    # Check initialization
    if not config_exists(project_root):
        print_error("RED9 not initialized. Run 'red9 init' first.")
        return

    config = load_config(project_root)

    console.print("\n[bold]RAG Hyperparameter Optimization[/bold]\n")

    # Import tuner
    try:
        from red9.indexing.tuner import RAGTuner
    except ImportError as e:
        print_error(f"Failed to import tuner: {e}")
        return

    tuner = RAGTuner(project_root, config)

    # Check for existing tuning
    existing = tuner.get_best_result()
    if existing:
        print_info(f"Previous tuning found (score: {existing.final_score:.3f})")
        print_info(
            f"  chunk_size={existing.chunk_size}, "
            f"overlap={existing.chunk_overlap}, "
            f"num_chunks={existing.num_chunks}"
        )
        rerun = console.input("[yellow]?[/yellow] Re-run tuning? [y/N]: ").strip().lower()
        if rerun != "y":
            if apply and not _is_config_tuned(config, existing):
                print_step(1, 1, "Applying existing tuning to config...")
                if tuner.apply_to_config(existing):
                    print_success("Config updated with tuned settings")
            return

    # Configure search space
    if quick:
        chunk_sizes = [512]
        chunk_overlaps = [50]
        num_chunks_options = [3, 5]
        max_configs = max_configs or 2
        print_info("Quick mode: testing minimal configurations")
    else:
        chunk_sizes = [256, 512, 1024]
        chunk_overlaps = [50, 100]
        num_chunks_options = [3, 5, 7]

    # Run tuning
    print_step(1, 3 if apply else 2, "Running optimization experiment...")
    console.print()

    try:
        with create_status("Collecting documents and generating benchmarks..."):
            pass  # Status will be shown by tuner

        result = tuner.tune(
            chunk_sizes=chunk_sizes,
            chunk_overlaps=chunk_overlaps,
            num_chunks_options=num_chunks_options,
            num_questions=questions,
            max_configs=max_configs,
            verbose=verbose,
        )
    except Exception as e:
        print_error(f"Tuning failed: {e}")
        return

    if not result:
        print_error("No results from tuning")
        return

    # Show results
    print_step(2, 3 if apply else 2, "Best configuration found")
    console.print()
    console.print(f"  [bold]Final Score:[/bold] {result.final_score:.3f}")
    console.print(f"  [bold]Chunk Size:[/bold] {result.chunk_size}")
    console.print(f"  [bold]Chunk Overlap:[/bold] {result.chunk_overlap}")
    console.print(f"  [bold]Num Chunks (top_k):[/bold] {result.num_chunks}")
    console.print()
    console.print("[dim]Scores breakdown:[/dim]")
    console.print(f"  Answer Correctness: {result.scores.get('answer_correctness', 0):.2f}")
    console.print(f"  Context Relevance: {result.scores.get('context_relevance', 0):.2f}")
    console.print(f"  Faithfulness: {result.scores.get('faithfulness', 0):.2f}")
    console.print()

    # Apply to config
    if apply:
        print_step(3, 3, "Applying to config.yaml...")
        if tuner.apply_to_config(result):
            print_success("Config updated with tuned settings")
        else:
            print_warning("Failed to update config")
    else:
        print_info("Run with --apply to update config.yaml with these settings")

    console.print("\n[bold green]Tuning complete![/bold green]")


def run_tune_show() -> None:
    """Show current tuning state."""
    project_root = Path.cwd()

    if not config_exists(project_root):
        print_error("RED9 not initialized. Run 'red9 init' first.")
        return

    config = load_config(project_root)

    from red9.indexing.tuner import RAGTuner

    tuner = RAGTuner(project_root, config)
    result = tuner.get_best_result()

    if not result:
        print_info("No tuning results found. Run 'red9 tune' to optimize.")
        return

    console.print("\n[bold]Current Tuning Results[/bold]\n")
    console.print(f"  [bold]Final Score:[/bold] {result.final_score:.3f}")
    console.print(f"  [bold]Chunk Size:[/bold] {result.chunk_size}")
    console.print(f"  [bold]Chunk Overlap:[/bold] {result.chunk_overlap}")
    console.print(f"  [bold]Num Chunks:[/bold] {result.num_chunks}")
    console.print(f"  [bold]Embedding Model:[/bold] {result.embedding_model}")
    console.print(f"  [bold]LLM Model:[/bold] {result.llm_model}")
    console.print(f"  [bold]Tuned At:[/bold] {result.tuned_at}")
    console.print()

    # Check if config matches
    if _is_config_tuned(config, result):
        print_success("Config is using tuned settings")
    else:
        print_warning("Config differs from tuned settings")
        print_info("Run 'red9 tune --apply' to update config")


def run_tune_clear() -> None:
    """Clear tuning state."""
    project_root = Path.cwd()

    if not config_exists(project_root):
        print_error("RED9 not initialized. Run 'red9 init' first.")
        return

    config = load_config(project_root)

    from red9.indexing.tuner import RAGTuner

    tuner = RAGTuner(project_root, config)
    tuner.clear()
    print_success("Tuning state cleared")


def _is_config_tuned(config: object, result: object) -> bool:
    """Check if config matches tuning result.

    Args:
        config: RED9 config.
        result: Tuning result.

    Returns:
        True if config matches tuned settings.
    """
    return (
        config.indexing.chunk_size == result.chunk_size
        and config.indexing.chunk_overlap == result.chunk_overlap
    )
