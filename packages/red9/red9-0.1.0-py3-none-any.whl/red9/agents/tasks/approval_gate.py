"""Approval Gate Task - Human-in-Loop for Workflow Phases.

Provides approval gates in the 7-phase workflow:
- After Exploration: Approve exploration findings before architecture
- After Architecture: Approve chosen approach before implementation
- After Review: Approve final changes before completion

Supports three modes:
- DEFAULT: Pause and request approval (interactive)
- AUTO (-y): Auto-approve for this run
- YOLO (--yolo): Skip all approval gates
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from stabilize import Task, TaskResult
from stabilize.models.stage import StageExecution

from red9.agents.notepad import Notepad
from red9.approval import ApprovalMode, get_approval_manager
from red9.logging import get_logger

logger = get_logger(__name__)


class ApprovalGateTask(Task):
    """Approval gate for human-in-loop workflow control.

    Pauses the workflow and requests user approval before proceeding.
    Can be configured to auto-approve or skip based on approval mode.
    """

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the approval gate.

        Expected context:
            - approval_type: Type of approval (exploration, architecture, final)
            - summary: Summary to present to user for approval
            - details: Detailed information about what's being approved
            - options: Optional list of options to choose from
            - project_root: Project root path
            - workflow_id: Current workflow ID

        Returns:
            TaskResult with approval decision.
        """
        project_root = stage.context.get("project_root")
        workflow_id = stage.context.get("workflow_id", "default")
        approval_type = stage.context.get("approval_type", "general")
        summary = stage.context.get("summary", "")
        details = stage.context.get("details", {})
        options = stage.context.get("options", [])

        # Get summary from upstream if not provided
        if not summary:
            summary = self._get_summary_from_upstream(stage)

        root_path = Path(project_root) if project_root else Path.cwd()
        notepad = Notepad(root_path, workflow_id)

        # Check approval mode
        approval_manager = get_approval_manager()

        if approval_manager.mode == ApprovalMode.YOLO:
            logger.info(f"YOLO mode: Auto-approving {approval_type} gate")
            notepad.add_entry(
                "decision",
                f"Auto-approved {approval_type} (YOLO mode)",
                "ApprovalGate",
            )
            return TaskResult.success(
                outputs={
                    "approved": True,
                    "approval_type": approval_type,
                    "mode": "yolo",
                }
            )

        if approval_manager.mode == ApprovalMode.AUTO:
            logger.info(f"AUTO mode: Auto-approving {approval_type} gate")
            notepad.add_entry(
                "decision",
                f"Auto-approved {approval_type} (AUTO mode)",
                "ApprovalGate",
            )
            return TaskResult.success(
                outputs={
                    "approved": True,
                    "approval_type": approval_type,
                    "mode": "auto",
                }
            )

        # Interactive approval required
        try:
            result = self._request_interactive_approval(
                approval_type=approval_type,
                summary=summary,
                details=details,
                options=options,
            )

            if result["approved"]:
                notepad.add_entry(
                    "decision",
                    f"User approved {approval_type}: {result.get('reason', 'No reason given')}",
                    "ApprovalGate",
                )
                return TaskResult.success(
                    outputs={
                        "approved": True,
                        "approval_type": approval_type,
                        "mode": "interactive",
                        "chosen_option": result.get("chosen_option"),
                        "user_feedback": result.get("feedback"),
                    }
                )
            else:
                notepad.add_entry(
                    "decision",
                    f"User rejected {approval_type}: {result.get('reason', 'No reason given')}",
                    "ApprovalGate",
                )
                return TaskResult.terminal(
                    error=f"Approval rejected: {result.get('reason', 'User rejected')}"
                )

        except KeyboardInterrupt:
            notepad.add_entry(
                "decision",
                f"User cancelled {approval_type} approval",
                "ApprovalGate",
            )
            return TaskResult.terminal(error="Approval cancelled by user")

    def _get_summary_from_upstream(self, stage: StageExecution) -> str:
        """Extract summary from upstream stage outputs.

        Args:
            stage: Current stage execution.

        Returns:
            Summary string from upstream.
        """
        for upstream in stage.upstream_stages():
            if upstream.outputs:
                # Look for common summary keys
                for key in ["aggregated_output", "combined_output", "summary"]:
                    if key in upstream.outputs:
                        value = upstream.outputs[key]
                        if isinstance(value, str):
                            return value[:2000]  # Truncate for display
        return "No summary available from upstream stages."

    def _request_interactive_approval(
        self,
        approval_type: str,
        summary: str,
        details: dict[str, Any],
        options: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Request approval interactively via console.

        Args:
            approval_type: Type of approval being requested.
            summary: Summary to display.
            details: Additional details.
            options: List of options to choose from (for architecture gates).

        Returns:
            Dict with approved, chosen_option, reason, feedback.
        """
        # Simple text output for CI/automation compatibility
        separator = "=" * 67

        print(f"\n{separator}")
        print(f"APPROVAL REQUIRED: {approval_type.replace('_', ' ').title()} Phase")
        print(f"{separator}\n")

        # Print summary
        print("Summary:")
        print("-" * 40)
        print(summary[:1500])  # Limit output
        if len(summary) > 1500:
            print("... (truncated)")
        print()

        # Print details if any
        if details:
            print("Details:")
            print("-" * 40)
            for key, value in details.items():
                if isinstance(value, list):
                    print(f"  {key}:")
                    for item in value[:10]:  # Limit to 10 items
                        print(f"    - {item}")
                else:
                    print(f"  {key}: {value}")
            print()

        # Print options if any (for architecture selection)
        if options:
            print("Options:")
            print("-" * 40)
            for i, opt in enumerate(options, 1):
                label = opt.get("label", f"Option {i}")
                description = opt.get("description", "")
                print(f"  [{i}] {label}")
                if description:
                    print(f"      {description}")
            print()

        # Get user input
        print("-" * 40)

        if options:
            print("Enter option number, or:")
        print("[A]pprove / [R]eject / [F]eedback: ", end="")
        sys.stdout.flush()

        try:
            user_input = input().strip().lower()
        except EOFError:
            # Non-interactive environment - auto-approve
            logger.warning("Non-interactive environment detected, auto-approving")
            return {"approved": True, "reason": "Non-interactive auto-approve"}

        # Parse input
        if user_input in ("a", "approve", "y", "yes"):
            return {"approved": True, "reason": "User approved"}

        if user_input in ("r", "reject", "n", "no"):
            print("Reason for rejection (optional): ", end="")
            sys.stdout.flush()
            try:
                reason = input().strip()
            except EOFError:
                reason = ""
            return {"approved": False, "reason": reason or "User rejected"}

        if user_input in ("f", "feedback"):
            print("Your feedback: ", end="")
            sys.stdout.flush()
            try:
                feedback = input().strip()
            except EOFError:
                feedback = ""
            return {"approved": True, "reason": "Approved with feedback", "feedback": feedback}

        # Check if it's an option number
        if options and user_input.isdigit():
            opt_num = int(user_input)
            if 1 <= opt_num <= len(options):
                chosen = options[opt_num - 1]
                return {
                    "approved": True,
                    "reason": f"Chose option: {chosen.get('label', opt_num)}",
                    "chosen_option": chosen.get("value", chosen.get("label")),
                }

        # Default to approve if input is ambiguous
        return {"approved": True, "reason": f"User input: {user_input}"}


class QuickApprovalGateTask(Task):
    """Lightweight approval gate that just checks mode and passes through.

    Used for gates where we don't need to display detailed information,
    just check if we should proceed based on approval mode.
    """

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute quick approval check.

        Expected context:
            - gate_name: Name of this gate for logging
            - continue_message: Message to show when continuing

        Returns:
            TaskResult - always succeeds unless YOLO/AUTO mode.
        """
        gate_name = stage.context.get("gate_name", "approval")
        continue_message = stage.context.get("continue_message", "Proceeding...")

        approval_manager = get_approval_manager()

        if approval_manager.mode in (ApprovalMode.YOLO, ApprovalMode.AUTO):
            logger.info(f"Quick gate '{gate_name}' passed ({approval_manager.mode.value})")
            return TaskResult.success(
                outputs={
                    "approved": True,
                    "gate_name": gate_name,
                    "mode": approval_manager.mode.value,
                }
            )

        # For default mode, show a simple prompt
        print(f"\n{continue_message}")
        print("Press Enter to continue, or Ctrl+C to cancel: ", end="")
        sys.stdout.flush()

        try:
            input()
            return TaskResult.success(
                outputs={
                    "approved": True,
                    "gate_name": gate_name,
                    "mode": "interactive",
                }
            )
        except (EOFError, KeyboardInterrupt):
            return TaskResult.terminal(error=f"Gate '{gate_name}' cancelled by user")
