"""Context Context Agent - Phase 0 of the Workflow.

Responsible for:
1. Detecting project stack and language.
2. Verifying LSP and tool availability.
3. Scanning project structure.
4. Generating/Updating context documentation (.red9/context/*.md).
"""

from __future__ import annotations

import json
from pathlib import Path

from stabilize import Task, TaskResult
from stabilize.models.stage import StageExecution

from red9.agents.notepad import Notepad
from red9.logging import get_logger
from red9.providers.base import LLMProvider
from red9.tools.base import ToolRegistry
from red9.workflows.runner import get_ui_event_callback

logger = get_logger(__name__)

CONTEXT_AGENT_SYSTEM_PROMPT = """You are the Context Agent (Phase 0) for RED9.

Your goal is to understand the codebase *once* and document it into the system memory (IssueDB).

## Your Tasks
1. **Detect Stack**: Identify languages, frameworks, and build tools.
2. **Scan Structure**: Understand the directory layout and key modules.
3. **Verify Tools**: Check if we can run builds/tests/diagnostics.
4. **Generate Context**: Store the following knowledge using `add_memory` (via Notepad):
   - `context:product`: Product overview, core features, target users.
   - `context:structure`: Directory tree, module responsibilities, key file locations.
   - `context:tech`: Technology stack, dependencies, build/test commands.

## Available Tools
- glob: Find files
- read_file: Read config files (package.json, pyproject.toml, etc.)
- run_diagnostics: Check if tools are working
- complete_task: Report completion when context is stored.

## Output
Call `complete_task` with a summary of the detected context.
"""


class ContextAgentTask(Task):
    """Phase 0: Context Injection Task. (One-Pass)"""

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

        project_root = stage.context.get("project_root")
        workflow_id = stage.context.get("workflow_id", "default")

        if not project_root:
            return TaskResult.terminal(error="project_root is required")

        root_path = Path(project_root)
        notepad = Notepad(root_path, workflow_id)

        try:
            # 1. BULK SCAN: Proactively gather information without asking LLM
            logger.info("ContextAgent: Performing bulk scan...")

            # Scan directory structure
            structure = []
            for path in root_path.rglob("*"):
                if any(part.startswith(".") for part in path.parts):
                    continue
                if "node_modules" in path.parts or "venv" in path.parts:
                    continue
                rel_path = path.relative_to(root_path)
                structure.append(f"{'  ' * (len(path.parts) - len(root_path.parts))} - {rel_path}")

            structure_str = "\n".join(structure[:100])  # Limit to 100 entries

            # Read key configs
            configs = {}
            for cfg in [
                "package.json",
                "pyproject.toml",
                "requirements.txt",
                "go.mod",
                "Cargo.toml",
            ]:
                cfg_path = root_path / cfg
                if cfg_path.exists():
                    configs[cfg] = cfg_path.read_text(encoding="utf-8")[:2000]

            config_str = "\n\n".join([f"### {k}\n{v}" for k, v in configs.items()])

            # 2. ONE-SHOT LLM CALL: Generate all 3 context docs at once
            prompt = f"""Analyze this project structure and configuration to generate context docs.

PROJECT STRUCTURE:
{structure_str}

CONFIGURATIONS:
{config_str}

Task: Generate 3 sections of documentation:
1. PRODUCT OVERVIEW: What is this project?
2. STRUCTURE ANALYSIS: Module responsibilities and key file locations.
3. TECH STACK: Languages, frameworks, and build/test commands.

Return the content formatted as a JSON object with keys: "product", "structure", "tech".
"""
            logger.info("ContextAgent: Calling LLM for one-shot analysis...")
            on_ui_event = get_ui_event_callback()
            if on_ui_event:
                on_ui_event({"type": "response_start", "streaming": False})
            response = self.provider.generate(
                prompt, system_prompt="You are a Technical Architect Agent."
            )
            if on_ui_event:
                on_ui_event({"type": "response_end", "has_tool_calls": False})

            # Handle potential markdown fence in response
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            try:
                data = json.loads(response)
                # Store in IssueDB
                for key in ["product", "structure", "tech"]:
                    content = data.get(key, "Not detected.")
                    notepad.add_entry(f"context:{key}", content, "ContextAgent")
            except Exception as je:
                logger.warning(f"Failed to parse JSON context, storing raw: {je}")
                notepad.add_entry("context:raw", response, "ContextAgent")

            notepad.add_entry("learning", "Bulk context analysis completed", "ContextAgent")

            return TaskResult.success(
                outputs={
                    "context_ready": True,
                    "summary": "Project context gathered and documented in IssueDB.",
                }
            )

        except Exception as e:
            return TaskResult.terminal(error=f"Context agent crash: {e}")
