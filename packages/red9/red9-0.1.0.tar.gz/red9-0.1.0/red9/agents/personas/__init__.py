"""Agent personas for RED9.

Exposes specialized personas for different agent roles.
"""

from red9.agents.personas.architect import ArchitectPersona, get_architect_persona
from red9.agents.personas.explorer import ExplorerPersona, get_explorer_persona
from red9.agents.personas.implementer import ImplementerPersona, get_implementer_persona
from red9.agents.personas.reviewer import ReviewerPersona, get_reviewer_persona

__all__ = [
    "ArchitectPersona",
    "get_architect_persona",
    "ExplorerPersona",
    "get_explorer_persona",
    "ReviewerPersona",
    "get_reviewer_persona",
    "ImplementerPersona",
    "get_implementer_persona",
    "get_specialist_prompt",
]


def get_specialist_prompt(persona: str = "general") -> str:
    """Get instructions for a specialist persona.

    Args:
        persona: The persona type ("general", "frontend", "backend", "data").

    Returns:
        Specific instructions for that specialist.
    """
    persona = persona.lower()

    base_instructions = """
## Coding Standards
- Write clean, maintainable code
- Follow project conventions
- Use appropriate error handling
- Add comments for complex logic
"""

    if persona == "frontend":
        return (
            base_instructions
            + """
## Frontend Specialist
- Focus on UI/UX and responsiveness
- Use modern framework practices (React/Vue/etc)
- Ensure accessibility (a11y) compliance
- Handle state management effectively
"""
        )
    elif persona == "backend":
        return (
            base_instructions
            + """
## Backend Specialist
- Focus on API design and data integrity
- Ensure proper validation and security
- Optimize for performance and scalability
- handle database transactions correctly
"""
        )
    elif persona == "data":
        return (
            base_instructions
            + """
## Data Specialist
- Focus on data processing and analysis
- efficient data structures and algorithms
- Ensure data quality and validation
"""
        )
    else:  # general
        return base_instructions
