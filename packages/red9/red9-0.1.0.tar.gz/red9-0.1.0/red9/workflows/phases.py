"""7-Phase Enterprise Workflow Definition.

Defines the enterprise workflow structure inspired by Claude Code's approach:
- Phase 1: Discovery - Classify task, ask clarifying questions
- Phase 2: Exploration - Parallel explorers (architecture, UX, tests)
- Phase 3: Clarification - User confirms understanding
- Phase 4: Architecture - Parallel architects (minimal, clean, pragmatic)
- Phase 5: Approval - User approves architecture approach
- Phase 6: Implementation - DDD agent implements the approved design
- Phase 7: Review - Parallel reviewers with confidence scoring
- Phase 8: Final - User approval and tests
- Phase 9: Completion - Summary and cleanup

Key Features:
- Parallel agent execution at exploration, architecture, and review phases
- Explicit user approval gates at critical decision points
- Confidence-based filtering for review issues (>=80 only)
- Schema validation between stages
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkflowPhase(str, Enum):
    """Phases in the enterprise workflow."""

    DISCOVERY = "discovery"
    EXPLORATION = "exploration"
    CLARIFICATION = "clarification"
    ARCHITECTURE = "architecture"
    APPROVAL = "approval"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    FINAL = "final"
    COMPLETION = "completion"


class ApprovalType(str, Enum):
    """Types of approval gates."""

    EXPLORATION = "exploration"  # After exploration, before architecture
    ARCHITECTURE = "architecture"  # After architecture, before implementation
    FINAL = "final"  # After review, before completion


@dataclass
class PhaseConfig:
    """Configuration for a workflow phase."""

    phase: WorkflowPhase
    name: str
    description: str
    parallel_agents: int = 1  # Number of parallel agents in this phase
    requires_approval: bool = False
    approval_type: ApprovalType | None = None
    stage_type: str = ""  # Stabilize stage type
    agent_roles: list[str] = field(default_factory=list)
    timeout_minutes: int = 10


# =============================================================================
# PHASE CONFIGURATIONS
# =============================================================================

PHASE_CONFIGS: dict[WorkflowPhase, PhaseConfig] = {
    WorkflowPhase.DISCOVERY: PhaseConfig(
        phase=WorkflowPhase.DISCOVERY,
        name="Discovery",
        description="Classify task complexity and gather initial context",
        parallel_agents=1,
        requires_approval=False,
        stage_type="context_agent",
        timeout_minutes=5,
    ),
    WorkflowPhase.EXPLORATION: PhaseConfig(
        phase=WorkflowPhase.EXPLORATION,
        name="Codebase Exploration",
        description="Parallel exploration of codebase from different perspectives",
        parallel_agents=3,  # architecture, UX, tests
        requires_approval=False,
        stage_type="explorer_agent",
        agent_roles=["architecture", "ux", "tests"],
        timeout_minutes=10,
    ),
    WorkflowPhase.CLARIFICATION: PhaseConfig(
        phase=WorkflowPhase.CLARIFICATION,
        name="Confirm Understanding",
        description="User confirms exploration findings and essential files",
        parallel_agents=1,
        requires_approval=True,
        approval_type=ApprovalType.EXPLORATION,
        stage_type="approval_gate",
        timeout_minutes=30,
    ),
    WorkflowPhase.ARCHITECTURE: PhaseConfig(
        phase=WorkflowPhase.ARCHITECTURE,
        name="Architecture Design",
        description="Parallel architecture proposals from different philosophies",
        parallel_agents=3,  # minimal, clean, pragmatic
        requires_approval=False,
        stage_type="architect_agent",
        agent_roles=["minimal", "clean", "pragmatic"],
        timeout_minutes=15,
    ),
    WorkflowPhase.APPROVAL: PhaseConfig(
        phase=WorkflowPhase.APPROVAL,
        name="Architecture Approval",
        description="User selects architecture approach to implement",
        parallel_agents=1,
        requires_approval=True,
        approval_type=ApprovalType.ARCHITECTURE,
        stage_type="approval_gate",
        timeout_minutes=30,
    ),
    WorkflowPhase.IMPLEMENTATION: PhaseConfig(
        phase=WorkflowPhase.IMPLEMENTATION,
        name="Implementation",
        description="DDD implementation of approved design",
        parallel_agents=1,
        requires_approval=False,
        stage_type="ddd_agent",
        timeout_minutes=30,
    ),
    WorkflowPhase.REVIEW: PhaseConfig(
        phase=WorkflowPhase.REVIEW,
        name="Code Review",
        description="Parallel review from different perspectives",
        parallel_agents=3,  # simplicity, bugs, conventions
        requires_approval=False,
        stage_type="reviewer_agent",
        agent_roles=["simplicity", "bugs", "conventions"],
        timeout_minutes=10,
    ),
    WorkflowPhase.FINAL: PhaseConfig(
        phase=WorkflowPhase.FINAL,
        name="Final Approval",
        description="User reviews issues and approves changes",
        parallel_agents=1,
        requires_approval=True,
        approval_type=ApprovalType.FINAL,
        stage_type="approval_gate",
        timeout_minutes=30,
    ),
    WorkflowPhase.COMPLETION: PhaseConfig(
        phase=WorkflowPhase.COMPLETION,
        name="Completion",
        description="Run tests, generate summary, complete workflow",
        parallel_agents=1,
        requires_approval=False,
        stage_type="doc_sync_agent",
        timeout_minutes=10,
    ),
}


# =============================================================================
# ENTERPRISE WORKFLOW DEFINITION
# =============================================================================


@dataclass
class EnterpriseWorkflowConfig:
    """Configuration for the full enterprise workflow."""

    name: str = "Enterprise 7-Phase Workflow"
    description: str = "Full enterprise workflow with parallel agents and approval gates"
    phases: list[WorkflowPhase] = field(default_factory=lambda: list(WorkflowPhase))
    skip_exploration: bool = False  # Skip for simple tasks
    skip_architecture: bool = False  # Skip for simple tasks
    skip_review: bool = False  # Skip for simple tasks
    use_minimal_agents: bool = False  # Use 1 agent per phase instead of 3

    def get_active_phases(self) -> list[WorkflowPhase]:
        """Get the list of active phases based on config."""
        phases = []

        # Discovery always runs
        phases.append(WorkflowPhase.DISCOVERY)

        if not self.skip_exploration:
            phases.append(WorkflowPhase.EXPLORATION)
            phases.append(WorkflowPhase.CLARIFICATION)

        if not self.skip_architecture:
            phases.append(WorkflowPhase.ARCHITECTURE)
            phases.append(WorkflowPhase.APPROVAL)

        # Implementation always runs
        phases.append(WorkflowPhase.IMPLEMENTATION)

        if not self.skip_review:
            phases.append(WorkflowPhase.REVIEW)
            phases.append(WorkflowPhase.FINAL)

        # Completion always runs
        phases.append(WorkflowPhase.COMPLETION)

        return phases

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "phases": [p.value for p in self.phases],
            "skip_exploration": self.skip_exploration,
            "skip_architecture": self.skip_architecture,
            "skip_review": self.skip_review,
            "use_minimal_agents": self.use_minimal_agents,
        }


def get_enterprise_config(complexity: str = "medium") -> EnterpriseWorkflowConfig:
    """Get enterprise workflow config based on task complexity.

    Args:
        complexity: "simple", "medium", or "complex"

    Returns:
        EnterpriseWorkflowConfig tuned for the complexity level.
    """
    if complexity == "simple":
        # For simple tasks, skip exploration, architecture, and review
        return EnterpriseWorkflowConfig(
            name="Simple Workflow",
            description="Minimal workflow for simple tasks",
            skip_exploration=True,
            skip_architecture=True,
            skip_review=True,
            use_minimal_agents=True,
        )
    elif complexity == "complex":
        # For complex tasks, use full workflow with 3 agents per phase
        return EnterpriseWorkflowConfig(
            name="Complex Enterprise Workflow",
            description="Full workflow with all phases and parallel agents",
            skip_exploration=False,
            skip_architecture=False,
            skip_review=False,
            use_minimal_agents=False,
        )
    else:  # medium
        # For medium tasks, use full workflow with minimal agents
        return EnterpriseWorkflowConfig(
            name="Medium Enterprise Workflow",
            description="Full workflow with minimal parallel agents",
            skip_exploration=False,
            skip_architecture=False,
            skip_review=False,
            use_minimal_agents=True,  # Use 1 agent per phase for speed
        )


# =============================================================================
# FAST MODE CONFIGURATION
# =============================================================================


@dataclass
class FastWorkflowConfig:
    """Configuration for fast/simple mode workflow.

    This skips the enterprise workflow and goes straight to implementation
    with a single agent.
    """

    name: str = "Fast Mode"
    description: str = "Single-agent implementation without exploration or review"
    skip_all_phases: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "skip_all_phases": self.skip_all_phases,
        }
