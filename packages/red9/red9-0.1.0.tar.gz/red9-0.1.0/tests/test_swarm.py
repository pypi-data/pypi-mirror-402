"""Unit tests for swarm infrastructure."""

from __future__ import annotations

from pathlib import Path

from red9.workflows.models import (
    MODEL_AGENTIC,
    MODEL_CODING,
    MODEL_REASONING,
    SWARM_MODEL_MAP,
    AggregationStrategy,
    SwarmAgentConfig,
    SwarmAgentResult,
    SwarmAgentRole,
    SwarmConfig,
    get_architecture_swarm,
    get_exploration_swarm,
    get_review_swarm,
)


class TestSwarmAgentRole:
    """Tests for SwarmAgentRole enum."""

    def test_all_roles_defined(self):
        """Verify all expected roles are defined."""
        expected_roles = {
            "explorer_architecture",
            "explorer_ux",
            "explorer_tests",
            "architect_minimal",
            "architect_clean",
            "architect_pragmatic",
            "reviewer_simplicity",
            "reviewer_bugs",
            "reviewer_conventions",
            "aggregator",
            "integrator",
        }
        actual_roles = {role.value for role in SwarmAgentRole}
        assert actual_roles == expected_roles

    def test_model_map_coverage(self):
        """Verify all roles have a model mapping."""
        for role in SwarmAgentRole:
            assert role.value in SWARM_MODEL_MAP, f"Missing model mapping for {role.value}"


class TestSwarmAgentConfig:
    """Tests for SwarmAgentConfig dataclass."""

    def test_basic_creation(self):
        """Test creating a basic agent config."""
        config = SwarmAgentConfig(
            role=SwarmAgentRole.EXPLORER_ARCHITECTURE,
            focus="system architecture",
            system_prompt_extension="Focus on patterns.",
        )
        assert config.role == SwarmAgentRole.EXPLORER_ARCHITECTURE
        assert config.focus == "system architecture"
        assert config.max_iterations == 20  # Reduced from 30 to prevent iteration explosion
        assert config.temperature == 0.7

    def test_get_model_default(self):
        """Test get_model returns correct model for role."""
        config = SwarmAgentConfig(
            role=SwarmAgentRole.EXPLORER_ARCHITECTURE,
            focus="test",
            system_prompt_extension="",
        )
        assert config.get_model() == MODEL_CODING

        config2 = SwarmAgentConfig(
            role=SwarmAgentRole.ARCHITECT_MINIMAL,
            focus="test",
            system_prompt_extension="",
        )
        assert config2.get_model() == MODEL_REASONING

        config3 = SwarmAgentConfig(
            role=SwarmAgentRole.AGGREGATOR,
            focus="test",
            system_prompt_extension="",
        )
        assert config3.get_model() == MODEL_AGENTIC

    def test_get_model_override(self):
        """Test get_model respects override."""
        config = SwarmAgentConfig(
            role=SwarmAgentRole.EXPLORER_ARCHITECTURE,
            focus="test",
            system_prompt_extension="",
            model_override="custom-model:latest",
        )
        assert config.get_model() == "custom-model:latest"

    def test_to_dict_from_dict(self):
        """Test serialization round-trip."""
        config = SwarmAgentConfig(
            role=SwarmAgentRole.ARCHITECT_CLEAN,
            focus="SOLID principles",
            system_prompt_extension="Design for testability.",
            max_iterations=50,
            temperature=0.5,
            output_key="clean_arch",
        )
        data = config.to_dict()
        restored = SwarmAgentConfig.from_dict(data)

        assert restored.role == config.role
        assert restored.focus == config.focus
        assert restored.system_prompt_extension == config.system_prompt_extension
        assert restored.max_iterations == config.max_iterations
        assert restored.temperature == config.temperature
        assert restored.output_key == config.output_key


class TestSwarmAgentResult:
    """Tests for SwarmAgentResult dataclass."""

    def test_basic_result(self):
        """Test creating a basic result."""
        config = SwarmAgentConfig(
            role=SwarmAgentRole.EXPLORER_TESTS,
            focus="test coverage",
            system_prompt_extension="",
        )
        result = SwarmAgentResult(
            agent_config=config,
            output="Found 3 test files.",
            success=True,
        )
        assert result.success
        assert result.error is None
        assert result.confidence == 0.0

    def test_failed_result(self):
        """Test creating a failed result."""
        config = SwarmAgentConfig(
            role=SwarmAgentRole.EXPLORER_TESTS,
            focus="test coverage",
            system_prompt_extension="",
        )
        result = SwarmAgentResult(
            agent_config=config,
            output="",
            success=False,
            error="Provider timeout",
        )
        assert not result.success
        assert result.error == "Provider timeout"

    def test_to_dict_from_dict(self):
        """Test serialization round-trip."""
        config = SwarmAgentConfig(
            role=SwarmAgentRole.REVIEWER_BUGS,
            focus="finding bugs",
            system_prompt_extension="",
        )
        result = SwarmAgentResult(
            agent_config=config,
            output="Found potential null pointer.",
            success=True,
            confidence=85.0,
            files_read=["src/main.py"],
        )
        data = result.to_dict()
        restored = SwarmAgentResult.from_dict(data)

        assert restored.success == result.success
        assert restored.output == result.output
        assert restored.confidence == result.confidence
        assert restored.files_read == result.files_read


class TestSwarmConfig:
    """Tests for SwarmConfig dataclass."""

    def test_basic_creation(self):
        """Test creating a basic swarm config."""
        config = SwarmConfig(name="test_swarm")
        assert config.name == "test_swarm"
        assert config.agents == []
        assert config.aggregation_strategy == AggregationStrategy.CONSENSUS
        assert config.max_concurrent == 3

    def test_with_agents(self):
        """Test creating swarm with agents."""
        agents = [
            SwarmAgentConfig(
                role=SwarmAgentRole.EXPLORER_ARCHITECTURE,
                focus="arch",
                system_prompt_extension="",
            ),
            SwarmAgentConfig(
                role=SwarmAgentRole.EXPLORER_UX,
                focus="ux",
                system_prompt_extension="",
            ),
        ]
        config = SwarmConfig(
            name="dual_explore",
            agents=agents,
            aggregation_strategy=AggregationStrategy.UNION,
        )
        assert len(config.agents) == 2
        assert config.aggregation_strategy == AggregationStrategy.UNION

    def test_to_dict_from_dict(self):
        """Test serialization round-trip."""
        agents = [
            SwarmAgentConfig(
                role=SwarmAgentRole.ARCHITECT_MINIMAL,
                focus="minimal changes",
                system_prompt_extension="Less is more.",
            ),
        ]
        config = SwarmConfig(
            name="arch_swarm",
            agents=agents,
            aggregation_strategy=AggregationStrategy.VOTING,
            max_concurrent=5,
        )
        data = config.to_dict()
        restored = SwarmConfig.from_dict(data)

        assert restored.name == config.name
        assert len(restored.agents) == 1
        assert restored.agents[0].role == SwarmAgentRole.ARCHITECT_MINIMAL
        assert restored.aggregation_strategy == AggregationStrategy.VOTING
        assert restored.max_concurrent == 5


class TestPreConfiguredSwarms:
    """Tests for pre-configured swarm functions."""

    def test_exploration_swarm(self):
        """Test get_exploration_swarm returns valid config."""
        swarm = get_exploration_swarm()
        assert swarm.name == "exploration_swarm"
        assert len(swarm.agents) == 3
        assert swarm.aggregation_strategy == AggregationStrategy.UNION

        roles = {a.role for a in swarm.agents}
        assert SwarmAgentRole.EXPLORER_ARCHITECTURE in roles
        assert SwarmAgentRole.EXPLORER_UX in roles
        assert SwarmAgentRole.EXPLORER_TESTS in roles

    def test_architecture_swarm(self):
        """Test get_architecture_swarm returns valid config."""
        swarm = get_architecture_swarm()
        assert swarm.name == "architecture_swarm"
        assert len(swarm.agents) == 3
        assert swarm.aggregation_strategy == AggregationStrategy.VOTING

        roles = {a.role for a in swarm.agents}
        assert SwarmAgentRole.ARCHITECT_MINIMAL in roles
        assert SwarmAgentRole.ARCHITECT_CLEAN in roles
        assert SwarmAgentRole.ARCHITECT_PRAGMATIC in roles

    def test_review_swarm(self):
        """Test get_review_swarm returns valid config."""
        swarm = get_review_swarm()
        assert swarm.name == "review_swarm"
        assert len(swarm.agents) == 3
        assert swarm.aggregation_strategy == AggregationStrategy.UNION

        roles = {a.role for a in swarm.agents}
        assert SwarmAgentRole.REVIEWER_SIMPLICITY in roles
        assert SwarmAgentRole.REVIEWER_BUGS in roles
        assert SwarmAgentRole.REVIEWER_CONVENTIONS in roles


class TestSwarmPrompts:
    """Tests for swarm prompts."""

    def test_all_roles_have_prompts(self):
        """Verify all roles have prompts defined."""
        from red9.agents.swarm_prompts import get_role_prompt

        for role in SwarmAgentRole:
            prompt = get_role_prompt(role)
            assert prompt, f"No prompt for {role.value}"
            assert len(prompt) > 100, f"Prompt too short for {role.value}"

    def test_prompt_quality(self):
        """Verify prompts contain expected sections."""
        from red9.agents.swarm_prompts import get_role_prompt

        # Check explorer prompt has rules and tools
        explorer_prompt = get_role_prompt(SwarmAgentRole.EXPLORER_ARCHITECTURE)
        assert "Rules" in explorer_prompt or "Tools" in explorer_prompt

        # Check architect prompt has minimalist/minimal approach
        architect_prompt = get_role_prompt(SwarmAgentRole.ARCHITECT_MINIMAL)
        assert "Minimal" in architect_prompt or "minimal" in architect_prompt.lower()

        # Check reviewer prompt has confidence threshold
        reviewer_prompt = get_role_prompt(SwarmAgentRole.REVIEWER_BUGS)
        assert "confidence" in reviewer_prompt.lower()


class TestContextInjector:
    """Tests for ContextInjector."""

    def test_no_context_file(self, tmp_path: Path):
        """Test behavior when no context file exists."""
        from red9.agents.context_injector import ContextInjector

        injector = ContextInjector(tmp_path)
        context = injector.get_context_for_directory(tmp_path)
        assert context == ""

    def test_finds_agents_md(self, tmp_path: Path):
        """Test finding AGENTS.md file."""
        from red9.agents.context_injector import ContextInjector

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# Agent Instructions\n\nFollow these rules.")

        injector = ContextInjector(tmp_path)
        context = injector.get_context_for_directory(tmp_path)
        assert "Agent Instructions" in context
        assert "Follow these rules" in context

    def test_priority_order(self, tmp_path: Path):
        """Test that AGENTS.md takes priority over README.md."""
        from red9.agents.context_injector import ContextInjector

        (tmp_path / "AGENTS.md").write_text("AGENTS content")
        (tmp_path / "README.md").write_text("README content")

        injector = ContextInjector(tmp_path)
        context = injector.get_context_for_directory(tmp_path)
        assert "AGENTS content" in context
        assert "README content" not in context

    def test_inject_into_prompt(self, tmp_path: Path):
        """Test injecting context into prompt."""
        from red9.agents.context_injector import ContextInjector

        (tmp_path / "AGENTS.md").write_text("Use pytest for testing.")

        injector = ContextInjector(tmp_path)
        prompt = "You are a code assistant."
        injected = injector.inject_into_prompt(prompt, tmp_path)

        assert "You are a code assistant." in injected
        assert "Use pytest for testing." in injected
        assert "Directory-Specific Context" in injected


class TestTodoEnforcer:
    """Tests for TodoEnforcer."""

    def test_detects_markdown_todos(self):
        """Test detecting markdown checkbox todos."""
        from red9.agents.hooks.todo_enforcer import TodoEnforcer

        enforcer = TodoEnforcer()

        output = "Done:\n- [x] Task 1\n- [ ] Task 2\n- [ ] Task 3"
        result = enforcer.check_output(output)

        assert result.has_incomplete_todos
        assert result.todo_count == 2

    def test_detects_code_todos(self):
        """Test detecting TODO comments."""
        from red9.agents.hooks.todo_enforcer import TodoEnforcer

        enforcer = TodoEnforcer()

        output = """
def foo():
    # TODO: Implement this
    pass

# FIXME: Handle edge case
"""
        result = enforcer.check_output(output)

        assert result.has_incomplete_todos
        assert result.todo_count == 2

    def test_no_todos(self):
        """Test output without todos."""
        from red9.agents.hooks.todo_enforcer import TodoEnforcer

        enforcer = TodoEnforcer()

        output = "All tasks completed successfully.\n- [x] Done\n- [x] Also done"
        result = enforcer.check_output(output)

        assert not result.has_incomplete_todos
        assert result.todo_count == 0

    def test_should_block_completion(self):
        """Test completion blocking logic."""
        from red9.agents.hooks.todo_enforcer import TodoEnforcer

        enforcer = TodoEnforcer()

        # Should not block if not calling complete_task
        should_block, _ = enforcer.should_block_completion("[ ] TODO", called_complete_task=False)
        assert not should_block

        # Should block if calling complete_task with todos
        should_block, warning = enforcer.should_block_completion(
            "[ ] TODO", called_complete_task=True
        )
        assert should_block
        assert "INCOMPLETE TODOS" in warning

        # Should not block if no todos
        should_block, _ = enforcer.should_block_completion("All done!", called_complete_task=True)
        assert not should_block
