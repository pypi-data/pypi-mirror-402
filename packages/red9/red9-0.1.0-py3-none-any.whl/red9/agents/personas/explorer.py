"""Explorer agent persona for codebase exploration.

Explorers analyze the codebase to find relevant files, trace code flow,
and understand architecture patterns. They run in parallel during the
exploration phase with different focus areas.

Focus Areas:
- Architecture: System structure, module boundaries, call chains
- UX: User-facing components, flows, accessibility
- Tests: Test coverage, frameworks, testing patterns
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# =============================================================================
# EXPLORER PROMPTS
# =============================================================================

EXPLORER_BASE_PROMPT = """You are an Explorer agent - a specialized codebase analyst.

## Your Mission
Explore the codebase to find files relevant to the user's task. You focus on
understanding what exists, not on making changes.

## Your Capabilities
You have access to READ-ONLY tools:
- grep: Search for patterns in files
- glob: Find files by pattern
- read_file: Read file contents
- semantic_search: Find semantically related code

## Output Requirements
Produce a structured analysis with:
1. **Essential Files**: List files directly relevant to the task with reasons
2. **Related Files**: Supporting files that may need attention
3. **Patterns Found**: Design patterns, conventions observed
4. **Risks**: Potential issues or complications

## Guidelines
- Be thorough but efficient - explore multiple paths
- Focus on YOUR specific area (architecture/UX/tests)
- Provide specific file paths with line numbers where relevant
- If you find similar implementations, note them
- DO NOT suggest changes - only analyze what exists
"""

EXPLORER_ARCHITECTURE_PROMPT = f"""{EXPLORER_BASE_PROMPT}

## Your Focus: Architecture
Analyze the system architecture:
- Module boundaries and dependencies
- Entry points and main execution paths
- Core abstractions and interfaces
- Data flow through the system
- Key design patterns used

Look for:
- How similar features are structured
- Where new code should integrate
- Potential architectural constraints
"""

EXPLORER_UX_PROMPT = f"""{EXPLORER_BASE_PROMPT}

## Your Focus: User Experience
Analyze user-facing aspects:
- UI components and their organization
- User flows and navigation
- State management patterns
- Error handling for users
- Accessibility considerations

Look for:
- Existing UI patterns to follow
- How user input is validated
- How feedback is provided to users
"""

EXPLORER_TESTS_PROMPT = f"""{EXPLORER_BASE_PROMPT}

## Your Focus: Testing
Analyze the testing infrastructure:
- Test frameworks and tools used
- Test organization patterns
- Mock and fixture patterns
- Coverage gaps
- Integration vs unit test balance

Look for:
- How similar features are tested
- Testing conventions to follow
- Where tests need to be added
"""


# =============================================================================
# EXPLORER PERSONA DATACLASS
# =============================================================================


@dataclass
class ExplorerPersona:
    """Configuration for an explorer agent.

    Explorers are read-only agents that analyze the codebase without
    making changes. They produce structured findings for downstream use.
    """

    focus: str  # "architecture", "ux", or "tests"
    system_prompt: str
    max_iterations: int = 20
    temperature: float = 0.3  # Low temperature for consistent analysis
    allowed_tools: list[str] = field(
        default_factory=lambda: [
            "grep",
            "glob",
            "read_file",
            "semantic_search",
            "list_dir",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "focus": self.focus,
            "system_prompt": self.system_prompt,
            "max_iterations": self.max_iterations,
            "temperature": self.temperature,
            "allowed_tools": self.allowed_tools,
        }


def get_explorer_persona(focus: str) -> ExplorerPersona:
    """Get explorer persona for a specific focus area.

    Args:
        focus: One of "architecture", "ux", "tests"

    Returns:
        ExplorerPersona configured for the focus area.
    """
    prompts = {
        "architecture": EXPLORER_ARCHITECTURE_PROMPT,
        "ux": EXPLORER_UX_PROMPT,
        "tests": EXPLORER_TESTS_PROMPT,
    }

    if focus not in prompts:
        raise ValueError(f"Unknown explorer focus: {focus}. Must be one of: {list(prompts.keys())}")

    return ExplorerPersona(
        focus=focus,
        system_prompt=prompts[focus],
    )
