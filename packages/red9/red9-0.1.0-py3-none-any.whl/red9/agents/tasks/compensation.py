"""Compensation Task - Executes recovery actions and routes to appropriate retry strategy.

This task is part of the autonomous error recovery system. It:
1. Executes compensation commands (pip install, env fixes, etc.)
2. Routes to the appropriate retry strategy based on diagnosis
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from stabilize import Task, TaskResult
from stabilize.errors import PermanentError
from stabilize.models.stage import StageExecution

from red9.logging import get_logger
from red9.sandbox import LocalSandbox

logger = get_logger(__name__)


class CompensationTask(Task):
    """Executes compensation and routes to appropriate retry strategy.

    Based on the diagnosis:
    - VERIFY_ONLY: Environment was fixed, just re-run verification
    - REGENERATE: Code needs to be regenerated with error context
    - STOP: Terminal failure, don't retry
    """

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute compensation command and prepare for retry."""
        # First check if DDD succeeded by looking at context
        # This handles the case where diagnosis passed through
        ddd_success = stage.context.get("ddd_success")
        if ddd_success:
            logger.info("Compensation: DDD success detected in context - passing through")
            return TaskResult.success(
                outputs={
                    "recovery_action": "PASS_THROUGH",
                    "ddd_success": True,
                    "ddd_outputs": stage.context.get("ddd_outputs", {}),
                }
            )

        # Check if there's no error_output in context (DDD succeeded)
        error_output = stage.context.get("error_output")
        if not error_output:
            # Look at the DDD stage (grandparent) to check if it succeeded
            # Diagnosis stage is the parent, DDD is the grandparent
            upstream = stage.upstream_stages()
            if upstream:
                diagnosis_stage = upstream[0]
                # Check if diagnosis passed through
                if (
                    diagnosis_stage.outputs
                    and diagnosis_stage.outputs.get("recovery_action") == "PASS_THROUGH"
                ):
                    logger.info(
                        "Compensation: PASS_THROUGH detected from diagnosis - passing through"
                    )
                    return TaskResult.success(
                        outputs={
                            "recovery_action": "PASS_THROUGH",
                            "ddd_success": True,
                            "ddd_outputs": diagnosis_stage.outputs.get("ddd_outputs", {}),
                        }
                    )
                # Check if diagnosis itself indicated no error
                ddd_outputs = (
                    diagnosis_stage.outputs.get("ddd_outputs") if diagnosis_stage.outputs else None
                )
                if ddd_outputs:
                    logger.info(
                        "Compensation: No error in context, DDD outputs found - passing through"
                    )
                    return TaskResult.success(
                        outputs={
                            "recovery_action": "PASS_THROUGH",
                            "ddd_success": True,
                            "ddd_outputs": ddd_outputs,
                        }
                    )

        # Get diagnosis output from upstream stage
        upstream = stage.upstream_stages()
        if not upstream or not upstream[0].outputs:
            # Last resort: check if there's truly no error to handle
            if not error_output:
                logger.info(
                    "Compensation: No error_output and no upstream outputs - assuming DDD success"
                )
                return TaskResult.success(
                    outputs={
                        "recovery_action": "PASS_THROUGH",
                        "ddd_success": True,
                        "ddd_outputs": {},
                    }
                )
            raise PermanentError("No diagnosis output found in upstream stages")

        diagnosis_output = upstream[0].outputs

        # Check for PASS_THROUGH case (DDD succeeded, no compensation needed)
        recovery_action = diagnosis_output.get("recovery_action")
        if recovery_action == "PASS_THROUGH":
            logger.info("Compensation: PASS_THROUGH mode - DDD succeeded, nothing to compensate")
            return TaskResult.success(
                outputs={
                    "recovery_action": "PASS_THROUGH",
                    "ddd_success": True,
                    "ddd_outputs": diagnosis_output.get("ddd_outputs", {}),
                }
            )

        diagnosis = diagnosis_output.get("diagnosis", {})
        compensation_cmd = diagnosis_output.get("compensation_command")
        fixed_run_command = diagnosis_output.get("fixed_run_command")
        project_root = stage.context.get("project_root")
        recovery_action = diagnosis_output.get("recovery_action", "REGENERATE")

        if not project_root:
            raise PermanentError("Missing project_root in context")

        root_path = Path(project_root)

        # Check for STOP action (terminal failure)
        if recovery_action == "STOP":
            logger.warning("Recovery action is STOP - not retrying")
            return TaskResult.failed_continue(
                error="Terminal failure - recovery stopped",
                outputs={
                    "recovery_action": "STOP",
                    "diagnosis": diagnosis,
                    "attempt_history": diagnosis_output.get("attempt_history", []),
                },
            )

        # Execute compensation command if provided
        compensation_result = None
        if compensation_cmd:
            logger.info(f"Executing compensation: {compensation_cmd}")
            compensation_result = self._run_compensation(compensation_cmd, root_path)

            if not compensation_result["success"]:
                logger.warning(f"Compensation command failed: {compensation_result['error']}")
                # Don't fail the stage - let retry try anyway
                # Some compensations (like pip install) might partially succeed

        # Build outputs for retry stage
        outputs: dict[str, Any] = {
            "recovery_action": recovery_action,
            "diagnosis": diagnosis,
            "attempt_history": diagnosis_output.get("attempt_history", []),
            "compensation_result": compensation_result,
        }

        if recovery_action == "VERIFY_ONLY":
            # Environment issue fixed - use the fixed run command
            outputs["fixed_run_command"] = fixed_run_command or self._detect_run_command(root_path)
            logger.info(f"VERIFY_ONLY mode - will run: {outputs['fixed_run_command']}")
        else:
            # REGENERATE mode - pass context for code regeneration
            outputs["retry_context"] = diagnosis_output.get("retry_context", "")
            logger.info("REGENERATE mode - code will be regenerated with error context")

        return TaskResult.success(outputs=outputs)

    def _run_compensation(self, command: str, root_path: Path) -> dict[str, Any]:
        """Execute a compensation command using LocalSandbox."""
        sandbox = LocalSandbox(root_path)
        result = sandbox.run_command(
            command,
            timeout=180,  # 3 minute timeout for installs
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        )

        return {
            "success": result.success,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-2000:] if result.stderr else "",
            "error": None if result.success else f"Exit code {result.exit_code}",
        }

    def _detect_run_command(self, root_path: Path) -> str:
        """Detect the appropriate run command for the project."""
        venv_path = root_path / ".venv"

        # Check for common test configurations
        if (root_path / "pytest.ini").exists() or (root_path / "pyproject.toml").exists():
            if venv_path.exists():
                return ".venv/bin/python -m pytest"
            return "python -m pytest"

        if (root_path / "setup.py").exists():
            if venv_path.exists():
                return ".venv/bin/python -m pytest"
            return "python -m pytest"

        # Default
        if venv_path.exists():
            return ".venv/bin/python -m pytest"
        return "pytest"
