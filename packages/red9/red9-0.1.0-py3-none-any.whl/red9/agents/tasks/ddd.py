"""DDD Implementation Task - Phase 2 of the Workflow.

Code generation with autonomous error recovery via diagnosis-driven retry.

This task generates code based on a spec, runs verification, and on failure
delegates to the autonomous recovery system (diagnosis -> compensation -> retry)
rather than using hardcoded retry loops.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from stabilize import Task, TaskResult
from stabilize.errors import PermanentError
from stabilize.models.stage import StageExecution

from red9.agents.notepad import Notepad
from red9.files.diff import generate_unified_diff
from red9.logging import get_logger
from red9.providers.base import GenerationConfig, LLMProvider
from red9.sandbox import LocalSandbox
from red9.tools.base import ToolRegistry
from red9.workflows.runner import get_stream_callback, get_ui_event_callback

logger = get_logger(__name__)

CODE_GEN_SYSTEM_PROMPT = """You are an expert code generator. Generate minimal, working code.

## Methodology: ANALYZE-PRESERVE-IMPROVE (MoAI-ADK Standard)
1. **ANALYZE**: Understand the existing code and the desired change.
2. **PRESERVE**: If modifying existing code, ensure **Characterization Tests** exist to capture current behavior.
3. **IMPROVE**: Implement the changes/refactoring while ensuring tests pass.

## Process
1. First, PLAN your changes. Explain your reasoning, file structure, and implementation details.
2. Then, generate the code in the specified JSON format.

OUTPUT FORMAT:
[Your reasoning here...]

```json
{"files": [{"path": "app.py", "content": "..."}], "run_command": "pytest -v"}
```

RULES:
1. MINIMIZE files - combine into 1-2 files when possible
2. Keep code SHORT - no excessive comments or docstrings
3. Use simple implementations (in-memory storage, not databases)
4. MANDATORY: Include tests in a `tests/` directory (e.g., `tests/test_app.py`) that verify the code.
5. The JSON must be valid and wrapped in ```json ... ``` block
6. The run_command MUST test the code (use pytest, python -m unittest, or similar)
7. NO SHELL EXPANSION: Do not use brace expansion (e.g. `{a,b}`) in file paths. Use explicit paths for every file.
"""


class DDDImplementationTask(Task):
    """Phase 2: Code generation with autonomous error recovery.

    Instead of hardcoded retry loops, this task:
    1. Generates code based on spec
    2. Runs verification
    3. On failure, returns failed_continue with error context
    4. The recovery system (diagnosis -> compensation -> retry) handles retries
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        fallback_provider: LLMProvider | None = None,
    ) -> None:
        self.provider = provider
        self.tools = tool_registry
        self.fallback_provider = fallback_provider or provider

    def execute(self, stage: StageExecution) -> TaskResult:
        from red9.workflows.runner import emit_phase_start

        emit_phase_start(stage)

        spec_content = stage.context.get("spec_content")
        project_root = stage.context.get("project_root")
        workflow_id = stage.context.get("workflow_id")

        # Check for accumulated context from recovery system
        accumulated_context = stage.context.get("accumulated_context", "")
        attempt_history = stage.context.get("attempt_history", [])

        # Support for iteration loop: issues_to_fix and iteration number
        issues_to_fix = stage.context.get("issues_to_fix", [])
        iteration = stage.context.get("iteration", 1)

        # Build issue context if issues_to_fix is provided but accumulated_context is empty
        if issues_to_fix and not accumulated_context:
            issue_descriptions = []
            for i in issues_to_fix:
                severity = i.get("severity", "unknown").upper()
                desc = i.get("description", "Unknown issue")
                loc = i.get("location", "unknown")
                issue_descriptions.append(f"- [{severity}] {desc} (location: {loc})")
            accumulated_context = f"""## Issues from Iteration {iteration - 1}

The following issues were found in the previous iteration and MUST be fixed:

{chr(10).join(issue_descriptions)}

Fix ALL issues above. Ensure the code passes quality gates.
"""

        # Try to get spec_content from upstream stage outputs (Phase 1 spec_agent)
        if not spec_content:
            upstream = stage.upstream_stages()
            if upstream and upstream[0].outputs:
                spec_content = upstream[0].outputs.get("spec_content")
                logger.info(f"DDD: Retrieved spec_content from upstream {upstream[0].ref_id}")

        # Fallback: read from disk if spec_agent persisted it
        if not spec_content and project_root and workflow_id:
            spec_path = Path(project_root) / ".red9" / "specs" / f"SPEC-{workflow_id[-6:]}.md"
            if spec_path.exists():
                spec_content = spec_path.read_text(encoding="utf-8")
                logger.info(f"DDD: Retrieved spec_content from disk: {spec_path}")

        if not spec_content or not project_root:
            logger.error(
                f"DDD missing spec_content. Context: {list(stage.context.keys())}, "
                f"Upstream: {[s.ref_id for s in stage.upstream_stages()]}"
            )
            raise PermanentError("Missing spec_content or project_root")

        root_path = Path(project_root)
        notepad = Notepad(root_path, workflow_id)
        config = GenerationConfig(max_tokens=8192, temperature=0.3)

        # Build prompt - include accumulated context if available
        if accumulated_context:
            prompt = f"""Generate MINIMAL code for this spec (in-memory storage, 1-2 files):

{spec_content}

## Previous Attempt Context
{accumulated_context}

Fix the issues mentioned above and return working code.
Return ONLY JSON: {{"files": [...], "run_command": "..."}}
"""
        else:
            prompt = f"""Generate MINIMAL code for this spec (in-memory storage, 1-2 files):

{spec_content}

Return ONLY JSON: {{"files": [...], "run_command": "..."}}
"""

        try:
            logger.info("DDD: Generating code")
            on_ui_event = get_ui_event_callback()
            on_token = get_stream_callback()

            if not on_ui_event:
                logger.warning("DDD: No UI event callback available - UI updates will be skipped")

            # Generate code
            if on_ui_event:
                on_ui_event({"type": "response_start", "streaming": bool(on_token)})

            if on_token:
                # Streaming mode
                response = ""
                for token in self.provider.stream(
                    prompt, system_prompt=CODE_GEN_SYSTEM_PROMPT, config=config
                ):
                    response += token
                    on_token(token)
            else:
                # Blocking mode
                response = self.provider.generate(
                    prompt, system_prompt=CODE_GEN_SYSTEM_PROMPT, config=config
                )

            if on_ui_event:
                on_ui_event({"type": "response_end", "has_tool_calls": False})

            # Parse response
            files_data = self._parse_code_response(response)
            # Attempt repair if parsing failed
            if not files_data:
                logger.warning(
                    "DDD: Invalid JSON response, attempting repair with fallback provider"
                )
                files_data = self._repair_json(response)

            if not files_data:
                logger.warning("DDD: Invalid JSON response (repair failed)")
                return TaskResult.failed_continue(
                    error="Failed to parse code response - invalid JSON",
                    outputs={"parse_error": True},
                    context={
                        "error_output": "Invalid JSON response from code generator",
                        "failed_command": "code_generation",
                        "attempt_history": attempt_history,
                    },
                )

            files = files_data.get("files", [])
            run_command = files_data.get("run_command")

            if not files:
                logger.warning("DDD: No files in response")
                return TaskResult.failed_continue(
                    error="No files generated",
                    outputs={"no_files": True},
                    context={
                        "error_output": "Code generator returned no files",
                        "failed_command": "code_generation",
                        "attempt_history": attempt_history,
                    },
                )

            # Write files
            files_modified = []
            for file_info in files:
                file_path = root_path / file_info["path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Capture original content for diff
                original_content = ""
                if file_path.exists():
                    try:
                        original_content = file_path.read_text(encoding="utf-8")
                    except Exception:
                        pass

                # Emit tool events for file write
                if on_ui_event:
                    on_ui_event(
                        {
                            "type": "tool_start",
                            "tool": "write_file",
                            "args": {"path": str(file_path)},
                        }
                    )

                file_path.write_text(file_info["content"], encoding="utf-8")

                if on_ui_event:
                    diff_text = generate_unified_diff(
                        original_content, file_info["content"], str(file_path)
                    )
                    on_ui_event(
                        {
                            "type": "tool_end",
                            "tool": "write_file",
                            "success": True,
                            "diff": diff_text,
                        }
                    )
                files_modified.append(str(file_path))
                logger.info(f"DDD: Wrote {file_path}")

            # No verification command - accept files as-is
            if not run_command:
                logger.info(f"DDD: No run_command provided, accepting {len(files_modified)} files")
                notepad.add_entry(
                    "learning",
                    f"Code generated (no verification): {len(files_modified)} files",
                    "DDDAgent",
                )
                return TaskResult.success(
                    outputs={
                        "files_modified": files_modified,
                        "summary": f"Generated {len(files_modified)} files (no verification)",
                        "spec_content": spec_content,
                    }
                )

            # Run verification
            logger.info(f"DDD: Running verification: {run_command}")
            result = self._run_verification(root_path, run_command)

            if result["success"]:
                logger.info("DDD: Verification PASSED")
                notepad.add_entry(
                    "learning",
                    f"Code verified successfully: {len(files_modified)} files",
                    "DDDAgent",
                )
                return TaskResult.success(
                    outputs={
                        "files_modified": files_modified,
                        "summary": f"Generated {len(files_modified)} files, verified",
                        "spec_content": spec_content,
                    }
                )

            # FAILURE - delegate to autonomous recovery system
            error_output = result["error_output"]
            logger.debug("DDD: Verification FAILED - delegating to recovery system")

            return TaskResult.failed_continue(
                error=f"Verification failed: {error_output[:200]}",
                outputs={
                    "files_modified": files_modified,
                    "files_data": files_data,
                },
                context={
                    "error_output": error_output,
                    "failed_command": run_command,
                    "attempt_history": attempt_history,
                    "spec_content": spec_content,
                    "original_files": files_data,
                },
            )

        except PermanentError:
            raise
        except Exception as e:
            logger.exception("DDD agent crash")
            raise PermanentError(f"DDD agent crash: {e}", cause=e)

    def _run_verification(self, root_path: Path, run_command: str) -> dict:
        """Run verification command using LocalSandbox and return result."""
        sandbox = LocalSandbox(root_path)
        result = sandbox.run_command(
            run_command,
            timeout=120,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        )

        if result.success:
            return {"success": True, "error_output": ""}

        error_output = (result.stdout + result.stderr)[-2000:]
        return {"success": False, "error_output": error_output}

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

    def _repair_json(self, invalid_json: str) -> dict | None:
        """Attempt to repair invalid JSON using the fallback provider."""
        prompt = f"""You are a JSON repair expert. The following output was expected to be valid \
JSON but failed parsing. Fix it and return ONLY the valid JSON object.

INVALID OUTPUT:
{invalid_json[:10000]}

Return ONLY valid JSON.
"""
        try:
            on_ui_event = get_ui_event_callback()
            if on_ui_event:
                on_ui_event({"type": "response_start", "streaming": False})
            response = self.fallback_provider.generate(
                prompt,
                system_prompt="You are a JSON repair expert. Return ONLY valid JSON.",
                config=GenerationConfig(max_tokens=8192, temperature=0.0),
            )
            if on_ui_event:
                on_ui_event({"type": "response_end", "has_tool_calls": False})
            return self._parse_code_response(response)
        except Exception as e:
            logger.warning(f"JSON repair failed: {e}")
            return None
