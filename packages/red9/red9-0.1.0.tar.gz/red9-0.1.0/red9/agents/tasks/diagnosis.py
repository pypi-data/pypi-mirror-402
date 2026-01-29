"""Diagnosis Agent - Analyzes failures and decides recovery strategy.

This task is part of the autonomous error recovery system. It analyzes
failure outputs and determines:
1. What type of failure occurred (CODE_BUG, ENV_SETUP, MISSING_DEP, etc.)
2. Whether to retry
3. What compensation action to take before retrying
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from stabilize import Task, TaskResult
from stabilize.errors import PermanentError
from stabilize.models.stage import StageExecution

from red9.logging import get_logger
from red9.providers.base import GenerationConfig, LLMProvider

logger = get_logger(__name__)

# Diagnosis categories
DIAGNOSIS_CODE_BUG = "CODE_BUG"
DIAGNOSIS_ENV_SETUP = "ENV_SETUP"
DIAGNOSIS_MISSING_DEP = "MISSING_DEP"
DIAGNOSIS_TRANSIENT = "TRANSIENT"
DIAGNOSIS_TERMINAL = "TERMINAL"
DIAGNOSIS_NO_ERROR = "NO_ERROR"  # DDD succeeded, no diagnosis needed

DIAGNOSIS_PROMPT = """You are a failure diagnosis expert. Analyze this error and decide the recovery strategy.

## Error Output
{error_output}

## Previous Attempts (most recent last)
{attempt_history}

## Project Context
- Root: {project_root}
- Command that failed: {failed_command}
- Files in project: {project_files}
- Environment variables relevant: VIRTUAL_ENV={virtual_env}

## Your Task
1. DIAGNOSE: What type of failure is this?
   - CODE_BUG: Logic error, test assertion failure, syntax error in generated code -> need to fix the code
   - ENV_SETUP: Wrong Python interpreter, venv not activated, wrong working directory -> fix command/environment
   - MISSING_DEP: Package not installed ("ModuleNotFoundError", "No module named") -> need pip install
   - TRANSIENT: Timeout, network issue, temporary lock -> just retry
   - TERMINAL: Impossible to fix (missing system library, hardware issue, permissions we can't change)

2. DECIDE: Should we retry?
   - **ALWAYS RETRY CODE_BUGs** at least 3 times. Do NOT give up on code bugs early.
   - If same error repeated 3+ times with same diagnosis and same compensation -> TERMINAL
   - If new information available or different approach possible -> worth retrying
   - If we haven't tried obvious fixes yet -> retry with compensation

3. COMPENSATE: What action fixes the root cause?
   - For ENV_SETUP: suggest modified run command (e.g., ".venv/bin/python -m pytest" instead of "pytest")
   - For MISSING_DEP: suggest "pip install <package>" or ".venv/bin/pip install <package>"
   - For CODE_BUG: no compensation command, but provide context for code regeneration. suggest checking logic.
   - For TRANSIENT: no compensation, just retry

## Stopping Criteria
Return should_retry=false if:
- Same error appeared 3+ times with no progress
- You've exhausted all reasonable compensation strategies
- The error is fundamentally unfixable (e.g., missing system library we can't install)
- You detect a loop (same diagnosis -> same compensation -> same error)

Return should_retry=true if:
- This is a new type of error
- Previous compensation was wrong and you have a better idea
- The error message contains new information
- You haven't tried obvious fixes yet
- It is a CODE_BUG (we should almost always try to fix code)

Return ONLY valid JSON (no markdown, no explanation):
{{
  "diagnosis": "CODE_BUG|ENV_SETUP|MISSING_DEP|TRANSIENT|TERMINAL",
  "explanation": "Brief explanation of what went wrong (1-2 sentences)",
  "should_retry": true|false,
  "compensation_command": "shell command to run before retry, or null if not needed",
  "fixed_run_command": "modified run command if ENV_SETUP, or null to use original",
  "retry_with_context": "Additional context to include in next code generation prompt (for CODE_BUG)",
  "confidence": 0.0-1.0
}}
"""


class DiagnosisTask(Task):
    """Analyzes failures and determines recovery strategy.

    This task examines error output, attempt history, and project context
    to diagnose the failure type and decide whether/how to retry.
    """

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def execute(self, stage: StageExecution) -> TaskResult:
        """Analyze the failure and decide on recovery strategy."""
        error_output = stage.context.get("error_output", "")
        attempt_history = stage.context.get("attempt_history", [])
        project_root = stage.context.get("project_root")
        failed_command = stage.context.get("failed_command", "pytest")

        if not project_root:
            raise PermanentError("Missing project_root in diagnosis context")

        # Check if DDD succeeded or failed by looking at upstream stage
        upstream = stage.upstream_stages()
        ddd_stage = upstream[0] if upstream else None

        # Try to get error_output from multiple sources:
        # 1. Current stage context (might be propagated)
        # 2. Upstream DDD stage outputs (where DDD puts it on failure)
        if not error_output and ddd_stage:
            # Check DDD stage outputs for error info
            ddd_outputs = ddd_stage.outputs or {}
            # If DDD had files_modified but no error, it succeeded
            if ddd_outputs.get("files_modified") and not ddd_outputs.get("error"):
                # DDD succeeded - pass through
                logger.info(
                    "Diagnosis: DDD succeeded (has files_modified, no error) - passing through"
                )
                return TaskResult.success(
                    outputs={
                        "diagnosis": {
                            "diagnosis": DIAGNOSIS_NO_ERROR,
                            "explanation": "DDD succeeded, no error to diagnose",
                            "should_retry": False,
                            "compensation_command": None,
                            "fixed_run_command": None,
                            "retry_with_context": "",
                            "confidence": 1.0,
                        },
                        "attempt_history": attempt_history,
                        "recovery_action": "PASS_THROUGH",
                        "ddd_success": True,
                        "ddd_outputs": ddd_outputs,
                    },
                    context={
                        "ddd_success": True,
                        "ddd_outputs": ddd_outputs,
                    },
                )

        # If still no error_output, check if DDD stage had an error in its outputs
        if not error_output and ddd_stage and ddd_stage.outputs:
            # DDD's failed_continue puts files_data but also has error indication
            # Check if there's files_data (partial success) or other error indicators
            pass  # Continue to diagnosis

        root_path = Path(project_root)

        # Get project file listing for context (limited to relevant files)
        project_files = self._list_project_files(root_path)
        virtual_env = os.environ.get("VIRTUAL_ENV", "not set")

        # Check for obvious patterns before calling LLM
        quick_diagnosis = self._quick_pattern_match(error_output, root_path)
        if quick_diagnosis and quick_diagnosis.get("high_confidence"):
            logger.info(f"Diagnosis (quick match): {quick_diagnosis['diagnosis']}")
            return self._build_result(quick_diagnosis, attempt_history)

        # Use LLM for complex diagnosis
        prompt = DIAGNOSIS_PROMPT.format(
            error_output=error_output[-4000:],  # Last 4000 chars
            attempt_history=json.dumps(attempt_history[-5:], indent=2),  # Last 5 attempts
            project_root=project_root,
            failed_command=failed_command,
            project_files=project_files,
            virtual_env=virtual_env,
        )

        try:
            response = self.provider.generate(
                prompt,
                system_prompt="You are a DevOps and debugging expert. Return only valid JSON.",
                config=GenerationConfig(max_tokens=1024, temperature=0.2),
            )

            diagnosis = self._parse_json(response)
            if not diagnosis:
                logger.warning("Failed to parse LLM diagnosis, using fallback")
                diagnosis = self._fallback_diagnosis(error_output)

        except Exception as e:
            logger.warning(f"LLM diagnosis failed: {e}, using fallback")
            diagnosis = self._fallback_diagnosis(error_output)

        diag_type = diagnosis.get("diagnosis")
        explanation = diagnosis.get("explanation", "")[:100]
        logger.info(f"Diagnosis: {diag_type} - {explanation}")
        return self._build_result(diagnosis, attempt_history)

    def _build_result(self, diagnosis: dict[str, Any], attempt_history: list[dict]) -> TaskResult:
        """Build TaskResult from diagnosis."""
        # Record this attempt in history
        new_history = list(attempt_history)
        new_history.append(
            {
                "diagnosis": diagnosis.get("diagnosis"),
                "compensation": diagnosis.get("compensation_command"),
                "explanation": diagnosis.get("explanation", "")[:200],
            }
        )

        # Check for terminal or no-retry
        is_terminal = diagnosis.get("diagnosis") == DIAGNOSIS_TERMINAL
        should_not_retry = not diagnosis.get("should_retry", True)
        if is_terminal or should_not_retry:
            return TaskResult.failed_continue(
                error=f"Terminal failure: {diagnosis.get('explanation', 'Unknown')}",
                outputs={
                    "diagnosis": diagnosis,
                    "attempt_history": new_history,
                    "recovery_action": "STOP",
                },
                context={
                    "recovery_action": "STOP",
                },
            )

        # Determine recovery action based on diagnosis type
        diag_type = diagnosis.get("diagnosis", DIAGNOSIS_CODE_BUG)
        if diag_type in (DIAGNOSIS_ENV_SETUP, DIAGNOSIS_MISSING_DEP):
            recovery_action = "VERIFY_ONLY"  # Just re-run with fixed command
        else:
            recovery_action = "REGENERATE"  # Need to regenerate code

        return TaskResult.success(
            outputs={
                "diagnosis": diagnosis,
                "attempt_history": new_history,
                "compensation_command": diagnosis.get("compensation_command"),
                "fixed_run_command": diagnosis.get("fixed_run_command"),
                "retry_context": diagnosis.get("retry_with_context", ""),
                "recovery_action": recovery_action,
            }
        )

    def _quick_pattern_match(self, error_output: str, root_path: Path) -> dict[str, Any] | None:
        """Quick pattern matching for common error types."""
        error_lower = error_output.lower()

        # Check for venv-related issues
        venv_path = root_path / ".venv"
        has_venv = venv_path.exists()

        # ModuleNotFoundError with venv available
        if "modulenotfounderror" in error_lower or "no module named" in error_lower:
            if has_venv:
                # Extract module name
                import re

                match = re.search(r"no module named ['\"]?(\w+)", error_lower)
                module = match.group(1) if match else "unknown"

                # Check if it's a venv activation issue vs missing package
                if module in ("pytest", "mypy", "ruff", "black"):
                    return {
                        "diagnosis": DIAGNOSIS_ENV_SETUP,
                        "explanation": f"Test runner '{module}' not found - venv not activated",
                        "should_retry": True,
                        "compensation_command": None,
                        "fixed_run_command": f".venv/bin/python -m {module}",
                        "retry_with_context": "",
                        "confidence": 0.9,
                        "high_confidence": True,
                    }
                else:
                    return {
                        "diagnosis": DIAGNOSIS_MISSING_DEP,
                        "explanation": f"Module '{module}' not installed",
                        "should_retry": True,
                        "compensation_command": f".venv/bin/pip install {module}",
                        "fixed_run_command": ".venv/bin/python -m pytest",
                        "retry_with_context": "",
                        "confidence": 0.85,
                        "high_confidence": True,
                    }

        # Syntax errors are code bugs
        if "syntaxerror" in error_lower:
            return {
                "diagnosis": DIAGNOSIS_CODE_BUG,
                "explanation": "Syntax error in generated code",
                "should_retry": True,
                "compensation_command": None,
                "fixed_run_command": None,
                "retry_with_context": f"Previous code had syntax error:\n{error_output[-1000:]}",
                "confidence": 0.95,
                "high_confidence": True,
            }

        # Assertion errors are code bugs (test failures)
        if "assertionerror" in error_lower or "assert" in error_lower and "failed" in error_lower:
            # Check how many times we've tried to fix this
            # If less than 3 attempts, definitely retry
            # logic is handled in _build_result mostly, but we set should_retry=True here explicitly
            return {
                "diagnosis": DIAGNOSIS_CODE_BUG,
                "explanation": "Test assertion failed - logic error in code",
                "should_retry": True,
                "compensation_command": None,
                "fixed_run_command": None,
                "retry_with_context": f"Tests failed with assertion error:\n{error_output[-1500:]}",
                "confidence": 0.9,
                "high_confidence": True,
            }

        # Connection/network errors are transient
        if any(x in error_lower for x in ["connection", "timeout", "network", "econnrefused"]):
            return {
                "diagnosis": DIAGNOSIS_TRANSIENT,
                "explanation": "Network/connection error - likely transient",
                "should_retry": True,
                "compensation_command": None,
                "fixed_run_command": None,
                "retry_with_context": "",
                "confidence": 0.8,
                "high_confidence": True,
            }

        return None  # No quick match, use LLM

    def _fallback_diagnosis(self, error_output: str) -> dict[str, Any]:
        """Fallback diagnosis when LLM fails."""
        error_lower = error_output.lower()

        if "modulenotfounderror" in error_lower or "no module named" in error_lower:
            return {
                "diagnosis": DIAGNOSIS_MISSING_DEP,
                "explanation": "Module not found - dependency issue",
                "should_retry": True,
                "compensation_command": None,
                "retry_with_context": "",
            }

        return {
            "diagnosis": DIAGNOSIS_CODE_BUG,
            "explanation": "Assuming code bug - verification failed",
            "should_retry": True,
            "compensation_command": None,
            "retry_with_context": f"Previous attempt failed:\n{error_output[-1000:]}",
        }

    def _list_project_files(self, root_path: Path, max_files: int = 30) -> str:
        """List relevant project files for context."""
        files = []
        ignore_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", ".red9"}

        try:
            for item in root_path.rglob("*"):
                if any(d in item.parts for d in ignore_dirs):
                    continue
                if item.is_file() and item.suffix in (".py", ".toml", ".cfg", ".txt", ".sh"):
                    rel = item.relative_to(root_path)
                    files.append(str(rel))
                    if len(files) >= max_files:
                        break
        except Exception as e:
            logger.warning(f"Error listing project files: {e}")

        return "\n".join(files[:max_files])

    def _parse_json(self, response: str) -> dict[str, Any] | None:
        """Parse JSON from LLM response."""
        import re

        response = response.strip()

        # Remove markdown code blocks
        if "```" in response:
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL)
            if match:
                response = match.group(1).strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

        return None
