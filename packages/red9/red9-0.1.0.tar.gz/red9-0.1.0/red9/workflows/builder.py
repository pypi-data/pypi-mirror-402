"""Workflow DAG construction from plans.

RED9 follows Test-Driven Development (TDD):
1. Plan what to do
2. Write tests FIRST
3. Implement code to pass the tests
4. Verify all tests pass

This ensures reliable, testable code for any language or framework.

Supports both linear (sequential) and parallel workflow construction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from stabilize import StageExecution, TaskExecution, Workflow
from ulid import ULID

from red9.workflows.models import (
    AggregationStrategy,
    PlanOutput,
    SubTaskType,
    SwarmConfig,
    get_architecture_swarm,
    get_exploration_swarm,
)
from red9.workflows.phases import get_enterprise_config


def build_simple_workflow(
    request: str,
    project_root: Path,
    mentioned_files: list[str] | None = None,
) -> Workflow:
    """Build a minimal single-agent workflow for simple tasks.

    This workflow is optimized for tasks like:
    - "write a simple fibonacci python app"
    - "create hello world"
    - "fix typo in file X"

    Uses ONE agent that writes code directly without:
    - Exploration swarms
    - Architecture analysis
    - Multiple review passes
    - Human approval gates

    Flow: code_agent → done

    Args:
        request: User's task request.
        project_root: Project root directory.
        mentioned_files: List of files mentioned in the request.

    Returns:
        Minimal Stabilize Workflow with single agent.
    """
    workflow_id = str(ULID())
    project_root_str = str(project_root)

    stages = [
        # Single implementation stage - code agent does everything
        StageExecution(
            ref_id="implement",
            type="simple_code_agent",
            name="Implement",
            context={
                "request": request,
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "mode": "simple",  # Signal to agent to be direct
                "mentioned_files": mentioned_files or [],
                "phase_number": 1,
                "total_phases": 1,
            },
            tasks=[
                TaskExecution.create(
                    name="Simple Code Agent",
                    implementing_class="simple_code_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        ),
    ]

    return Workflow.create(
        application="red9",
        name=f"Simple: {request[:50]}",
        stages=stages,
    )


def build_task_workflow(
    request: str,
    issue_id: int,
    plan: dict[str, Any] | None = None,
    project_root: Path | None = None,
) -> Workflow:
    """Build a Stabilize workflow for a task request.

    Creates a TDD-focused linear DAG:
    1. IssueSetup - marks issue as in-progress
    2. PlanAgent - analyzes request, creates plan with test requirements
    3. TestWriteAgent - writes tests FIRST (TDD approach)
    4. CodeAgent - implements the changes to pass the tests
    5. TestRunAgent - runs tests to verify implementation
    6. IssueComplete - updates issue status

    Args:
        request: User's task request.
        issue_id: IssueDB issue ID for tracking.
        plan: Optional pre-computed plan (not used, plan always runs).
        project_root: Project root directory.

    Returns:
        Configured Stabilize Workflow.
    """
    workflow_id = str(ULID())
    project_root_str = str(project_root) if project_root else None

    stages = [
        # Stage 1: Issue Setup
        StageExecution(
            ref_id="issue_setup",
            type="issue_setup",
            name="Initialize Issue",
            context={
                "issue_id": issue_id,
                "workflow_id": workflow_id,
                "project_root": project_root_str,
            },
            tasks=[
                TaskExecution.create(
                    name="Setup Issue",
                    implementing_class="issue_setup",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        ),
        # Stage 2: Plan Agent (includes test planning)
        StageExecution(
            ref_id="plan",
            type="plan_agent",
            name="Plan Implementation",
            requisite_stage_ref_ids={"issue_setup"},
            context={
                "request": request,
                "issue_id": issue_id,
                "workflow_id": workflow_id,
                "project_root": project_root_str,
            },
            tasks=[
                TaskExecution.create(
                    name="Run Plan Agent",
                    implementing_class="plan_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        ),
        # Stage 3: Write Tests FIRST (TDD approach)
        StageExecution(
            ref_id="write_tests",
            type="test_write_agent",
            name="Write Tests First",
            requisite_stage_ref_ids={"plan"},
            context={
                "request": request,
                "issue_id": issue_id,
                "workflow_id": workflow_id,
                "project_root": project_root_str,
                "phase": "write_tests",
            },
            tasks=[
                TaskExecution.create(
                    name="Write Tests Agent",
                    implementing_class="test_write_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        ),
        # Stage 4: Code Agent (implements to pass tests)
        StageExecution(
            ref_id="code",
            type="code_agent",
            name="Implement Changes",
            requisite_stage_ref_ids={"write_tests"},
            context={
                "request": request,
                "issue_id": issue_id,
                "workflow_id": workflow_id,
                "project_root": project_root_str,
            },
            tasks=[
                TaskExecution.create(
                    name="Run Code Agent",
                    implementing_class="code_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        ),
        # Stage 5: Run Tests (verify implementation)
        StageExecution(
            ref_id="run_tests",
            type="test_run_agent",
            name="Run Tests",
            requisite_stage_ref_ids={"code"},
            context={
                "request": request,
                "issue_id": issue_id,
                "workflow_id": workflow_id,
                "project_root": project_root_str,
                "phase": "run_tests",
            },
            tasks=[
                TaskExecution.create(
                    name="Run Tests Agent",
                    implementing_class="test_run_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        ),
        # Stage 6: Issue Complete
        StageExecution(
            ref_id="complete",
            type="issue_complete",
            name="Complete Issue",
            requisite_stage_ref_ids={"run_tests"},
            context={
                "issue_id": issue_id,
                "workflow_id": workflow_id,
                "project_root": project_root_str,
            },
            tasks=[
                TaskExecution.create(
                    name="Complete Issue",
                    implementing_class="issue_complete",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        ),
    ]

    return Workflow.create(
        application="red9",
        name=f"Task: {request[:50]}",
        stages=stages,
    )


def build_ask_workflow(
    question: str,
    project_root: Path | None = None,
) -> Workflow:
    """Build a workflow for answering a question.

    Creates a simple single-stage workflow.

    Args:
        question: User's question.
        project_root: Project root directory.

    Returns:
        Configured Stabilize Workflow.
    """
    workflow_id = str(ULID())

    stages = [
        StageExecution(
            ref_id="answer",
            type="plan_agent",  # Use plan agent for answering questions
            name="Generate Answer",
            context={
                "request": question,
                "is_question": True,
                "workflow_id": workflow_id,
                "project_root": str(project_root) if project_root else None,
            },
            tasks=[
                TaskExecution.create(
                    name="Answer Question",
                    implementing_class="plan_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    ]

    return Workflow.create(
        application="red9",
        name=f"Ask: {question[:50]}",
        stages=stages,
    )


def build_parallel_workflow(
    request: str,
    issue_id: int,
    plan_output: PlanOutput,
    project_root: Path | None = None,
    max_parallel_stages: int = 4,
) -> Workflow:
    """Build a Stabilize workflow with parallel stage execution.

    Creates a DAG where independent sub-tasks run in parallel after the plan stage.
    Respects the max_parallel_stages config for concurrency limits.

    The workflow structure:
    1. IssueSetup - sequential (marks issue as in-progress)
    2. Plan - sequential (analyzes request, creates decomposition)
    3. Parallel Group(s) - multiple agents work on independent tasks
    4. Merge - sequential (combines parallel results)
    5. TestRun - sequential (runs all tests)
    6. IssueComplete - sequential (updates issue status)

    Args:
        request: User's task request.
        issue_id: IssueDB issue ID for tracking.
        plan_output: Structured plan output with sub-tasks and parallel groups.
        project_root: Project root directory.
        max_parallel_stages: Maximum concurrent stages.

    Returns:
        Configured Stabilize Workflow with parallel execution.
    """
    workflow_id = str(ULID())
    project_root_str = str(project_root) if project_root else None

    stages: list[StageExecution] = []

    # Stage 1: Issue Setup (sequential)
    stages.append(
        StageExecution(
            ref_id="issue_setup",
            type="issue_setup",
            name="Initialize Issue",
            context={
                "issue_id": issue_id,
                "workflow_id": workflow_id,
                "project_root": project_root_str,
            },
            tasks=[
                TaskExecution.create(
                    name="Setup Issue",
                    implementing_class="issue_setup",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # Stage 2: Plan (sequential) - already done if plan_output provided
    # Include plan output in context for downstream stages
    stages.append(
        StageExecution(
            ref_id="plan",
            type="plan_agent",
            name="Plan Implementation",
            requisite_stage_ref_ids={"issue_setup"},
            context={
                "request": request,
                "issue_id": issue_id,
                "workflow_id": workflow_id,
                "project_root": project_root_str,
                "plan_provided": True,
                "plan_data": plan_output.to_dict(),
            },
            tasks=[
                TaskExecution.create(
                    name="Run Plan Agent",
                    implementing_class="plan_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # Stage 3: Decompose Agent - analyzes plan for parallel potential
    # Uses AI to identify independent sub-tasks and create parallel groups
    stages.append(
        StageExecution(
            ref_id="decompose",
            type="decompose_agent",
            name="Analyze Parallel Potential",
            requisite_stage_ref_ids={"plan"},
            context={
                "request": request,
                "issue_id": issue_id,
                "workflow_id": workflow_id,
                "project_root": project_root_str,
                "plan_data": plan_output.to_dict(),
            },
            tasks=[
                TaskExecution.create(
                    name="Run Decompose Agent",
                    implementing_class="decompose_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # Stage 4+: Parallel groups for independent sub-tasks
    parallel_stage_refs: set[str] = set()

    if plan_output.parallel_groups:
        # Use pre-defined parallel groups
        for group in plan_output.parallel_groups:
            group_ref = f"parallel_{group.id}"
            parallel_stage_refs.add(group_ref)

            stages.append(
                StageExecution(
                    ref_id=group_ref,
                    type="code_agent",
                    name=f"Parallel: {group.name}",
                    requisite_stage_ref_ids={"decompose"},  # Depend on decompose
                    context={
                        "request": request,
                        "issue_id": issue_id,
                        "workflow_id": workflow_id,
                        "project_root": project_root_str,
                        "parallel_group": group.to_dict(),
                        "max_concurrent": min(group.max_concurrent, max_parallel_stages),
                    },
                    tasks=[
                        TaskExecution.create(
                            name=f"Execute {group.name}",
                            implementing_class="code_agent",
                            stage_start=True,
                            stage_end=True,
                        )
                    ],
                )
            )
    elif plan_output.sub_tasks:
        # Create parallel stages from independent sub-tasks
        # Group by files without mutual dependencies
        independent_tasks = [t for t in plan_output.sub_tasks if not t.dependencies]
        dependent_tasks = [t for t in plan_output.sub_tasks if t.dependencies]

        # Create stages for independent tasks (can run in parallel)
        for i, task in enumerate(independent_tasks[:max_parallel_stages]):
            stage_ref = f"parallel_task_{task.id}"
            parallel_stage_refs.add(stage_ref)

            implementing_class = _get_implementing_class(task.task_type)

            stages.append(
                StageExecution(
                    ref_id=stage_ref,
                    type=implementing_class,
                    name=f"Task: {task.name}",
                    requisite_stage_ref_ids={"decompose"},  # Depend on decompose
                    context={
                        "request": request,
                        "issue_id": issue_id,
                        "workflow_id": workflow_id,
                        "project_root": project_root_str,
                        "sub_task": task.to_dict(),
                        "files": task.files,
                    },
                    tasks=[
                        TaskExecution.create(
                            name=task.name,
                            implementing_class=implementing_class,
                            stage_start=True,
                            stage_end=True,
                        )
                    ],
                )
            )

        # Add dependent tasks after their dependencies
        for task in dependent_tasks:
            stage_ref = f"dependent_task_{task.id}"
            dep_refs = {f"parallel_task_{dep}" for dep in task.dependencies}

            implementing_class = _get_implementing_class(task.task_type)

            stages.append(
                StageExecution(
                    ref_id=stage_ref,
                    type=implementing_class,
                    name=f"Task: {task.name}",
                    requisite_stage_ref_ids=dep_refs if dep_refs else {"decompose"},
                    context={
                        "request": request,
                        "issue_id": issue_id,
                        "workflow_id": workflow_id,
                        "project_root": project_root_str,
                        "sub_task": task.to_dict(),
                        "files": task.files,
                    },
                    tasks=[
                        TaskExecution.create(
                            name=task.name,
                            implementing_class=implementing_class,
                            stage_start=True,
                            stage_end=True,
                        )
                    ],
                )
            )
            parallel_stage_refs.add(stage_ref)

    # If no parallel groups were created, fall back to linear workflow
    if not parallel_stage_refs:
        return build_task_workflow(request, issue_id, plan_output.to_dict(), project_root)

    # Stage: Merge Agent - aggregates results from parallel stages
    # Collects files_modified, detects conflicts before running tests
    stages.append(
        StageExecution(
            ref_id="merge",
            type="merge_agent",
            name="Merge Parallel Results",
            requisite_stage_ref_ids=parallel_stage_refs,  # Wait for ALL parallel stages
            context={
                "request": request,
                "issue_id": issue_id,
                "workflow_id": workflow_id,
                "project_root": project_root_str,
            },
            tasks=[
                TaskExecution.create(
                    name="Merge Results",
                    implementing_class="merge_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # Stage: Run Tests (after merge completes)
    stages.append(
        StageExecution(
            ref_id="run_tests",
            type="test_run_agent",
            name="Run Tests",
            requisite_stage_ref_ids={"merge"},  # Wait for merge to complete
            context={
                "request": request,
                "issue_id": issue_id,
                "workflow_id": workflow_id,
                "project_root": project_root_str,
                "phase": "run_tests",
            },
            tasks=[
                TaskExecution.create(
                    name="Run Tests Agent",
                    implementing_class="test_run_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # Stage: Issue Complete
    stages.append(
        StageExecution(
            ref_id="complete",
            type="issue_complete",
            name="Complete Issue",
            requisite_stage_ref_ids={"run_tests"},
            context={
                "issue_id": issue_id,
                "workflow_id": workflow_id,
                "project_root": project_root_str,
            },
            tasks=[
                TaskExecution.create(
                    name="Complete Issue",
                    implementing_class="issue_complete",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    return Workflow.create(
        application="red9",
        name=f"Parallel Task: {request[:50]}",
        stages=stages,
    )


def build_v2_workflow(
    request: str,
    project_root: Path,
) -> Workflow:
    """Build the Red9 v2 Workflow with autonomous error recovery.

    This implements the "MoAI-ADK" style architecture with strict phases
    and reduced chattiness via comprehensive context injection.

    Flow:
        p_index -> p0_context -> p1_spec -> p2_ddd
        -> p2_recovery_diagnosis -> p2_recovery_compensation -> p2_recovery_retry
        -> p2b_test -> p3_sync

    The recovery stages (diagnosis/compensation/retry) handle DDD failures
    autonomously. If DDD succeeds, recovery stages quickly pass through.
    If DDD fails, the recovery system diagnoses the issue, applies compensation,
    and retries intelligently.

    Args:
        request: User's task request.
        project_root: Project root directory.

    Returns:
        Configured Stabilize Workflow.
    """
    workflow_id = str(ULID())
    project_root_str = str(project_root)

    # V2 workflow has 5 main phases (0-4), plus recovery stages
    total_phases = 5

    stages = [
        # Index Setup (pre-phase, not shown in progress)
        StageExecution(
            ref_id="p_index",
            type="index_setup",
            name="Index Setup",
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "phase_number": 0,
                "total_phases": total_phases,
            },
            tasks=[
                TaskExecution.create(
                    name="Index Setup",
                    implementing_class="index_setup",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        ),
        # Phase 1: Context & Verification
        StageExecution(
            ref_id="p0_context",
            type="context_agent",
            name="Context & Verification",
            requisite_stage_ref_ids={"p_index"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "phase_number": 1,
                "total_phases": total_phases,
            },
            tasks=[
                TaskExecution.create(
                    name="Context Agent",
                    implementing_class="context_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        ),
        # Phase 2: SPEC-First Planning
        StageExecution(
            ref_id="p1_spec",
            type="spec_agent",
            name="SPEC Planning",
            requisite_stage_ref_ids={"p0_context"},
            context={
                "request": request,
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "phase_number": 2,
                "total_phases": total_phases,
            },
            tasks=[
                TaskExecution.create(
                    name="Spec Agent",
                    implementing_class="spec_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        ),
    ]

    # Phase 3: Implementation Loop
    stages.append(
        StageExecution(
            ref_id="p2_iteration_loop",
            type="iteration_loop",
            name="Implementation Loop",
            requisite_stage_ref_ids={"p1_spec"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "request": request,
                "max_iterations": 10,
                "phase_number": 3,
                "total_phases": total_phases,
            },
            tasks=[
                TaskExecution.create(
                    name="Iteration Loop",
                    implementing_class="iteration_loop",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # Phase 4: Test Verification
    stages.append(
        StageExecution(
            ref_id="p2b_test",
            type="test_run_agent",
            name="Test Verification",
            requisite_stage_ref_ids={"p2_iteration_loop"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "request": request,
                "phase_number": 4,
                "total_phases": total_phases,
            },
            tasks=[
                TaskExecution.create(
                    name="Test Run Agent",
                    implementing_class="test_run_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )
    # Phase 5: Documentation Sync
    stages.append(
        StageExecution(
            ref_id="p3_sync",
            type="doc_sync_agent",
            name="Finalization",
            requisite_stage_ref_ids={"p2b_test"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "phase_number": 5,
                "total_phases": total_phases,
            },
            tasks=[
                TaskExecution.create(
                    name="Doc Sync Agent",
                    implementing_class="doc_sync_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    return Workflow.create(
        application="red9",
        name=f"v2 Task: {request[:50]}",
        stages=stages,
    )


def _is_empty_project(project_root: Path) -> bool:
    """Check if project is empty or new (no meaningful code files).

    Used to skip exploration phase for new projects where there's nothing
    to explore. This avoids wasting LLM calls on empty codebases.

    Args:
        project_root: Project root directory.

    Returns:
        True if project has no meaningful source files.
    """
    if not project_root.exists():
        return True

    # Common source file extensions
    code_extensions = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".go",
        ".rs",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".rb",
        ".php",
        ".swift",
    }

    # Count source files (excluding common non-code directories)
    exclude_dirs = {".git", ".red9", "node_modules", "__pycache__", ".venv", "venv"}
    source_file_count = 0

    try:
        for item in project_root.rglob("*"):
            # Skip excluded directories
            if any(excluded in item.parts for excluded in exclude_dirs):
                continue
            if item.is_file() and item.suffix in code_extensions:
                source_file_count += 1
                if source_file_count >= 3:  # Found enough files, not empty
                    return False
    except (PermissionError, OSError):
        pass

    return source_file_count < 3


def _get_implementing_class(task_type: SubTaskType) -> str:
    """Map SubTaskType to implementing class name.

    Args:
        task_type: The sub-task type.

    Returns:
        Implementing class name for Stabilize.
    """
    mapping = {
        SubTaskType.PLAN: "plan_agent",
        SubTaskType.CODE: "code_agent",
        SubTaskType.TEST_WRITE: "test_write_agent",
        SubTaskType.TEST_RUN: "test_run_agent",
        SubTaskType.REFACTOR: "code_agent",
        SubTaskType.DOCUMENTATION: "code_agent",
        SubTaskType.REVIEW: "plan_agent",
    }
    return mapping.get(task_type, "code_agent")


def should_use_parallel_workflow(
    plan_output: PlanOutput | dict[str, Any],
    min_tasks_for_parallel: int = 2,
) -> bool:
    """Determine if a parallel workflow should be used.

    Args:
        plan_output: Plan output (PlanOutput object or dict).
        min_tasks_for_parallel: Minimum independent tasks to trigger parallel.

    Returns:
        True if parallel workflow is beneficial.
    """
    if isinstance(plan_output, dict):
        plan_output = PlanOutput.from_dict(plan_output)

    # Check if there are enough independent tasks
    independent_tasks = [t for t in plan_output.sub_tasks if not t.dependencies]
    if len(independent_tasks) >= min_tasks_for_parallel:
        return True

    # Check for pre-defined parallel groups
    if plan_output.parallel_groups:
        return True

    # Check complexity
    if plan_output.estimated_complexity == "high":
        return len(plan_output.files_to_modify) >= min_tasks_for_parallel

    return False


def _add_swarm_stages(
    stages: list[StageExecution],
    swarm_config: SwarmConfig,
    phase_prefix: str,
    phase_name: str,
    requisite_stage_ref_ids: set[str],
    project_root_str: str,
    workflow_id: str,
    request: str,
    aggregation_strategy: AggregationStrategy,
    output_key: str,
) -> set[str]:
    """Add N parallel agent stages plus aggregator for a swarm phase.

    Instead of one stage with ThreadPoolExecutor, this creates N Stabilize
    stages (one per agent) that run in parallel via Stabilize's DAG.

    Args:
        stages: List to append stages to.
        swarm_config: Swarm configuration with agent definitions.
        phase_prefix: Prefix for stage ref_ids (e.g., "p2_explore").
        phase_name: Human-readable phase name (e.g., "Exploration").
        requisite_stage_ref_ids: Dependencies for the agent stages.
        project_root_str: Project root path as string.
        workflow_id: Workflow identifier.
        request: User's original request.
        aggregation_strategy: How to aggregate results.
        output_key: Key for aggregated output.

    Returns:
        Set containing the aggregator stage ref_id.
    """
    # Create N parallel agent stages
    agent_stage_refs: set[str] = set()

    for i, agent_config in enumerate(swarm_config.agents):
        ref_id = f"{phase_prefix}_{i}"
        agent_stage_refs.add(ref_id)

        stages.append(
            StageExecution(
                ref_id=ref_id,
                type="swarm_agent",
                name=f"{phase_name}: {agent_config.role.value}",
                requisite_stage_ref_ids=requisite_stage_ref_ids,
                context={
                    "project_root": project_root_str,
                    "workflow_id": workflow_id,
                    "request": request,
                    "agent_config": agent_config.to_dict(),
                },
                tasks=[
                    TaskExecution.create(
                        name=f"Agent: {agent_config.role.value}",
                        implementing_class="swarm_agent",
                        stage_start=True,
                        stage_end=True,
                    )
                ],
            )
        )

    # Create aggregator stage that depends on ALL agent stages
    aggregator_ref = f"{phase_prefix}_aggregate"
    stages.append(
        StageExecution(
            ref_id=aggregator_ref,
            type="swarm_aggregator",
            name=f"{phase_name}: Aggregate Results",
            requisite_stage_ref_ids=agent_stage_refs,
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "aggregation_strategy": aggregation_strategy.value,
                "output_key": output_key,
            },
            tasks=[
                TaskExecution.create(
                    name=f"Aggregate {phase_name}",
                    implementing_class="swarm_aggregator",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    return {aggregator_ref}


def build_swarm_workflow(
    request: str,
    project_root: Path,
    minimal: bool = False,
) -> Workflow:
    """Build the optimized Swarm Workflow with parallel agent execution.

    This is the DEFAULT workflow for RED9, implementing Claude Code parity.

    Each swarm phase creates N parallel Stabilize stages (one per agent) that
    run concurrently via Stabilize's native DAG parallelism.

    Optimized Flow (7 phases, removed redundant review/test phases):
    Phase 1: Context Gathering (Index + Context Agent)
    Phase 2: Exploration Swarm (N parallel explorers -> aggregator)
    Phase 3: Approve Exploration (human gate)
    Phase 4: Architecture Swarm (N parallel architects -> aggregator with voting)
    Phase 5: Approve Architecture (human gate)
    Phase 6: Implementation Loop (Spec -> DDD + Review + Quality Gate iterations)
    Phase 7: Completion (Doc Sync)

    Note: Review Swarm and Test Verification phases were REMOVED because:
    - The iteration loop already includes review internally
    - The iteration loop quality gates already verify tests pass

    Args:
        request: User's task request.
        project_root: Project root directory.
        minimal: If True, use single-agent swarms for faster execution.

    Returns:
        Configured Stabilize Workflow with native parallel swarm execution.
    """
    workflow_id = str(ULID())
    project_root_str = str(project_root)

    # Detect if this is an empty/new project (skip exploration if so)
    is_empty_project = _is_empty_project(project_root)

    # Use minimal swarms for simple tasks or when explicitly requested
    use_minimal = minimal or is_empty_project

    # Get pre-configured swarm configurations (minimal for simple tasks)
    exploration_swarm = get_exploration_swarm(minimal=use_minimal)
    architecture_swarm = get_architecture_swarm(minimal=use_minimal)

    stages: list[StageExecution] = []

    # =========================================================================
    # PHASE 1: Context Gathering (Index + Context Agent)
    # =========================================================================

    # Phase 1a: Index Setup (ensures RAG is ready)
    stages.append(
        StageExecution(
            ref_id="p1_index",
            type="index_setup",
            name="Phase 1a: Index Setup",
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
            },
            tasks=[
                TaskExecution.create(
                    name="Index Setup",
                    implementing_class="index_setup",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # Phase 1b: Context Agent
    stages.append(
        StageExecution(
            ref_id="p1_context",
            type="context_agent",
            name="Phase 1b: Context Gathering",
            requisite_stage_ref_ids={"p1_index"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "request": request,
            },
            tasks=[
                TaskExecution.create(
                    name="Context Agent",
                    implementing_class="context_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # =========================================================================
    # PHASE 2: Exploration Swarm (N parallel explorers via native Stabilize)
    # =========================================================================

    explore_aggregator_refs = _add_swarm_stages(
        stages=stages,
        swarm_config=exploration_swarm,
        phase_prefix="p2_explore",
        phase_name="Phase 2: Exploration",
        requisite_stage_ref_ids={"p1_context"},
        project_root_str=project_root_str,
        workflow_id=workflow_id,
        request=request,
        aggregation_strategy=AggregationStrategy.UNION,
        output_key="exploration_summary",
    )

    # =========================================================================
    # PHASE 3: Approve Exploration (Human Gate)
    # =========================================================================

    stages.append(
        StageExecution(
            ref_id="p3_approve_explore",
            type="approval_gate",
            name="Phase 3: Approve Exploration",
            requisite_stage_ref_ids=explore_aggregator_refs,
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "approval_type": "exploration",
            },
            tasks=[
                TaskExecution.create(
                    name="Exploration Approval Gate",
                    implementing_class="approval_gate",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # =========================================================================
    # PHASE 4: Architecture Swarm (N parallel architects via native Stabilize)
    # =========================================================================

    arch_aggregator_refs = _add_swarm_stages(
        stages=stages,
        swarm_config=architecture_swarm,
        phase_prefix="p4_architect",
        phase_name="Phase 4: Architecture",
        requisite_stage_ref_ids={"p3_approve_explore"},
        project_root_str=project_root_str,
        workflow_id=workflow_id,
        request=request,
        aggregation_strategy=AggregationStrategy.VOTING,
        output_key="chosen_architecture",
    )

    # =========================================================================
    # PHASE 5: Approve Architecture (Human Gate)
    # =========================================================================

    stages.append(
        StageExecution(
            ref_id="p5_approve_arch",
            type="approval_gate",
            name="Phase 5: Approve Architecture",
            requisite_stage_ref_ids=arch_aggregator_refs,
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "approval_type": "architecture",
                "options": [
                    {
                        "label": "Minimal",
                        "value": "minimal",
                        "description": "Smallest footprint, reuse existing code",
                    },
                    {
                        "label": "Clean",
                        "value": "clean",
                        "description": "SOLID principles, clean architecture",
                    },
                    {
                        "label": "Pragmatic",
                        "value": "pragmatic",
                        "description": "Balance quality with speed",
                    },
                ],
            },
            tasks=[
                TaskExecution.create(
                    name="Architecture Approval Gate",
                    implementing_class="approval_gate",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # =========================================================================
    # PHASE 6: Implementation (DDD Agent)
    # =========================================================================

    # Phase 6a: Spec Generation (from chosen architecture)
    stages.append(
        StageExecution(
            ref_id="p6_spec",
            type="spec_agent",
            name="Phase 6a: Generate Spec",
            requisite_stage_ref_ids={"p5_approve_arch"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "request": request,
            },
            tasks=[
                TaskExecution.create(
                    name="Spec Agent",
                    implementing_class="spec_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # Phase 6b: Implementation Loop (DDD + Review + Quality Gate)
    # Replaces linear DDD -> Recovery chain with a robust iteration loop
    stages.append(
        StageExecution(
            ref_id="p6_iteration_loop",
            type="iteration_loop",
            name="Phase 6b: Implementation Loop",
            requisite_stage_ref_ids={"p6_spec"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "request": request,
                "max_iterations": 10,  # Loop up to 10 times to fix issues
            },
            tasks=[
                TaskExecution.create(
                    name="Iteration Loop",
                    implementing_class="iteration_loop",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # =========================================================================
    # PHASE 7: Completion (Doc Sync)
    # =========================================================================
    # NOTE: Review Swarm and Test Verification phases were REMOVED because:
    # - The iteration loop already includes review internally via ReviewCodeTool
    # - The iteration loop quality gates already verify tests pass
    # - Running them again after the loop is redundant and wastes LLM calls

    stages.append(
        StageExecution(
            ref_id="p7_complete",
            type="doc_sync_agent",
            name="Phase 7: Completion",
            requisite_stage_ref_ids={"p6_iteration_loop"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
            },
            tasks=[
                TaskExecution.create(
                    name="Doc Sync Agent",
                    implementing_class="doc_sync_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    return Workflow.create(
        application="red9",
        name=f"Swarm: {request[:50]}",
        stages=stages,
    )


def build_enterprise_workflow(
    request: str,
    project_root: Path,
    complexity: str = "medium",
    fast_mode: bool = False,
) -> Workflow:
    """Build the Enterprise 7-Phase Workflow with specialized agent personas.

    This is the NEW default workflow for RED9, implementing Claude Code parity
    with the following phases:

    Phase 1: Discovery - Context gathering and task understanding
    Phase 2: Exploration - Parallel explorers (architecture, UX, tests)
    Phase 3: Clarification - User confirms essential files
    Phase 4: Architecture - Parallel architects (minimal, clean, pragmatic)
    Phase 5: Approval - User selects architecture approach
    Phase 6: Implementation - DDD agent implements approved design
    Phase 7: Review - Parallel reviewers with confidence scoring
    Phase 8: Final - User approval
    Phase 9: Completion - Tests and summary

    Args:
        request: User's task request.
        project_root: Project root directory.
        complexity: Task complexity ("simple", "medium", "complex").
        fast_mode: If True, skip exploration/architecture/review phases.

    Returns:
        Configured Stabilize Workflow with enterprise phases.
    """
    workflow_id = str(ULID())
    project_root_str = str(project_root)

    # Get workflow config based on complexity
    if fast_mode:
        # Fast mode: single-agent implementation only
        return build_simple_workflow(request, project_root)

    config = get_enterprise_config(complexity)
    stages: list[StageExecution] = []

    # Track phase numbers for UI display
    phase_num = 1

    # =========================================================================
    # PHASE 1: Discovery (Context Gathering)
    # =========================================================================
    stages.append(
        StageExecution(
            ref_id="p1_discovery",
            type="context_agent",
            name=f"Phase {phase_num}: Discovery",
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "request": request,
                "phase_number": phase_num,
            },
            tasks=[
                TaskExecution.create(
                    name="Context Agent",
                    implementing_class="context_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )
    phase_num += 1

    # =========================================================================
    # PHASE 2: Exploration (Parallel Explorers)
    # =========================================================================
    if not config.skip_exploration:
        if config.use_minimal_agents:
            explorer_roles = ["architecture"]
        else:
            explorer_roles = ["architecture", "ux", "tests"]
        explorer_refs: set[str] = set()

        for role in explorer_roles:
            ref_id = f"p2_explore_{role}"
            explorer_refs.add(ref_id)

            stages.append(
                StageExecution(
                    ref_id=ref_id,
                    type="explorer_agent",
                    name=f"Phase {phase_num}: Explore ({role})",
                    requisite_stage_ref_ids={"p1_discovery"},
                    context={
                        "project_root": project_root_str,
                        "workflow_id": workflow_id,
                        "request": request,
                        "focus": role,
                        "phase_number": phase_num,
                    },
                    tasks=[
                        TaskExecution.create(
                            name=f"Explorer ({role})",
                            implementing_class="explorer_agent",
                            stage_start=True,
                            stage_end=True,
                        )
                    ],
                )
            )

        # Exploration aggregator
        stages.append(
            StageExecution(
                ref_id="p2_aggregate",
                type="swarm_aggregator",
                name=f"Phase {phase_num}: Aggregate Exploration",
                requisite_stage_ref_ids=explorer_refs,
                context={
                    "project_root": project_root_str,
                    "workflow_id": workflow_id,
                    "aggregation_strategy": "union",
                    "output_key": "exploration_summary",
                },
                tasks=[
                    TaskExecution.create(
                        name="Aggregate Exploration",
                        implementing_class="swarm_aggregator",
                        stage_start=True,
                        stage_end=True,
                    )
                ],
            )
        )
        phase_num += 1

        # =========================================================================
        # PHASE 3: Clarification (Approval Gate)
        # =========================================================================
        stages.append(
            StageExecution(
                ref_id="p3_clarify",
                type="approval_gate",
                name=f"Phase {phase_num}: Confirm Understanding",
                requisite_stage_ref_ids={"p2_aggregate"},
                context={
                    "project_root": project_root_str,
                    "workflow_id": workflow_id,
                    "approval_type": "exploration",
                    "phase_number": phase_num,
                },
                tasks=[
                    TaskExecution.create(
                        name="Exploration Approval",
                        implementing_class="approval_gate",
                        stage_start=True,
                        stage_end=True,
                    )
                ],
            )
        )
        phase_num += 1

    # Determine prereqs for architecture phase
    arch_prereqs = {"p3_clarify"} if not config.skip_exploration else {"p1_discovery"}

    # =========================================================================
    # PHASE 4: Architecture (Parallel Architects)
    # =========================================================================
    if not config.skip_architecture:
        if config.use_minimal_agents:
            architect_approaches = ["pragmatic"]
        else:
            architect_approaches = ["minimal", "clean", "pragmatic"]
        architect_refs: set[str] = set()

        for approach in architect_approaches:
            ref_id = f"p4_arch_{approach}"
            architect_refs.add(ref_id)

            stages.append(
                StageExecution(
                    ref_id=ref_id,
                    type="architect_agent",
                    name=f"Phase {phase_num}: Architect ({approach})",
                    requisite_stage_ref_ids=arch_prereqs,
                    context={
                        "project_root": project_root_str,
                        "workflow_id": workflow_id,
                        "request": request,
                        "approach": approach,
                        "phase_number": phase_num,
                    },
                    tasks=[
                        TaskExecution.create(
                            name=f"Architect ({approach})",
                            implementing_class="architect_agent",
                            stage_start=True,
                            stage_end=True,
                        )
                    ],
                )
            )

        # Architecture aggregator (voting)
        stages.append(
            StageExecution(
                ref_id="p4_aggregate",
                type="swarm_aggregator",
                name=f"Phase {phase_num}: Aggregate Architecture",
                requisite_stage_ref_ids=architect_refs,
                context={
                    "project_root": project_root_str,
                    "workflow_id": workflow_id,
                    "aggregation_strategy": "voting",
                    "output_key": "chosen_architecture",
                },
                tasks=[
                    TaskExecution.create(
                        name="Aggregate Architecture",
                        implementing_class="swarm_aggregator",
                        stage_start=True,
                        stage_end=True,
                    )
                ],
            )
        )
        phase_num += 1

        # =========================================================================
        # PHASE 5: Approval (Architecture Selection)
        # =========================================================================
        stages.append(
            StageExecution(
                ref_id="p5_approve",
                type="approval_gate",
                name=f"Phase {phase_num}: Select Architecture",
                requisite_stage_ref_ids={"p4_aggregate"},
                context={
                    "project_root": project_root_str,
                    "workflow_id": workflow_id,
                    "approval_type": "architecture",
                    "phase_number": phase_num,
                    "options": [
                        {
                            "label": "Minimal",
                            "value": "minimal",
                            "description": "Smallest footprint",
                        },
                        {
                            "label": "Clean",
                            "value": "clean",
                            "description": "SOLID principles",
                        },
                        {
                            "label": "Pragmatic",
                            "value": "pragmatic",
                            "description": "Balanced approach",
                        },
                    ],
                },
                tasks=[
                    TaskExecution.create(
                        name="Architecture Approval",
                        implementing_class="approval_gate",
                        stage_start=True,
                        stage_end=True,
                    )
                ],
            )
        )
        phase_num += 1

    # Determine prereqs for implementation phase
    impl_prereqs = {"p5_approve"} if not config.skip_architecture else arch_prereqs

    # =========================================================================
    # PHASE 6: Implementation (Spec + Iteration Loop)
    # =========================================================================
    # Spec generation
    stages.append(
        StageExecution(
            ref_id="p6_spec",
            type="spec_agent",
            name=f"Phase {phase_num}: Generate Spec",
            requisite_stage_ref_ids=impl_prereqs,
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "request": request,
                "phase_number": phase_num,
            },
            tasks=[
                TaskExecution.create(
                    name="Spec Agent",
                    implementing_class="spec_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # Iteration Loop: DDD + Review + Quality Gate until pass
    # This replaces the old DDD → diagnosis → compensation → retry → review sequence
    stages.append(
        StageExecution(
            ref_id="p6_iteration_loop",
            type="iteration_loop",
            name=f"Phase {phase_num}: Implementation Loop",
            requisite_stage_ref_ids={"p6_spec"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "request": request,
                "phase_number": phase_num,
                "max_iterations": 10,  # Configurable iteration limit
            },
            tasks=[
                TaskExecution.create(
                    name="Iteration Loop",
                    implementing_class="iteration_loop",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )
    phase_num += 1

    # NOTE: Review phase removed - it's now inside the iteration loop
    # The IterationLoopTask handles DDD + Review + Quality Gate internally
    # See: red9/agents/tasks/iteration_loop.py

    # Determine prereqs for completion
    # Completion depends on iteration loop (which includes review internally)
    completion_prereqs = {"p6_iteration_loop"}

    # =========================================================================
    # PHASE 9: Completion (Tests + Summary)
    # =========================================================================
    stages.append(
        StageExecution(
            ref_id="p9_test",
            type="test_run_agent",
            name=f"Phase {phase_num}: Test Verification",
            requisite_stage_ref_ids=completion_prereqs,
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "request": request,
                "phase_number": phase_num,
            },
            tasks=[
                TaskExecution.create(
                    name="Test Run Agent",
                    implementing_class="test_run_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    stages.append(
        StageExecution(
            ref_id="p9_complete",
            type="doc_sync_agent",
            name=f"Phase {phase_num}: Completion",
            requisite_stage_ref_ids={"p9_test"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "phase_number": phase_num,
            },
            tasks=[
                TaskExecution.create(
                    name="Doc Sync Agent",
                    implementing_class="doc_sync_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    return Workflow.create(
        application="red9",
        name=f"Enterprise: {request[:50]}",
        stages=stages,
    )


def build_iterative_workflow(
    request: str,
    project_root: Path,
    max_iterations: int = 10,
) -> Workflow:
    """Build a workflow with iteration loop for quality-gated completion.

    This workflow implements the moai-adk pattern:
    1. Context gathering
    2. Spec generation
    3. Iteration loop (DDD + Review + Quality Gate) until pass
    4. Doc sync / completion

    The iteration loop runs until:
    - Quality gates pass (coverage >= 80%, no oversized files)
    - No critical/high severity issues remain
    - Tests pass

    Or until max_iterations is reached.

    Args:
        request: User's task request.
        project_root: Project root directory.
        max_iterations: Maximum iterations for the loop (default 10).

    Returns:
        Configured Stabilize Workflow with iteration loop.
    """
    workflow_id = str(ULID())
    project_root_str = str(project_root)

    stages: list[StageExecution] = []

    # =========================================================================
    # PHASE 0: Index Setup
    # =========================================================================
    stages.append(
        StageExecution(
            ref_id="p0_index",
            type="index_setup",
            name="Phase 0: Index Setup",
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
            },
            tasks=[
                TaskExecution.create(
                    name="Index Setup",
                    implementing_class="index_setup",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # =========================================================================
    # PHASE 1: Context Gathering
    # =========================================================================
    stages.append(
        StageExecution(
            ref_id="p1_context",
            type="context_agent",
            name="Phase 1: Context Gathering",
            requisite_stage_ref_ids={"p0_index"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "request": request,
            },
            tasks=[
                TaskExecution.create(
                    name="Context Agent",
                    implementing_class="context_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # =========================================================================
    # PHASE 2: Spec Generation
    # =========================================================================
    stages.append(
        StageExecution(
            ref_id="p2_spec",
            type="spec_agent",
            name="Phase 2: Spec Generation",
            requisite_stage_ref_ids={"p1_context"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "request": request,
            },
            tasks=[
                TaskExecution.create(
                    name="Spec Agent",
                    implementing_class="spec_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # =========================================================================
    # PHASE 3: Iteration Loop (DDD + Review + Quality Gate)
    # =========================================================================
    stages.append(
        StageExecution(
            ref_id="p3_iteration_loop",
            type="iteration_loop",
            name="Phase 3: Implementation Loop",
            requisite_stage_ref_ids={"p2_spec"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
                "request": request,
                "max_iterations": max_iterations,
            },
            tasks=[
                TaskExecution.create(
                    name="Iteration Loop",
                    implementing_class="iteration_loop",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    # =========================================================================
    # PHASE 4: Documentation Sync & Completion
    # =========================================================================
    stages.append(
        StageExecution(
            ref_id="p4_complete",
            type="doc_sync_agent",
            name="Phase 4: Doc Sync & Completion",
            requisite_stage_ref_ids={"p3_iteration_loop"},
            context={
                "project_root": project_root_str,
                "workflow_id": workflow_id,
            },
            tasks=[
                TaskExecution.create(
                    name="Doc Sync Agent",
                    implementing_class="doc_sync_agent",
                    stage_start=True,
                    stage_end=True,
                )
            ],
        )
    )

    return Workflow.create(
        application="red9",
        name=f"Iterative: {request[:50]}",
        stages=stages,
    )
