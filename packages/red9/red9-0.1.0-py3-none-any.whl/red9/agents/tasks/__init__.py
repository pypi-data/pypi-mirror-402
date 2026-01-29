"""Stabilize Task implementations for agents."""

from red9.agents.tasks.code import CodeAgentTask
from red9.agents.tasks.issue_complete import IssueCompleteTask
from red9.agents.tasks.issue_setup import IssueSetupTask
from red9.agents.tasks.iteration_loop import IterationLoopTask
from red9.agents.tasks.plan import PlanAgentTask
from red9.agents.tasks.test import TestAgentTask

__all__ = [
    "IssueSetupTask",
    "IssueCompleteTask",
    "PlanAgentTask",
    "CodeAgentTask",
    "TestAgentTask",
    "IterationLoopTask",
]
