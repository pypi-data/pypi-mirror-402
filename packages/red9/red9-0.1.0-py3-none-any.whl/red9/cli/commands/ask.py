"""RED9 ask command implementation."""

from __future__ import annotations

from pathlib import Path

from red9.cli.output import (
    console,
    create_status,
    print_error,
    print_markdown,
    print_success,
)
from red9.config import config_exists, load_config


def run_ask(question: str) -> None:
    """Ask a question about the codebase.

    Always executes through Stabilize workflow engine for consistency
    and observability.

    Args:
        question: Question to ask.
    """
    project_root = Path.cwd()

    if not config_exists(project_root):
        print_error("RED9 is not initialized. Run 'red9 init' first.")
        return

    config = load_config(project_root)

    console.print(f"\n[bold]Question:[/bold] {question}\n")

    # Always use Stabilize workflow
    with create_status("Running ask workflow..."):
        answer = _run_ask_workflow(project_root, config, question)

    if answer:
        console.print("[bold]Answer:[/bold]\n")
        print_markdown(answer)
    else:
        print_error("Could not find an answer. Make sure Ollama is running.")


def _run_ask_workflow(
    project_root: Path,
    config,
    question: str,
) -> str | None:
    """Run ask workflow through Stabilize.

    Args:
        project_root: Project root directory.
        config: RED9 configuration.
        question: Question to ask.

    Returns:
        Answer or None.
    """
    try:
        from red9.indexing import IndexManager
        from red9.providers.ollama import OllamaProvider
        from red9.tools.base import ToolRegistry
        from red9.tools.complete_task import CompleteTaskTool
        from red9.tools.glob import GlobTool
        from red9.tools.grep import GrepTool
        from red9.tools.read_file import ReadFileTool
        from red9.tools.semantic_search import SemanticSearchTool
        from red9.workflows import build_ask_workflow, create_infrastructure, run_workflow

        # Create provider
        provider = OllamaProvider(
            base_url=config.provider.base_url,
            model=config.provider.model,
            embedding_model=config.provider.embedding_model,
        )

        # Initialize RAG for semantic search
        index_manager = IndexManager(project_root, config)

        # Early exit for empty repos
        if not index_manager.has_indexable_files():
            return "This repository has no code files to search. Add some code files first."

        # Check for file changes and update if needed
        needs_update, added, modified, deleted = index_manager.needs_update()
        if needs_update:
            total_changes = added + modified + deleted
            console.print(f"[dim]Updating index for {total_changes} changed files...[/dim]")
            index_manager.update_index(provider=None)
            print_success(f"Updated index: +{added} ~{modified} -{deleted} files")

        # Load RAG assistant for semantic search
        rag_assistant = None
        if index_manager.has_indexable_files():
            # Check if first run
            embeddings_dir = project_root / ".red9" / "embeddings"
            cache_exists = embeddings_dir.exists() and any(embeddings_dir.iterdir())
            if not cache_exists:
                console.print("[dim]First run - generating embeddings...[/dim]")

            rag_assistant = index_manager.get_rag_assistant(provider=None)

        # Create tool registry with read-only tools + semantic search
        tool_registry = ToolRegistry()
        tool_registry.register(ReadFileTool())
        tool_registry.register(GlobTool())
        tool_registry.register(GrepTool())
        tool_registry.register(CompleteTaskTool())

        # Always register semantic search - it handles None assistant gracefully
        tool_registry.register(SemanticSearchTool(rag_assistant))

        # Create infrastructure
        infrastructure = create_infrastructure(
            project_root=project_root,
            provider=provider,
            tool_registry=tool_registry,
            rag_assistant=rag_assistant,
        )

        # Build workflow
        workflow = build_ask_workflow(question, project_root)

        # Run workflow through Stabilize
        result = run_workflow(infrastructure, workflow, timeout=300.0)

        if result.status.name == "SUCCEEDED":
            # Extract answer from the workflow stages
            for stage in result.stages:
                if stage.ref_id == "answer":
                    if stage.status.name == "SUCCEEDED" and stage.outputs:
                        return stage.outputs.get("summary")

            return "Workflow completed but no answer found in outputs."

        else:
            # Extract actual error from failed stages
            for stage in result.stages:
                if stage.status.name in ("TERMINAL", "FAILED"):
                    for task in stage.tasks:
                        if task.result and task.result.error:
                            return f"Error: {task.result.error}"
            return f"Workflow failed with status: {result.status.name}"

    except ImportError as e:
        return f"Missing dependency: {e}"
    except Exception as e:
        return f"Workflow error: {e}"
