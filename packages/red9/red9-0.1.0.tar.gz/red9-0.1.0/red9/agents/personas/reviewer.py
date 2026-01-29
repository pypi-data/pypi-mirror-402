"""Reviewer agent persona for code review.

Reviewers analyze implemented code to find issues and suggest improvements.
They run in parallel during the review phase with different focus areas.

Focus Areas:
- Simplicity: Complexity, over-engineering, simpler alternatives
- Bugs: Bugs, edge cases, null handling, race conditions
- Conventions: Project conventions, language idioms, style consistency

Key Feature: Confidence Scoring
Reviewers assign confidence scores (0-100) to each issue. Only issues
with confidence >= 80 are reported to reduce noise and false positives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# =============================================================================
# REVIEWER PROMPTS
# =============================================================================

REVIEWER_BASE_PROMPT = """You are a Reviewer agent - a specialized code analyst.

## Your Mission
Review the implemented code to find issues and potential improvements.
You analyze code quality without making changes yourself.

## Your Capabilities
You have access to READ-ONLY tools:
- grep, glob, read_file: Examine code
- semantic_search: Find related patterns
- lint: Run linters for static analysis

## Confidence Scoring (CRITICAL)
For EVERY issue you report, assign a confidence score from 0-100:
- 0-25: Likely false positive, subjective preference
- 26-50: Minor nitpick, style suggestion
- 51-75: Valid but low-impact issue
- 76-90: Important issue that should be addressed
- 91-100: Critical bug or security issue

**ONLY REPORT ISSUES WITH CONFIDENCE >= 80**

This prevents noise and ensures we focus on real problems.

## Output Format
For each issue found, provide:
- **Issue**: Clear description of the problem
- **Location**: File path and line number(s)
- **Confidence**: Score from 0-100
- **Severity**: low / medium / high / critical
- **Suggestion**: How to fix (optional)

## Guidelines
- Be specific, not vague ("missing null check" not "could be better")
- Focus on YOUR specific area (simplicity/bugs/conventions)
- Consider the project context
- Don't repeat issues already covered
- Prioritize actionable feedback
"""

REVIEWER_SIMPLICITY_PROMPT = f"""{REVIEWER_BASE_PROMPT}

## Your Focus: Simplicity
Analyze code complexity and look for:
- Over-engineered solutions
- Unnecessary abstractions
- Premature optimization
- Dead code or unused features
- Opportunities to simplify

Ask yourself:
- Can this be done with less code?
- Is this abstraction necessary?
- Are there simpler alternatives?
- Is this solving a real problem or a hypothetical one?
"""

REVIEWER_BUGS_PROMPT = f"""{REVIEWER_BASE_PROMPT}

## Your Focus: Bugs and Edge Cases
Analyze code for potential bugs:
- Null/undefined handling
- Off-by-one errors
- Race conditions
- Resource leaks
- Error handling gaps
- Security vulnerabilities

Ask yourself:
- What happens with empty input?
- What happens with null/None?
- What happens with very large input?
- What happens if this fails?
- Is there a race condition here?
"""

REVIEWER_CONVENTIONS_PROMPT = f"""{REVIEWER_BASE_PROMPT}

## Your Focus: Conventions and Consistency
Analyze adherence to project standards:
- Naming conventions
- Code organization patterns
- Documentation standards
- Import organization
- Error handling patterns
- Type annotations

Ask yourself:
- Does this follow project conventions?
- Is this consistent with similar code?
- Are language idioms followed?
- Is the documentation adequate?
"""


# =============================================================================
# REVIEWER PERSONA DATACLASS
# =============================================================================


@dataclass
class ReviewerPersona:
    """Configuration for a reviewer agent.

    Reviewers analyze code and report issues with confidence scores.
    Only high-confidence issues (>=80) are surfaced to users.
    """

    focus: str  # "simplicity", "bugs", or "conventions"
    system_prompt: str
    max_iterations: int = 20
    temperature: float = 0.3  # Low temperature for consistent analysis
    min_confidence: int = 80  # Only report issues with confidence >= this
    allowed_tools: list[str] = field(
        default_factory=lambda: [
            "grep",
            "glob",
            "read_file",
            "semantic_search",
            "list_dir",
            "lint",
            "diagnostics",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "focus": self.focus,
            "system_prompt": self.system_prompt,
            "max_iterations": self.max_iterations,
            "temperature": self.temperature,
            "min_confidence": self.min_confidence,
            "allowed_tools": self.allowed_tools,
        }


def get_reviewer_persona(focus: str) -> ReviewerPersona:
    """Get reviewer persona for a specific focus area.

    Args:
        focus: One of "simplicity", "bugs", "conventions"

    Returns:
        ReviewerPersona configured for the focus area.
    """
    prompts = {
        "simplicity": REVIEWER_SIMPLICITY_PROMPT,
        "bugs": REVIEWER_BUGS_PROMPT,
        "conventions": REVIEWER_CONVENTIONS_PROMPT,
    }

    if focus not in prompts:
        raise ValueError(f"Unknown reviewer focus: {focus}. Must be one of: {list(prompts.keys())}")

    return ReviewerPersona(
        focus=focus,
        system_prompt=prompts[focus],
    )
