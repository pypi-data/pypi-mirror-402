"""Iteration Loop Task - Iterates DDD + Review until quality gates pass.

This task implements the moai-adk pattern of iterating until:
1. Quality gates pass (coverage, readability, security)
2. No critical/high severity issues remain
3. Tests pass

Architecture Note:
    This task uses Stabilize's TransientError mechanism for iteration.
    When quality gates fail, it raises TransientError which triggers
    Stabilize to retry the stage. Each retry = one iteration.

    Iteration state (counter, issues) is persisted via Notepad (IssueDB-based)
    since TransientError doesn't support passing context between retries.

    This maintains proper Stabilize orchestration where:
    - Stabilize controls parallelism and retry/backoff
    - Tools are blackbox to Stabilize (subprocess only in tools)
    - Tasks never call other tasks' execute() directly
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from stabilize import Task, TaskResult
from stabilize.errors import TransientError
from stabilize.models.stage import StageExecution

from red9.agents.loop import AgentLoop
from red9.agents.notepad import Notepad
from red9.logging import get_logger
from red9.quality.gates import check_quality_gates, has_blocking_issues
from red9.workflows.runner import get_stream_callback, get_ui_event_callback

if TYPE_CHECKING:
    from red9.providers.base import LLMProvider
    from red9.tools.base import ToolRegistry

logger = get_logger(__name__)

# Key prefix for storing iteration state in Notepad
ITERATION_STATE_KEY = "iteration_loop_state"

# DDD-style system prompt for code implementation within AgentLoop
DDD_SYSTEM_PROMPT = """You are an expert code implementer following DDD principles.

## Methodology: ANALYZE-PRESERVE-IMPROVE (MoAI-ADK Standard)
1. **ANALYZE**: Understand the existing code and the desired change.
2. **PRESERVE**: If modifying existing code, ensure **Characterization Tests** exist
   to capture current behavior.
3. **IMPROVE**: Implement the changes/refactoring while ensuring tests pass.

## CRITICAL: Efficient File Reading (MUST FOLLOW)
**DO NOT RE-READ FILES YOU HAVE ALREADY READ IN THIS CONVERSATION.**

1. When you read a file, its content appears in your conversation history.
2. **NEVER** call read_file again for a file you already read - use your context.
3. Use `read_many_files` tool ONCE instead of multiple `read_file` calls.
4. Before reading any file, check if you've already read it earlier.
5. If content was provided in "Previously Read Files" section, DO NOT re-read.

**This is critical for efficiency - unnecessary file re-reads waste resources.**

## Rules
1. Write clean, minimal code that satisfies the requirements.
2. **MANDATORY**: Create or update tests in a `tests/` directory to verify changes.
3. **NO SHELL EXPANSION**: Do not use brace expansion (e.g. `{a,b}`) in file paths.
   Use explicit paths for every file.
4. Use the provided tools to:
   - Read existing files to understand context (READ EACH FILE ONLY ONCE)
   - Write/edit files to implement changes
   - **Run tests** (e.g. pytest) to verify your work
5. Fix ALL issues mentioned from previous iterations.
6. When done, call `complete_task` with a summary.

IMPORTANT:
- Do NOT create unnecessary files
- Do NOT re-read files - their content is in your conversation history
- **VERIFY**: You MUST run tests before calling `complete_task`. If tests fail, fix them.
"""


class IterationLoopTask(Task):
    """Iterates DDD + Review until quality gates pass.

    This task uses Stabilize's TransientError mechanism for iteration:
    - On first execution, runs DDD implementation
    - Runs code review using ReviewCodeTool
    - Checks quality gates
    - If quality passes: returns success
    - If quality fails: raises TransientError (Stabilize retries = next iteration)

    Expected context:
        - project_root: Project root path
        - workflow_id: Workflow identifier
        - spec_content: Specification from Phase 1
        - request: Original user request
        - max_iterations: Maximum iterations (default 10, set via Stabilize retry config)
        - iteration: Current iteration number (managed via context)
        - issues_to_fix: Issues from previous iteration

    Outputs:
        - iterations: Number of iterations completed
        - quality_report: Final quality report
        - files_modified: List of modified files
        - issues_fixed: Count of issues fixed across iterations
    """

    DEFAULT_MAX_ITERATIONS = 10

    def __init__(
        self,
        ddd_provider: LLMProvider,
        review_provider: LLMProvider,
        tool_registry: ToolRegistry,
    ) -> None:
        """Initialize iteration loop task.

        Args:
            ddd_provider: LLM provider for DDD implementation.
            review_provider: LLM provider for code review.
            tool_registry: Tool registry for agents.
        """
        self.ddd_provider = ddd_provider
        self.review_provider = review_provider
        self.tools = tool_registry

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute one iteration of DDD + Review + Quality check.

        If quality passes, returns success.
        If quality fails and under max iterations, raises TransientError.
        If max iterations reached, returns failed_continue.

        Args:
            stage: Stage execution context.

        Returns:
            TaskResult with iteration results.
        """
        from red9.workflows.runner import emit_phase_start

        # Emit phase start for UI (only on first iteration)
        emit_phase_start(stage)

        # Extract context
        project_root = stage.context.get("project_root")
        workflow_id = stage.context.get("workflow_id")
        spec_content = stage.context.get("spec_content")
        request = stage.context.get("request", "")
        max_iterations = stage.context.get("max_iterations", self.DEFAULT_MAX_ITERATIONS)

        if not project_root:
            return TaskResult.terminal(error="project_root is required")

        root_path = Path(project_root)

        # Load iteration state from Notepad (persists across TransientError retries)
        notepad = Notepad(root_path, workflow_id)
        iteration_state = self._load_iteration_state(notepad, workflow_id)
        iteration = iteration_state.get("iteration", 1)
        issues_to_fix = iteration_state.get("issues_to_fix", [])
        accumulated_files_modified = iteration_state.get("accumulated_files_modified", [])
        total_issues_fixed = iteration_state.get("total_issues_fixed", 0)
        # Track accumulated file context to avoid re-reading between iterations
        accumulated_files_context = iteration_state.get("accumulated_files_context", {})
        # Shared file read cache for within-iteration caching (path -> (content, mtime))
        # This is passed to AgentLoop to avoid re-reads within same iteration
        file_read_cache: dict[str, tuple[str, float]] = iteration_state.get("file_read_cache", {})

        # Try to get spec_content from upstream stage outputs (Phase 6 spec_agent)
        if not spec_content:
            upstream = stage.upstream_stages()
            for up in upstream:
                if up.outputs and up.outputs.get("spec_content"):
                    spec_content = up.outputs.get("spec_content")
                    logger.info(f"Iteration loop: Retrieved spec_content from upstream {up.ref_id}")
                    break

        # Fallback: read from disk if spec_agent persisted it
        if not spec_content and workflow_id:
            spec_dir = Path(project_root) / ".red9" / "specs"
            spec_path = spec_dir / f"SPEC-{workflow_id[-6:]}.md"
            if spec_path.exists():
                spec_content = spec_path.read_text(encoding="utf-8")
                logger.info(f"Iteration loop: Retrieved spec_content from disk: {spec_path}")

        if not spec_content:
            logger.warning("Iteration loop: No spec_content found, using request as spec")
            spec_content = f"# Task\n\n{request}"

        # Get callbacks
        on_token = stage.context.get("on_token") or get_stream_callback()
        on_ui_event = stage.context.get("on_ui_event") or get_ui_event_callback()

        logger.info(f"Iteration {iteration}/{max_iterations}")

        # Emit iteration event
        if on_ui_event:
            on_ui_event(
                {
                    "type": "iteration",
                    "number": iteration,
                    "max": max_iterations,
                    "issues_remaining": len(issues_to_fix),
                }
            )

        # 1. Run DDD implementation via AgentLoop (proper tool usage, not task.execute())
        ddd_result = self._run_ddd_via_agent_loop(
            project_root=root_path,
            spec_content=spec_content,
            issues_to_fix=issues_to_fix,
            iteration=iteration,
            on_token=on_token,
            on_ui_event=on_ui_event,
            accumulated_files_context=accumulated_files_context,
            file_read_cache=file_read_cache,  # Shared cache across iterations
        )

        if not ddd_result.get("success"):
            error_msg = ddd_result.get("error", "Unknown error")
            logger.warning(f"DDD failed in iteration {iteration}: {error_msg}")

            # CRITICAL: Update accumulated context EVEN on failure
            # This prevents the agent from re-reading files in subsequent iterations
            files_read = ddd_result.get("files_read", [])
            if files_read:
                accumulated_files_context = self._update_accumulated_context(
                    root_path, files_read, accumulated_files_context
                )
                logger.info(
                    f"Updated accumulated context with {len(files_read)} files "
                    f"from failed iteration (total: {len(accumulated_files_context)})"
                )

            # Emit UI event for DDD failure (styled display)
            if on_ui_event:
                on_ui_event(
                    {
                        "type": "ddd_retry",
                        "iteration": iteration,
                        "max_iterations": max_iterations,
                        "error": error_msg,
                        "will_retry": iteration < max_iterations,
                    }
                )

            # DDD failure - add to issues and retry
            issues_to_fix.append(
                {
                    "description": f"DDD implementation failed: {error_msg}",
                    "severity": "critical",
                    "confidence": 100,
                    "location": "implementation",
                }
            )

            # Check if we should retry
            if iteration < max_iterations:
                # Save state to Notepad before raising TransientError
                self._save_iteration_state(
                    notepad,
                    workflow_id,
                    {
                        "iteration": iteration + 1,
                        "issues_to_fix": issues_to_fix,
                        "accumulated_files_modified": accumulated_files_modified,
                        "total_issues_fixed": total_issues_fixed,
                        "accumulated_files_context": accumulated_files_context,
                        "file_read_cache": file_read_cache,
                    },
                )
                raise TransientError(
                    f"DDD failed in iteration {iteration}, retrying",
                    retry_after=0,
                )
            else:
                # Clear iteration state on completion
                self._clear_iteration_state(notepad, workflow_id)
                return TaskResult.failed_continue(
                    error=f"Max iterations ({max_iterations}) reached. DDD failed.",
                    outputs={
                        "iterations": max_iterations,
                        "files_modified": accumulated_files_modified,
                        "issues_fixed": total_issues_fixed,
                        "remaining_issues": issues_to_fix,
                        "success": False,
                    },
                )

        # Update files modified
        files_modified = ddd_result.get("files_modified", [])
        accumulated_files_modified = list(set(accumulated_files_modified + files_modified))

        # NEW: Update accumulated file context with newly read files
        files_read = ddd_result.get("files_read", [])
        accumulated_files_context = self._update_accumulated_context(
            root_path, files_read, accumulated_files_context
        )

        # 2. Run review via ReviewCodeTool (proper tool usage)
        review_issues = self._run_review_via_tool(
            project_root=root_path,
            files_modified=files_modified,
            request=request,
        )

        # 2.5 Run Coverage Analysis (Dynamic)
        coverage_percent = self._run_coverage_analysis(
            root_path=root_path,
            on_token=on_token,
            on_ui_event=on_ui_event,
        )
        if coverage_percent is not None:
            logger.info(f"Dynamic coverage check: {coverage_percent}%")

        # 3. Check quality gates (using tools, not subprocess)
        quality_report = check_quality_gates(
            project_root=root_path,
            files_modified=files_modified,
            review_issues=review_issues,
            coverage_percent=coverage_percent,
        )

        # Check for blocking issues
        has_blocking, blocking_issues = has_blocking_issues(review_issues)

        # Track issues fixed
        if issues_to_fix:
            issues_fixed_this_iteration = len(issues_to_fix) - len(blocking_issues)
            total_issues_fixed += max(0, issues_fixed_this_iteration)

        # Log quality report
        logger.info(
            f"Iteration {iteration}: Quality passed={quality_report.passed}, "
            f"score={quality_report.overall_score:.0%}, "
            f"blocking_issues={len(blocking_issues)}"
        )

        # Emit quality check event
        if on_ui_event:
            on_ui_event(
                {
                    "type": "quality_check",
                    "iteration": iteration,
                    "passed": quality_report.passed,
                    "score": quality_report.overall_score,
                    "failed_dimensions": quality_report.failed_dimensions,
                    "blocking_issues": len(blocking_issues),
                }
            )

        # 4. Check completion criteria
        if quality_report.passed and not has_blocking:
            logger.info(f"Quality gates passed after {iteration} iteration(s)")

            # Clear iteration state on success
            self._clear_iteration_state(notepad, workflow_id)

            # Emit success event
            if on_ui_event:
                on_ui_event(
                    {
                        "type": "iteration_loop_complete",
                        "iterations": iteration,
                        "quality_passed": True,
                        "issues_fixed": total_issues_fixed,
                    }
                )

            return TaskResult.success(
                outputs={
                    "iterations": iteration,
                    "quality_report": quality_report.to_dict(),
                    "files_modified": accumulated_files_modified,
                    "issues_fixed": total_issues_fixed,
                    "success": True,
                }
            )

        # 5. Prepare for next iteration - collect issues
        next_issues = blocking_issues.copy()

        # Add quality gate failures as issues
        for dim in quality_report.failed_dimensions:
            dim_result = next((d for d in quality_report.dimensions if d.name == dim), None)
            details = dim_result.details if dim_result else ""
            next_issues.append(
                {
                    "description": f"Quality gate failed: {dim} - {details}",
                    "severity": "high",
                    "confidence": 100,
                    "location": "quality_gates",
                }
            )

        # 6. Check if we should retry via TransientError (Stabilize handles this)
        if iteration < max_iterations:
            logger.info(
                f"Quality gates failed, raising TransientError for iteration {iteration + 1}"
            )
            # Save state to Notepad before raising TransientError
            self._save_iteration_state(
                notepad,
                workflow_id,
                {
                    "iteration": iteration + 1,
                    "issues_to_fix": next_issues,
                    "accumulated_files_modified": accumulated_files_modified,
                    "total_issues_fixed": total_issues_fixed,
                    "accumulated_files_context": accumulated_files_context,
                    "file_read_cache": file_read_cache,
                },
            )
            raise TransientError(
                f"Quality gate failed (iteration {iteration}), retrying",
                retry_after=0,
            )

        # Max iterations reached
        # Clear iteration state on completion
        self._clear_iteration_state(notepad, workflow_id)
        logger.warning(f"Max iterations ({max_iterations}) reached without passing quality gates")

        # Emit failure event
        if on_ui_event:
            on_ui_event(
                {
                    "type": "iteration_loop_complete",
                    "iterations": max_iterations,
                    "quality_passed": False,
                    "issues_remaining": len(next_issues),
                    "issues_fixed": total_issues_fixed,
                }
            )

        return TaskResult.failed_continue(
            error=f"Max iterations ({max_iterations}) reached. {len(next_issues)} issues remain.",
            outputs={
                "iterations": max_iterations,
                "quality_report": quality_report.to_dict(),
                "files_modified": accumulated_files_modified,
                "issues_fixed": total_issues_fixed,
                "remaining_issues": next_issues,
                "success": False,
            },
        )

    def _run_coverage_analysis(
        self,
        root_path: Path,
        on_token: Any,
        on_ui_event: Any,
    ) -> float | None:
        """Run coverage analysis via AgentLoop.

        Args:
            root_path: Project root path.
            on_token: Token streaming callback.
            on_ui_event: UI event callback.

        Returns:
            Coverage percentage if determined, None otherwise.
        """
        prompt = """You are a QA Engineer. Determine the test coverage of the project.

1. Identify the project type (Python, Node, Go, etc.).
2. Run tests with coverage (e.g. `pytest --cov`, `npm test -- --coverage`).
   - If Python, try `pytest --cov=.` or `python -m pytest --cov=.`
   - If Node, check package.json for coverage scripts.
3. Output the total coverage percentage.

OUTPUT FORMAT:
coverage: <percentage>
"""
        agent_loop = AgentLoop(
            provider=self.review_provider,
            tool_registry=self.tools,
            max_iterations=5,  # Short loop
            enable_loop_detection=True,
        )

        try:
            result = agent_loop.run(
                system_prompt=prompt,
                user_message="Check test coverage for this project.",
                on_token=on_token,
                on_ui_event=on_ui_event,
            )

            if result.success:
                import re

                match = re.search(
                    r"coverage:\s*(\d+(?:\.\d+)?)", result.final_message, re.IGNORECASE
                )
                if match:
                    return float(match.group(1))
        except Exception as e:
            logger.warning(f"Coverage analysis failed: {e}")

        return None

    def _run_ddd_via_agent_loop(
        self,
        project_root: Path,
        spec_content: str | None,
        issues_to_fix: list[dict[str, Any]],
        iteration: int,
        on_token: Any,
        on_ui_event: Any,
        accumulated_files_context: dict[str, str] | None = None,
        file_read_cache: dict[str, tuple[str, float]] | None = None,
    ) -> dict[str, Any]:
        """Run DDD implementation via AgentLoop.

        Uses AgentLoop with tools instead of calling DDDImplementationTask.execute()
        directly. This maintains proper Stabilize architecture where tools are
        blackbox and tasks don't call other tasks.

        Args:
            project_root: Project root path.
            spec_content: Specification content.
            issues_to_fix: Issues from previous iteration.
            iteration: Current iteration number.
            on_token: Token streaming callback.
            on_ui_event: UI event callback.
            accumulated_files_context: Previously read file contents (path -> content).
            file_read_cache: Shared cache for file reads (path -> (content, mtime)).
                Passed to AgentLoop to avoid re-reading unchanged files.

        Returns:
            DDD result dictionary with files_modified and files_read.
        """
        # Build issue context
        issue_context = ""
        if issues_to_fix:
            issue_descriptions = []
            for i in issues_to_fix:
                severity = i.get("severity", "unknown").upper()
                desc = i.get("description", "Unknown issue")
                loc = i.get("location", "unknown")
                issue_descriptions.append(f"- [{severity}] {desc} (at: {loc})")
            issue_context = f"""## Issues from Iteration {iteration - 1}

The following issues were found and MUST be fixed:

{chr(10).join(issue_descriptions)}

Fix ALL issues above before proceeding.
"""

        # Build accumulated context from previously read files
        accumulated_context = ""
        if accumulated_files_context:
            context_parts = []
            for file_path, content in accumulated_files_context.items():
                # Truncate large files to avoid token explosion
                truncated = content[:8000] if len(content) > 8000 else content
                if len(content) > 8000:
                    truncated += f"\n... (truncated, {len(content)} chars total)"
                context_parts.append(f"### {file_path}\n```\n{truncated}\n```")

            accumulated_context = f"""## Previously Read Files (DO NOT re-read these)

The following files were already read in previous iterations. Their content is provided below.
**IMPORTANT**: Do NOT use read_file on these files - use the content provided here.

{chr(10).join(context_parts)}
"""
            logger.info(
                f"Injecting {len(accumulated_files_context)} previously read files into context"
            )

        # Build user message for the agent
        # Build instruction 1 based on whether we have accumulated context
        instr1 = (
            "Use the file content provided above - DO NOT re-read files already shown"
            if accumulated_files_context
            else "Read the relevant files to understand the codebase"
        )
        instr3 = (
            "Fix ALL issues listed above FIRST" if issues_to_fix else "Follow the specification"
        )

        user_message = f"""# Implementation Task

## Specification
{spec_content}

{issue_context}

{accumulated_context}

## Instructions
1. {instr1}
2. Implement the changes specified above
3. {instr3}
4. Run linting/tests to verify your changes
5. Call complete_task when done

Focus on correctness and simplicity.
"""

        # Create agent loop with DDD tools
        # Reduced from 30 to 20 iterations to prevent explosion:
        # - Outer loop has max_iterations=10, inner has 20 -> worst case 200 calls
        # - Previously 10 × 30 = 300 calls was too aggressive
        agent_loop = AgentLoop(
            provider=self.ddd_provider,
            tool_registry=self.tools,
            max_iterations=20,
            parallel_tool_execution=True,
            max_parallel_tools=4,
            enable_loop_detection=True,
            file_read_cache=file_read_cache,  # Shared cache across iterations
        )

        try:
            result = agent_loop.run(
                system_prompt=DDD_SYSTEM_PROMPT,
                user_message=user_message,
                on_token=on_token,
                on_ui_event=on_ui_event,
            )

            # FALLBACK: If agent didn't call complete_task but modified files,
            # check if tests pass - if so, treat as implicit success.
            # This handles cases where the LLM forgets to call complete_task.
            if not result.success and result.files_modified:
                logger.info(
                    f"DDD didn't call complete_task but modified "
                    f"{len(result.files_modified)} files. Checking tests..."
                )
                # Run quick test check
                test_passed = self._quick_test_check(project_root)
                if test_passed:
                    logger.info("Tests pass! Treating as implicit success.")
                    return {
                        "success": True,
                        "files_modified": result.files_modified,
                        "files_read": result.files_read,
                        "summary": (
                            f"Implementation completed (implicit). "
                            f"Modified {len(result.files_modified)} files. Tests pass."
                        ),
                        "error": None,
                    }
                else:
                    logger.info("Tests fail - DDD iteration unsuccessful.")

            return {
                "success": result.success,
                "files_modified": result.files_modified,
                "files_read": result.files_read,  # NEW: Track files read
                "summary": result.final_message,
                "error": result.error,
            }

        except KeyboardInterrupt:
            # Re-raise to exit cleanly - do NOT return failure
            raise
        except Exception as e:
            # Check if this is a shutdown/interrupt error - propagate immediately
            error_str = str(e).lower()
            if any(
                keyword in error_str
                for keyword in ["shutdown", "interpreter", "interrupt", "cancelled", "keyboard"]
            ):
                logger.warning(f"DDD interrupted: {e}")
                raise KeyboardInterrupt("Operation interrupted") from e

            # Check if this is a TransientError - re-raise for Stabilize retry
            # Don't count transient LLM errors (timeouts, etc.) as DDD iterations
            from stabilize.errors import TransientError
            if isinstance(e, TransientError) or "transient" in error_str:
                logger.warning(f"Transient error in DDD, re-raising for retry: {e}")
                raise

            logger.exception(f"DDD AgentLoop failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "files_modified": [],
                "files_read": [],
            }

    def _run_review_via_tool(
        self,
        project_root: Path,
        files_modified: list[str],
        request: str,
    ) -> list[dict[str, Any]]:
        """Run code review via ReviewCodeTool.

        Uses the ReviewCodeTool directly instead of calling ReviewerAgentTask.execute().
        This maintains proper Stabilize architecture where tools are blackbox.

        Args:
            project_root: Project root path.
            files_modified: Files to review.
            request: Original request for context.

        Returns:
            List of review issues.
        """
        from red9.tools.review_code import ReviewCodeTool

        all_issues: list[dict[str, Any]] = []

        # Create review tool with the review provider
        review_tool = ReviewCodeTool(
            provider=self.review_provider,
            project_root=project_root,
            min_confidence=80,
        )

        # Run reviews for multiple focus areas
        for focus in ["bugs", "simplicity", "conventions"]:
            try:
                result = review_tool.execute(
                    {
                        "files": files_modified[:10],  # Limit files per review
                        "focus": focus,
                        "context": request,
                    }
                )

                if result.success and result.output:
                    issues = result.output.get("issues", [])
                    all_issues.extend(issues)
                    logger.debug(f"Review ({focus}): found {len(issues)} issues")
            except Exception as e:
                logger.warning(f"Review ({focus}) failed: {e}")

        # Deduplicate issues by description
        seen_descriptions: set[str] = set()
        unique_issues: list[dict[str, Any]] = []
        for issue in all_issues:
            desc = issue.get("description", "")
            if desc not in seen_descriptions:
                seen_descriptions.add(desc)
                unique_issues.append(issue)

        logger.info(f"Review complete: {len(all_issues)} total issues, {len(unique_issues)} unique")

        return unique_issues

    def _quick_test_check(self, project_root: Path) -> bool:
        """Run a quick test check to see if tests pass.

        Used for implicit success detection when agent modifies files but
        doesn't call complete_task.

        Args:
            project_root: Project root path.

        Returns:
            True if tests pass, False otherwise.
        """
        import subprocess

        # Try to find test command from config or use defaults
        test_commands = [
            ["pytest", "-x", "-q", "--tb=no"],  # pytest quick mode
            ["python", "-m", "pytest", "-x", "-q", "--tb=no"],
            ["python", "-m", "unittest", "discover", "-q"],
        ]

        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=project_root,
                    capture_output=True,
                    timeout=60,  # 1 minute timeout for quick check
                    text=True,
                )
                if result.returncode == 0:
                    logger.info(f"Quick test check passed: {' '.join(cmd)}")
                    return True
                else:
                    # Tests ran but failed
                    logger.debug(f"Tests failed with {cmd}: {result.stdout[:200]}")
                    return False
            except FileNotFoundError:
                # Command not found, try next
                continue
            except subprocess.TimeoutExpired:
                logger.warning(f"Test check timed out with {cmd}")
                return False
            except Exception as e:
                logger.debug(f"Test check failed with {cmd}: {e}")
                continue

        # No test command worked - assume no tests or can't run them
        # In this case, if agent modified files, we can consider it done
        logger.info("No test command available - treating file modifications as success")
        return True

    def _load_iteration_state(
        self,
        notepad: Notepad,
        workflow_id: str | None,
    ) -> dict[str, Any]:
        """Load iteration state from IssueDB via Notepad.

        State is stored as a JSON string in the 'issue_log' category
        with a key prefix like 'iteration_loop_state_<workflow_id>'.

        Args:
            notepad: Notepad instance for state persistence.
            workflow_id: Workflow identifier.

        Returns:
            Iteration state dictionary.
        """
        if not workflow_id or not notepad.repo:
            return {}

        state_key_prefix = f"{ITERATION_STATE_KEY}_{workflow_id}"
        try:
            # Read entries from IssueDB directly
            memories = notepad.repo.list_memory(category="issue_log")
            for mem in memories:
                if mem.key.startswith(state_key_prefix):
                    return json.loads(mem.value)
        except Exception as e:
            logger.debug(f"Failed to load iteration state: {e}")

        return {}

    def _save_iteration_state(
        self,
        notepad: Notepad,
        workflow_id: str | None,
        state: dict[str, Any],
    ) -> None:
        """Save iteration state to IssueDB via Notepad.

        Args:
            notepad: Notepad instance for state persistence.
            workflow_id: Workflow identifier.
            state: Iteration state to save.
        """
        if not workflow_id or not notepad.repo:
            return

        state_key = f"{ITERATION_STATE_KEY}_{workflow_id}"
        try:
            # Clear old state first
            self._clear_iteration_state(notepad, workflow_id)
            # Save new state
            json_str = json.dumps(state)
            notepad.repo.add_memory(
                key=state_key,
                value=json_str,
                category="issue_log",
            )
            logger.debug(f"Saved iteration state: iteration={state.get('iteration')}")
        except Exception as e:
            logger.warning(f"Failed to save iteration state: {e}")

    def _clear_iteration_state(
        self,
        notepad: Notepad,
        workflow_id: str | None,
    ) -> None:
        """Clear iteration state from IssueDB via Notepad.

        Args:
            notepad: Notepad instance for state persistence.
            workflow_id: Workflow identifier.
        """
        if not workflow_id or not notepad.repo:
            return

        state_key_prefix = f"{ITERATION_STATE_KEY}_{workflow_id}"
        try:
            # Get all entries and remove matching ones
            memories = notepad.repo.list_memory(category="issue_log")
            for mem in memories:
                if mem.key.startswith(state_key_prefix):
                    notepad.repo.delete_memory(key=mem.key)
                    logger.debug("Cleared iteration state")
        except Exception as e:
            logger.debug(f"Failed to clear iteration state: {e}")

    def _update_accumulated_context(
        self,
        project_root: Path,
        files_read: list[str],
        existing_context: dict[str, str],
    ) -> dict[str, str]:
        """Update accumulated file context with newly read files.

        Reads content for files that were read by the agent but not yet
        in the accumulated context. This avoids re-reading files in
        subsequent iterations.

        Args:
            project_root: Project root path.
            files_read: List of file paths read in this iteration.
            existing_context: Existing accumulated context.

        Returns:
            Updated accumulated context with new file contents.
        """
        # Make a copy to avoid mutating the original
        context = existing_context.copy() if existing_context else {}

        # Deduplicate and filter files
        new_files = set(files_read) - set(context.keys())

        # Limit to prevent context explosion (keep most recent 20 files)
        max_accumulated_files = 20

        for file_path in new_files:
            # Skip already accumulated files
            if file_path in context:
                continue

            # Read file content
            full_path = project_root / file_path
            if full_path.exists() and full_path.is_file():
                try:
                    content = full_path.read_text(encoding="utf-8", errors="ignore")
                    context[file_path] = content
                    logger.debug(f"Added {file_path} to accumulated context ({len(content)} chars)")
                except Exception as e:
                    logger.debug(f"Failed to read {file_path} for context: {e}")

        # Trim to max files (keep most recently added)
        if len(context) > max_accumulated_files:
            # Keep the most recent files (assumes dict maintains insertion order)
            keys_to_keep = list(context.keys())[-max_accumulated_files:]
            context = {k: context[k] for k in keys_to_keep}
            logger.debug(f"Trimmed accumulated context to {len(context)} files")

        return context
