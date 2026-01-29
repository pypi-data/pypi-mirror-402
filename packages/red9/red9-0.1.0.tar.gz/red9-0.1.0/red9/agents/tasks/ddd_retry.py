"""DDD Retry Task - Smart retry based on diagnosis.

This task is part of the autonomous error recovery system. It:
1. Routes based on recovery_action from compensation
2. For VERIFY_ONLY: Just re-runs verification with fixed command
3. For REGENERATE: Regenerates code with accumulated error context
4. Implements dynamic stopping via diagnosis feedback
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from stabilize import Task, TaskResult
from stabilize.errors import PermanentError
from stabilize.models.stage import StageExecution

from red9.agents.notepad import Notepad
from red9.logging import get_logger
from red9.providers.base import GenerationConfig, LLMProvider
from red9.sandbox import LocalSandbox
from red9.tools.base import ToolRegistry

logger = get_logger(__name__)

# Maximum recovery iterations (LLM decides within this, not hardcoded 3)
MAX_RECOVERY_ITERATIONS = 10

CODE_GEN_SYSTEM_PROMPT = """You are an expert code generator. Generate minimal, working code.

OUTPUT FORMAT - Return ONLY this JSON (no markdown, no explanation):
{"files": [{"path": "app.py", "content": "..."}], "run_command": "pytest -v"}

RULES:
1. MINIMIZE files - combine into 1-2 files when possible
2. Keep code SHORT - no excessive comments or docstrings
3. Use simple implementations (in-memory storage, not databases)
4. Include tests that actually verify the code works
5. Return ONLY the JSON object, nothing else
6. The run_command MUST test the code (use pytest, python -m unittest, or similar)
"""

FIX_CODE_PROMPT = """The previous code failed verification. Here is the accumulated context from {num_attempts} previous attempt(s).

## Error History (most recent last)
{error_history}

## Current Error
{current_error}

## Previous Files
{previous_files}

## Additional Context from Diagnosis
{diagnosis_context}

Fix the code to make the tests pass. Pay special attention to:
1. The specific error messages and what they indicate
2. Any patterns in repeated failures
3. The diagnosis context suggesting what to fix

Return the complete updated JSON with ALL files.
Return ONLY JSON: {{"files": [...], "run_command": "..."}}
"""


class DDDRetryTask(Task):
    """Smart retry that routes based on diagnosis.

    This task checks the recovery_action from the compensation stage:
    - VERIFY_ONLY: Environment was fixed, just re-run verification
    - REGENERATE: Code needs to be regenerated with error context
    - STOP: Terminal failure, don't proceed
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
    ) -> None:
        self.provider = provider
        self.tools = tool_registry

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the appropriate retry strategy."""
        # First check if DDD succeeded by looking at context
        ddd_success = stage.context.get("ddd_success")
        if ddd_success:
            logger.info("DDDRetry: DDD success detected in context - passing through")
            return TaskResult.success(
                outputs={
                    "recovery_action": "PASS_THROUGH",
                    "ddd_success": True,
                    "files_modified": stage.context.get("ddd_outputs", {}).get(
                        "files_modified", []
                    ),
                    "summary": "DDD succeeded, no retry needed",
                }
            )

        # Get compensation output from upstream
        upstream = stage.upstream_stages()

        # Check if upstream has PASS_THROUGH outputs
        if upstream and upstream[0].outputs:
            compensation_output = upstream[0].outputs
            if compensation_output.get("recovery_action") == "PASS_THROUGH":
                logger.info("DDDRetry: PASS_THROUGH from compensation - passing through")
                ddd_outputs = compensation_output.get("ddd_outputs", {})
                return TaskResult.success(
                    outputs={
                        "recovery_action": "PASS_THROUGH",
                        "ddd_success": True,
                        "files_modified": ddd_outputs.get("files_modified", []),
                        "summary": ddd_outputs.get("summary", "DDD succeeded, no retry needed"),
                    }
                )

        if not upstream or not upstream[0].outputs:
            # Last resort: if no error_output in context, assume DDD succeeded
            error_output = stage.context.get("error_output")
            if not error_output:
                logger.info(
                    "DDDRetry: No error_output and no upstream outputs - assuming DDD success"
                )
                return TaskResult.success(
                    outputs={
                        "recovery_action": "PASS_THROUGH",
                        "ddd_success": True,
                        "files_modified": [],
                        "summary": "No retry needed",
                    }
                )
            raise PermanentError("No compensation output found in upstream stages")

        compensation_output = upstream[0].outputs
        recovery_action = compensation_output.get("recovery_action", "REGENERATE")
        project_root = stage.context.get("project_root")
        workflow_id = stage.context.get("workflow_id")

        if not project_root:
            raise PermanentError("Missing project_root in context")

        root_path = Path(project_root)

        # Handle STOP action
        if recovery_action == "STOP":
            logger.warning("Recovery action is STOP - failing gracefully")
            return TaskResult.failed_continue(
                error="Recovery stopped by diagnosis (terminal failure)",
                outputs={
                    "recovery_action": "STOP",
                    "attempt_history": compensation_output.get("attempt_history", []),
                },
            )

        # Handle PASS_THROUGH - DDD succeeded, no retry needed
        if recovery_action == "PASS_THROUGH":
            logger.info("PASS_THROUGH: DDD succeeded, no retry needed")
            ddd_outputs = compensation_output.get("ddd_outputs", {})
            return TaskResult.success(
                outputs={
                    "recovery_action": "PASS_THROUGH",
                    "ddd_success": True,
                    "files_modified": ddd_outputs.get("files_modified", []),
                    "summary": ddd_outputs.get("summary", "DDD succeeded"),
                }
            )

        # Handle VERIFY_ONLY - just re-run the verification
        if recovery_action == "VERIFY_ONLY":
            return self._handle_verify_only(stage, compensation_output, root_path, workflow_id)

        # Handle REGENERATE - regenerate code with error context
        return self._handle_regenerate(stage, compensation_output, root_path, workflow_id)

    def _handle_verify_only(
        self,
        stage: StageExecution,
        compensation_output: dict[str, Any],
        root_path: Path,
        workflow_id: str | None,
    ) -> TaskResult:
        """Re-run verification with fixed command (no code regeneration)."""
        fixed_run_command = compensation_output.get("fixed_run_command", "pytest")
        attempt_history = compensation_output.get("attempt_history", [])

        logger.info(f"VERIFY_ONLY: Re-running with command: {fixed_run_command}")

        sandbox = LocalSandbox(root_path)
        result = sandbox.run_command(
            fixed_run_command,
            timeout=120,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        )

        if result.success:
            logger.info("VERIFY_ONLY: Verification PASSED after environment fix")
            if workflow_id:
                notepad = Notepad(root_path, workflow_id)
                msg = f"Recovery succeeded with VERIFY_ONLY after {len(attempt_history)} attempts"
                notepad.add_entry("learning", msg, "DDDRetryAgent")
            return TaskResult.success(
                outputs={
                    "verified": True,
                    "recovery_mode": "VERIFY_ONLY",
                    "attempt_history": attempt_history,
                }
            )

        # Still failing - need to escalate to REGENERATE
        error_output = (result.stdout + result.stderr)[-2000:]
        logger.warning("VERIFY_ONLY: Verification still failing, escalating to REGENERATE")

        # Trigger another diagnosis-compensation-retry cycle
        return TaskResult.failed_continue(
            error="Verification still failing after environment fix",
            outputs={
                "verified": False,
                "recovery_mode": "VERIFY_ONLY",
                "error_output": error_output,
            },
            context={
                "error_output": error_output,
                "failed_command": fixed_run_command,
                "attempt_history": attempt_history,
                "needs_regeneration": True,  # Signal to try code regeneration
            },
        )

    def _handle_regenerate(
        self,
        stage: StageExecution,
        compensation_output: dict[str, Any],
        root_path: Path,
        workflow_id: str | None,
    ) -> TaskResult:
        """Regenerate code with accumulated error context."""
        attempt_history = compensation_output.get("attempt_history", [])
        retry_context = compensation_output.get("retry_context", "")
        original_files = stage.context.get("original_files")

        # Check if we've hit max iterations
        if len(attempt_history) >= MAX_RECOVERY_ITERATIONS:
            logger.error(f"Max recovery iterations ({MAX_RECOVERY_ITERATIONS}) reached")
            return TaskResult.failed_continue(
                error=f"Max recovery iterations ({MAX_RECOVERY_ITERATIONS}) reached",
                outputs={
                    "verified": False,
                    "recovery_mode": "REGENERATE",
                    "attempt_history": attempt_history,
                },
            )

        notepad = Notepad(root_path, workflow_id) if workflow_id else None

        # Build error history for prompt
        error_history = self._format_error_history(attempt_history)

        # Prepare previous files JSON
        previous_files_json = "No previous files available"
        if original_files and isinstance(original_files, dict):
            files = original_files.get("files", [])
            if files:
                previous_files_json = json.dumps(files, indent=2)

        config = GenerationConfig(max_tokens=8192, temperature=0.3)

        # Build regeneration prompt
        prompt = FIX_CODE_PROMPT.format(
            num_attempts=len(attempt_history),
            error_history=error_history,
            current_error=(
                attempt_history[-1].get("explanation", "") if attempt_history else "Unknown"
            ),
            previous_files=previous_files_json,
            diagnosis_context=retry_context,
        )

        logger.info(f"REGENERATE: Iteration {len(attempt_history) + 1}")

        try:
            response = self.provider.generate(
                prompt, system_prompt=CODE_GEN_SYSTEM_PROMPT, config=config
            )

            files_data = self._parse_code_response(response)
            if not files_data or not files_data.get("files"):
                logger.warning("REGENERATE: Failed to parse code response")
                return TaskResult.failed_continue(
                    error="Failed to parse code regeneration response",
                    outputs={"verified": False, "recovery_mode": "REGENERATE"},
                    context={
                        "error_output": "Invalid JSON response from code generator",
                        "attempt_history": attempt_history,
                    },
                )

            # Write files
            files_modified = self._write_files(root_path, files_data["files"])
            run_command = files_data.get("run_command", "pytest")

            # Run verification
            return self._run_verification(
                root_path, run_command, files_modified, files_data, attempt_history, notepad
            )

        except Exception as e:
            logger.exception("REGENERATE: Code generation failed")
            return TaskResult.failed_continue(
                error=f"Code regeneration failed: {e}",
                outputs={"verified": False, "recovery_mode": "REGENERATE"},
                context={
                    "error_output": str(e),
                    "attempt_history": attempt_history,
                },
            )

    def _run_verification(
        self,
        root_path: Path,
        run_command: str,
        files_modified: list[str],
        files_data: dict[str, Any],
        attempt_history: list[dict],
        notepad: Notepad | None,
    ) -> TaskResult:
        """Run verification command using LocalSandbox and return appropriate result."""
        logger.info(f"REGENERATE: Running verification: {run_command}")

        sandbox = LocalSandbox(root_path)
        result = sandbox.run_command(
            run_command,
            timeout=120,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        )

        if result.success:
            logger.info("REGENERATE: Verification PASSED!")
            if notepad:
                msg = f"Recovery succeeded with REGENERATE after {len(attempt_history)} attempts"
                notepad.add_entry("learning", msg, "DDDRetryAgent")
            return TaskResult.success(
                outputs={
                    "files_modified": files_modified,
                    "verified": True,
                    "recovery_mode": "REGENERATE",
                    "iterations": len(attempt_history) + 1,
                }
            )

        # Failed - trigger another diagnosis cycle
        error_output = (result.stdout + result.stderr)[-2000:]
        logger.warning(f"REGENERATE: Verification failed, iteration {len(attempt_history) + 1}")

        return TaskResult.failed_continue(
            error="Verification failed after code regeneration",
            outputs={
                "files_modified": files_modified,
                "verified": False,
                "files_data": files_data,
            },
            context={
                "error_output": error_output,
                "failed_command": run_command,
                "attempt_history": attempt_history,
                "original_files": files_data,
            },
        )

    def _format_error_history(self, attempt_history: list[dict]) -> str:
        """Format attempt history for the prompt."""
        if not attempt_history:
            return "No previous attempts"

        lines = []
        for i, attempt in enumerate(attempt_history[-5:], 1):  # Last 5 attempts
            diag = attempt.get("diagnosis", "UNKNOWN")
            explanation = attempt.get("explanation", "No explanation")
            compensation = attempt.get("compensation", "None")
            lines.append(f"Attempt {i}:")
            lines.append(f"  Diagnosis: {diag}")
            lines.append(f"  Explanation: {explanation}")
            if compensation:
                lines.append(f"  Compensation tried: {compensation}")
            lines.append("")

        return "\n".join(lines)

    def _write_files(self, root_path: Path, files: list[dict[str, str]]) -> list[str]:
        """Write files to disk."""
        files_modified = []
        for file_info in files:
            file_path = root_path / file_info["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file_info["content"], encoding="utf-8")
            files_modified.append(str(file_path))
            logger.info(f"REGENERATE: Wrote {file_path}")
        return files_modified

    def _parse_code_response(self, response: str) -> dict | None:
        """Parse JSON code generation response."""
        response = response.strip()

        # Remove markdown code blocks if present
        if "```" in response:
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL)
            if match:
                response = match.group(1).strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in response
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

            logger.error(f"Failed to parse JSON: {response[:500]}")
            return None
