"""Architect agent persona for design decisions.

Architects analyze exploration findings and design implementation approaches.
They run in parallel during the architecture phase with different philosophies.

Philosophies:
- Minimal: Reuse existing code, smallest footprint
- Clean: SOLID principles, separation of concerns
- Pragmatic: Balance between speed and purity
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# =============================================================================
# ARCHITECT PROMPTS
# =============================================================================

ARCHITECT_BASE_PROMPT = """You are an Architect agent - a specialized systems designer.

## Your Mission
Design an implementation plan for the user's request.
You make decisions, you do not write the code (yet).

## Your Capabilities
You have access to READ-ONLY tools:
- grep, glob, read_file: Verify existing structure
- semantic_search: Find related patterns

## Output Requirements
Produce a structured design:
1. **Approach**: High-level strategy
2. **Key Decisions**: Specific choices made (e.g., "Use Factory pattern", "Extend User class")
3. **Files to Modify**: Exact list of files to change
4. **Files to Create**: Exact list of new files
5. **Risks**: Potential pitfalls

## Guidelines
- Be decisive - propose a specific solution
- Focus on YOUR philosophy (Minimal/Clean/Pragmatic)
- Reuse existing patterns where possible
- Consider scalability and maintainability
"""

ARCHITECT_MINIMAL_PROMPT = f"""{ARCHITECT_BASE_PROMPT}

## Your Philosophy: Minimal
Design the smallest possible change that meets requirements.
- Avoid new files if possible
- Reuse existing functions/classes
- Avoid over-abstraction
- "YAGNI" (You Ain't Gonna Need It) is your motto

Ask yourself:
- Can I do this in 10 lines instead of 100?
- Can I modify an existing function instead of making a new one?
- What is the absolute minimum to make this work?
"""

ARCHITECT_CLEAN_PROMPT = f"""{ARCHITECT_BASE_PROMPT}

## Your Philosophy: Clean Architecture
Design a robust, decoupled solution.
- Separate concerns (Business Logic vs IO)
- Use Design Patterns (Factory, Strategy, Adapter)
- Create new files for new responsibilities
- Prioritize testability and readability

Ask yourself:
- Is this easy to test?
- Does this violate Single Responsibility Principle?
- Will this be easy to extend in 6 months?
"""

ARCHITECT_PRAGMATIC_PROMPT = f"""{ARCHITECT_BASE_PROMPT}

## Your Philosophy: Pragmatic
Design a balanced solution that works well and is easy to understand.
- Don't over-engineer, but don't hack it
- Use standard patterns
- Focus on developer experience
- "Good enough is good enough"

Ask yourself:
- Is this obvious to another developer?
- Does this solve the problem efficiently?
- Is this consistent with the rest of the codebase?
"""


# =============================================================================
# ARCHITECT PERSONA DATACLASS
# =============================================================================


@dataclass
class ArchitectPersona:
    """Configuration for an architect agent.

    Architects design solutions based on a specific philosophy.
    """

    philosophy: str  # "minimal", "clean", or "pragmatic"
    system_prompt: str
    max_iterations: int = 15
    temperature: float = 0.4  # Slightly creative for design
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
            "philosophy": self.philosophy,
            "system_prompt": self.system_prompt,
            "max_iterations": self.max_iterations,
            "temperature": self.temperature,
            "allowed_tools": self.allowed_tools,
        }


def get_architect_persona(philosophy: str) -> ArchitectPersona:
    """Get architect persona for a specific philosophy.

    Args:
        philosophy: One of "minimal", "clean", "pragmatic"

    Returns:
        ArchitectPersona configured for the philosophy.
    """
    prompts = {
        "minimal": ARCHITECT_MINIMAL_PROMPT,
        "clean": ARCHITECT_CLEAN_PROMPT,
        "pragmatic": ARCHITECT_PRAGMATIC_PROMPT,
    }

    if philosophy not in prompts:
        raise ValueError(
            f"Unknown architect philosophy: {philosophy}. Must be one of: {list(prompts.keys())}"
        )

    return ArchitectPersona(
        philosophy=philosophy,
        system_prompt=prompts[philosophy],
    )
