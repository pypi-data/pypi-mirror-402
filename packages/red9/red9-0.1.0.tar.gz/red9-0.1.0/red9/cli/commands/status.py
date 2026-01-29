"""RED9 status command implementation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from rich.table import Table

from red9.cli.output import (
    console,
    print_error,
    print_header,
    print_info,
)
from red9.config import config_exists, load_config

if TYPE_CHECKING:
    from stabilize import SqliteWorkflowStore, Workflow


def run_status(history: bool) -> None:
    """Show current workflow status.

    Args:
        history: If True, show past workflows.
    """
    project_root = Path.cwd()

    if not config_exists(project_root):
        print_error("RED9 is not initialized. Run 'red9 init' first.")
        return

    config = load_config(project_root)
    workflows_db = project_root / config.workflow.db_path

    if not workflows_db.exists():
        print_info("No workflows have been executed yet.")
        return

    try:
        from stabilize import SqliteWorkflowStore

        store = SqliteWorkflowStore(f"sqlite:///{workflows_db}")

        if history:
            _show_workflow_history(store)
        else:
            _show_current_workflow(store)

    except ImportError:
        print_error("Stabilize is not installed. Cannot show workflow status.")
    except Exception as e:
        print_error(f"Error reading workflow status: {e}")


def _get_status_emoji(status: str) -> str:
    """Get emoji for workflow/stage status.

    Args:
        status: Status string.

    Returns:
        Emoji representation.
    """
    status_lower = str(status).lower()
    if "succeeded" in status_lower or "completed" in status_lower:
        return "[green]OK[/green]"
    elif "failed" in status_lower or "terminal" in status_lower:
        return "[red]FAIL[/red]"
    elif "running" in status_lower:
        return "[yellow]RUN[/yellow]"
    elif "canceled" in status_lower or "stopped" in status_lower:
        return "[dim]STOP[/dim]"
    elif "skipped" in status_lower:
        return "[dim]SKIP[/dim]"
    elif "not_started" in status_lower:
        return "[dim]WAIT[/dim]"
    return "[dim]?[/dim]"


def _format_timestamp(ts: int | None) -> str:
    """Format millisecond timestamp to readable string.

    Args:
        ts: Timestamp in milliseconds, or None.

    Returns:
        Formatted time string.
    """
    if ts is None:
        return "-"
    try:
        dt = datetime.fromtimestamp(ts / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return "-"


def _show_current_workflow(store: SqliteWorkflowStore) -> None:
    """Show the most recent workflow status.

    Args:
        store: Workflow store.
    """
    print_header("Current Workflow")

    try:
        # Get recent workflows for RED9 application
        workflows = store.list_workflows("red9", limit=1)

        if not workflows:
            console.print("[dim]No workflows found[/dim]")
            print_info("Run 'red9 task \"your request\"' to start a new workflow")
            return

        # Retrieve the full workflow with stages
        workflow = store.retrieve(workflows[0].id)
        _display_workflow_details(workflow)

    except Exception as e:
        print_error(f"Error reading workflow: {e}")


def _show_workflow_history(store: SqliteWorkflowStore) -> None:
    """Show workflow history.

    Args:
        store: Workflow store.
    """
    print_header("Workflow History")

    try:
        # Get recent workflows for RED9 application
        workflows = store.list_workflows("red9", limit=10)

        if not workflows:
            console.print("[dim]No workflows found[/dim]")
            return

        # Create summary table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Status", width=6)
        table.add_column("Name", max_width=50)
        table.add_column("Started", width=20)
        table.add_column("Stages", width=8)
        table.add_column("ID", max_width=26)

        # Retrieve full workflows with stages
        full_workflows = [store.retrieve(wf.id) for wf in workflows]

        for workflow in full_workflows:
            status_emoji = _get_status_emoji(str(workflow.status))
            name = getattr(workflow, "name", str(workflow.id)[:20])

            # Get stage count and status
            stages = getattr(workflow, "stages", [])
            succeeded = sum(1 for s in stages if "succeeded" in str(s.status).lower())
            stage_summary = f"{succeeded}/{len(stages)}"

            # Get start time
            start_time = _format_timestamp(getattr(workflow, "start_time", None))

            table.add_row(
                status_emoji,
                name[:50],
                start_time,
                stage_summary,
                str(workflow.id)[:26],
            )

        console.print(table)
        console.print()

        # Show details of most recent workflow
        if full_workflows:
            console.print("[bold]Most Recent Workflow Details:[/bold]")
            _display_workflow_details(full_workflows[0])

    except Exception as e:
        print_error(f"Error reading workflow history: {e}")


def _display_workflow_details(workflow: Workflow) -> None:
    """Display detailed workflow information.

    Args:
        workflow: Workflow to display.
    """
    # Workflow header
    status_emoji = _get_status_emoji(str(workflow.status))
    name = getattr(workflow, "name", str(workflow.id)[:30])
    console.print(f"\n{status_emoji} [bold]{name}[/bold]")
    console.print(f"   ID: [dim]{workflow.id}[/dim]")
    console.print(f"   Status: {workflow.status}")

    start_time = _format_timestamp(getattr(workflow, "start_time", None))
    end_time = _format_timestamp(getattr(workflow, "end_time", None))
    console.print(f"   Started: {start_time}")
    if end_time != "-":
        console.print(f"   Ended: {end_time}")

    # Show stages
    stages = getattr(workflow, "stages", [])
    if stages:
        console.print("\n   [bold]Stages:[/bold]")
        for stage in stages:
            stage_status = _get_status_emoji(str(stage.status))
            stage_name = getattr(stage, "name", stage.ref_id)

            # Check for errors in stage context
            error_msg = ""
            context = getattr(stage, "context", {})
            if context:
                exception_info = context.get("exception", {})
                if exception_info:
                    details = exception_info.get("details", {})
                    error = details.get("error", "")
                    if error:
                        error_msg = f" [red]({error[:50]}...)[/red]"

            console.print(f"      {stage_status} {stage_name}{error_msg}")

    console.print()
