"""Interactive chat mode implementation."""

from __future__ import annotations

import shlex
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

from red9.cli.output import print_error, print_info, print_success
from red9.config import config_exists
from red9.core.session import Red9Session
from red9.tools.base import validate_path

console = Console()


def run_chat() -> None:
    """Start interactive chat session."""
    project_root = Path.cwd()

    if not config_exists(project_root):
        print_error("RED9 is not initialized. Run 'red9 init' first.")
        return

    session = Red9Session(project_root)
    session._prepare_infrastructure()

    # Session state
    added_files: set[str] = set()

    print_success("Started Red9 Chat Mode")
    print_info("Type your request or use commands:")
    print_info("  /add <file>  - Add file to context")
    print_info("  /drop <file> - Remove file from context")
    print_info("  /map         - Show repo map")
    print_info("  /exit        - Exit chat")

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]>[/bold green]").strip()
            if not user_input:
                continue

            if user_input.startswith("/"):
                _handle_command(user_input, session, added_files)
                continue

            # Execute task/chat
            _handle_message(user_input, session, added_files)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Exiting...[/dim]")
            break
        except Exception as e:
            print_error(f"Error: {e}")


def _handle_command(input_str: str, session: Red9Session, added_files: set[str]) -> None:
    """Handle slash commands."""
    parts = shlex.split(input_str)
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "/exit":
        raise KeyboardInterrupt

    elif cmd == "/add":
        if not args:
            print_error("Usage: /add <file>")
            return

        for arg in args:
            # Handle globs
            Path(arg)
            if "*" in arg:
                files = list(session.project_root.glob(arg))
                if not files:
                    print_info(f"No files matched: {arg}")
                for f in files:
                    if f.is_file():
                        rel = f.relative_to(session.project_root)
                        added_files.add(str(rel))
                        print_success(f"Added {rel}")
            else:
                f, err = validate_path(arg, must_exist=True)
                if err or not f:
                    print_error(f"Could not add {arg}: {err or 'File not found'}")
                    continue
                rel = f.relative_to(session.project_root)
                added_files.add(str(rel))
                print_success(f"Added {rel}")

    elif cmd == "/drop":
        if not args:
            added_files.clear()
            print_success("Dropped all files")
            return

        for arg in args:
            if arg in added_files:
                added_files.remove(arg)
                print_success(f"Dropped {arg}")
            else:
                print_info(f"{arg} not in context")

    elif cmd == "/map":
        repo_map = session.get_repo_map()
        console.print(Markdown(f"```\n{repo_map}\n```"))

    else:
        print_error(f"Unknown command: {cmd}")


def _handle_message(message: str, session: Red9Session, added_files: set[str]) -> None:
    """Handle normal user message (task request)."""

    # Context augmentation
    context_prefix = ""
    if added_files:
        context_prefix = (
            "I have loaded these files into context:\n"
            + "\n".join(f"- {f}" for f in added_files)
            + "\n\n"
        )

    full_request = context_prefix + message

    # For now, we reuse the standard task execution
    # Ideally, we would have a lighter-weight "Chat" workflow
    # But the robust task workflow is what sets red9 apart.

    console.print("[dim]Executing task...[/dim]")

    try:
        # We need to capture the output more gracefully than the standard task runner
        # For now, let it print to stdout as usual
        success = session.execute_task(full_request)

        if success:
            print_success("Done.")
        else:
            print_error("Task failed.")

    except Exception as e:
        print_error(f"Execution error: {e}")
