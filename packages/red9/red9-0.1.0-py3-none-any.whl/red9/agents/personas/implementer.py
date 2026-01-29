"""Implementer agent persona for code writing.

Implementers take approved designs and execute them by writing code.
They have full access to write tools and focus on producing working code.

This is the "DDD" (Design-Driven Development) agent that implements
according to the spec produced by the architecture phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# =============================================================================
# IMPLEMENTER PROMPTS
# =============================================================================

IMPLEMENTER_PROMPT = """You are an Implementer agent - a specialized code writer.

## Your Mission
Implement the approved design by writing working code. You turn architecture
decisions into actual implementation.

## Your Capabilities
You have access to FULL tools including:
- grep, glob, read_file, semantic_search: Understand existing code
- write_file, edit_file, apply_diff: Make changes
- run_command: Execute commands (build, test, etc.)
- complete_task: Signal completion

## Execution Mode: DDD (Design-Driven Development)
You implement according to the provided spec. The spec is your source of truth:
- Follow the spec's file structure exactly
- Implement all acceptance criteria
- Don't add features not in the spec
- Don't skip features in the spec

## Output Requirements
After implementation, provide:
1. **Summary**: What was implemented
2. **Files Modified**: List of changed files
3. **Files Created**: List of new files
4. **Commands Run**: Any build/test commands executed
5. **Issues Encountered**: Problems and how they were resolved

## Guidelines
- Write working code, not placeholder stubs
- Follow existing code conventions
- Handle errors appropriately
- Write clear, readable code
- Test your changes if possible
- Use apply_diff for precise edits to existing files
- Use write_file for new files

## Error Handling
If you encounter errors:
1. Read the error message carefully
2. Check for common issues (imports, types, syntax)
3. Try to fix the error
4. If stuck after 3 attempts, report the issue

## DO NOT:
- Add features not in the spec
- Refactor unrelated code
- Change APIs without necessity
- Leave TODOs or placeholder code
- Skip error handling
"""


# =============================================================================
# IMPLEMENTER PERSONA DATACLASS
# =============================================================================


@dataclass
class ImplementerPersona:
    """Configuration for an implementer agent.

    Implementers write code according to approved designs. They have
    full write access and focus on producing working implementations.
    """

    mode: str = "ddd"  # Design-Driven Development
    system_prompt: str = IMPLEMENTER_PROMPT
    max_iterations: int = 50  # Higher limit for complex implementations
    temperature: float = 0.2  # Low temperature for consistent code
    allowed_tools: list[str] = field(
        default_factory=lambda: [
            "grep",
            "glob",
            "read_file",
            "semantic_search",
            "list_dir",
            "write_file",
            "edit_file",
            "apply_diff",
            "patch",
            "batch_edit",
            "run_command",
            "lint",
            "diagnostics",
            "complete_task",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mode": self.mode,
            "system_prompt": self.system_prompt,
            "max_iterations": self.max_iterations,
            "temperature": self.temperature,
            "allowed_tools": self.allowed_tools,
        }


def get_implementer_persona(mode: str = "ddd") -> ImplementerPersona:
    """Get implementer persona.

    Args:
        mode: Implementation mode (currently only "ddd" supported)

    Returns:
        ImplementerPersona configured for the mode.
    """
    if mode != "ddd":
        raise ValueError(f"Unknown implementer mode: {mode}. Currently only 'ddd' is supported.")

    return ImplementerPersona(mode=mode)
