"""Agent implementations as Stabilize Tasks."""

from red9.agents.loop import (
    AgentLoop,
    AgentResult,
    format_guidelines,
    load_agent_context,
)
from red9.agents.prompts import (
    CODE_AGENT_SYSTEM_PROMPT,
    FIX_AGENT_SYSTEM_PROMPT,
    PLAN_AGENT_SYSTEM_PROMPT,
    REVIEW_AGENT_SYSTEM_PROMPT,
    TEST_AGENT_SYSTEM_PROMPT,
    get_agent_prompt,
)

__all__ = [
    "AgentLoop",
    "AgentResult",
    "load_agent_context",
    "format_guidelines",
    "PLAN_AGENT_SYSTEM_PROMPT",
    "CODE_AGENT_SYSTEM_PROMPT",
    "TEST_AGENT_SYSTEM_PROMPT",
    "FIX_AGENT_SYSTEM_PROMPT",
    "REVIEW_AGENT_SYSTEM_PROMPT",
    "get_agent_prompt",
]
