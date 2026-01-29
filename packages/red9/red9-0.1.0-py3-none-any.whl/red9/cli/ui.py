"""UI components for Red9 task execution.

Implements a clear, informative UI:
- Static header with task title
- Phase progress display (7-phase enterprise workflow)
- Parallel agent execution status
- Visible tool calls (like Claude Code)
- Minimal spinner only when thinking
- Streaming LLM output with intelligent JSON formatting
"""

from __future__ import annotations

import json
import sys
from enum import Enum, auto
from typing import Any

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text
from rich.theme import Theme

from red9.core.signals import token_stream, ui_event


class UIColors:
    """Semantic colors for UI elements."""

    TOOL_BASH = "dim"  # Danger - shell
    TOOL_EDIT = "bold #4CAF50"  # Success - file modifications
    TOOL_READ = "bold #03A9F4"  # Info - reading files
    TOOL_SEARCH = "bold #2196F3"  # Info - searching
    ERROR = "bold #FF5252"
    SUCCESS = "bold #4CAF50"
    WARNING = "bold #FFC107"
    DIM = "dim"
    THINKING = "italic #9E9E9E"
    PHASE = "bold #3F51B5"


class OutputState(Enum):
    """State machine for coordinated output rendering."""

    IDLE = auto()
    THINKING = auto()
    STREAMING_JSON = auto()
    STREAMING_TEXT = auto()
    TOOL_EXECUTING = auto()


class OutputBuffer:
    """Smart token accumulator with content type detection.

    Detects whether incoming tokens form JSON, markdown, or plain text,
    enabling appropriate rendering when flushed.
    """

    def __init__(self) -> None:
        self.buffer = ""
        self.content_type: str = "unknown"  # json, text, markdown

    def append(self, token: str) -> None:
        """Append token and detect content type."""
        self.buffer += token
        self._detect_content_type()

    def _detect_content_type(self) -> None:
        """Auto-detect if content is JSON, markdown, or text."""
        stripped = self.buffer.strip()
        if stripped.startswith("{") or stripped.startswith("```json"):
            self.content_type = "json"
        elif stripped.startswith("#") or stripped.startswith("* ") or stripped.startswith("- "):
            self.content_type = "markdown"
        else:
            self.content_type = "text"

    def is_json(self) -> bool:
        """Check if buffer content appears to be JSON."""
        return self.content_type == "json"

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return not self.buffer.strip()

    def clear(self) -> str:
        """Clear buffer and return content."""
        content = self.buffer
        self.buffer = ""
        self.content_type = "unknown"
        return content

    def get_content(self) -> str:
        """Get buffer content without clearing."""
        return self.buffer


# Fields to extract from agent JSON responses for display
DISPLAY_FIELDS = [
    "thoughts",
    "reasoning",
    "thinking",  # Original thinking fields
    "summary",
    "description",
    "explanation",  # Agent explanation
    "rationale",  # Agent output fields
    "approach",
    "plan",  # Planning fields
]

# Structured fields to format as lists
STRUCTURED_FIELDS = [
    ("files_to_modify", "Files to modify"),
    ("files_to_create", "Files to create"),
    ("issues", "Issues found"),
    ("key_decisions", "Key decisions"),
    ("risks", "Risks"),
    ("relevant_files", "Relevant files"),
    ("trade_offs", "Trade-offs"),
]

# Custom theme
RED9_THEME = Theme(
    {
        "info": "cyan",
        "warning": "bold yellow",
        "error": "bold red",
        "success": "bold green",
        "thinking": "italic grey50",
        "tool": "white",
        "tool_name": "bold cyan",
        "tool_arg": "white",
        "phase": "bold blue",
        "agent_active": "cyan",
        "agent_done": "green",
        "agent_failed": "red",
        "complexity_simple": "green",
        "complexity_medium": "yellow",
        "complexity_complex": "red",
        "stream": "grey70",  # Slightly brighter for readability
        "stream_code": "cyan",  # Code in streamed output
        # Semantic colors
        "tool.bash": UIColors.TOOL_BASH,
        "tool.edit": UIColors.TOOL_EDIT,
        "tool.read": UIColors.TOOL_READ,
        "tool.search": UIColors.TOOL_SEARCH,
    }
)

# Force terminal detection to ensure colors work even if piping (optional)
console = Console(theme=RED9_THEME, force_terminal=True)


class TaskDisplay:
    """Manages the task execution display with visible progress.

    Uses OutputBuffer for smart content type detection and state machine
    for coordinated output rendering without interleaved content.
    """

    def __init__(self, title: str) -> None:
        self.title = title
        self.status_message = "Thinking..."
        self.live: Live | None = None
        self.is_streaming = False
        self.current_phase = ""
        self.tool_history: list[str] = []
        self._last_tool_printed = False
        # Parallel agent tracking
        self.parallel_agents: dict[str, dict[str, Any]] = {}  # agent_id -> status info
        self.phase_number = 0
        self.total_phases = 9  # 7-phase enterprise workflow
        # Smart output buffering
        self._buffer = OutputBuffer()  # Smart token accumulator
        self._state = OutputState.IDLE  # State machine for coordinated output

    def __enter__(self) -> TaskDisplay:
        # Print header once
        console.print()
        console.print(Panel(f"[bold cyan]{self.title}[/bold cyan]", border_style="dim blue"))
        console.print()

        # Start "Thinking" status
        self._start_status()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._stop_status()
        self._flush_buffer()  # Flush any remaining content
        self._state = OutputState.IDLE
        if self.is_streaming:
            console.print()  # Ensure newline at end

    def update(self, token: str) -> None:
        """Buffer incoming tokens for rendering at completion.

        Uses OutputBuffer for smart content type detection.
        JSON content is silently buffered; text may show progress.
        """
        self._buffer.append(token)
        self.is_streaming = True

        # Update state based on detected content type
        if self._buffer.is_json():
            self._state = OutputState.STREAMING_JSON
            # JSON is silently buffered - don't show raw tokens
        else:
            self._state = OutputState.STREAMING_TEXT
            # Optionally stream text updates to status
            # if self.live:
            #     self.status_message = "Generating..."
            #     self._update_status()

    def _flush_buffer(self) -> None:
        """Render buffered content with smart formatting.

        JSON content is formatted as readable key-value pairs.
        Other content is rendered as markdown.
        """
        if self._buffer.is_empty():
            return

        content = self._buffer.clear().strip()
        self._state = OutputState.IDLE

        if not content:
            return

        # Stop spinner before rendering
        self._stop_status()

        # Try to parse as JSON and format nicely
        display_content = self._extract_display_content(content)

        if not display_content:
            return

        # Render with Rich Markdown in a subtle panel for premium look
        try:
            md = Markdown(display_content)
            # Use a subtle panel with dim border for agent thinking
            panel = Panel(
                md,
                border_style="dim blue",
                padding=(0, 1),
                title="[dim]Agent Analysis[/dim]",
                title_align="left",
            )
            console.print()
            console.print(panel)
        except Exception:
            # Fallback to plain dim text
            console.print(f"\n[dim]{display_content}[/dim]")

    def _extract_display_content(self, content: str) -> str:
        """Extract user-relevant content from LLM output.

        If content is JSON, extract and format relevant fields nicely.
        Otherwise return content as-is.
        """
        # Try to parse as JSON
        try:
            # Handle JSON possibly wrapped in markdown code block
            json_str = content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                potential = content.split("```")[1].split("```")[0].strip()
                if potential.startswith("{"):
                    json_str = potential

            if json_str.strip().startswith("{"):
                data = json.loads(json_str.strip())

                # Format the JSON data nicely
                return self._format_agent_json(data)

        except (json.JSONDecodeError, IndexError, KeyError):
            pass

        # Not JSON or couldn't parse - return as-is
        return content

    def _format_agent_json(self, data: dict[str, Any]) -> str:
        """Convert agent JSON to human-readable markdown format.

        Extracts and formats known fields from agent responses,
        presenting them in a clean, scannable format.
        """
        lines: list[str] = []

        # 1. Show approach first if present (most important for understanding intent)
        if "approach" in data and data["approach"]:
            approach = data["approach"]
            lines.append(f"**Approach:** {approach}")

        # 2. Extract primary text fields (thoughts, reasoning, explanation, etc.)
        for field in DISPLAY_FIELDS:
            if field in data and data[field] and field != "approach":
                value = data[field]
                if isinstance(value, str) and value.strip():
                    # Truncate very long text but show more
                    if len(value) > 500:
                        value = value[:500] + "..."
                    # Don't duplicate approach
                    if "approach" in lines[0] if lines else False:
                        if value == data.get("approach"):
                            continue
                    lines.append(f"\n{value}")
                    break  # Only show first found text field

        # 3. Format structured fields as bullet lists
        for field_key, field_label in STRUCTURED_FIELDS:
            if field_key in data and data[field_key]:
                items = data[field_key]
                if isinstance(items, list) and items:
                    lines.append(f"\n**{field_label}:**")
                    for item in items[:7]:  # Limit to 7 items
                        if isinstance(item, dict):
                            # Handle dict items (e.g., issues with description)
                            desc = item.get("description") or item.get("path") or str(item)
                            lines.append(f"  • {desc[:100]}")
                        else:
                            lines.append(f"  • {str(item)[:100]}")
                    if len(items) > 7:
                        lines.append(f"  • _...and {len(items) - 7} more_")

        # 4. Show confidence/estimated metrics if present
        metrics = []
        if "confidence" in data:
            conf = data["confidence"]
            conf_style = "🟢" if conf >= 80 else "🟡" if conf >= 50 else "🔴"
            metrics.append(f"{conf_style} Confidence: {conf}%")
        if "estimated_impact" in data:
            metrics.append(f"Impact: {data['estimated_impact']}")
        if "estimated_imports" in data:
            metrics.append(f"Imports: {data['estimated_imports']}")

        if metrics:
            lines.append("\n" + " | ".join(metrics))

        # If we extracted nothing useful, return empty
        if not lines:
            return ""

        return "\n".join(lines)

    def handle_event(self, event: dict[str, Any]) -> None:
        """Handle structured UI event (Tool start/end, phase changes, agents)."""
        event_type = event.get("type")

        if event_type == "complexity":
            # Display task complexity classification
            complexity = event.get("complexity", "medium")
            style = f"complexity_{complexity}"
            console.print(f"[dim]Complexity:[/dim] [{style}]{complexity.upper()}[/{style}]")

        elif event_type == "phase_start":
            # New phase starting - print phase header
            phase = event.get("phase", "")
            phase_num = event.get("phase_number", 0)
            total = event.get("total_phases", 0)
            if phase and phase != self.current_phase:
                self._stop_status()
                self.current_phase = phase
                self.phase_number = phase_num
                if total > 0:
                    self.total_phases = total
                if self.is_streaming:
                    sys.stdout.write("\n")
                    self.is_streaming = False
                # Clear parallel agent status for new phase
                self.parallel_agents = {}
                # Show phase with progress indicator
                progress_str = f"({phase_num}/{self.total_phases})" if phase_num > 0 else ""
                console.print(f"\n[phase]▶ Phase {phase_num}: {phase}[/phase] {progress_str}")
                self._start_status()

        elif event_type == "agent_start":
            # Parallel agent started
            agent_id = event.get("agent_id", "unknown")
            role = event.get("role", "agent")
            focus = event.get("focus", "")[:40]
            self.parallel_agents[agent_id] = {
                "role": role,
                "status": "running",
                "focus": focus,
            }
            self._print_parallel_status()

        elif event_type == "agent_end":
            # Parallel agent completed
            agent_id = event.get("agent_id", "unknown")
            success = event.get("success", True)
            if agent_id in self.parallel_agents:
                self.parallel_agents[agent_id]["status"] = "done" if success else "failed"
            self._print_parallel_status()

        elif event_type == "essential_files":
            # Display essential files found by explorers
            files = event.get("files", [])
            if files:
                self._stop_status()
                console.print("\n[dim]Essential Files:[/dim]")
                for f in files[:10]:  # Limit to first 10
                    path = f.get("path", f) if isinstance(f, dict) else f
                    reason = f.get("reason", "") if isinstance(f, dict) else ""
                    if reason:
                        console.print(f"  [cyan]{path}[/cyan] [dim]({reason})[/dim]")
                    else:
                        console.print(f"  [cyan]{path}[/cyan]")
                self._start_status()

        elif event_type == "approval_request":
            # Show approval request
            self._stop_status()
            approval_type = event.get("approval_type", "")
            options = event.get("options", [])
            console.print(f"\n[warning]Approval Required: {approval_type}[/warning]")
            if options:
                for opt in options:
                    label = opt.get("label", "")
                    desc = opt.get("description", "")
                    console.print(f"  • [bold]{label}[/bold]: {desc}")

        elif event_type == "tool_start":
            # Flush any buffered content before showing tool call
            self._flush_buffer()

            if self.is_streaming:
                self.is_streaming = False

            tool = event.get("tool", "unknown")
            args = event.get("args", {})

            # Determine tool type for color
            tool_color = "dim"
            icon = "→"

            if tool in ("run_command", "shell"):
                tool_color = UIColors.TOOL_BASH
                icon = "!"
            elif tool in ("write_file", "edit_file", "apply_diff", "replace", "batch_edit"):
                tool_color = UIColors.TOOL_EDIT
                icon = "✓"
            elif tool in ("read_file", "list_directory", "glob"):
                tool_color = UIColors.TOOL_READ
                icon = "○"
            elif tool in ("semantic_search", "grep", "search_file_content"):
                tool_color = UIColors.TOOL_SEARCH
                icon = "🔍"

            arg_str = self._format_tool_call(tool, args)

            # Print tool call visibly with semantic color
            console.print(f"[{tool_color}]{icon} {tool}[/{tool_color}] {arg_str}")

            self.tool_history.append(tool)
            self._last_tool_printed = True

            # Show minimal spinner while executing
            self.status_message = f"Running {tool}..."
            self._start_status()

        elif event_type == "tool_end":
            self._stop_status()
            success = event.get("success", True)
            duration = event.get("duration_ms", 0)
            error = event.get("error", "")

            # Print result indicator
            if success:
                # We already showed the tool call in color, so we don't need much here
                # unless it was very slow
                if duration > 1000:
                    console.print(f"  [dim]↳ done in {duration / 1000:.1f}s[/dim]")
            else:
                # Show error icon and message on the same line
                if error:
                    short_error = error[:100] + "..." if len(error) > 100 else error
                    console.print(f"  [error]✗[/error] [dim italic]{short_error}[/dim italic]")
                else:
                    console.print("  [error]✗ Failed[/error]")

            self._last_tool_printed = False
            self.status_message = "Thinking..."
            self._start_status()

        elif event_type == "review_issues":
            # Display high-confidence review issues
            issues = event.get("issues", [])
            if issues:
                self._stop_status()
                console.print(f"\n[warning]Review Issues ({len(issues)} found):[/warning]")
                for issue in issues[:5]:  # Limit to first 5
                    confidence = issue.get("confidence", 0)
                    severity = issue.get("severity", "medium")
                    desc = issue.get("description", "")[:80]
                    location = issue.get("location", "")
                    severity_style = {
                        "critical": "bold red",
                        "high": "red",
                        "medium": "yellow",
                        "low": "dim",
                    }.get(severity, "dim")
                    console.print(
                        f"  [{severity_style}]{severity.upper()}[/{severity_style}] "
                        f"[dim]({confidence}%)[/dim] {desc}"
                    )
                    if location:
                        console.print(f"    [dim]at {location}[/dim]")
                self._start_status()

        elif event_type == "iteration":
            # Display iteration progress
            self._stop_status()
            current = event.get("number", 1)
            max_iter = event.get("max", 10)
            issues_remaining = event.get("issues_remaining", 0)
            console.print(
                f"\n[dim]─── Iteration {current}/{max_iter} "
                f"({issues_remaining} issues remaining) ───[/dim]"
            )
            self._start_status()

        elif event_type == "ddd_retry":
            # Display DDD failure with styled box
            self._stop_status()
            iteration = event.get("iteration", 1)
            max_iter = event.get("max_iterations", 10)
            error = event.get("error", "Unknown error")
            will_retry = event.get("will_retry", True)

            # Truncate long errors
            if len(error) > 80:
                error = error[:77] + "..."

            if will_retry:
                console.print(f"\n[yellow]⟳ Iteration {iteration} incomplete - retrying[/yellow]")
                console.print(f"[dim]  {error}[/dim]")
            else:
                console.print(f"\n[red]✗ Max iterations ({max_iter}) reached[/red]")
                console.print(f"[dim]  {error}[/dim]")
            self._start_status()

        elif event_type == "quality_check":
            # Display quality gate results
            self._stop_status()
            passed = event.get("passed", False)
            score = event.get("score", 0)
            blocking = event.get("blocking_issues", 0)
            failed_dims = event.get("failed_dimensions", [])
            status = "[green]✓[/green]" if passed else "[red]✗[/red]"
            console.print(
                f"[dim]    Quality: {status} score={score:.0%}, "
                f"blocking={blocking}, failed={failed_dims}[/dim]"
            )
            self._start_status()

        elif event_type == "iteration_loop_complete":
            # Display iteration loop completion
            self._stop_status()
            iterations = event.get("iterations", 0)
            quality_passed = event.get("quality_passed", False)
            issues_fixed = event.get("issues_fixed", 0)
            issues_remaining = event.get("issues_remaining", 0)

            if quality_passed:
                console.print(
                    f"\n[green]✓ Quality gates passed after {iterations} "
                    f"iteration(s) ({issues_fixed} issues fixed)[/green]"
                )
            else:
                console.print(
                    f"\n[yellow]⚠ Max iterations reached. "
                    f"{issues_remaining} issues remain.[/yellow]"
                )

        elif event_type == "response_start":
            # LLM response starting - ensure clean state
            self._state = OutputState.THINKING
            self.status_message = "Generating response..."
            self._start_status()

        elif event_type == "response_end":
            # LLM response complete - flush buffer
            self._flush_buffer()
            self._state = OutputState.IDLE
            self.status_message = "Thinking..."
            self._start_status()

    def _print_parallel_status(self) -> None:
        """Print status of parallel agents."""
        if not self.parallel_agents:
            return

        self._stop_status()
        for agent_id, info in self.parallel_agents.items():
            status = info.get("status", "running")
            role = info.get("role", "agent")
            focus = info.get("focus", "")

            if status == "running":
                icon = "[agent_active]⟳[/agent_active]"
            elif status == "done":
                icon = "[agent_done]✓[/agent_done]"
            else:
                icon = "[agent_failed]✗[/agent_failed]"

            if focus:
                console.print(f"  {icon} {role}: {focus}...")
            else:
                console.print(f"  {icon} {role}")

        self._start_status()

    def _start_status(self) -> None:
        """Start the Live spinner."""
        if self.live:
            return

        # Use the "dots" spinner which is classic and minimal
        spinner = Spinner("dots", text=Text(self.status_message, style="thinking"))
        self.live = Live(
            spinner,
            console=console,
            refresh_per_second=60,  # 30 FPS for smooth animation
            transient=True,  # Disappear when stopped
        )
        self.live.start()

    def _stop_status(self) -> None:
        """Stop the Live spinner."""
        if self.live:
            self.live.stop()
            self.live = None

    def _update_status(self) -> None:
        """Update or start the status display."""
        if not self.live:
            self._start_status()
        else:
            self.live.update(Spinner("dots", text=Text(self.status_message, style="thinking")))

    def _format_tool_call(self, tool: str, args: dict) -> str:
        """Format tool call arguments for display."""
        if tool == "read_file":
            return f"[cyan]{args.get('file_path', '')}[/cyan]"
        elif tool == "write_file":
            path = args.get("file_path", "")
            return f"[green]{path}[/green]"
        elif tool == "run_command":
            cmd = args.get("command", "")
            return f"[red]{cmd[:50] + '...' if len(cmd) > 50 else cmd}[/red]"
        elif tool == "grep":
            pattern = args.get("pattern", "")
            return f'"{pattern}"'
        elif tool == "glob":
            pattern = args.get("pattern", "")
            return f'"{pattern}"'
        elif tool == "semantic_search":
            query = args.get("query", "")
            return f'"{query[:40]}..."' if len(query) > 40 else f'"{query}"'
        elif tool == "apply_diff":
            return f"[green]{args.get('file_path', '')}[/green]"
        elif tool == "edit_file":
            return f"[green]{args.get('file_path', '')}[/green]"
        elif tool == "complete_task":
            return ""
        else:
            # Generic: show first meaningful arg
            for key in ["file_path", "path", "pattern", "query", "command"]:
                if key in args:
                    val = str(args[key])
                    return val[:40] + "..." if len(val) > 40 else val
            return ""

    def _format_args(self, args: dict) -> str:
        """Legacy format method for compatibility."""
        if "file_path" in args:
            return f" {args['file_path']}"
        elif "command" in args:
            cmd = args["command"]
            return f" {cmd[:30]}..." if len(cmd) > 30 else f" {cmd}"
        elif "pattern" in args:
            return f" {args['pattern']}"
        return ""


# =============================================================================
# Split-Screen Layout with Toolbox
# =============================================================================


class Toolbox:
    """State container for the toolbox panel.

    Tracks files modified, tool history, metrics, and other
    information to display in the right-side panel.
    """

    def __init__(self) -> None:
        self.files_modified: list[str] = []
        self.files_read: list[str] = []
        self.tool_history: list[dict[str, Any]] = []
        self.current_phase: str = ""
        self.phase_number: int = 0
        self.total_phases: int = 9
        self.iterations: int = 0
        self.llm_calls: int = 0
        self.start_time: float = 0
        self.status: str = "idle"
        self.status_detail: str = ""  # What we're currently doing
        self.last_tool: str = ""
        self.errors: list[str] = []
        self.warnings: list[str] = []  # Informational messages (not errors)

    def add_tool_call(self, tool: str, args: dict, success: bool = True) -> None:
        """Record a tool call."""
        self.tool_history.append(
            {
                "tool": tool,
                "args": args,
                "success": success,
            }
        )
        self.last_tool = tool

        # Track file operations
        file_path = args.get("file_path", args.get("path", ""))
        if file_path:
            if tool in ("write_file", "edit_file", "apply_diff", "patch"):
                if file_path not in self.files_modified:
                    self.files_modified.append(file_path)
            elif tool in ("read_file", "glob", "grep"):
                if file_path not in self.files_read:
                    self.files_read.append(file_path)

    def add_error(self, error: str) -> None:
        """Record an error (filters out informational messages)."""
        # Skip informational messages that aren't real errors
        informational_patterns = [
            "unavailable",
            "not found",
            "empty",
            "no results",
            "skipped",
            "not indexed",
        ]
        error_lower = error.lower()
        if any(pattern in error_lower for pattern in informational_patterns):
            # Add as warning instead of error
            self.add_warning(error)
            return

        self.errors.append(error[:50])
        if len(self.errors) > 5:
            self.errors = self.errors[-5:]

    def add_warning(self, warning: str) -> None:
        """Record a warning (informational, not a real error)."""
        short_warning = warning[:40]
        if short_warning not in self.warnings:
            self.warnings.append(short_warning)
        if len(self.warnings) > 3:
            self.warnings = self.warnings[-3:]

    def set_phase(self, phase: str, number: int, total: int = 0) -> None:
        """Update current phase."""
        self.current_phase = phase
        self.phase_number = number
        if total > 0:
            self.total_phases = total

    def render(self) -> Panel:
        """Render the toolbox as a Rich Panel."""
        import time

        sections = []

        # Status section with animated spinner for active states
        status_text = Text()
        status_text.append("Status: ", style="dim")

        # Animated spinner for thinking/executing states
        spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        frame_idx = int(time.time() * 60) % len(spinner_frames)  # 8 FPS

        status_style = {
            "idle": "dim",
            "thinking": "yellow",
            "executing": "cyan",
            "done": "green",
            "error": "red",
        }.get(self.status, "dim")

        if self.status in ("thinking", "executing"):
            status_text.append(f"{spinner_frames[frame_idx]} ", style=status_style)
        status_text.append(self.status.upper(), style=status_style)

        # Show detail about what we're doing
        if self.status_detail:
            status_text.append(f"\n  {self.status_detail}", style="dim italic")

        sections.append(status_text)

        # Phase progress (always show)
        phase_text = Text()
        if self.current_phase:
            phase_text.append(f"\nPhase {self.phase_number}/{self.total_phases}: ", style="dim")
            phase_text.append(self.current_phase, style="bold blue")
        else:
            phase_text.append("\nPhase: ", style="dim")
            phase_text.append("Working...", style="italic")
        sections.append(phase_text)

        # Metrics
        metrics = Text()
        metrics.append("\n─── Metrics ───\n", style="dim blue")
        metrics.append(f"LLM Calls: {self.llm_calls}\n", style="dim")
        metrics.append(f"Tool Calls: {len(self.tool_history)}\n", style="dim")
        if self.iterations > 0:
            metrics.append(f"Iterations: {self.iterations}\n", style="dim")
        sections.append(metrics)

        # Files modified
        if self.files_modified:
            files_text = Text()
            files_text.append("\n─── Modified ───\n", style="dim green")
            for f in self.files_modified[-5:]:  # Last 5
                files_text.append(f"  ✓ {f[-30:]}\n", style="green")
            if len(self.files_modified) > 5:
                files_text.append(f"  ...+{len(self.files_modified) - 5} more\n", style="dim")
            sections.append(files_text)

        # Recent tools
        if self.tool_history:
            tools_text = Text()
            tools_text.append("\n─── Recent Tools ───\n", style="dim cyan")
            for entry in self.tool_history[-5:]:  # Last 5
                tool = entry["tool"]
                icon = "✓" if entry["success"] else "✗"
                style = "dim" if entry["success"] else "red"
                tools_text.append(f"  {icon} {tool}\n", style=style)
            sections.append(tools_text)

        # Warnings (informational, not errors)
        if self.warnings:
            warnings_text = Text()
            warnings_text.append("\n─── Info ───\n", style="dim yellow")
            for warn in self.warnings[-2:]:
                warnings_text.append(f"  ○ {warn}\n", style="dim")
            sections.append(warnings_text)

        # Errors (real issues)
        if self.errors:
            errors_text = Text()
            errors_text.append("\n─── Errors ───\n", style="dim red")
            for err in self.errors[-3:]:
                errors_text.append(f"  • {err}\n", style="red")
            sections.append(errors_text)

        # Combine all sections
        content = Text()
        for section in sections:
            content.append_text(section)

        return Panel(
            content,
            title="[bold]Toolbox[/bold]",
            border_style="dim blue",
            padding=(1, 1),
        )


class SplitScreenDisplay:
    """Split-screen display with main area (2/3) and toolbox (1/3).

    Provides a premium layout with:
    - Left panel: Main output (task progress, agent output)
    - Right panel: Toolbox (files, metrics, tool history)
    - Full history dumped on exit for scrollback

    Usage:
        with SplitScreenDisplay("Task: implement feature") as display:
            display.update_main("Processing...")
            display.toolbox.add_tool_call("read_file", {"path": "foo.py"})
    """

    def __init__(self, title: str) -> None:
        import threading

        self.title = title
        self.toolbox = Toolbox()
        self.live: Live | None = None
        self.layout: Layout | None = None
        self.main_content: list[Any] = []  # Renderables for main panel
        self.full_history: list[Any] = []  # Full history for dump on exit
        self._status_message = "Initializing..."
        # Streaming token buffer
        self._token_buffer = OutputBuffer()
        self._streaming = False
        # Lock for thread-safe layout updates
        self._update_lock = threading.Lock()
        # Animation control
        self._stop_animation = threading.Event()
        self._animation_thread: threading.Thread | None = None
        self._exiting = False

    def _make_layout(self) -> Layout:
        """Create the split layout structure."""
        layout = Layout()

        # Split into main (2/3) and toolbox (1/3)
        layout.split_row(
            Layout(name="main", ratio=2),
            Layout(name="toolbox", ratio=1, minimum_size=30),
        )

        return layout

    def _render_main(self) -> Panel:
        """Render the main content panel - fills available space."""
        import time

        if not self.main_content:
            # Show animated spinner when no content
            spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            frame_idx = int(time.time() * 60) % len(spinner_frames)  # 8 FPS animation
            spinner_text = Text()
            spinner_text.append(f"{spinner_frames[frame_idx]} ", style="cyan")
            spinner_text.append(self._status_message, style="italic dim")
            content = spinner_text
        else:
            # Show recent items - Rich Layout handles the sizing
            # Show last ~30 items (reasonable for most terminals)
            visible_items = self.main_content[-30:]

            # Add streaming buffer content if active
            if self._streaming and not self._token_buffer.is_empty():
                buffer_text = Text(self._token_buffer.buffer[-200:], style="dim italic")
                visible_items = [*visible_items, buffer_text]

            content = Group(*visible_items)

        return Panel(
            content,
            title=f"[bold cyan]{self.title}[/bold cyan]",
            subtitle="[dim]History saved on exit[/dim]",
            border_style="blue",
            padding=(0, 1),
        )

    def _update_layout(self) -> None:
        """Update the layout with current content (thread-safe)."""
        if self._exiting:
            return
        with self._update_lock:
            if self.layout and self.live:
                try:
                    self.layout["main"].update(self._render_main())
                    self.layout["toolbox"].update(self.toolbox.render())
                except Exception:
                    pass  # Ignore rendering errors

    def __enter__(self) -> SplitScreenDisplay:
        """Start the split-screen display."""
        import threading
        import time

        # Suppress threading exceptions globally during our session
        self._old_excepthook = getattr(threading, "excepthook", None)
        threading.excepthook = self._silent_excepthook

        self.layout = self._make_layout()
        self._update_layout()

        # Use screen mode for full terminal control, reduces flicker
        self.live = Live(
            self.layout,
            console=console,
            refresh_per_second=60,  # 8 FPS - smooth enough, less flicker
            transient=False,
            screen=False,  # Don't use alternate screen (preserves scrollback)
            auto_refresh=True,  # We control updates
        )
        self.live.start()

        self.toolbox.start_time = time.time()
        self.toolbox.status = "thinking"
        self.toolbox.status_detail = "Starting task..."

        # Background thread for smooth animation
        self._stop_animation.clear()
        self._animation_thread = threading.Thread(
            target=self._animation_loop, daemon=True, name="ui-animation"
        )
        self._animation_thread.start()

        return self

    def _silent_excepthook(self, args: Any) -> None:
        """Silently handle thread exceptions during UI operation."""
        # Ignore KeyboardInterrupt and SystemExit in threads
        if args.exc_type in (KeyboardInterrupt, SystemExit, BrokenPipeError):
            return
        # Log others but don't crash
        pass

    def _animation_loop(self) -> None:
        """Background thread that updates the display at ~8 FPS."""
        import time

        while not self._stop_animation.is_set():
            if self._exiting:
                break
            try:
                with self._update_lock:
                    if self.layout and self.live and not self._stop_animation.is_set():
                        self.layout["main"].update(self._render_main())
                        self.layout["toolbox"].update(self.toolbox.render())
                        self.live.refresh()
            except Exception:
                pass  # Ignore all errors during animation
            # ~8 FPS = 125ms per frame
            # for 60, we must sleep ~16ms (time.sleep(1/60))
            time.sleep(1 / 60)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop the display and dump full history for scrollback."""
        import threading

        self._exiting = True

        # 1. Stop the animation thread first
        self._stop_animation.set()
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=0.3)

        # 2. Stop the live display
        if self.live:
            self.toolbox.status = "done" if exc_type is None else "error"
            try:
                self.live.stop()
            except Exception:
                pass

        # 3. Restore original excepthook
        if self._old_excepthook:
            threading.excepthook = self._old_excepthook

        # 4. Dump full history to console for scrollback
        # This is the key feature - all content is preserved
        if self.full_history:
            console.print("\n" + "═" * 60)
            console.print("[bold]Full Session History[/bold] (scroll up to review)")
            console.print("═" * 60 + "\n")
            for item in self.full_history:
                try:
                    console.print(item)
                except Exception:
                    pass  # Skip items that can't be printed
            console.print("\n" + "═" * 60)
            console.print(f"[dim]Total: {len(self.full_history)} items[/dim]")

        # 5. Clear references
        self.live = None
        self.layout = None

    def add_content(self, content: Any) -> None:
        """Add renderable content to the main panel."""
        self.main_content.append(content)
        self.full_history.append(content)  # Also add to full history
        self._update_layout()

    def update(self, token: str) -> None:
        """Handle streaming token (for LLM thinking output).

        Accumulates tokens and flushes when complete JSON/text is detected.
        """
        self._streaming = True
        self._token_buffer.append(token)

        # Check if we have a complete thought to display
        if self._token_buffer.buffer.endswith("}") or self._token_buffer.buffer.endswith("\n\n"):
            self._flush_thinking()
        else:
            # Just update display to show current buffer
            self._update_layout()

    def _flush_thinking(self) -> None:
        """Flush accumulated thinking tokens to display."""
        if self._token_buffer.is_empty():
            return

        content = self._token_buffer.clear().strip()
        self._streaming = False

        if not content:
            return

        # Try to extract useful content from JSON
        display_content = self._extract_thinking(content)
        if display_content:
            # Show thinking in a subtle panel
            thinking_panel = Panel(
                Markdown(display_content),
                border_style="dim",
                padding=(0, 1),
                title="[dim]Thinking[/dim]",
                title_align="left",
            )
            self.add_content(thinking_panel)

    def _extract_thinking(self, content: str) -> str:
        """Extract readable content from LLM response (may be JSON)."""
        # Try to parse as JSON first
        try:
            stripped = content.strip()
            if stripped.startswith("{"):
                data = json.loads(stripped)

                lines = []

                # Extract key thinking fields (human-readable text)
                text_fields = [
                    "thoughts",
                    "reasoning",
                    "thinking",
                    "approach",
                    "explanation",
                    "summary",
                    "description",
                    "rationale",
                ]
                for field in text_fields:
                    if field in data and data[field]:
                        value = data[field]
                        if isinstance(value, str) and value.strip():
                            # Skip if it looks like JSON fragments
                            if value.strip().startswith("[") or value.strip().startswith("{"):
                                continue
                            if len(value) > 300:
                                value = value[:300] + "..."
                            lines.append(value)
                            break

                # Extract patterns found (common in explorer output)
                if "patterns_found" in data and data["patterns_found"]:
                    patterns = data["patterns_found"]
                    if isinstance(patterns, list) and patterns:
                        lines.append("\n**Patterns:**")
                        for p in patterns[:4]:
                            if isinstance(p, str):
                                lines.append(f"  • {p[:80]}")

                # Extract related files summary
                if "related_files" in data and data["related_files"]:
                    files = data["related_files"]
                    if isinstance(files, list) and files:
                        lines.append(f"\n**Files:** {len(files)} relevant files found")

                # Show key decisions if present
                if "key_decisions" in data and data["key_decisions"]:
                    decisions = data["key_decisions"][:3]
                    lines.append("\n**Decisions:**")
                    for d in decisions:
                        if isinstance(d, str):
                            lines.append(f"  • {d[:80]}")
                        elif isinstance(d, dict):
                            desc = d.get("description", d.get("decision", str(d)))
                            lines.append(f"  • {str(desc)[:80]}")

                if lines:
                    return "\n".join(lines)

        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        # If not JSON or extraction failed, check if content is readable
        # Skip cryptic content (JSON fragments, arrays, etc.)
        stripped = content.strip()
        if stripped.startswith("[") or stripped.startswith("{"):
            return ""  # Skip raw JSON
        if '": [' in stripped or '": {' in stripped:
            return ""  # Skip JSON fragments

        # Show truncated raw content only if it looks like natural text
        if len(content) > 200:
            return content[:200] + "..."
        return content if len(content) > 20 else ""  # Skip very short content

    def add_text(self, text: str, style: str = "") -> None:
        """Add text to the main panel."""
        self.add_content(Text(text, style=style))

    def add_phase(self, phase: str, number: int, total: int = 0) -> None:
        """Add phase indicator to main panel and update toolbox."""
        self.toolbox.set_phase(phase, number, total)
        phase_text = Text()
        progress = f"/{self.toolbox.total_phases}" if self.toolbox.total_phases > 0 else ""
        phase_text.append(f"\n▶ Phase {number}{progress}: ", style="bold blue")
        phase_text.append(phase, style="blue")
        self.add_content(phase_text)

    def add_tool_call(self, tool: str, args: dict, success: bool = True, error: str = "") -> None:
        """Record and display a tool call."""
        self.toolbox.add_tool_call(tool, args, success)
        self.toolbox.status = "executing"

        # Determine tool color
        tool_color = "dim"
        icon = "→"
        if tool in ("run_command", "shell"):
            tool_color = UIColors.TOOL_BASH
            icon = "!"
        elif tool in ("write_file", "edit_file", "apply_diff"):
            tool_color = UIColors.TOOL_EDIT
            icon = "✓"
        elif tool in ("read_file", "glob"):
            tool_color = UIColors.TOOL_READ
            icon = "○"
        elif tool in ("grep", "semantic_search"):
            tool_color = UIColors.TOOL_SEARCH
            icon = "🔍"

        # Format args
        arg_str = ""
        for key in ["file_path", "path", "pattern", "query", "command"]:
            if key in args:
                val = str(args[key])
                arg_str = val[:40] + "..." if len(val) > 40 else val
                break

        tool_text = Text()
        tool_text.append(f"{icon} {tool} ", style=tool_color)
        tool_text.append(arg_str, style="dim")
        if not success and error:
            tool_text.append(f" ✗ {error[:30]}", style="red")

        self.add_content(tool_text)

        if not success:
            self.toolbox.add_error(error)

        self._update_layout()

    def set_status(self, status: str, message: str = "") -> None:
        """Update the status."""
        self.toolbox.status = status
        if message:
            self._status_message = message
        self._update_layout()

    def increment_llm_calls(self) -> None:
        """Increment LLM call counter."""
        self.toolbox.llm_calls += 1
        self._update_layout()

    def handle_event(self, event: dict[str, Any]) -> None:
        """Handle a UI event (compatible with TaskDisplay)."""
        event_type = event.get("type")

        if event_type == "complexity":
            # Display task complexity
            complexity = event.get("complexity", "medium")
            style = {"simple": "green", "medium": "yellow", "complex": "red"}.get(complexity, "dim")
            self.add_content(Text(f"Complexity: {complexity.upper()}", style=style))

        elif event_type == "phase_start":
            phase = event.get("phase", "")
            phase_num = event.get("phase_number", 0)
            total = event.get("total_phases", 0)
            self.add_phase(phase, phase_num, total)
            self.toolbox.status_detail = f"Phase {phase_num}: {phase}"

        elif event_type == "agent_start":
            # Parallel agent started
            role = event.get("role", "agent")
            focus = event.get("focus", "")[:30]
            agent_text = Text()
            agent_text.append("  ⟳ ", style="cyan")
            agent_text.append(f"{role}", style="bold")
            if focus:
                agent_text.append(f": {focus}...", style="dim")
            self.add_content(agent_text)
            self.toolbox.status = "thinking"
            self.toolbox.status_detail = f"{role}: {focus[:20]}..." if focus else role

        elif event_type == "agent_end":
            # Parallel agent completed
            success = event.get("success", True)
            role = event.get("role", "agent")
            icon = "✓" if success else "✗"
            style = "green" if success else "red"
            self.add_content(Text(f"  {icon} {role} done", style=style))

        elif event_type == "tool_start":
            tool = event.get("tool", "unknown")
            args = event.get("args", {})
            self.add_tool_call(tool, args)
            # Show what tool is running
            arg_hint = ""
            for key in ["file_path", "path", "pattern", "query", "command"]:
                if key in args:
                    arg_hint = str(args[key])[:25]
                    break
            self.toolbox.status_detail = f"{tool} {arg_hint}".strip()

        elif event_type == "tool_end":
            success = event.get("success", True)
            error = event.get("error", "")
            duration = event.get("duration_ms", 0)
            if not success:
                self.toolbox.add_error(error)
                self.add_content(Text(f"    ✗ {error[:50]}", style="red"))
            elif duration > 1000:
                self.add_content(Text(f"    ↳ done in {duration / 1000:.1f}s", style="dim"))
            self.toolbox.status = "thinking"
            self.toolbox.status_detail = "Processing results..."
            self._update_layout()

        elif event_type == "response_start":
            self.set_status("thinking", "Generating response...")
            self.toolbox.status_detail = f"LLM call #{self.toolbox.llm_calls + 1}"
            self.increment_llm_calls()

        elif event_type == "response_end":
            self.set_status("thinking", "Processing...")
            self.toolbox.status_detail = "Analyzing response..."

        elif event_type == "iteration":
            current = event.get("number", 1)
            max_iter = event.get("max", 10)
            issues = event.get("issues_remaining", 0)
            self.toolbox.iterations = current
            iter_text = Text()
            iter_text.append(f"\n─── Iteration {current}/{max_iter}", style="dim")
            if issues > 0:
                iter_text.append(f" ({issues} issues remaining)", style="yellow")
            iter_text.append(" ───", style="dim")
            self.add_content(iter_text)
            self._update_layout()

        elif event_type == "ddd_retry":
            # Display DDD failure with styled message
            iteration = event.get("iteration", 1)
            max_iter = event.get("max_iterations", 10)
            error = event.get("error", "Unknown error")
            will_retry = event.get("will_retry", True)

            # Truncate long errors
            if len(error) > 60:
                error = error[:57] + "..."

            retry_text = Text()
            if will_retry:
                retry_text.append(f"\n⟳ Iteration {iteration} incomplete", style="yellow")
                retry_text.append(f" - {error}", style="dim")
            else:
                retry_text.append(f"\n✗ Max iterations ({max_iter}) reached", style="red")
                retry_text.append(f" - {error}", style="dim")
            self.add_content(retry_text)
            self._update_layout()

        elif event_type == "essential_files":
            files = event.get("files", [])
            if files:
                files_text = Text("\nEssential Files:\n", style="dim cyan")
                for f in files[:7]:
                    path = f.get("path", f) if isinstance(f, dict) else f
                    reason = f.get("reason", "") if isinstance(f, dict) else ""
                    files_text.append(f"  • {path}", style="cyan")
                    if reason:
                        files_text.append(f" ({reason})", style="dim")
                    files_text.append("\n")
                if len(files) > 7:
                    files_text.append(f"  ...+{len(files) - 7} more\n", style="dim")
                self.add_content(files_text)

        elif event_type == "approval_request":
            # Show approval request
            approval_type = event.get("approval_type", "")
            self.add_content(Text(f"\n⚠ Approval Required: {approval_type}", style="bold yellow"))

        elif event_type == "review_issues":
            # Display review issues
            issues = event.get("issues", [])
            if issues:
                issues_text = Text(f"\nReview Issues ({len(issues)}):\n", style="yellow")
                for issue in issues[:5]:
                    severity = issue.get("severity", "medium")
                    desc = issue.get("description", "")[:60]
                    sev_style = {
                        "critical": "bold red",
                        "high": "red",
                        "medium": "yellow",
                        "low": "dim",
                    }.get(severity, "dim")
                    issues_text.append(f"  [{severity.upper()}] ", style=sev_style)
                    issues_text.append(f"{desc}\n", style="dim")
                self.add_content(issues_text)

        elif event_type == "quality_check":
            # Display quality gate results
            passed = event.get("passed", False)
            score = event.get("score", 0)
            icon = "✓" if passed else "✗"
            style = "green" if passed else "red"
            self.add_content(Text(f"  Quality: {icon} score={score:.0%}", style=style))

        elif event_type == "iteration_loop_complete":
            # Display iteration completion
            iterations = event.get("iterations", 0)
            quality_passed = event.get("quality_passed", False)
            issues_fixed = event.get("issues_fixed", 0)
            if quality_passed:
                self.add_content(
                    Text(
                        f"\n✓ Quality passed after {iterations} iteration(s) "
                        f"({issues_fixed} fixed)",
                        style="bold green",
                    )
                )
            else:
                remaining = event.get("issues_remaining", 0)
                self.add_content(
                    Text(
                        f"\n⚠ Max iterations reached. {remaining} issues remain.",
                        style="yellow",
                    )
                )


# =============================================================================
# Enterprise Display - Claude-Code-inspired clean UI
# =============================================================================


class EnterpriseDisplay:
    """Claude-Code-inspired enterprise CLI display.

    Features:
    - Clean vertical flow (no sidebar)
    - Streaming agent thinking/reasoning
    - Syntax-highlighted file diffs
    - Todo list with checkboxes
    - Status bar with metrics (time, tokens, file changes)

    Usage:
        with EnterpriseDisplay("Task: implement feature") as display:
            display.handle_event(event)
    """

    def __init__(self, title: str) -> None:
        import time

        self.title = title
        self.start_time = time.time()

        # Metrics tracking
        self.token_count = 0
        self.llm_calls = 0
        self.files_changed: dict[str, dict[str, int]] = {}  # path -> {added, removed}
        self.active_model = ""

        # Phase tracking
        self.current_phase = ""
        self.phase_number = 0
        self.total_phases = 7

        # Todo tracking
        self.todos: list[dict[str, Any]] = []

        # State tracking for exit codes
        self.critical_issues: list[dict] = []
        self.quality_passed = False

        # Output state
        self._last_tool: str = ""

        # Streaming text buffer
        self._buffer = OutputBuffer()
        self._is_streaming = False

        # Live status spinner
        self._live: Live | None = None
        self._status_message = "Initializing..."
        self._thinking_content = ""

    def __enter__(self) -> EnterpriseDisplay:
        """Start the display - print header."""
        console.print()
        console.print(f"[bold cyan]○ {self.title}[/bold cyan]")
        console.print("─" * 60)
        console.print()

        # Connect signals
        token_stream.connect(self.on_token_signal)
        ui_event.connect(self.on_ui_event_signal)

        # Start with thinking spinner
        self._start_spinner("Analyzing task...")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """End the display - print final status bar."""
        # Disconnect signals
        token_stream.disconnect(self.on_token_signal)
        ui_event.disconnect(self.on_ui_event_signal)

        self._stop_spinner()
        # Clear buffer without displaying (avoid garbage output on exit)
        self._buffer.clear()
        self._print_status_bar(final=True)
        # NOTE: Don't print success/failure message here - task.py handles it
        # based on the actual workflow result (success=True/False).
        # EnterpriseDisplay only tracks UI state, not workflow completion status.

    def on_token_signal(self, sender: Any, token: str) -> None:
        """Handle token stream signal."""
        self.update(token)

    def on_ui_event_signal(self, sender: Any, event: dict[str, Any]) -> None:
        """Handle UI event signal."""
        self.handle_event(event)

        # Track state for exit code
        if event.get("type") == "review_issues":
            for issue in event.get("issues", []):
                if issue.get("severity") in ("critical", "high"):
                    self.critical_issues.append(issue)

        if event.get("type") == "iteration_loop_complete":
            self.quality_passed = event.get("quality_passed", False)

    def _get_live_renderable(self) -> Any:
        """Get the current live renderable (spinner + thinking panel)."""
        spinner = Spinner("dots", text=Text(f" {self._status_message}", style="dim italic"))

        if not self._thinking_content.strip():
            return spinner

        # Create a thinking panel if we have content
        # Only show last 10 lines to keep it compact but visible
        lines = self._thinking_content.splitlines()
        if len(lines) > 10:
            content = "...\n" + "\n".join(lines[-10:])
            # Preserve trailing newline for visual stability during streaming
            if self._thinking_content.endswith("\n"):
                content += "\n"
        else:
            content = self._thinking_content

        # Unescape literal newlines for readability
        # (fixes "text\ntext" display issues in JSON streams)
        content = content.replace("\\n", "\n")

        panel = Panel(
            Text(content, style="dim"),
            title="[dim italic]Thinking[/dim italic]",
            border_style="dim blue",
            padding=(0, 1),
            width=console.width - 4,  # Slightly narrower than full width
        )

        return Group(panel, spinner)

    def _start_spinner(self, message: str = "Thinking...") -> None:
        """Start the live status spinner."""
        self._status_message = message

        if self._live:
            # Already running - just update the text
            self._live.update(self._get_live_renderable())
            return

        self._live = Live(
            self._get_live_renderable(),
            console=console,
            refresh_per_second=60,
            transient=True,  # Disappear when stopped
        )
        self._live.start()

    def _stop_spinner(self) -> None:
        """Stop the live status spinner."""
        if self._live:
            self._live.stop()
            self._live = None
        self._thinking_content = ""  # Clear thinking content on stop

    def _update_spinner(self, message: str) -> None:
        """Update the spinner message."""
        self._status_message = message
        if self._live:
            self._live.update(self._get_live_renderable())

    def update(self, token: str) -> None:
        """Handle streaming token - accumulate and update spinner."""
        self._buffer.append(token)
        self._thinking_content += token
        self._is_streaming = True
        self.token_count += len(token)

        # Show progress in spinner (every few tokens or on newlines to prevent visual lag)
        if self._live and (self.token_count % 2 == 0 or "\n" in token):
            self._live.update(self._get_live_renderable())

    def _flush_buffer(self) -> None:
        """Flush accumulated tokens and display formatted content in a panel."""
        if self._buffer.is_empty():
            return

        content = self._buffer.clear().strip()
        self._is_streaming = False

        if not content:
            return

        # Extract readable content (handles both JSON and plain text)
        display_content = self._extract_display_content(content)

        if not display_content:
            return

        # Render in a styled panel (Bright for readability)
        # Use Text without dim style
        text = Text(display_content)
        panel = Panel(
            text,
            border_style="blue",  # Bright border
            padding=(0, 1),
            title="[bold blue]Agent[/bold blue]",  # Bright title
            title_align="left",
        )
        console.print(panel)

    def _extract_display_content(self, content: str) -> str:
        """Extract readable content from agent output (JSON or plain text)."""
        stripped = content.strip()

        # Skip garbage/fragments (JSON pieces, brackets, etc.)
        if not stripped or len(stripped) < 20:
            return ""

        # Skip if looks like JSON fragments or garbage
        garbage_patterns = [
            '": {',
            '": [',
            '"}',
            "}]",
            "0 }",
            "} ]",
            '":',
            "[]",
            "{}",
            "],[",
        ]
        if any(p in stripped for p in garbage_patterns) and len(stripped) < 50:
            return ""

        # Skip if looks like file content (markdown docs, code, etc.)
        file_content_patterns = [
            "```",  # Code blocks
            "## ",  # Markdown headers
            "**##",  # Bold headers
            "| --- |",  # Tables
            "| @ |",  # Table markers
            "#!/",  # Shebang
            "import ",  # Code imports
            "from ",  # Python imports
            "def ",  # Function definitions
            "class ",  # Class definitions
            "```python",
            "```markdown",
        ]
        if any(p in stripped for p in file_content_patterns):
            # This looks like file content, not agent thinking
            # Extract just the first line if it's a natural language intro
            first_line = stripped.split("\n")[0].strip()
            if (
                len(first_line) > 30
                and not any(p in first_line for p in file_content_patterns)
                and first_line[0].isupper()  # Starts with capital (sentence)
            ):
                return first_line
            return ""

        # Skip if mostly punctuation/brackets
        alpha_count = sum(1 for c in stripped if c.isalpha())
        if alpha_count < len(stripped) * 0.3:  # Less than 30% letters
            return ""

        # Try to parse as JSON first
        try:
            json_str = content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                # Try extracting from generic code block
                potential = content.split("```")[1].split("```")[0].strip()
                if potential.startswith("{"):
                    json_str = potential

            if json_str.strip().startswith("{"):
                data = json.loads(json_str.strip())
                return self._format_json_content(data)

        except (json.JSONDecodeError, IndexError, KeyError):
            pass

        # Not JSON - check if it's readable text (not code/gibberish)
        # Skip if looks like raw JSON fragments
        if stripped.startswith("[") or stripped.startswith("{"):
            return ""

        # Skip very long content (likely file content)
        if len(stripped) > 500:
            # Just show first paragraph
            first_para = stripped.split("\n\n")[0]
            if len(first_para) > 200:
                return first_para[:200] + "..."
            return first_para

        return stripped

    def _format_json_content(self, data: dict[str, Any]) -> str:
        """Format JSON agent response into readable markdown."""
        lines: list[str] = []

        # 1. Extract primary thinking/reasoning text
        text_fields = [
            "thoughts",
            "reasoning",
            "thinking",
            "approach",
            "summary",
            "description",
            "explanation",
            "rationale",
        ]
        for field in text_fields:
            if field in data and data[field]:
                value = data[field]
                if isinstance(value, str) and value.strip():
                    # Skip if it looks like JSON
                    if value.strip().startswith("{") or value.strip().startswith("["):
                        continue
                    text = value[:400] + "..." if len(value) > 400 else value
                    lines.append(text)
                    break  # Only show first found

        # 2. Format structured data nicely
        # Essential/related files
        for key in ["essential_files", "related_files", "files_to_modify"]:
            if key in data and data[key]:
                items = data[key]
                if isinstance(items, list) and items:
                    label = key.replace("_", " ").title()
                    lines.append(f"\n**{label}:**")
                    for item in items[:5]:
                        if isinstance(item, dict):
                            path = item.get("path", "")
                            reason = item.get("reason", "")
                            if path:
                                lines.append(f"- `{path}`" + (f" - {reason}" if reason else ""))
                        elif isinstance(item, str):
                            lines.append(f"- `{item}`")
                    if len(items) > 5:
                        lines.append(f"- *... and {len(items) - 5} more*")

        # Patterns found
        if "patterns_found" in data and data["patterns_found"]:
            patterns = data["patterns_found"]
            if isinstance(patterns, list) and patterns:
                lines.append("\n**Patterns:**")
                for p in patterns[:4]:
                    if isinstance(p, str):
                        lines.append(f"- {p}")
                if len(patterns) > 4:
                    lines.append(f"- *... and {len(patterns) - 4} more*")

        # Risks
        if "risks" in data and data["risks"]:
            risks = data["risks"]
            if isinstance(risks, list) and risks:
                lines.append("\n**Risks:**")
                for r in risks[:3]:
                    if isinstance(r, str):
                        lines.append(f"- ⚠️ {r}")

        # If nothing extracted, return empty
        if not lines:
            return ""

        return "\n".join(lines)

    def handle_event(self, event: dict[str, Any]) -> None:
        """Handle a structured UI event."""
        event_type = event.get("type")

        if event_type == "phase_start":
            self._stop_spinner()
            self._flush_buffer()  # Flush before phase change
            self._handle_phase_start(event)
            self._start_spinner("Working...")
        elif event_type == "tool_start":
            self._stop_spinner()
            self._flush_buffer()  # Flush before tool call
            self._handle_tool_start(event)
            # Show spinner with tool name
            tool = event.get("tool", "unknown")
            self._start_spinner(f"Running {tool}...")
        elif event_type == "tool_end":
            self._stop_spinner()
            self._handle_tool_end(event)
            self._start_spinner("Thinking...")
        elif event_type == "response_start":
            self.llm_calls += 1
            if "model" in event:
                self.active_model = event["model"]
            self._update_spinner("Generating response...")
        elif event_type == "response_end":
            self._stop_spinner()
            self._flush_buffer()  # Flush at end of LLM response
            self._start_spinner("Thinking...")
        elif event_type == "todos_update":
            self.todos = event.get("todos", [])
            self._render_todos()
        elif event_type == "complexity":
            complexity = event.get("complexity", "medium")
            style = {"simple": "green", "medium": "yellow", "complex": "red"}.get(complexity, "dim")
            console.print(f"[dim]Complexity:[/dim] [{style}]{complexity}[/{style}]")
        elif event_type == "iteration":
            self._stop_spinner()
            current = event.get("number", 1)
            max_iter = event.get("max", 10)
            issues = event.get("issues_remaining", 0)
            console.print(
                f"\n[dim]─── Iteration {current}/{max_iter} ({issues} issues remaining) ───[/dim]"
            )
            self._start_spinner(f"Iteration {current}: implementing...")
        elif event_type == "ddd_retry":
            self._stop_spinner()
            iteration = event.get("iteration", 1)
            max_iter = event.get("max_iterations", 10)
            error = event.get("error", "Unknown error")
            will_retry = event.get("will_retry", True)

            # Truncate long errors
            if len(error) > 60:
                error = error[:57] + "..."

            if will_retry:
                console.print(f"[yellow]⟳ Iteration {iteration} incomplete[/yellow]")
                console.print(f"[dim]  {error}[/dim]")
            else:
                console.print(f"[red]✗ Max iterations ({max_iter}) reached[/red]")
                console.print(f"[dim]  {error}[/dim]")
            self._start_spinner("Retrying...")
        elif event_type == "quality_check":
            self._stop_spinner()
            passed = event.get("passed", False)
            score = event.get("score", 0)
            blocking = event.get("blocking_issues", 0)
            icon = "✓" if passed else "✗"
            style = "green" if passed else "red"
            # Show blocking issues count if not passed
            if passed:
                console.print(f"[{style}]{icon} Quality: {score:.0%}[/{style}]")
            else:
                console.print(
                    f"[{style}]{icon} Quality: {score:.0%}[/{style}] "
                    f"[dim]({blocking} blocking issues)[/dim]"
                )

    def _handle_phase_start(self, event: dict[str, Any]) -> None:
        """Handle phase start event."""
        phase = event.get("phase", "")
        phase_num = event.get("phase_number", 0)
        total = event.get("total_phases", 0)
        self.current_phase = phase
        self.phase_number = phase_num
        if total > 0:
            self.total_phases = total

        console.print()
        progress = f" ({phase_num}/{self.total_phases})" if phase_num > 0 else ""
        console.print(f"[bold blue]▶ Phase {phase_num}: {phase}[/bold blue]{progress}")

    def _handle_tool_start(self, event: dict[str, Any]) -> None:
        """Handle tool start event - show tool call."""
        tool = event.get("tool", "unknown")
        args = event.get("args", {})
        self._last_tool = tool

        # Determine icon and color based on tool type
        if tool in ("run_command", "shell"):
            icon, color = "!", UIColors.TOOL_BASH
        elif tool in ("write_file", "edit_file", "apply_diff", "batch_edit"):
            icon, color = "✎", UIColors.TOOL_EDIT
        elif tool in ("read_file", "read_many_files", "list_dir"):
            icon, color = "○", UIColors.TOOL_READ
        elif tool in ("grep", "glob", "semantic_search", "ast_grep"):
            icon, color = "⌕", UIColors.TOOL_SEARCH
        else:
            icon, color = "→", "dim"

        # Format arguments
        arg_str = self._format_tool_args(tool, args)

        console.print(f"[{color}]{icon} {tool}[/{color}] {arg_str}")

    def _handle_tool_end(self, event: dict[str, Any]) -> None:
        """Handle tool end event - show diff if present."""
        tool = event.get("tool", "")
        success = event.get("success", True)
        diff = event.get("diff")
        output = event.get("output", {})
        duration = event.get("duration_ms", 0)
        error = event.get("error", "")

        # Show error if failed
        if not success:
            # Check for security/blocked command errors
            is_security_error = error and any(
                k in error.lower() for k in ("access denied", "blocked", "traversal", "security")
            )

            if is_security_error:
                panel = Panel(
                    Text(error, style="white"),
                    title="[bold red]⚠️ Security Alert[/bold red]",
                    border_style="bold red",
                    padding=(0, 1),
                )
                console.print(panel)
            elif error:
                short_error = error[:80] + "..." if len(error) > 80 else error
                console.print(f"  [red]✗ {short_error}[/red]")
            else:
                console.print("  [red]✗ Failed[/red]")
            return

        # Show diff if present (the key feature!)
        if diff and tool in ("write_file", "edit_file", "apply_diff", "batch_edit"):
            file_path = ""
            is_new_file = False
            if isinstance(output, dict):
                file_path = output.get("file_path", "")
                is_new_file = output.get("is_new_file", False)

            if is_new_file:
                self._render_new_file(file_path, diff)
            else:
                self._render_diff(file_path, diff)
        elif duration > 1000:
            # Show duration for slow operations
            console.print(f"  [dim]↳ done in {duration / 1000:.1f}s[/dim]")

    def _render_new_file(self, file_path: str, diff_text: str) -> None:
        """Render a new file content with syntax highlighting instead of diff."""
        from rich.markdown import Markdown
        from rich.syntax import Syntax

        # Reconstruct content from diff (strip + prefix)
        lines = []
        for line in diff_text.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                lines.append(line[1:])

        content = "\n".join(lines)

        # Limit lines shown
        display_text = content
        if len(lines) > 50:
            display_text = "\n".join(lines[:50]) + f"\n\n... ({len(lines) - 50} more lines)"

        # Track file changes (all added)
        short_path = file_path.split("/")[-1] if file_path else "new_file"
        self.files_changed[file_path or short_path] = {"added": len(lines), "removed": 0}

        header = f"Create({short_path})"
        footer = f"+{len(lines)} lines"

        renderable: Any = None
        ext = file_path.split(".")[-1].lower() if file_path else ""

        # Special handling for Markdown
        if ext in ("md", "markdown"):
            renderable = Markdown(display_text)
        else:
            # Code Syntax Highlighting
            lexer = "text"
            if ext in ("py", "pyw"):
                lexer = "python"
            elif ext in ("js", "mjs"):
                lexer = "javascript"
            elif ext in ("ts", "tsx"):
                lexer = "typescript"
            elif ext in ("html", "htm"):
                lexer = "html"
            elif ext in ("css",):
                lexer = "css"
            elif ext in ("json",):
                lexer = "json"
            elif ext in ("sh", "bash"):
                lexer = "bash"
            elif ext in ("rs",):
                lexer = "rust"
            elif ext in ("go",):
                lexer = "go"
            elif ext in ("java",):
                lexer = "java"
            elif ext in ("cpp", "c", "h", "hpp"):
                lexer = "cpp"
            elif ext in ("yaml", "yml"):
                lexer = "yaml"
            elif ext in ("toml",):
                lexer = "toml"

            # Use ansi_dark as requested
            renderable = Syntax(display_text, lexer, theme="ansi_dark", line_numbers=True)

        panel = Panel(
            renderable,
            title=f"[bold]{header}[/bold]",
            subtitle=f"[dim]{footer}[/dim]",
            border_style="green",
            padding=(0, 1),
        )
        console.print(panel)

    def _render_diff(self, file_path: str, diff_text: str) -> None:
        """Render a unified diff with syntax highlighting."""
        from rich.syntax import Syntax

        lines = diff_text.splitlines()
        added = 0
        removed = 0

        # Calculate stats
        for line in lines:
            if line.startswith("+++") or line.startswith("---"):
                continue
            elif line.startswith("+"):
                added += 1
            elif line.startswith("-"):
                removed += 1

        # Track file changes for status bar
        short_path = file_path.split("/")[-1] if file_path else "file"
        self.files_changed[file_path or short_path] = {"added": added, "removed": removed}

        # Create diff panel with file path header
        header = f"Update({short_path})" if file_path else "Update"
        footer = f"+{added} -{removed}"

        # Limit lines shown
        if len(lines) > 30:
            display_text = "\n".join(lines[:30]) + f"\n\n... ({len(lines) - 30} more lines)"
        else:
            display_text = diff_text

        # Use rich Syntax with diff lexer for pygments highlighting
        # Enable line numbers and use ansi_dark as requested
        syntax = Syntax(display_text, "diff", theme="ansi_dark", line_numbers=True)

        panel = Panel(
            syntax,
            title=f"[bold]{header}[/bold]",
            subtitle=f"[dim]{footer}[/dim]",
            border_style="green" if added >= removed else "yellow",
            padding=(0, 1),
        )
        console.print(panel)

    def _render_todos(self) -> None:
        """Render todo list with checkboxes."""
        if not self.todos:
            return

        console.print()
        console.print("[dim]─── Tasks ───[/dim]")

        for todo in self.todos[-5:]:  # Show last 5
            status = todo.get("status", "pending")
            text = todo.get("content", todo.get("text", ""))

            if status == "completed":
                console.print(f"[green]■[/green] [dim strikethrough]{text}[/dim strikethrough]")
            elif status == "in_progress":
                console.print(f"[yellow]◐[/yellow] [bold]{text}[/bold]")
            else:
                console.print(f"[dim]□[/dim] {text}")

    def _print_status_bar(self, final: bool = False) -> None:
        """Print status bar with metrics."""
        import time

        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        # Calculate totals
        total_added = sum(f["added"] for f in self.files_changed.values())
        total_removed = sum(f["removed"] for f in self.files_changed.values())

        console.print()
        console.print("─" * 60)

        bar = Text()
        bar.append(f"Phase {self.phase_number}/{self.total_phases}", style="blue")
        bar.append(" │ ", style="dim")
        bar.append(f"{minutes}m {seconds}s", style="dim")
        bar.append(" │ ", style="dim")
        bar.append(f"{self.llm_calls} LLM calls", style="dim")

        if self.active_model:
            bar.append(" │ ", style="dim")
            bar.append(f"{self.active_model}", style="dim cyan")

        if self.token_count > 0:
            bar.append(" │ ", style="dim")
            if self.token_count > 1000000:
                tokens_str = f"{self.token_count / 1000000:.1f}M"
            elif self.token_count > 1000:
                tokens_str = f"{self.token_count / 1000:.1f}K"
            else:
                tokens_str = str(self.token_count)
            bar.append(f"{tokens_str} tokens", style="dim cyan")

        bar.append(" │ ", style="dim")
        bar.append(f"{len(self.files_changed)} files ", style="dim")
        bar.append(f"+{total_added}", style="green")
        bar.append(" ", style="dim")
        bar.append(f"-{total_removed}", style="red")

        console.print(bar)

    def _format_tool_args(self, tool: str, args: dict[str, Any]) -> str:
        """Format tool arguments for display."""
        if tool == "read_file":
            return f"[cyan]{args.get('file_path', '')}[/cyan]"
        elif tool == "write_file":
            return f"[green]{args.get('file_path', '')}[/green]"
        elif tool == "edit_file":
            return f"[green]{args.get('file_path', '')}[/green]"
        elif tool == "apply_diff":
            return f"[green]{args.get('file_path', '')}[/green]"
        elif tool in ("run_command", "shell"):
            cmd = args.get("command", "")
            return f"[red]{cmd[:50]}{'...' if len(cmd) > 50 else ''}[/red]"
        elif tool == "grep":
            return f'"{args.get("pattern", "")}"'
        elif tool == "glob":
            return f'"{args.get("pattern", "")}"'
        elif tool == "semantic_search":
            query = args.get("query", "")
            return f'"{query[:40]}{"..." if len(query) > 40 else ""}"'
        else:
            # Generic: show first meaningful arg
            for key in ["file_path", "path", "pattern", "query", "command"]:
                if key in args:
                    val = str(args[key])
                    return val[:40] + "..." if len(val) > 40 else val
            return ""
