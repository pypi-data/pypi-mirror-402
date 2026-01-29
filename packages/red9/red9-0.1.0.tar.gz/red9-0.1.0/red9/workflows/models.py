"""Workflow models for multi-agent parallel execution.

Provides structured dataclasses for task decomposition and parallel workflow construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# =============================================================================
# Model Selection Constants for Multi-Model Swarm Strategy
# =============================================================================

MODEL_REASONING = "gpt-oss:120b-cloud"  # Architects - system design, planning
MODEL_CODING = "qwen3-coder:480b-cloud"  # Explorers, Coders - reading/writing code
MODEL_AGENTIC = "nemotron-3-nano:30b-cloud"  # QA, Integrator, generic tasks


class SwarmAgentRole(str, Enum):
    """Roles for agents in a swarm.

    Each role maps to a specific model and focus area.
    """

    # Explorers - analyze codebase (use coding model)
    EXPLORER_ARCHITECTURE = "explorer_architecture"
    EXPLORER_UX = "explorer_ux"
    EXPLORER_TESTS = "explorer_tests"

    # Architects - design solutions (use reasoning model)
    ARCHITECT_MINIMAL = "architect_minimal"
    ARCHITECT_CLEAN = "architect_clean"
    ARCHITECT_PRAGMATIC = "architect_pragmatic"

    # Reviewers - analyze code quality (use coding model)
    REVIEWER_SIMPLICITY = "reviewer_simplicity"
    REVIEWER_BUGS = "reviewer_bugs"
    REVIEWER_CONVENTIONS = "reviewer_conventions"

    # Aggregators/Integrators (use agentic model)
    AGGREGATOR = "aggregator"
    INTEGRATOR = "integrator"


# Model selection by role
SWARM_MODEL_MAP: dict[str, str] = {
    # Explorers read codebases → use coding model
    "explorer_architecture": MODEL_CODING,
    "explorer_ux": MODEL_CODING,
    "explorer_tests": MODEL_CODING,
    # Architects do reasoning → use reasoning model
    "architect_minimal": MODEL_REASONING,
    "architect_clean": MODEL_REASONING,
    "architect_pragmatic": MODEL_REASONING,
    # Reviewers analyze code → use coding model
    "reviewer_simplicity": MODEL_CODING,
    "reviewer_bugs": MODEL_CODING,
    "reviewer_conventions": MODEL_CODING,
    # Aggregators/Integrators → use agentic model
    "aggregator": MODEL_AGENTIC,
    "integrator": MODEL_AGENTIC,
}


@dataclass
class SwarmAgentConfig:
    """Configuration for a single agent in a swarm.

    Defines the role, focus area, and execution parameters for an agent.
    """

    role: SwarmAgentRole
    focus: str  # What this agent should focus on
    system_prompt_extension: str  # Additional prompt guidance for this agent
    max_iterations: int = 20  # Max agentic turns (reduced from 30 to prevent explosion)
    model_override: str | None = None  # Override default model for this agent
    output_key: str = "response"  # Key for storing output (enables template substitution)
    temperature: float = 0.7

    def get_model(self) -> str:
        """Get the model for this agent based on role or override."""
        if self.model_override:
            return self.model_override
        return SWARM_MODEL_MAP.get(self.role.value, MODEL_AGENTIC)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "role": self.role.value,
            "focus": self.focus,
            "system_prompt_extension": self.system_prompt_extension,
            "max_iterations": self.max_iterations,
            "model_override": self.model_override,
            "output_key": self.output_key,
            "temperature": self.temperature,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SwarmAgentConfig:
        """Create from dictionary."""
        return cls(
            role=SwarmAgentRole(data["role"]),
            focus=data["focus"],
            system_prompt_extension=data["system_prompt_extension"],
            max_iterations=data.get("max_iterations", 20),
            model_override=data.get("model_override"),
            output_key=data.get("output_key", "response"),
            temperature=data.get("temperature", 0.7),
        )


@dataclass
class SwarmAgentResult:
    """Result from a single agent in a swarm.

    Stores the agent's output and metadata for aggregation.
    """

    agent_config: SwarmAgentConfig
    output: str
    success: bool
    error: str | None = None
    files_modified: list[str] = field(default_factory=list)
    files_read: list[str] = field(default_factory=list)
    confidence: float = 0.0  # 0-100 confidence score

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_config": self.agent_config.to_dict(),
            "output": self.output,
            "success": self.success,
            "error": self.error,
            "files_modified": self.files_modified,
            "files_read": self.files_read,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SwarmAgentResult:
        """Create from dictionary."""
        return cls(
            agent_config=SwarmAgentConfig.from_dict(data["agent_config"]),
            output=data["output"],
            success=data["success"],
            error=data.get("error"),
            files_modified=data.get("files_modified", []),
            files_read=data.get("files_read", []),
            confidence=data.get("confidence", 0.0),
        )


class AggregationStrategy(str, Enum):
    """Strategy for aggregating swarm results."""

    CONSENSUS = "consensus"  # Synthesize common themes and reconcile differences
    UNION = "union"  # Combine all unique insights
    VOTING = "voting"  # Select approach with most support


@dataclass
class SwarmConfig:
    """Configuration for a swarm of agents.

    A swarm is a group of agents that work in parallel on a shared task,
    each with a different perspective or focus area.
    """

    name: str  # e.g., "exploration_swarm", "architecture_swarm"
    agents: list[SwarmAgentConfig] = field(default_factory=list)
    aggregation_strategy: AggregationStrategy = AggregationStrategy.CONSENSUS
    max_concurrent: int = 3  # Max agents running in parallel

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "agents": [a.to_dict() for a in self.agents],
            "aggregation_strategy": self.aggregation_strategy.value,
            "max_concurrent": self.max_concurrent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SwarmConfig:
        """Create from dictionary."""
        return cls(
            name=data["name"],
            agents=[SwarmAgentConfig.from_dict(a) for a in data.get("agents", [])],
            aggregation_strategy=AggregationStrategy(data.get("aggregation_strategy", "consensus")),
            max_concurrent=data.get("max_concurrent", 3),
        )


# =============================================================================
# Pre-defined Swarm Configurations for 7-Phase Workflow
# =============================================================================


def get_exploration_swarm(minimal: bool = False) -> SwarmConfig:
    """Get pre-configured exploration swarm.

    Args:
        minimal: If True, use only 1 agent for faster execution.

    Returns:
        SwarmConfig with 1 or 3 agents.
    """
    if minimal:
        # Single agent for simple/medium tasks
        return SwarmConfig(
            name="exploration_swarm",
            agents=[
                SwarmAgentConfig(
                    role=SwarmAgentRole.EXPLORER_ARCHITECTURE,
                    focus="find relevant files for the task",
                    system_prompt_extension="List the files needed. Be fast.",
                    output_key="explore_architecture",
                    temperature=0.2,
                    max_iterations=10,  # Limit iterations for speed
                ),
            ],
            aggregation_strategy=AggregationStrategy.UNION,
            max_concurrent=1,
        )

    # Full swarm for complex tasks
    return SwarmConfig(
        name="exploration_swarm",
        agents=[
            SwarmAgentConfig(
                role=SwarmAgentRole.EXPLORER_ARCHITECTURE,
                focus="system architecture, module boundaries, call chains, patterns",
                system_prompt_extension="Focus on understanding the overall system architecture.",
                output_key="explore_architecture",
                temperature=0.3,
            ),
            SwarmAgentConfig(
                role=SwarmAgentRole.EXPLORER_UX,
                focus="UI components, user flows, accessibility, user experience",
                system_prompt_extension="Focus on user-facing aspects and user flows.",
                output_key="explore_ux",
                temperature=0.3,
            ),
            SwarmAgentConfig(
                role=SwarmAgentRole.EXPLORER_TESTS,
                focus="test coverage, test frameworks, testing patterns, gaps",
                system_prompt_extension="Focus on testing infrastructure and coverage.",
                output_key="explore_tests",
                temperature=0.3,
            ),
        ],
        aggregation_strategy=AggregationStrategy.UNION,
        max_concurrent=3,
    )


def get_architecture_swarm(minimal: bool = False) -> SwarmConfig:
    """Get pre-configured architecture swarm.

    Args:
        minimal: If True, use only 1 agent (minimal approach) for faster execution.

    Returns:
        SwarmConfig with 1 or 3 agents.
    """
    if minimal:
        # Single agent - always use minimal approach for simple tasks
        return SwarmConfig(
            name="architecture_swarm",
            agents=[
                SwarmAgentConfig(
                    role=SwarmAgentRole.ARCHITECT_MINIMAL,
                    focus="smallest possible footprint",
                    system_prompt_extension="MINIMAL changes only. Be fast.",
                    output_key="arch_minimal",
                    temperature=0.3,
                    max_iterations=10,
                ),
            ],
            aggregation_strategy=AggregationStrategy.VOTING,
            max_concurrent=1,
        )

    # Full swarm for complex tasks
    return SwarmConfig(
        name="architecture_swarm",
        agents=[
            SwarmAgentConfig(
                role=SwarmAgentRole.ARCHITECT_MINIMAL,
                focus="smallest footprint, reuse code, minimal changes",
                system_prompt_extension="MINIMAL changes. Prefer modification.",
                output_key="arch_minimal",
                temperature=0.4,
            ),
            SwarmAgentConfig(
                role=SwarmAgentRole.ARCHITECT_CLEAN,
                focus="SOLID principles, clean architecture, separation of concerns",
                system_prompt_extension="Design following clean architecture principles.",
                output_key="arch_clean",
                temperature=0.4,
            ),
            SwarmAgentConfig(
                role=SwarmAgentRole.ARCHITECT_PRAGMATIC,
                focus="balance quality with delivery speed, good enough is better than perfect",
                system_prompt_extension="Balance quality with practical delivery speed.",
                output_key="arch_pragmatic",
                temperature=0.4,
            ),
        ],
        aggregation_strategy=AggregationStrategy.VOTING,
        max_concurrent=3,
    )


def get_review_swarm(minimal: bool = False) -> SwarmConfig:
    """Get pre-configured review swarm.

    Args:
        minimal: If True, use only 1 agent (bugs only) for faster execution.

    Returns:
        SwarmConfig with 1 or 3 agents.
    """
    if minimal:
        # Single agent - focus on bugs only for simple tasks
        return SwarmConfig(
            name="review_swarm",
            agents=[
                SwarmAgentConfig(
                    role=SwarmAgentRole.REVIEWER_BUGS,
                    focus="bugs and errors only",
                    system_prompt_extension="Check for bugs. Be fast.",
                    output_key="review_bugs",
                    temperature=0.2,
                    max_iterations=10,
                ),
            ],
            aggregation_strategy=AggregationStrategy.UNION,
            max_concurrent=1,
        )

    # Full swarm for complex tasks
    return SwarmConfig(
        name="review_swarm",
        agents=[
            SwarmAgentConfig(
                role=SwarmAgentRole.REVIEWER_SIMPLICITY,
                focus="complexity, over-engineering, simpler alternatives",
                system_prompt_extension="Ask: Can this be simpler?",
                output_key="review_simplicity",
                temperature=0.3,
            ),
            SwarmAgentConfig(
                role=SwarmAgentRole.REVIEWER_BUGS,
                focus="bugs, edge cases, null handling, race conditions",
                system_prompt_extension="Find bugs and edge cases.",
                output_key="review_bugs",
                temperature=0.3,
            ),
            SwarmAgentConfig(
                role=SwarmAgentRole.REVIEWER_CONVENTIONS,
                focus="project conventions, language idioms, style consistency",
                system_prompt_extension="Check project and language conventions are followed.",
                output_key="review_conventions",
                temperature=0.3,
            ),
        ],
        aggregation_strategy=AggregationStrategy.UNION,
        max_concurrent=3,
    )


class SubTaskType(str, Enum):
    """Types of sub-tasks for decomposition."""

    PLAN = "plan"
    CODE = "code"
    TEST_WRITE = "test_write"
    TEST_RUN = "test_run"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    REVIEW = "review"


class SubTaskStatus(str, Enum):
    """Status of a sub-task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class SubTask:
    """A decomposed sub-task that can run independently or in parallel.

    Represents a unit of work that can be assigned to an agent.
    """

    id: str
    name: str
    description: str
    task_type: SubTaskType
    files: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # IDs of dependent sub-tasks
    status: SubTaskStatus = SubTaskStatus.PENDING
    priority: int = 0  # Higher = more important
    estimated_complexity: str = "medium"  # low, medium, high
    outputs: dict[str, Any] = field(default_factory=dict)

    def can_run(self, completed_tasks: set[str]) -> bool:
        """Check if this task can run based on completed dependencies.

        Args:
            completed_tasks: Set of completed task IDs.

        Returns:
            True if all dependencies are satisfied.
        """
        return all(dep in completed_tasks for dep in self.dependencies)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type.value,
            "files": self.files,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "priority": self.priority,
            "estimated_complexity": self.estimated_complexity,
            "outputs": self.outputs,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SubTask:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            task_type=SubTaskType(data["task_type"]),
            files=data.get("files", []),
            dependencies=data.get("dependencies", []),
            status=SubTaskStatus(data.get("status", "pending")),
            priority=data.get("priority", 0),
            estimated_complexity=data.get("estimated_complexity", "medium"),
            outputs=data.get("outputs", {}),
        )


@dataclass
class ParallelGroup:
    """A group of sub-tasks that can execute in parallel.

    All tasks in a group have no dependencies on each other and can
    run concurrently up to max_parallel_stages limit.
    """

    id: str
    name: str
    tasks: list[SubTask] = field(default_factory=list)
    max_concurrent: int = 4
    completed: bool = False

    def get_runnable_tasks(self, completed_task_ids: set[str]) -> list[SubTask]:
        """Get tasks that can run now.

        Args:
            completed_task_ids: Set of completed task IDs.

        Returns:
            List of tasks ready to run.
        """
        return [
            task
            for task in self.tasks
            if task.status == SubTaskStatus.PENDING and task.can_run(completed_task_ids)
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "tasks": [t.to_dict() for t in self.tasks],
            "max_concurrent": self.max_concurrent,
            "completed": self.completed,
        }


@dataclass
class PlanOutput:
    """Structured output from the planning agent.

    Provides typed data for downstream stages instead of free-form text.
    """

    summary: str
    files_to_modify: list[str] = field(default_factory=list)
    files_to_create: list[str] = field(default_factory=list)
    files_to_read: list[str] = field(default_factory=list)
    test_requirements: list[str] = field(default_factory=list)
    sub_tasks: list[SubTask] = field(default_factory=list)
    parallel_groups: list[ParallelGroup] = field(default_factory=list)
    estimated_complexity: str = "medium"
    requires_human_review: bool = False
    notes: str = ""

    def get_all_files(self) -> list[str]:
        """Get all files involved in the plan."""
        all_files = set(self.files_to_modify + self.files_to_create + self.files_to_read)
        for task in self.sub_tasks:
            all_files.update(task.files)
        return list(all_files)

    def has_parallel_potential(self) -> bool:
        """Check if this plan can benefit from parallel execution."""
        if len(self.parallel_groups) > 0:
            return True
        # If there are multiple sub-tasks without mutual dependencies
        if len(self.sub_tasks) > 1:
            for task in self.sub_tasks:
                if not task.dependencies:
                    return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "summary": self.summary,
            "files_to_modify": self.files_to_modify,
            "files_to_create": self.files_to_create,
            "files_to_read": self.files_to_read,
            "test_requirements": self.test_requirements,
            "sub_tasks": [t.to_dict() for t in self.sub_tasks],
            "parallel_groups": [g.to_dict() for g in self.parallel_groups],
            "estimated_complexity": self.estimated_complexity,
            "requires_human_review": self.requires_human_review,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanOutput:
        """Create from dictionary."""
        sub_tasks = [SubTask.from_dict(t) for t in data.get("sub_tasks", [])]
        parallel_groups = []
        for g in data.get("parallel_groups", []):
            parallel_groups.append(
                ParallelGroup(
                    id=g["id"],
                    name=g["name"],
                    tasks=[SubTask.from_dict(t) for t in g.get("tasks", [])],
                    max_concurrent=g.get("max_concurrent", 4),
                    completed=g.get("completed", False),
                )
            )
        return cls(
            summary=data.get("summary", ""),
            files_to_modify=data.get("files_to_modify", []),
            files_to_create=data.get("files_to_create", []),
            files_to_read=data.get("files_to_read", []),
            test_requirements=data.get("test_requirements", []),
            sub_tasks=sub_tasks,
            parallel_groups=parallel_groups,
            estimated_complexity=data.get("estimated_complexity", "medium"),
            requires_human_review=data.get("requires_human_review", False),
            notes=data.get("notes", ""),
        )


@dataclass
class TaskDecomposition:
    """Result of analyzing a request for parallel execution potential.

    Used by the decomposition agent to break complex tasks into parallel groups.
    """

    original_request: str
    can_parallelize: bool
    parallel_groups: list[ParallelGroup] = field(default_factory=list)
    sequential_fallback: list[SubTask] = field(default_factory=list)
    reason: str = ""

    def get_total_tasks(self) -> int:
        """Get total number of tasks."""
        count = len(self.sequential_fallback)
        for group in self.parallel_groups:
            count += len(group.tasks)
        return count

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "original_request": self.original_request,
            "can_parallelize": self.can_parallelize,
            "parallel_groups": [g.to_dict() for g in self.parallel_groups],
            "sequential_fallback": [t.to_dict() for t in self.sequential_fallback],
            "reason": self.reason,
        }
