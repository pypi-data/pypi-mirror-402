"""RED9 - Enterprise Multi-Agent Coding System.

RED9 leverages Stabilize for workflow orchestration, IssueDB for task management,
and Ragit for codebase understanding through RAG.
"""

__version__ = "0.1.0"
__author__ = "Rodmena Limited"

from red9.config.schema import Red9Config

__all__ = [
    "__version__",
    "Red9Config",
]
