"""Unit tests for RED9 parallel workflow functionality."""

from __future__ import annotations

from pathlib import Path

from red9.workflows.builder import (
    _get_implementing_class,
    build_parallel_workflow,
    should_use_parallel_workflow,
)
from red9.workflows.models import (
    ParallelGroup,
    PlanOutput,
    SubTask,
    SubTaskStatus,
    SubTaskType,
    TaskDecomposition,
)


class TestSubTask:
    """Tests for SubTask dataclass."""

    def test_create_subtask(self) -> None:
        """Test creating a sub-task."""
        task = SubTask(
            id="task_1",
            name="Modify auth.py",
            description="Update authentication logic",
            task_type=SubTaskType.CODE,
            files=["src/auth.py"],
        )

        assert task.id == "task_1"
        assert task.name == "Modify auth.py"
        assert task.task_type == SubTaskType.CODE
        assert task.status == SubTaskStatus.PENDING
        assert len(task.files) == 1

    def test_can_run_no_dependencies(self) -> None:
        """Test task can run when it has no dependencies."""
        task = SubTask(
            id="task_1",
            name="Independent task",
            description="No dependencies",
            task_type=SubTaskType.CODE,
            dependencies=[],
        )

        assert task.can_run(set()) is True
        assert task.can_run({"task_2", "task_3"}) is True

    def test_can_run_with_dependencies(self) -> None:
        """Test task can run when dependencies are satisfied."""
        task = SubTask(
            id="task_2",
            name="Dependent task",
            description="Depends on task_1",
            task_type=SubTaskType.CODE,
            dependencies=["task_1"],
        )

        # Cannot run when dependency not completed
        assert task.can_run(set()) is False
        assert task.can_run({"task_3"}) is False

        # Can run when dependency completed
        assert task.can_run({"task_1"}) is True
        assert task.can_run({"task_1", "task_3"}) is True

    def test_to_dict_and_from_dict(self) -> None:
        """Test serialization and deserialization."""
        task = SubTask(
            id="task_1",
            name="Test task",
            description="Test description",
            task_type=SubTaskType.TEST_WRITE,
            files=["tests/test_auth.py"],
            dependencies=["task_0"],
            priority=5,
        )

        data = task.to_dict()
        restored = SubTask.from_dict(data)

        assert restored.id == task.id
        assert restored.name == task.name
        assert restored.task_type == task.task_type
        assert restored.files == task.files
        assert restored.dependencies == task.dependencies
        assert restored.priority == task.priority


class TestParallelGroup:
    """Tests for ParallelGroup dataclass."""

    def test_create_group(self) -> None:
        """Test creating a parallel group."""
        tasks = [
            SubTask(
                id="task_1",
                name="Task 1",
                description="First",
                task_type=SubTaskType.CODE,
            ),
            SubTask(
                id="task_2",
                name="Task 2",
                description="Second",
                task_type=SubTaskType.CODE,
            ),
        ]
        group = ParallelGroup(
            id="group_1",
            name="Auth changes",
            tasks=tasks,
            max_concurrent=4,
        )

        assert group.id == "group_1"
        assert len(group.tasks) == 2
        assert group.max_concurrent == 4
        assert group.completed is False

    def test_get_runnable_tasks(self) -> None:
        """Test getting tasks ready to run."""
        tasks = [
            SubTask(
                id="task_1",
                name="Task 1",
                description="Independent",
                task_type=SubTaskType.CODE,
                dependencies=[],
            ),
            SubTask(
                id="task_2",
                name="Task 2",
                description="Depends on task_1",
                task_type=SubTaskType.CODE,
                dependencies=["task_1"],
            ),
            SubTask(
                id="task_3",
                name="Task 3",
                description="Independent",
                task_type=SubTaskType.CODE,
                dependencies=[],
            ),
        ]
        group = ParallelGroup(id="group_1", name="Test", tasks=tasks)

        # Initially only independent tasks are runnable
        runnable = group.get_runnable_tasks(set())
        assert len(runnable) == 2
        assert any(t.id == "task_1" for t in runnable)
        assert any(t.id == "task_3" for t in runnable)
        assert not any(t.id == "task_2" for t in runnable)  # Has unsatisfied deps

        # After task_1 completes, task_2 becomes runnable too
        # Note: completed_task_ids tracks which deps are satisfied, not which are done
        # All tasks are still PENDING status, so all 3 become runnable
        runnable = group.get_runnable_tasks({"task_1"})
        assert len(runnable) == 3  # All tasks can now run
        assert any(t.id == "task_2" for t in runnable)  # Now runnable


class TestPlanOutput:
    """Tests for PlanOutput dataclass."""

    def test_create_plan_output(self) -> None:
        """Test creating a plan output."""
        plan = PlanOutput(
            summary="Add authentication feature",
            files_to_modify=["src/auth.py", "src/users.py"],
            files_to_create=["src/tokens.py"],
            test_requirements=["Test login", "Test logout"],
        )

        assert "Add authentication" in plan.summary
        assert len(plan.files_to_modify) == 2
        assert len(plan.files_to_create) == 1
        assert len(plan.test_requirements) == 2

    def test_get_all_files(self) -> None:
        """Test getting all files from plan."""
        task = SubTask(
            id="task_1",
            name="Task",
            description="Test",
            task_type=SubTaskType.CODE,
            files=["extra.py"],
        )
        plan = PlanOutput(
            summary="Test",
            files_to_modify=["a.py"],
            files_to_create=["b.py"],
            files_to_read=["c.py"],
            sub_tasks=[task],
        )

        all_files = plan.get_all_files()
        assert "a.py" in all_files
        assert "b.py" in all_files
        assert "c.py" in all_files
        assert "extra.py" in all_files

    def test_has_parallel_potential(self) -> None:
        """Test checking for parallel potential."""
        # No sub-tasks = no parallel potential
        plan_simple = PlanOutput(summary="Simple")
        assert plan_simple.has_parallel_potential() is False

        # With parallel groups = parallel potential
        group = ParallelGroup(id="g1", name="G1", tasks=[])
        plan_with_groups = PlanOutput(summary="With groups", parallel_groups=[group])
        assert plan_with_groups.has_parallel_potential() is True

        # With independent sub-tasks = parallel potential
        task1 = SubTask(
            id="t1", name="T1", description="D", task_type=SubTaskType.CODE, dependencies=[]
        )
        task2 = SubTask(
            id="t2", name="T2", description="D", task_type=SubTaskType.CODE, dependencies=[]
        )
        plan_with_tasks = PlanOutput(summary="With tasks", sub_tasks=[task1, task2])
        assert plan_with_tasks.has_parallel_potential() is True

    def test_to_dict_and_from_dict(self) -> None:
        """Test serialization and deserialization."""
        plan = PlanOutput(
            summary="Test plan",
            files_to_modify=["a.py"],
            estimated_complexity="high",
            requires_human_review=True,
        )

        data = plan.to_dict()
        restored = PlanOutput.from_dict(data)

        assert restored.summary == plan.summary
        assert restored.files_to_modify == plan.files_to_modify
        assert restored.estimated_complexity == plan.estimated_complexity
        assert restored.requires_human_review == plan.requires_human_review


class TestTaskDecomposition:
    """Tests for TaskDecomposition dataclass."""

    def test_get_total_tasks(self) -> None:
        """Test counting total tasks."""
        group = ParallelGroup(
            id="g1",
            name="G1",
            tasks=[
                SubTask(id="t1", name="T1", description="D", task_type=SubTaskType.CODE),
                SubTask(id="t2", name="T2", description="D", task_type=SubTaskType.CODE),
            ],
        )
        sequential = SubTask(id="t3", name="T3", description="D", task_type=SubTaskType.CODE)

        decomp = TaskDecomposition(
            original_request="Test",
            can_parallelize=True,
            parallel_groups=[group],
            sequential_fallback=[sequential],
        )

        assert decomp.get_total_tasks() == 3  # 2 in group + 1 sequential


class TestBuildParallelWorkflow:
    """Tests for parallel workflow building."""

    def test_build_with_empty_plan(self, tmp_path: Path) -> None:
        """Test building parallel workflow with empty plan."""
        plan = PlanOutput(summary="Empty plan")

        # Should fall back to sequential workflow
        workflow = build_parallel_workflow(
            request="Test request",
            issue_id=1,
            plan_output=plan,
            project_root=tmp_path,
        )

        assert workflow is not None
        assert "Test request" in workflow.name

    def test_build_with_sub_tasks(self, tmp_path: Path) -> None:
        """Test building parallel workflow with sub-tasks."""
        tasks = [
            SubTask(
                id="t1",
                name="Task 1",
                description="First",
                task_type=SubTaskType.CODE,
                files=["a.py"],
            ),
            SubTask(
                id="t2",
                name="Task 2",
                description="Second",
                task_type=SubTaskType.CODE,
                files=["b.py"],
            ),
        ]
        plan = PlanOutput(
            summary="Multi-file plan",
            sub_tasks=tasks,
        )

        workflow = build_parallel_workflow(
            request="Multi-file task",
            issue_id=1,
            plan_output=plan,
            project_root=tmp_path,
            max_parallel_stages=4,
        )

        assert workflow is not None
        # Should have parallel stages
        assert len(workflow.stages) > 2  # More than just setup + complete

    def test_build_with_parallel_groups(self, tmp_path: Path) -> None:
        """Test building parallel workflow with parallel groups."""
        group = ParallelGroup(
            id="auth",
            name="Auth changes",
            tasks=[
                SubTask(
                    id="t1",
                    name="Update login",
                    description="Modify login",
                    task_type=SubTaskType.CODE,
                    files=["login.py"],
                ),
            ],
        )
        plan = PlanOutput(
            summary="Grouped plan",
            parallel_groups=[group],
        )

        workflow = build_parallel_workflow(
            request="Grouped task",
            issue_id=1,
            plan_output=plan,
            project_root=tmp_path,
        )

        assert workflow is not None
        assert "Parallel" in workflow.name


class TestShouldUseParallelWorkflow:
    """Tests for parallel workflow detection."""

    def test_single_file_not_parallel(self) -> None:
        """Test single file task doesn't trigger parallel."""
        plan = PlanOutput(
            summary="Single file change",
            files_to_modify=["one_file.py"],
        )

        assert should_use_parallel_workflow(plan) is False

    def test_multiple_files_is_parallel(self) -> None:
        """Test multiple files can trigger parallel."""
        task1 = SubTask(
            id="t1", name="T1", description="D", task_type=SubTaskType.CODE, dependencies=[]
        )
        task2 = SubTask(
            id="t2", name="T2", description="D", task_type=SubTaskType.CODE, dependencies=[]
        )
        plan = PlanOutput(
            summary="Multi-file change",
            files_to_modify=["a.py", "b.py"],
            sub_tasks=[task1, task2],
        )

        assert should_use_parallel_workflow(plan) is True

    def test_dict_input(self) -> None:
        """Test function works with dict input."""
        plan_dict = {
            "summary": "Test",
            "files_to_modify": ["a.py", "b.py"],
            "sub_tasks": [
                {"id": "t1", "name": "T1", "description": "D", "task_type": "code"},
                {"id": "t2", "name": "T2", "description": "D", "task_type": "code"},
            ],
        }

        assert should_use_parallel_workflow(plan_dict) is True

    def test_high_complexity_parallel(self) -> None:
        """Test high complexity with multiple files triggers parallel."""
        plan = PlanOutput(
            summary="Complex change",
            files_to_modify=["a.py", "b.py"],
            estimated_complexity="high",
        )

        assert should_use_parallel_workflow(plan) is True


class TestGetImplementingClass:
    """Tests for implementing class mapping."""

    def test_code_type(self) -> None:
        """Test CODE type maps to code_agent."""
        assert _get_implementing_class(SubTaskType.CODE) == "code_agent"

    def test_test_write_type(self) -> None:
        """Test TEST_WRITE type maps to test_write_agent."""
        assert _get_implementing_class(SubTaskType.TEST_WRITE) == "test_write_agent"

    def test_test_run_type(self) -> None:
        """Test TEST_RUN type maps to test_run_agent."""
        assert _get_implementing_class(SubTaskType.TEST_RUN) == "test_run_agent"

    def test_plan_type(self) -> None:
        """Test PLAN type maps to plan_agent."""
        assert _get_implementing_class(SubTaskType.PLAN) == "plan_agent"
