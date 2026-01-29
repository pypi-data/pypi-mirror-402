"""Spec Agent Task - Phase 1 of the Workflow.

Responsible for:
1. Creating a Git Worktree for isolation.
2. Drafting SPEC files (EARS format) based on User Request + Phase 0 Context.
3. Reviewing and Finalizing the SPEC.
"""

from __future__ import annotations

from pathlib import Path

from stabilize import Task, TaskResult
from stabilize.models.stage import StageExecution

from red9.agents.notepad import Notepad
from red9.logging import get_logger
from red9.providers.base import LLMProvider
from red9.tools.base import ToolRegistry
from red9.workflows.runner import get_stream_callback, get_ui_event_callback

logger = get_logger(__name__)

SPEC_AGENT_SYSTEM_PROMPT = """You are the Spec Agent (Phase 1) for RED9.

Your goal is to define WHAT needs to be done before anyone writes a line of code.
You adhere to the **MoAI-ADK** standard for specification.

## Inputs
- **User Request**: The raw intent.
- **Context**: Retrieved from IssueDB (Product, Structure, Tech).

## Your Tasks
1. **Analyze**: Understand the request in the context of the existing project.
2. **Draft SPEC**: Create a detailed specification.
   - **STRICTLY** use **EARS** format (Easy Approach to Requirements Syntax).
   - Define **Acceptance Criteria**.
   - Define **Test Scenarios** (Positive, Negative, Edge Cases).
3. **Store SPEC**: Use `complete_task` to return the full SPEC content. Do NOT write to a file.
   - The system will store the SPEC in IssueDB.

## EARS Format Example
- **Precondition**: "When the user is logged in..."
- **Trigger**: "...and clicks the 'Pay' button..."
- **System Behavior**: "...the system shall validate the balance..."
- **Response**: "...and confirm the transaction."

## Available Tools
- read_file: Read source files if needed for detail
- semantic_search: Look up relevant existing code
- complete_task: Submit the SPEC

## Output
Call `complete_task` with the final SPEC content in the summary.
"""


class SpecAgentTask(Task):
    """Phase 1: SPEC-First Planning. (One-Pass)"""

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
    ) -> None:
        self.provider = provider
        self.tools = tool_registry

    def execute(self, stage: StageExecution) -> TaskResult:
        from red9.workflows.runner import emit_phase_start

        # Emit phase start for UI
        emit_phase_start(stage)

        request = stage.context.get("request")
        project_root = stage.context.get("project_root")
        workflow_id = stage.context.get("workflow_id")

        if not request or not project_root:
            return TaskResult.terminal(error="Missing request or project_root")

        root_path = Path(project_root)
        notepad = Notepad(root_path, workflow_id)

        # 1. Gather Context from IssueDB
        context_summary = notepad.get_summary()

        # 2. ONE-SHOT SPEC GENERATION
        spec_id = f"SPEC-{workflow_id[-6:]}"
        prompt = f"""Generate an EARS-format SPEC for the following user request.

USER REQUEST:
{request}

PROJECT CONTEXT:
{context_summary}

Task:
1. Define the functional requirements using EARS (Precondition, Trigger, System Behavior, Response).
2. Define Acceptance Criteria.
3. Define Test Scenarios.
4. List the files that need to be created or modified.

Provide a comprehensive, high-fidelity technical specification.
"""
        logger.info("SpecAgent: Generating one-shot SPEC...")
        on_ui_event = get_ui_event_callback()
        on_token = get_stream_callback()  # Import this if needed, but it's available in runner

        if on_ui_event:
            on_ui_event({"type": "response_start", "streaming": bool(on_token)})

        if on_token:
            spec_content = ""
            # Assuming provider has stream method (Base LLMProvider does)
            for token in self.provider.stream(
                prompt, system_prompt="You are a Senior Systems Architect."
            ):
                spec_content += token
                on_token(token)
        else:
            spec_content = self.provider.generate(
                prompt, system_prompt="You are a Senior Systems Architect."
            )

        if on_ui_event:
            on_ui_event({"type": "response_end", "has_tool_calls": False})

        # Persist spec to disk for Phase 2 fallback
        spec_dir = root_path / ".red9" / "specs"
        spec_dir.mkdir(parents=True, exist_ok=True)
        spec_path = spec_dir / f"{spec_id}.md"
        spec_path.write_text(spec_content, encoding="utf-8")
        logger.info(f"SpecAgent: Persisted spec to {spec_path}")

        # 3. Finalize
        notepad.add_entry("decision", f"SPEC_FINALIZED:\n{spec_content}", "SpecAgent")

        return TaskResult.success(
            outputs={
                "spec_id": spec_id,
                "spec_content": spec_content,
                "summary": f"Spec {spec_id} created successfully.",
            }
        )
