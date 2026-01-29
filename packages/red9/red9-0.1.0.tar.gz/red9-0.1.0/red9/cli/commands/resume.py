"""RED9 resume command implementation."""

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
from red9.core.session import Red9Session


def _list_resumable_workflows(project_root: Path) -> list[tuple[str, str, str]]:
    """List workflows that can be resumed.

    Returns:
        List of (workflow_id, status, request) tuples.
    """
    try:
        from stabilize import SqliteWorkflowStore

        config = load_config(project_root)
        db_path = project_root / config.workflow.db_path
        if not db_path.exists():
            return []

        db_url = f"sqlite:///{db_path}"
        store = SqliteWorkflowStore(db_url)

        # Get recent workflows
        workflows = store.list_workflows(limit=10)

        resumable = []
        for wf in workflows:
            # Only show workflows that can be resumed
            if wf.status.name in ("PENDING", "RUNNING", "FAILED"):
                request = wf.context.get("request", "Unknown task")[:50]
                resumable.append((wf.id, wf.status.name, request))

        return resumable
    except Exception:
        return []


def run_resume(
    workflow_id: str | None,
) -> None:
    """Resume a paused or failed workflow.

    Args:
        workflow_id: ID of the workflow to resume, or None to list resumable workflows.
    """
    project_root = Path.cwd()

    if not config_exists(project_root):
        print_error("RED9 is not initialized.")
        return

    # If no workflow_id provided, list resumable workflows
    if not workflow_id:
        print_info("No workflow ID provided. Checking for resumable workflows...")
        resumable = _list_resumable_workflows(project_root)

        if not resumable:
            print_warning("No resumable workflows found.")
            print_info("Run 'red9 status --history' to see past workflows.")
            return

        console.print("\n[bold]Resumable workflows:[/bold]\n")
        for wf_id, status, request in resumable:
            console.print(f"  [cyan]{wf_id}[/cyan]  [{status}]  {request}...")

        console.print("\n[dim]Usage: red9 resume <WORKFLOW_ID>[/dim]")
        return

    session = Red9Session(project_root)

    # We need to load infrastructure
    session._prepare_infrastructure()

    console.print(f"\n[bold]Resuming workflow:[/bold] {workflow_id}\n")

    try:
        from stabilize import SqliteWorkflowStore

        # Manually reconstruct infrastructure components to get the specific workflow
        # (Session doesn't expose store directly nicely yet)
        config = session.config
        db_path = project_root / config.workflow.db_path
        db_url = f"sqlite:///{db_path}"
        store = SqliteWorkflowStore(db_url)

        # Load workflow
        workflow = store.retrieve(workflow_id)
        if not workflow:
            print_error(f"Workflow {workflow_id} not found.")
            return

        if workflow.status.name in ("SUCCEEDED", "TERMINAL", "CANCELLED"):
            print_warning(f"Workflow {workflow_id} is already {workflow.status.name}")
            return

        print_step(1, 1, "Resuming execution...")

        timeout = float(config.workflow.stage_timeout_minutes * 60)

        with create_status("Running agents..."):
            # Ensure orchestrator is started for this workflow if needed
            session.infrastructure.orchestrator.start(workflow)
            session.infrastructure.processor.process_all(timeout=timeout)

        # Refresh state
        workflow = store.retrieve(workflow_id)
        if workflow.status.name == "SUCCEEDED":
            print_success("Workflow completed successfully!")
        else:
            print_error(f"Workflow finished with status: {workflow.status.name}")

    except Exception as e:
        print_error(f"Resume failed: {e}")
