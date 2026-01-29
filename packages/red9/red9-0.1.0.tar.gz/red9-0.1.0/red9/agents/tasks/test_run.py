"""Test run agent task - runs tests to verify implementation.

Uses error history context for intelligent retry behavior.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from stabilize import Task, TaskResult
from stabilize.errors import PermanentError
from stabilize.models.stage import StageExecution

from red9.agents.error_handler import get_error_history, handle_transient_error
from red9.agents.loop import AgentLoop, format_guidelines, load_agent_context
from red9.agents.notepad import Notepad
from red9.agents.prompts import TEST_RUN_AGENT_SYSTEM_PROMPT
from red9.config import config_exists, load_config
from red9.errors import is_transient_error
from red9.logging import get_logger
from red9.providers.base import LLMProvider
from red9.tools.base import ToolRegistry

logger = get_logger(__name__)


class TestRunAgentTask(Task):
    """Test run agent that executes tests and verifies implementation.

    This is a Stabilize Task that:
    1. Discovers test files created in the write_tests phase
    2. Runs the appropriate test command (configurable via .red9/config.yaml)
    3. Analyzes test results
    4. Reports success/failure with details

    If tests fail, the task fails - ensuring code quality.
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        rag_assistant: Any | None = None,
    ) -> None:
        """Initialize test run agent task.

        Args:
            provider: LLM provider for agent execution.
            tool_registry: Registry of available tools.
            rag_assistant: Optional Ragit RAGAssistant for semantic search.
        """
        self.provider = provider
        self.tools = tool_registry
        self.rag = rag_assistant

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the test run agent.

        Args:
            stage: Stage execution context.

        Returns:
            TaskResult with test results or error.
        """
        request = stage.context.get("request", "")
        issue_id = stage.context.get("issue_id")
        workflow_id = stage.context.get("workflow_id", "default")
        project_root = stage.context.get("project_root")
        error_history = get_error_history(stage.context)

        try:
            # Determine paths
            if project_root:
                root = Path(project_root)
                db_path = str(root / ".red9" / ".issue.db")
            else:
                root = Path.cwd()
                db_path = ".red9/.issue.db"

            # Initialize Notepad
            notepad = Notepad(root, workflow_id)

            # Load configuration for test commands
            test_config_info = ""
            if config_exists(root):
                try:
                    config = load_config(root)
                    if config.tests.commands:
                        test_config_info = "\n\nPROJECT CONFIGURATION OVERRIDES:\n"
                        for lang, cmd in config.tests.commands.items():
                            test_config_info += f"- {lang}: {cmd}\n"
                except Exception:
                    pass

            # Load project guidelines from IssueDB
            guidelines = load_agent_context(
                db_path,
                categories=["conventions", "testing", "workflow"],
            )
            guidelines_text = format_guidelines(guidelines)

            # Get Notepad Wisdom
            wisdom_text = notepad.get_summary()

            # Build context
            context_parts = []
            if guidelines_text:
                context_parts.append(guidelines_text)
            if wisdom_text:
                context_parts.append(wisdom_text)

            full_context = "\n\n".join(context_parts) if context_parts else None

            # Create agent loop
            agent = AgentLoop(
                provider=self.provider,
                tool_registry=self.tools,
                max_iterations=20,
            )

            # Build user message for test running
            user_message = f"""Run and verify tests for the following implementation:

{request}

IMPORTANT STEPS:
1. First, discover what test files exist in the project:
   - Look for test_*.py, *_test.py, *.test.js, *.spec.ts, *_test.go, etc.
   - Use glob to find test files

2. Determine the correct test command based on the project:{test_config_info}
   - Python: pytest, python -m pytest, or python -m unittest
   - JavaScript/TypeScript: npm test, yarn test, npx jest, npx vitest
   - Go: go test ./...
   - Rust: cargo test
   - Check for package.json, pyproject.toml, Cargo.toml, go.mod, etc.

3. IF NO TESTS FOUND:
   - If this is a simple task (e.g. HTML/CSS only, or prototype without test setup), call complete_task with tests_passed=true and note "No tests found - skipping".
   - If you cannot call complete_task, output exactly: "NO TESTS FOUND - SKIPPING TESTING".
   - Do NOT fail the task just because tests are missing unless the user explicitly asked for tests.

4. Run the tests and capture output

5. Analyze the results:
   - Count passed/failed tests
   - Identify any failures and their causes
   - Check for test coverage if available

6. Call complete_task with:
   - tests_passed: true/false
   - Summary of test results
   - List of any failures

The task FAILS if any tests fail - this ensures code quality."""

            # Get streaming callback from context or module-level registry
            from red9.workflows.runner import get_stream_callback

            on_token = stage.context.get("on_token") or get_stream_callback()

            # Run the agent
            result = agent.run(
                system_prompt=TEST_RUN_AGENT_SYSTEM_PROMPT,
                user_message=user_message,
                context=full_context,
                error_history=error_history if error_history else None,
                on_token=on_token,
            )

            if not result.success:
                # Log failure
                notepad.add_entry("issue", f"Test run failed: {result.error}", "TestRunAgent")

                self._add_issue_comment(
                    db_path,
                    issue_id,
                    f"❌ Test run failed: {result.error}",
                )
                return TaskResult.failed_continue(error=result.error or "Test run agent failed")

            # Check if tests passed from the outputs
            # First check explicit tests_passed flag
            tests_passed = result.outputs.get("tests_passed")

            # If not explicitly set, try to infer from the final message
            if tests_passed is None:
                tests_passed = self._infer_tests_passed(result.final_message)
                logger.info(f"Inferred tests_passed={tests_passed} from output")

            if not tests_passed:
                error_msg = f"Tests failed: {result.final_message[:500]}"
                notepad.add_entry(
                    "issue", f"Tests failed: {result.final_message[:200]}", "TestRunAgent"
                )

                self._add_issue_comment(
                    db_path,
                    issue_id,
                    f"❌ Tests failed:\n\n{result.final_message[:500]}",
                )
                return TaskResult.failed_continue(error=error_msg)

            # Add progress comment to issue
            notepad.add_entry("learning", "All tests passed", "TestRunAgent")

            self._add_issue_comment(
                db_path,
                issue_id,
                f"✅ All tests passed:\n\n{result.final_message[:300]}...",
            )

            return TaskResult.success(
                outputs={
                    "tests_passed": True,
                    "summary": result.final_message,
                    "tool_calls_made": result.tool_calls_made,
                }
            )

        except Exception as e:
            # Transient errors use error history for intelligent retry
            if is_transient_error(e):
                return handle_transient_error(e, error_history, agent_name="TestRun agent")
            # Permanent errors fail immediately
            raise PermanentError(f"Test run agent error: {e}", cause=e)

    def _infer_tests_passed(self, message: str) -> bool:
        """Infer whether tests passed from the output message.

        Looks for common patterns in test output to determine success/failure.

        Args:
            message: The final message or test output.

        Returns:
            True if tests appear to have passed, False otherwise.
        """
        message_lower = message.lower()

        # Failure patterns - if any of these are present, tests failed
        failure_patterns = [
            "failed",
            "failure",
            "error:",
            "errors:",
            "0 passed",
            "tests failed",
            "test failed",
            "assertion error",
            "assertionerror",
            "traceback",
            "exception",
        ]

        # Success patterns - these indicate tests passed
        success_patterns = [
            "passed",
            "ok",
            "success",
            "all tests pass",
            "tests pass",
            "test pass",
            "100%",
            "PASS",  # Go test (case-sensitive match done separately)
            "test result: ok",  # Rust/Cargo
            "0 failures",  # Generic
            "0 errors",  # Generic
            "completed successfully",  # Generic
            "build succeeded",  # Build tools
            "no errors",  # Generic
            "no tests found",  # Allow skipping if no tests
            "no test files",  # Allow skipping
            "skipping testing",  # Explicit skip
            "no tests to run",
            "0 tests",
            "found no tests",
            "found nothing",
            "no test configuration",
            "no testing infrastructure",
        ]

        # Check for explicit failure indicators
        for pattern in failure_patterns:
            if pattern in message_lower:
                # But check if it's in context of "0 failed" which means success
                if "0 failed" in message_lower or "0 failures" in message_lower:
                    continue
                # Check if "failed" is preceded by a number > 0
                failed_match = re.search(r"(\d+)\s*failed", message_lower)
                if failed_match and int(failed_match.group(1)) > 0:
                    logger.info(f"Detected {failed_match.group(1)} failed tests")
                    return False
                # Check for error/exception indicators
                if pattern in ("error:", "errors:", "traceback", "exception", "assertionerror"):
                    logger.info(f"Detected error pattern: {pattern}")
                    return False

        # Check for success patterns
        for pattern in success_patterns:
            if pattern in message_lower:
                # Verify it's not "0 passed"
                if pattern == "passed":
                    passed_match = re.search(r"(\d+)\s*passed", message_lower)
                    if passed_match and int(passed_match.group(1)) > 0:
                        logger.info(f"Detected {passed_match.group(1)} passed tests")
                        return True
                else:
                    return True

        # Check if this looks like test output at all
        test_indicators = ["test", "spec", "assert", "expect", "pytest", "jest", "mocha", "junit"]
        has_test_content = any(ind in message_lower for ind in test_indicators)

        if not has_test_content:
            # No test-related content found - likely a simple task without tests
            logger.debug("No test output detected - assuming success for non-test task")
            return True

        # Has test content but no clear pass/fail signal - be cautious
        logger.debug("Could not determine test status from output, defaulting to failed")
        return False

    def _add_issue_comment(
        self,
        db_path: str,
        issue_id: int | None,
        comment: str,
    ) -> None:
        """Add a comment to the issue.

        Args:
            db_path: Path to IssueDB database.
            issue_id: Issue ID (optional).
            comment: Comment text.
        """
        if not issue_id:
            return

        try:
            from issuedb.repository import IssueRepository

            repo = IssueRepository(db_path=db_path)
            repo.add_comment(issue_id, comment)
        except Exception as e:
            logger.warning(f"Failed to add issue comment to issue {issue_id}: {e}")
