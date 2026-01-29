"""Task decomposition agent - analyzes complex tasks for parallel execution.

Breaks down complex tasks into independent sub-tasks that can run in parallel.
Uses error history context for intelligent retry behavior.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from stabilize import Task, TaskResult
from stabilize.errors import PermanentError
from stabilize.models.stage import StageExecution

from red9.agents.error_handler import get_error_history, handle_transient_error
from red9.agents.loop import AgentLoop
from red9.errors import is_transient_error
from red9.logging import get_logger
from red9.providers.base import LLMProvider
from red9.tools.base import ToolRegistry
from red9.workflows.models import (
    ParallelGroup,
    PlanOutput,
    SubTask,
    SubTaskStatus,
    SubTaskType,
    TaskDecomposition,
)

logger = get_logger(__name__)

DECOMPOSE_SYSTEM_PROMPT = """You are a task decomposition specialist.

Your job is to analyze complex software tasks and break them down into
independent sub-tasks that can be executed in parallel.

## Your Goal
Given a task request and a plan, identify which parts can be worked on
independently and in parallel.

## Guidelines for Decomposition

1. **Independence**: Sub-tasks should be independent - they shouldn't modify
   the same files or have dependencies on each other's output.

2. **File-based grouping**: Group work by files that can be modified
   independently.

3. **Test separation**: Tests can often be written in parallel with
   implementation if they're in separate files.

4. **Parallel potential**:
   - Different modules or components can usually be worked on in parallel
   - Adding new files is usually parallelizable
   - Modifying existing files with no shared state is parallelizable
   - Changes that depend on other changes must be sequential

5. **Conservative approach**: When in doubt, keep tasks sequential.
   It's better to be safe than to create conflicts.

## Output Format
When you identify parallel groups, use the complete_task tool with structured output like:
{
    "can_parallelize": true,
    "parallel_groups": [
        {
            "name": "Group name",
            "tasks": ["task1 description", "task2 description"],
            "files": ["file1.py", "file2.py"]
        }
    ],
    "sequential_tasks": ["task that must be sequential"],
    "reason": "Why this decomposition makes sense"
}

## Available Tools
- read_file: Read file contents to understand dependencies
- glob: Find files matching patterns
- grep: Search for code patterns to understand dependencies
- complete_task: Report your decomposition analysis

First analyze the codebase to understand file dependencies, then create your decomposition.
"""


class DecomposeAgentTask(Task):
    """Task decomposition agent that analyzes complex tasks for parallel execution.

    This is a Stabilize Task that:
    1. Analyzes the plan output from the planning agent
    2. Identifies independent sub-tasks that can run in parallel
    3. Creates parallel groups for the workflow builder
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
    ) -> None:
        """Initialize decomposition agent task.

        Args:
            provider: LLM provider for agent execution.
            tool_registry: Registry of available tools.
        """
        self.provider = provider
        self.tools = tool_registry

    def execute(self, stage: StageExecution) -> TaskResult:
        """Execute the decomposition agent.

        Args:
            stage: Stage execution context with plan data.

        Returns:
            TaskResult with decomposition or error.
        """
        request = stage.context.get("request", "")
        plan_data = stage.context.get("plan_data", {})
        error_history = get_error_history(stage.context)
        # project_root available for future use with file analysis

        if not request:
            return TaskResult.terminal(error="request is required in stage context")

        try:
            # Create agent loop with read-only tools for analysis
            agent = AgentLoop(
                provider=self.provider,
                tool_registry=self.tools,
                max_iterations=15,
                parallel_tool_execution=True,
            )

            # Build user message with plan context
            user_message = self._build_decomposition_prompt(request, plan_data)

            # Run the decomposition agent
            result = agent.run(
                system_prompt=DECOMPOSE_SYSTEM_PROMPT,
                user_message=user_message,
                error_history=error_history if error_history else None,
            )

            if not result.success:
                return TaskResult.terminal(error=result.error or "Decomposition agent failed")

            # Extract decomposition from result
            decomposition = self._extract_decomposition(result.outputs, plan_data)

            return TaskResult.success(
                outputs={
                    "decomposition": decomposition.to_dict(),
                    "can_parallelize": decomposition.can_parallelize,
                    "parallel_groups": [g.to_dict() for g in decomposition.parallel_groups],
                    "reason": decomposition.reason,
                }
            )

        except Exception as e:
            if is_transient_error(e):
                return handle_transient_error(e, error_history, agent_name="Decompose agent")
            raise PermanentError(f"Decomposition agent error: {e}", cause=e)

    def _build_decomposition_prompt(self, request: str, plan_data: dict[str, Any]) -> str:
        """Build the decomposition prompt with plan context.

        Args:
            request: Original task request.
            plan_data: Plan data from planning agent.

        Returns:
            Formatted prompt string.
        """
        prompt_parts = [
            f"## Original Task\n{request}\n",
        ]

        if plan_data:
            if plan_data.get("summary"):
                prompt_parts.append(f"## Plan Summary\n{plan_data['summary']}\n")

            if plan_data.get("files_to_modify"):
                files = plan_data["files_to_modify"]
                prompt_parts.append(f"## Files to Modify\n{', '.join(files)}\n")

            if plan_data.get("files_to_create"):
                files = plan_data["files_to_create"]
                prompt_parts.append(f"## Files to Create\n{', '.join(files)}\n")

            if plan_data.get("test_requirements"):
                tests = plan_data["test_requirements"]
                prompt_parts.append(f"## Test Requirements\n{chr(10).join(tests)}\n")

        prompt_parts.append(
            "\nAnalyze these files and the task to determine which parts can be "
            "worked on in parallel. Use the tools to understand file dependencies."
        )

        return "\n".join(prompt_parts)

    def _extract_decomposition(
        self, outputs: dict[str, Any], plan_data: dict[str, Any]
    ) -> TaskDecomposition:
        """Extract decomposition from agent outputs.

        Args:
            outputs: Agent output dictionary.
            plan_data: Original plan data.

        Returns:
            TaskDecomposition object.
        """
        can_parallelize = outputs.get("can_parallelize", False)
        reason = outputs.get("reason", "")

        parallel_groups: list[ParallelGroup] = []
        sequential_fallback: list[SubTask] = []

        # Parse parallel groups from output
        raw_groups = outputs.get("parallel_groups", [])
        for i, group_data in enumerate(raw_groups):
            if isinstance(group_data, dict):
                tasks: list[SubTask] = []
                group_name = group_data.get("name", f"group_{i + 1}")
                group_files = group_data.get("files", [])
                group_tasks = group_data.get("tasks", [])

                for j, task_desc in enumerate(group_tasks):
                    task_files = []
                    # Try to associate files with this task
                    if j < len(group_files):
                        task_files = [group_files[j]]

                    tasks.append(
                        SubTask(
                            id=f"parallel_{i}_{j}",
                            name=task_desc[:50] if isinstance(task_desc, str) else f"Task {j + 1}",
                            description=task_desc if isinstance(task_desc, str) else str(task_desc),
                            task_type=SubTaskType.CODE,
                            files=task_files,
                            dependencies=[],
                            status=SubTaskStatus.PENDING,
                        )
                    )

                if tasks:
                    parallel_groups.append(
                        ParallelGroup(
                            id=f"group_{i + 1}",
                            name=group_name,
                            tasks=tasks,
                            max_concurrent=4,
                        )
                    )

        # Parse sequential tasks
        raw_sequential = outputs.get("sequential_tasks", [])
        for i, task_desc in enumerate(raw_sequential):
            # Determine dependencies - each sequential task depends on previous
            deps = [f"sequential_{i - 1}"] if i > 0 else []

            sequential_fallback.append(
                SubTask(
                    id=f"sequential_{i}",
                    name=task_desc[:50] if isinstance(task_desc, str) else f"Sequential {i + 1}",
                    description=task_desc if isinstance(task_desc, str) else str(task_desc),
                    task_type=SubTaskType.CODE,
                    files=[],
                    dependencies=deps,
                    status=SubTaskStatus.PENDING,
                )
            )

        # If no groups found, try to auto-decompose from plan data
        if not parallel_groups and not sequential_fallback and plan_data:
            parallel_groups, sequential_fallback = self._auto_decompose(plan_data)
            if parallel_groups:
                can_parallelize = True
                reason = "Auto-decomposed based on independent files"

        return TaskDecomposition(
            original_request=plan_data.get("summary", ""),
            can_parallelize=can_parallelize,
            parallel_groups=parallel_groups,
            sequential_fallback=sequential_fallback,
            reason=reason,
        )

    def _auto_decompose(
        self, plan_data: dict[str, Any]
    ) -> tuple[list[ParallelGroup], list[SubTask]]:
        """Auto-decompose based on plan data when agent doesn't provide groups.

        Args:
            plan_data: Plan data with files to modify.

        Returns:
            Tuple of (parallel_groups, sequential_tasks).
        """
        files_to_modify = plan_data.get("files_to_modify", [])
        files_to_create = plan_data.get("files_to_create", [])

        parallel_groups: list[ParallelGroup] = []
        sequential_tasks: list[SubTask] = []

        # Group files by directory - files in different directories are likely independent
        dir_groups: dict[str, list[str]] = {}
        for file_path in files_to_modify + files_to_create:
            directory = str(Path(file_path).parent)
            if directory not in dir_groups:
                dir_groups[directory] = []
            dir_groups[directory].append(file_path)

        # If we have multiple directories, create parallel groups
        if len(dir_groups) > 1:
            for i, (directory, files) in enumerate(dir_groups.items()):
                tasks = [
                    SubTask(
                        id=f"dir_{i}_file_{j}",
                        name=f"Modify {Path(f).name}",
                        description=f"Apply changes to {f}",
                        task_type=SubTaskType.CODE,
                        files=[f],
                        dependencies=[],
                        status=SubTaskStatus.PENDING,
                    )
                    for j, f in enumerate(files)
                ]
                parallel_groups.append(
                    ParallelGroup(
                        id=f"dir_group_{i}",
                        name=f"Changes in {directory}",
                        tasks=tasks,
                        max_concurrent=4,
                    )
                )
        else:
            # All files in same directory - less likely to be parallelizable
            for i, file_path in enumerate(files_to_modify + files_to_create):
                sequential_tasks.append(
                    SubTask(
                        id=f"file_{i}",
                        name=f"Modify {Path(file_path).name}",
                        description=f"Apply changes to {file_path}",
                        task_type=SubTaskType.CODE,
                        files=[file_path],
                        dependencies=[f"file_{i - 1}"] if i > 0 else [],
                        status=SubTaskStatus.PENDING,
                    )
                )

        return parallel_groups, sequential_tasks


def analyze_parallel_potential(
    plan_output: PlanOutput | dict[str, Any],
    min_files_for_parallel: int = 2,
) -> TaskDecomposition:
    """Quick analysis of parallel potential without running an agent.

    This is a lightweight function that analyzes a plan to determine
    if parallel execution would be beneficial.

    Args:
        plan_output: Plan output from planning agent.
        min_files_for_parallel: Minimum files to consider parallel.

    Returns:
        TaskDecomposition with parallel potential analysis.
    """
    if isinstance(plan_output, dict):
        plan_output = PlanOutput.from_dict(plan_output)

    files_to_modify = plan_output.files_to_modify
    files_to_create = plan_output.files_to_create
    all_files = files_to_modify + files_to_create

    if len(all_files) < min_files_for_parallel:
        return TaskDecomposition(
            original_request=plan_output.summary,
            can_parallelize=False,
            reason=f"Only {len(all_files)} files - not enough for parallel execution",
        )

    # Group files by directory
    dir_groups: dict[str, list[str]] = {}
    for file_path in all_files:
        directory = str(Path(file_path).parent)
        if directory not in dir_groups:
            dir_groups[directory] = []
        dir_groups[directory].append(file_path)

    # Separate test files from implementation files
    test_files: list[str] = []
    impl_files: list[str] = []
    for f in all_files:
        if "test" in f.lower() or f.endswith("_test.py") or f.endswith(".test.ts"):
            test_files.append(f)
        else:
            impl_files.append(f)

    parallel_groups: list[ParallelGroup] = []

    # Create parallel groups for different directories
    if len(dir_groups) > 1:
        for i, (directory, files) in enumerate(dir_groups.items()):
            tasks = [
                SubTask(
                    id=f"dir_{i}_file_{j}",
                    name=f"Modify {Path(f).name}",
                    description=f"Apply changes to {f}",
                    task_type=SubTaskType.TEST_WRITE if "test" in f.lower() else SubTaskType.CODE,
                    files=[f],
                    dependencies=[],
                )
                for j, f in enumerate(files)
            ]
            parallel_groups.append(
                ParallelGroup(
                    id=f"dir_group_{i}",
                    name=f"Changes in {Path(directory).name or 'root'}",
                    tasks=tasks,
                )
            )

    # Or create separate groups for tests vs implementation
    elif test_files and impl_files:
        impl_tasks = [
            SubTask(
                id=f"impl_{i}",
                name=f"Implement {Path(f).name}",
                description=f"Apply changes to {f}",
                task_type=SubTaskType.CODE,
                files=[f],
                dependencies=[],
            )
            for i, f in enumerate(impl_files)
        ]
        test_tasks = [
            SubTask(
                id=f"test_{i}",
                name=f"Test {Path(f).name}",
                description=f"Write tests in {f}",
                task_type=SubTaskType.TEST_WRITE,
                files=[f],
                dependencies=[],
            )
            for i, f in enumerate(test_files)
        ]

        if impl_tasks:
            parallel_groups.append(
                ParallelGroup(
                    id="implementation",
                    name="Implementation",
                    tasks=impl_tasks,
                )
            )
        if test_tasks:
            parallel_groups.append(
                ParallelGroup(
                    id="tests",
                    name="Tests",
                    tasks=test_tasks,
                )
            )

    can_parallelize = len(parallel_groups) > 1 or (
        len(parallel_groups) == 1 and len(parallel_groups[0].tasks) > 1
    )

    return TaskDecomposition(
        original_request=plan_output.summary,
        can_parallelize=can_parallelize,
        parallel_groups=parallel_groups,
        reason=(
            f"Found {len(parallel_groups)} parallel groups across {len(dir_groups)} directories"
            if can_parallelize
            else "Files are too interdependent for parallel execution"
        ),
    )
