"""RED9 CLI main entry point."""

from __future__ import annotations

import click
from rich.console import Console

from red9 import __version__

# ASCII Logo - compact and professional
LOGO = """
[bold red]██████╗ ███████╗██████╗ [/bold red][bold white] █████╗ [/bold white]
[bold red]██╔══██╗██╔════╝██╔══██╗[/bold red][bold white]██╔══██╗[/bold white]
[bold red]██████╔╝█████╗  ██║  ██║[/bold red][bold white]╚██████║[/bold white]
[bold red]██╔══██╗██╔══╝  ██║  ██║[/bold red][bold white] ╚═══██║[/bold white]
[bold red]██║  ██║███████╗██████╔╝[/bold red][bold white] █████╔╝[/bold white]
[bold red]╚═╝  ╚═╝╚══════╝╚═════╝ [/bold red][bold white] ╚════╝ [/bold white]
"""

console = Console()


def show_banner(show_version: bool = True) -> None:
    """Display the RED9 banner."""
    console.print(LOGO)
    if show_version:
        console.print(f"[dim]v{__version__} • Enterprise Multi-Agent Coding System[/dim]\n")


@click.group()
@click.version_option(version=__version__, prog_name="red9")
@click.pass_context
def main(ctx: click.Context) -> None:
    """RED9 - Enterprise Multi-Agent Coding System.

    RED9 leverages Stabilize for workflow orchestration, IssueDB for task
    management, and Ragit for codebase understanding.
    """
    ctx.ensure_object(dict)


@main.command()
@click.option("--provider", default="ollama", help="LLM provider to use")
@click.option("--model", default=None, help="Model to use for generation")
@click.option("--embedding-model", default=None, help="Model to use for embeddings")
def init(provider: str, model: str | None, embedding_model: str | None) -> None:
    """Initialize RED9 in the current directory."""
    from red9.cli.commands.init import run_init

    run_init(provider, model, embedding_model)


@main.command()
@click.argument("request", required=False, default="")
@click.option("--plan-only", is_flag=True, help="Show plan without executing")
@click.option(
    "--parallel",
    is_flag=True,
    help="Enable parallel execution for independent sub-tasks",
)
@click.option(
    "--workflow",
    "-w",
    type=click.Choice(["v2", "v1", "swarm", "enterprise", "iterative"]),
    default="v2",
    help="Workflow: v2 (autonomous), enterprise (approvals), iterative, swarm, v1",
)
@click.option(
    "--fast",
    is_flag=True,
    help="Fast mode: single-agent implementation without exploration/review",
)
@click.option(
    "--yolo",
    is_flag=True,
    help="Auto-approve ALL approval gates (DANGEROUS - skips human review)",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Auto-approve for this run (still shows approval prompts)",
)
def task(
    request: str,
    plan_only: bool,
    parallel: bool,
    workflow: str,
    fast: bool,
    yolo: bool,
    yes: bool,
) -> None:
    """Execute a coding task.

    REQUEST is optional - if not provided, starts interactive mode.

    Requests are automatically classified using LLM:
      - CHAT mode: Questions, explanations (uses Ragit context)
      - SWARM mode: Code changes, implementations (full workflow)

    Workflow modes (for SWARM):
      - v2: Spec-first autonomous workflow - no approval gates (DEFAULT)
      - enterprise: 7-Phase with parallel agents and approval gates
      - iterative: Quality-gated loop (DDD → Review → Quality Gate)
      - swarm: Legacy 7-Phase workflow
      - v1: TDD workflow (plan → test → code → verify)

    Use --fast for simple tasks (fibonacci, hello world) - single agent, no overhead.
    Use --yolo to skip ALL approval gates in enterprise/swarm mode.
    Use -y to auto-approve while still showing approval information.
    """
    from red9.cli.commands.task import run_task

    run_task(request, plan_only, parallel, workflow, fast, yolo, yes)


@main.command()
def chat() -> None:
    """Start interactive chat session."""
    from red9.cli.commands.chat import run_chat

    run_chat()


@main.command()
@click.argument("workflow_id", required=False)
def resume(workflow_id: str | None) -> None:
    """Resume a paused or failed workflow.

    If no WORKFLOW_ID is provided, shows a list of resumable workflows.
    """
    from red9.cli.commands.resume import run_resume

    run_resume(workflow_id)


@main.command()
@click.argument("question")
def ask(question: str) -> None:
    """Ask a question about the codebase.

    QUESTION is what you want to know about the code.
    """
    from red9.cli.commands.ask import run_ask

    run_ask(question)


@main.command()
@click.option("--history", is_flag=True, help="Show past workflows")
def status(history: bool) -> None:
    """Show current workflow status."""
    from red9.cli.commands.status import run_status

    run_status(history)


@main.command()
@click.option("--priority", type=click.Choice(["low", "medium", "high", "critical"]))
@click.option("--status", "issue_status", type=click.Choice(["open", "in-progress", "closed"]))
@click.option("--limit", "-l", type=int, default=20, help="Maximum issues to show")
def todos(priority: str | None, issue_status: str | None, limit: int) -> None:
    """List pending issues/tasks."""
    from red9.cli.commands.todos import run_todos

    run_todos(priority, issue_status, limit)


@main.group()
def memory() -> None:
    """Manage memory storage for agent guidelines."""
    pass


@memory.command("add")
@click.argument("key")
@click.argument("value")
@click.option("-c", "--category", default="general", help="Memory category")
def memory_add(key: str, value: str, category: str) -> None:
    """Store a memory value."""
    from red9.cli.commands.memory import add_memory

    add_memory(key, value, category)


@memory.command("list")
@click.option("-c", "--category", default=None, help="Filter by category")
def memory_list(category: str | None) -> None:
    """List stored memory."""
    from red9.cli.commands.memory import list_memory

    list_memory(category)


@memory.command("delete")
@click.argument("key")
def memory_delete(key: str) -> None:
    """Delete a memory entry."""
    from red9.cli.commands.memory import delete_memory

    delete_memory(key)


@main.command()
@click.option("-c", "--category", default=None, help="Filter by category")
@click.option("-i", "--issue-id", type=int, default=None, help="Filter by issue ID")
def lessons(category: str | None, issue_id: int | None) -> None:
    """Show lessons learned."""
    from red9.cli.commands.lessons import run_lessons

    run_lessons(category, issue_id)


@main.group()
def tune() -> None:
    """Optimize RAG hyperparameters for the codebase."""
    pass


@tune.command("run")
@click.option("--apply", is_flag=True, help="Apply best result to config.yaml")
@click.option("--questions", "-q", default=5, help="Number of benchmark questions")
@click.option("--max-configs", "-m", type=int, default=None, help="Max configs to test")
@click.option("--quick", is_flag=True, help="Quick mode with fewer configurations")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed progress")
def tune_run(
    apply: bool,
    questions: int,
    max_configs: int | None,
    quick: bool,
    verbose: bool,
) -> None:
    """Run RAG hyperparameter optimization.

    Automatically finds optimal chunk_size, chunk_overlap, and num_chunks
    for your codebase using LLM-as-judge evaluation.
    """
    from red9.cli.commands.tune import run_tune

    run_tune(apply, questions, max_configs, quick, verbose)


@tune.command("show")
def tune_show() -> None:
    """Show current tuning results."""
    from red9.cli.commands.tune import run_tune_show

    run_tune_show()


@tune.command("clear")
def tune_clear() -> None:
    """Clear tuning state."""
    from red9.cli.commands.tune import run_tune_clear

    run_tune_clear()


if __name__ == "__main__":
    main()
