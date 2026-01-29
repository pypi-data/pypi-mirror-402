"""RED9 task command implementation."""

from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console

from red9.cli.error_handler import display_error
from red9.cli.main import show_banner
from red9.config import config_exists
from red9.core.session import Red9Session

console = Console()


def run_task(
    request: str,
    plan_only: bool,
    parallel: bool = False,
    workflow: str = "v2",
    fast: bool = False,
    yolo: bool = False,
    yes: bool = False,
) -> None:
    """Execute a coding task.

    Args:
        request: Task description.
        plan_only: If True, show plan without executing.
        parallel: If True, use parallel execution when beneficial.
        workflow: Workflow mode - "v2" (default), "enterprise", "swarm", or "v1".
        fast: If True, use fast mode (single agent, no exploration/review).
        yolo: If True, skip ALL approval gates.
        yes: If True, auto-approve while showing prompts.
    """
    # Show banner for task execution
    show_banner()

    project_root = Path.cwd()

    if not config_exists(project_root):
        console.print("[red]✗ RED9 is not initialized.[/red]")
        console.print("[dim]  Run:[/dim] red9 init")
        sys.exit(1)

    # Configure approval mode based on flags
    approval_mode = "default"
    if yolo:
        approval_mode = "yolo"
    elif yes:
        approval_mode = "auto"

    # Create session
    session = Red9Session(project_root, approval_mode=approval_mode)

    # If no request provided, enter interactive mode
    if not request:
        _interactive_mode(session, parallel, workflow, fast)
        return

    def on_token(token: str) -> None:
        """Handle streaming tokens."""
        sys.stdout.write(token)
        sys.stdout.flush()

    # Classify request using LLM to determine chat vs swarm mode
    console.print("[dim]Analyzing task...[/dim]", end=" ")
    mode = session.classify_request(request)

    if mode == "chat":
        console.print("[dim]→ CHAT mode[/dim]\n")
    else:
        # Try heuristic fast detection first (instant, no LLM call)
        auto_fast = False
        if not fast and workflow == "v2":
            heuristic_result = session.classify_complexity_fast(request)
            if heuristic_result == "simple":
                fast = True
                auto_fast = True
                console.print("[dim]→ AUTO-FAST mode (simple task)[/dim]\n")

        # Show workflow type (skip if already shown auto-fast message)
        if fast and not auto_fast:
            # Explicit --fast flag
            console.print("[dim]→ FAST mode (single agent)[/dim]\n")
        elif not fast:
            # Show workflow name based on selected workflow
            workflow_display = {
                "v2": "V2 (autonomous)",
                "enterprise": "ENTERPRISE",
                "swarm": "SWARM",
                "iterative": "ITERATIVE",
                "v1": "V1 (TDD)",
            }
            name = workflow_display.get(workflow, workflow.upper())
            console.print(f"[dim]→ {name} workflow[/dim]\n")

    if mode == "chat":
        # Chat mode: Use Ragit context to answer questions
        console.print(f"[dim]You:[/dim] {request}\n")
        try:
            session.simple_chat(request, on_token=on_token)
            console.print()
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
            sys.exit(130)
        except Exception as e:
            console.print()
            display_error(e, project_root)
            sys.exit(1)
        return

    # Execute the full task workflow
    from red9.cli.ui import EnterpriseDisplay

    try:
        with EnterpriseDisplay(f"Task: {request}") as display:
            # EnterpriseDisplay handles signal connection internally
            success = session.execute_task(
                request=request,
                parallel=parallel,
                workflow_mode=workflow,
                fast_mode=fast,
                on_token=None,  # Use signals (EnterpriseDisplay handles them)
                on_ui_event=None,  # Use signals (EnterpriseDisplay handles them)
            )

        if success:
            # Check display state for critical issues (captured via signals)
            if display.critical_issues and not display.quality_passed:
                n_issues = len(display.critical_issues)
                console.print(f"\n[red]✗ Task blocked by {n_issues} critical/high issues[/red]")
                console.print("[yellow]Run 'red9 resume' to iterate and fix issues[/yellow]")
                import os

                os._exit(1)
            elif display.critical_issues:
                console.print(
                    f"\n[yellow]⚠ Task completed with {len(display.critical_issues)} "
                    "critical/high issues (quality gates passed)[/yellow]"
                )
            else:
                console.print("\n[green]✓ Task completed successfully[/green]")
                import os

                os._exit(0)
        else:
            console.print("\n[red]✗ Task failed[/red]")
            # Use os._exit for immediate termination (avoids executor shutdown spam
            # from threads still running during interpreter shutdown)
            import os

            os._exit(1)

    except KeyboardInterrupt:
        # Suppress any remaining output and exit cleanly
        import atexit
        import concurrent.futures.thread
        import os
        import signal
        import threading
        import warnings

        # Ignore further SIGINT signals
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # Suppress all warnings during exit
        warnings.filterwarnings("ignore")

        # Set a silent exception hook for threads
        def silent_hook(args: threading.ExceptHookArgs) -> None:
            pass  # Silently ignore all thread exceptions during exit

        threading.excepthook = silent_hook

        # Disable the concurrent.futures atexit handler that causes the error
        try:
            atexit.unregister(concurrent.futures.thread._python_exit)
        except Exception:
            pass

        console.print("\n\n[yellow]⚠ Operation cancelled by user[/yellow]")

        # Use os._exit for immediate termination (skips cleanup that causes errors)
        os._exit(130)
    except Exception as e:
        console.print()
        display_error(e, project_root)
        sys.exit(1)


def _interactive_mode(
    session: Red9Session,
    parallel: bool,
    workflow: str,
    fast: bool = False,
) -> None:
    """Run in interactive mode."""
    from rich.prompt import Prompt

    # Show banner for interactive mode
    show_banner()

    mode_str = "[bold cyan]FAST[/bold cyan]" if fast else "[bold blue]ENTERPRISE[/bold blue]"
    console.print(f"[bold]Interactive Mode[/bold] • {mode_str}")
    console.print("[dim]Type your task or 'exit' to quit. Commands: /map, /status, /help[/dim]\n")

    while True:
        try:
            request = Prompt.ask("[bold green]>[/bold green]").strip()

            if not request:
                continue

            if request.lower() in ("exit", "quit", "/exit", "/quit"):
                console.print("[dim]Goodbye[/dim]")
                break

            console.print()

            def on_token(token: str) -> None:
                sys.stdout.write(token)
                sys.stdout.flush()

            # Classify request using LLM
            console.print("[dim]Analyzing...[/dim]", end=" ")
            mode = session.classify_request(request)

            if mode == "chat":
                console.print("[dim]→ CHAT[/dim]\n")
            else:
                if fast:
                    console.print("[dim]→ FAST[/dim]\n")
                else:
                    complexity = session.get_task_complexity(request)
                    workflow_names = {
                        "simple": "SIMPLE",
                        "medium": "ENTERPRISE",
                        "complex": "ENTERPRISE (full)",
                    }
                    console.print(f"[dim]→ {workflow_names.get(complexity, 'ENTERPRISE')}[/dim]\n")

            if mode == "chat":
                # Chat mode: answer with Ragit context
                session.simple_chat(request, on_token=on_token)
                console.print("\n")
                continue

            # Run full workflow for coding tasks
            from red9.cli.ui import EnterpriseDisplay

            with EnterpriseDisplay(f"Task: {request}"):
                success = session.execute_task(
                    request=request,
                    parallel=parallel,
                    workflow_mode=workflow,
                    fast_mode=fast,
                    on_token=None,
                    on_ui_event=None,
                )

            if success:
                console.print("\n[green]✓ Done[/green]\n")
            else:
                console.print("\n[red]✗ Failed[/red]\n")

        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye[/dim]")
            break
        except Exception as e:
            display_error(e, session.project_root)
            console.print()
