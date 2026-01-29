"""Tests for swarm workflow construction and approval gates."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from red9.workflows.builder import build_swarm_workflow


class TestBuildSwarmWorkflow:
    """Tests for build_swarm_workflow function."""

    def test_creates_workflow(self, tmp_path: Path):
        """Test that workflow is created successfully."""
        workflow = build_swarm_workflow(
            request="Add user authentication",
            project_root=tmp_path,
        )

        assert workflow is not None
        assert workflow.name.startswith("Swarm:")
        assert "Add user authentication" in workflow.name

    def test_has_all_phases(self, tmp_path: Path):
        """Test that workflow has all optimized phases.

        The optimized workflow has 7 phases (removed redundant review/test):
        Phase 1: Context (Index + Context Agent)
        Phase 2: Exploration Swarm (N parallel explorers -> aggregator)
        Phase 3: Approve Exploration
        Phase 4: Architecture Swarm (N parallel architects -> aggregator)
        Phase 5: Approve Architecture
        Phase 6: Implementation (Spec + Iteration Loop)
        Phase 7: Completion (Doc Sync)
        """
        workflow = build_swarm_workflow(
            request="Add feature",
            project_root=tmp_path,
        )

        # Get stage ref_ids
        stage_refs = {stage.ref_id for stage in workflow.stages}

        # Phase 1: Context
        assert "p1_index" in stage_refs
        assert "p1_context" in stage_refs

        # Phase 2: Exploration (now uses individual agent stages + aggregate)
        assert "p2_explore_aggregate" in stage_refs
        # At least one explorer agent stage should exist
        assert any(
            ref.startswith("p2_explore_") and ref != "p2_explore_aggregate" for ref in stage_refs
        )

        # Phase 3: Approval
        assert "p3_approve_explore" in stage_refs

        # Phase 4: Architecture (now uses individual agent stages + aggregate)
        assert "p4_architect_aggregate" in stage_refs
        # At least one architect agent stage should exist
        assert any(
            ref.startswith("p4_architect_") and ref != "p4_architect_aggregate"
            for ref in stage_refs
        )

        # Phase 5: Approval
        assert "p5_approve_arch" in stage_refs

        # Phase 6: Implementation (Spec + Iteration Loop)
        assert "p6_spec" in stage_refs
        assert "p6_iteration_loop" in stage_refs

        # Phase 7: Completion (review/test phases removed - handled by iteration loop)
        assert "p7_complete" in stage_refs

        # Verify removed phases are NOT present
        assert "p7_review" not in stage_refs  # Removed - handled by iteration loop
        assert "p8_approve_final" not in stage_refs  # Removed
        assert "p9_test" not in stage_refs  # Removed - handled by iteration loop
        assert "p9_sync" not in stage_refs  # Renamed to p7_complete

    def test_dependencies_correct(self, tmp_path: Path):
        """Test that stage dependencies are correctly set."""
        workflow = build_swarm_workflow(
            request="Add feature",
            project_root=tmp_path,
        )

        # Build lookup
        stages_by_ref = {stage.ref_id: stage for stage in workflow.stages}

        # Check sequential dependencies
        assert stages_by_ref["p1_context"].requisite_stage_ref_ids == {"p1_index"}

        # Exploration agents depend on context
        explore_agents = [
            s
            for s in workflow.stages
            if s.ref_id.startswith("p2_explore_") and "aggregate" not in s.ref_id
        ]
        for agent_stage in explore_agents:
            assert agent_stage.requisite_stage_ref_ids == {"p1_context"}

        # Exploration aggregate depends on all explorer agents
        assert stages_by_ref["p3_approve_explore"].requisite_stage_ref_ids == {
            "p2_explore_aggregate"
        }

        # Architect agents depend on exploration approval
        arch_agents = [
            s
            for s in workflow.stages
            if s.ref_id.startswith("p4_architect_") and "aggregate" not in s.ref_id
        ]
        for agent_stage in arch_agents:
            assert agent_stage.requisite_stage_ref_ids == {"p3_approve_explore"}

        # Final completion depends on iteration loop
        assert stages_by_ref["p7_complete"].requisite_stage_ref_ids == {"p6_iteration_loop"}

    def test_swarm_stages_have_config(self, tmp_path: Path):
        """Test that swarm agent stages have proper configuration.

        In the new architecture, each agent runs as a separate Stabilize stage
        with its own agent_config (not swarm_config). The aggregator stage
        combines results from all agent stages.
        """
        workflow = build_swarm_workflow(
            request="Add feature",
            project_root=tmp_path,
        )

        stages_by_ref = {stage.ref_id: stage for stage in workflow.stages}

        # Check exploration agent stages have agent_config
        explore_agents = [
            s
            for s in workflow.stages
            if s.ref_id.startswith("p2_explore_") and "aggregate" not in s.ref_id
        ]
        assert len(explore_agents) >= 1  # At least one explorer (minimal mode uses 1)
        for agent_stage in explore_agents:
            assert "agent_config" in agent_stage.context
            agent_config = agent_stage.context["agent_config"]
            assert "role" in agent_config
            assert agent_config["role"].startswith("explorer_")

        # Check architecture agent stages have agent_config
        arch_agents = [
            s
            for s in workflow.stages
            if s.ref_id.startswith("p4_architect_") and "aggregate" not in s.ref_id
        ]
        assert len(arch_agents) >= 1  # At least one architect
        for agent_stage in arch_agents:
            assert "agent_config" in agent_stage.context
            agent_config = agent_stage.context["agent_config"]
            assert "role" in agent_config
            assert agent_config["role"].startswith("architect_")

        # Verify aggregator stages exist and have aggregation strategy
        assert "p2_explore_aggregate" in stages_by_ref
        assert "aggregation_strategy" in stages_by_ref["p2_explore_aggregate"].context

        assert "p4_architect_aggregate" in stages_by_ref
        assert "aggregation_strategy" in stages_by_ref["p4_architect_aggregate"].context

    def test_approval_gates_have_options(self, tmp_path: Path):
        """Test that architecture approval gate has options."""
        workflow = build_swarm_workflow(
            request="Add feature",
            project_root=tmp_path,
        )

        stages_by_ref = {stage.ref_id: stage for stage in workflow.stages}

        # Architecture approval should have approach options
        arch_approval = stages_by_ref["p5_approve_arch"]
        assert "options" in arch_approval.context
        options = arch_approval.context["options"]
        assert len(options) == 3

        option_values = {opt["value"] for opt in options}
        assert "minimal" in option_values
        assert "clean" in option_values
        assert "pragmatic" in option_values


class TestApprovalGateTask:
    """Tests for ApprovalGateTask."""

    def test_yolo_mode_auto_approves(self):
        """Test that YOLO mode auto-approves without prompting."""
        from stabilize.models.stage import StageExecution

        from red9.agents.tasks.approval_gate import ApprovalGateTask
        from red9.approval import configure_approval

        # Configure YOLO mode
        configure_approval(mode="yolo")

        task = ApprovalGateTask()

        # Create mock stage
        stage = MagicMock(spec=StageExecution)
        stage.context = {
            "project_root": "/tmp/test",
            "workflow_id": "test-123",
            "approval_type": "exploration",
            "summary": "Test summary",
        }
        stage.upstream_stages.return_value = []

        result = task.execute(stage)

        assert result.outputs["approved"] is True
        assert result.outputs["mode"] == "yolo"

    def test_auto_mode_auto_approves(self):
        """Test that AUTO mode auto-approves."""
        from stabilize.models.stage import StageExecution

        from red9.agents.tasks.approval_gate import ApprovalGateTask
        from red9.approval import configure_approval

        # Configure AUTO mode
        configure_approval(mode="auto")

        task = ApprovalGateTask()

        stage = MagicMock(spec=StageExecution)
        stage.context = {
            "project_root": "/tmp/test",
            "workflow_id": "test-456",
            "approval_type": "architecture",
            "summary": "Architecture summary",
        }
        stage.upstream_stages.return_value = []

        result = task.execute(stage)

        assert result.outputs["approved"] is True
        assert result.outputs["mode"] == "auto"


class TestSwarmAggregatorTask:
    """Tests for SwarmAggregatorTask."""

    def test_aggregates_results(self):
        """Test that aggregator processes swarm results."""
        from unittest.mock import MagicMock

        from stabilize.models.stage import StageExecution

        from red9.agents.tasks.swarm_aggregator import SwarmAggregatorTask
        from red9.workflows.models import SwarmAgentConfig, SwarmAgentResult, SwarmAgentRole

        # Create mock provider
        mock_provider = MagicMock()
        mock_provider.generate.return_value = """
{
    "consensus_points": ["All agree on modular design"],
    "unified_recommendation": "Use modular approach"
}
"""

        task = SwarmAggregatorTask(mock_provider)

        # Create mock swarm results
        results = [
            SwarmAgentResult(
                agent_config=SwarmAgentConfig(
                    role=SwarmAgentRole.EXPLORER_ARCHITECTURE,
                    focus="arch",
                    system_prompt_extension="",
                ),
                output="Found modular architecture.",
                success=True,
            ).to_dict(),
            SwarmAgentResult(
                agent_config=SwarmAgentConfig(
                    role=SwarmAgentRole.EXPLORER_UX,
                    focus="ux",
                    system_prompt_extension="",
                ),
                output="UI is component-based.",
                success=True,
            ).to_dict(),
        ]

        stage = MagicMock(spec=StageExecution)
        stage.context = {
            "project_root": "/tmp/test",
            "workflow_id": "test-789",
            "swarm_results": results,
            "aggregation_strategy": "consensus",
            "output_key": "exploration_summary",
        }
        stage.upstream_stages.return_value = []

        result = task.execute(stage)

        assert result.outputs["agents_aggregated"] == 2
        assert "exploration_summary" in result.outputs
        mock_provider.generate.assert_called_once()


class TestCLIFlags:
    """Tests for CLI flags."""

    def test_workflow_choices(self):
        """Test that workflow accepts valid choices."""
        from click.testing import CliRunner

        from red9.cli.main import main

        runner = CliRunner()

        # Test invalid workflow
        result = runner.invoke(main, ["task", "test", "--workflow", "invalid"])
        assert result.exit_code != 0
        assert "Invalid value" in result.output

    def test_help_shows_options(self):
        """Test that help shows all options."""
        from click.testing import CliRunner

        from red9.cli.main import main

        runner = CliRunner()
        result = runner.invoke(main, ["task", "--help"])

        assert "--workflow" in result.output
        assert "--yolo" in result.output
        assert "-y" in result.output
        assert "v1" in result.output
        assert "v2" in result.output
        assert "swarm" in result.output
