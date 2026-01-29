"""Agent hooks for modifying agent behavior.

Hooks can intercept and modify agent execution at various points:
- Before tool execution
- After tool execution
- Before agent completion
- After agent output
"""

from red9.agents.hooks.todo_enforcer import TodoEnforcer

__all__ = ["TodoEnforcer"]
