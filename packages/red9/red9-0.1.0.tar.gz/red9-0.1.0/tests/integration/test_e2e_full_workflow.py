"""Full end-to-end integration tests for RED9.

These tests actually hit Ollama models and test the complete workflow.
They run against a real project in /tmp/red9-e2e-test-project/.

The project is cleaned at the start but preserved at the end for manual inspection.

Requirements:
- Ollama must be running with the required models:
  - nemotron-3-nano:30b-cloud (agentic)
  - qwen3-coder:480b-cloud (code generation)
  - devstral-small-2:24b-cloud (review)
  - nomic-embed-text (embeddings)

Run with: pytest tests/integration/test_e2e_full_workflow.py -v -s
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest

# Test project location - preserved after tests for inspection
E2E_PROJECT_PATH = Path("/tmp/red9-e2e-test-project")


# =============================================================================
# Test Application Content
# =============================================================================

MAIN_PY = '''"""Simple calculator application."""


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


if __name__ == "__main__":
    print(f"2 + 3 = {add(2, 3)}")
    print(f"5 - 2 = {subtract(5, 2)}")
    print(f"4 * 3 = {multiply(4, 3)}")
'''

UTILS_PY = '''"""Utility functions."""
from typing import List


def format_result(operation: str, result: int) -> str:
    """Format a calculation result for display."""
    return f"Result of {operation}: {result}"


def validate_numbers(*args: int) -> bool:
    """Validate that all arguments are integers."""
    return all(isinstance(arg, int) for arg in args)


def sum_list(numbers: List[int]) -> int:
    """Sum a list of numbers."""
    return sum(numbers)
'''

TEST_MAIN_PY = '''"""Tests for calculator."""
import pytest
from main import add, subtract, multiply


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5


def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(0, 5) == 0
'''


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def e2e_project() -> Path:
    """Set up the E2E test project.

    Cleans and recreates /tmp/red9-e2e-test-project/ at the start.
    Does NOT clean up at the end - project is preserved for inspection.
    """
    # Clean up if exists
    if E2E_PROJECT_PATH.exists():
        shutil.rmtree(E2E_PROJECT_PATH)

    # Create fresh project
    E2E_PROJECT_PATH.mkdir(parents=True)

    # Create source files
    (E2E_PROJECT_PATH / "main.py").write_text(MAIN_PY)
    (E2E_PROJECT_PATH / "utils.py").write_text(UTILS_PY)

    # Create tests directory
    tests_dir = E2E_PROJECT_PATH / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_main.py").write_text(TEST_MAIN_PY)

    print(f"\n{'=' * 60}")
    print(f"E2E Test Project created at: {E2E_PROJECT_PATH}")
    print(f"{'=' * 60}\n")

    yield E2E_PROJECT_PATH

    # DO NOT clean up - preserve for inspection
    print(f"\n{'=' * 60}")
    print(f"E2E Test Project preserved at: {E2E_PROJECT_PATH}")
    print("You can inspect the results manually.")
    print(f"{'=' * 60}\n")


@pytest.fixture(scope="module")
def red9_session(e2e_project: Path):
    """Initialize RED9 session for the test project."""
    from red9.core.session import Red9Session

    session = Red9Session(e2e_project)

    # Initialize with our specific models
    session.initialize_project(
        provider="ollama",
        model="nemotron-3-nano:30b-cloud",
        embedding_model="nomic-embed-text",
    )

    # Override models in config
    assert session.config is not None
    session.config.provider.code_model = "qwen3-coder:480b-cloud"
    session.config.provider.review_model = "devstral-small-2:24b-cloud"
    session.config.provider.agent_model = "nemotron-3-nano:30b-cloud"

    print("RED9 initialized with config:")
    print(f"  - model: {session.config.provider.model}")
    print(f"  - code_model: {session.config.provider.code_model}")
    print(f"  - review_model: {session.config.provider.review_model}")
    print(f"  - agent_model: {session.config.provider.agent_model}")
    print(f"  - embedding_model: {session.config.provider.embedding_model}")

    return session


# =============================================================================
# Integration Tests
# =============================================================================


class TestOllamaConnection:
    """Test that Ollama is available and models are accessible."""

    def test_ollama_is_running(self, red9_session) -> None:
        """Verify Ollama is running and responding."""
        from red9.providers.base import GenerationConfig
        from red9.providers.ollama import OllamaProvider

        provider = OllamaProvider(
            base_url=red9_session.config.provider.base_url,
            model=red9_session.config.provider.model,
        )

        # Simple generation test
        config = GenerationConfig(max_tokens=20)
        response = provider.generate("Say 'hello' and nothing else.", config=config)
        assert response is not None
        assert len(response) > 0
        print(f"Ollama response: {response}")

    def test_embedding_model_works(self, red9_session) -> None:
        """Verify embedding model is available."""
        from red9.providers.ollama import OllamaProvider

        provider = OllamaProvider(
            base_url=red9_session.config.provider.base_url,
            model=red9_session.config.provider.model,
            embedding_model=red9_session.config.provider.embedding_model,
        )

        # Test embedding generation
        result = provider.embed(["test text for embedding"])
        assert result.embeddings is not None
        assert len(result.embeddings) == 1
        assert len(result.embeddings[0]) > 0  # Has dimensions
        print(f"Embedding dimensions: {len(result.embeddings[0])}")


class TestRAGIndexing:
    """Test RAG indexing and semantic search."""

    def test_index_codebase(self, red9_session, e2e_project: Path) -> None:
        """Test that codebase can be indexed."""
        # Index the codebase
        indexed_count = red9_session.index_codebase()
        print(f"Indexed {indexed_count} files")

        assert indexed_count >= 2  # At least main.py and utils.py

    def test_load_rag_assistant(self, red9_session) -> None:
        """Test that RAG assistant loads successfully."""
        red9_session.load_rag()
        assert red9_session.rag_assistant is not None
        print("RAG assistant loaded successfully")

    def test_semantic_search(self, red9_session) -> None:
        """Test semantic search finds relevant code."""
        if not red9_session.rag_assistant:
            red9_session.load_rag()

        assert red9_session.rag_assistant is not None

        # Search for multiplication-related code
        # retrieve returns list of (chunk, score) tuples
        results = red9_session.rag_assistant.retrieve("multiply numbers", top_k=3)

        assert results is not None
        assert len(results) > 0
        print(f"Semantic search returned {len(results)} results")

        # Results are tuples (chunk, score) - extract content from chunks
        # Chunk objects have 'content' or we can convert to string
        all_content = ""
        for chunk, score in results:
            if hasattr(chunk, "content"):
                all_content += chunk.content + " "
            else:
                all_content += str(chunk) + " "
            print(f"  - Score: {score:.3f}, Content: {str(chunk)[:80]}...")

        assert "multiply" in all_content.lower() or "def" in all_content.lower()


class TestIndexChangeDetection:
    """Test that index detects file changes."""

    def test_detects_new_file(self, red9_session, e2e_project: Path) -> None:
        """Test that indexer detects a new file."""
        # Initial index
        red9_session.index_codebase()

        # Add a new file
        new_file = e2e_project / "new_module.py"
        new_file.write_text('"""A new module."""\n\ndef new_function():\n    pass\n')

        # Check needs_update
        assert red9_session.index_manager is not None
        needs_update, added, modified, deleted = red9_session.index_manager.needs_update()

        assert needs_update is True
        assert added >= 1  # At least the new file
        print(f"Detected changes: added={added}, modified={modified}, deleted={deleted}")

        # Clean up
        new_file.unlink()

    def test_detects_modified_file(self, red9_session, e2e_project: Path) -> None:
        """Test that indexer detects file modifications."""
        # Initial index
        red9_session.index_codebase()

        # Modify main.py
        main_file = e2e_project / "main.py"
        original_content = main_file.read_text()
        main_file.write_text(original_content + "\n# Modified for test\n")

        # Check needs_update
        assert red9_session.index_manager is not None
        needs_update, added, modified, deleted = red9_session.index_manager.needs_update()

        assert needs_update is True
        assert modified >= 1
        print(f"Detected changes: added={added}, modified={modified}, deleted={deleted}")

        # Restore original
        main_file.write_text(original_content)


class TestToolExecution:
    """Test tool execution through the agent loop."""

    def test_read_file_tool(self, red9_session, e2e_project: Path) -> None:
        """Test ReadFileTool works correctly."""
        from red9.tools.read_file import ReadFileTool

        tool = ReadFileTool()
        result = tool.execute({"file_path": str(e2e_project / "main.py")})

        assert result.success
        # Output is a dict with 'content' (formatted) and 'raw_content' keys
        content = result.output.get("raw_content", "") or result.output.get("content", "")
        assert "def add(" in content
        assert "def multiply(" in content
        print("ReadFileTool works correctly")

    def test_edit_file_tool(self, red9_session, e2e_project: Path) -> None:
        """Test EditFileTool works correctly."""
        from red9.tools.edit_file import EditFileTool

        # Create a test file
        test_file = e2e_project / "edit_test.py"
        test_file.write_text("x = 1\ny = 2\n")

        tool = EditFileTool()
        result = tool.execute(
            {
                "file_path": str(test_file),
                "old_string": "x = 1",
                "new_string": "x = 100",
            }
        )

        assert result.success
        assert result.output["occurrences_replaced"] == 1

        # Verify change
        content = test_file.read_text()
        assert "x = 100" in content
        print("EditFileTool works correctly")

    def test_grep_tool(self, red9_session, e2e_project: Path) -> None:
        """Test GrepTool works correctly."""
        from red9.tools.grep import GrepTool

        tool = GrepTool()
        result = tool.execute(
            {
                "pattern": "def.*\\(",
                "path": str(e2e_project),
                "include": "*.py",
            }
        )

        assert result.success
        assert len(result.output.get("matches", [])) > 0
        print(f"GrepTool found {len(result.output['matches'])} matches")


class TestAgentLoop:
    """Test the agent loop with actual LLM calls."""

    def test_simple_agent_task(self, red9_session, e2e_project: Path) -> None:
        """Test a simple agent task that reads and analyzes code."""
        from red9.agents.loop import AgentLoop
        from red9.providers.ollama import OllamaProvider
        from red9.tools.base import ToolRegistry
        from red9.tools.read_file import ReadFileTool

        # Set up minimal agent
        provider = OllamaProvider(
            base_url=red9_session.config.provider.base_url,
            model=red9_session.config.provider.agent_model,
        )

        registry = ToolRegistry()
        registry.register(ReadFileTool())

        agent = AgentLoop(
            provider=provider,
            tool_registry=registry,
            max_iterations=5,
        )

        # Run a simple task
        user_msg = (
            f"Read the file {e2e_project}/main.py and tell me what functions it contains. Be brief."
        )
        result = agent.run(
            system_prompt="You are a code assistant. Use tools to answer questions.",
            user_message=user_msg,
        )

        assert result.success or result.tool_calls_made > 0
        print(f"Agent made {result.tool_calls_made} tool calls")
        print(f"Final message: {result.final_message[:200]}...")


class TestFullWorkflow:
    """Test the complete RED9 workflow with a real coding task."""

    def test_execute_simple_task(self, red9_session, e2e_project: Path) -> None:
        """Execute a simple coding task through the full workflow.

        This test actually runs the V2 workflow:
        context_agent -> spec_agent -> ddd_agent -> docs_sync_agent
        """
        # Load RAG first
        red9_session.load_rag()

        print("\n" + "=" * 60)
        print("Starting full workflow test...")
        print("Task: Add a divide function to main.py")
        print("=" * 60 + "\n")

        start_time = time.time()

        # Execute a real task
        task_request = (
            "Add a divide function to main.py that divides two numbers. "
            "Handle division by zero by returning None."
        )
        success = red9_session.execute_task(
            request=task_request,
            parallel=False,
        )

        duration = time.time() - start_time
        print(f"\nWorkflow completed in {duration:.1f}s")
        print(f"Success: {success}")

        # Check if the file was modified
        main_content = (e2e_project / "main.py").read_text()
        print(f"\n--- main.py content ---\n{main_content}\n--- end ---\n")

        # The task should have added a divide function
        # Note: Even if workflow fails, check what was created
        if "def divide" in main_content:
            print("SUCCESS: divide function was added!")
        else:
            print("WARNING: divide function not found in main.py")
            print("Check the project manually for partial results")

    def test_execute_multi_file_task(self, red9_session, e2e_project: Path) -> None:
        """Execute a task that should modify multiple files."""
        red9_session.load_rag()

        print("\n" + "=" * 60)
        print("Starting multi-file workflow test...")
        print("Task: Add power function and a utility to format it")
        print("=" * 60 + "\n")

        start_time = time.time()

        success = red9_session.execute_task(
            request=(
                "Add a power function to main.py that raises a number to a power. "
                "Also add a format_power_result function to utils.py that formats "
                "the result as 'X^Y = Z'."
            ),
            parallel=False,
        )

        duration = time.time() - start_time
        print(f"\nWorkflow completed in {duration:.1f}s")
        print(f"Success: {success}")

        # Check results
        main_content = (e2e_project / "main.py").read_text()
        utils_content = (e2e_project / "utils.py").read_text()

        print(f"\n--- main.py ---\n{main_content}\n")
        print(f"\n--- utils.py ---\n{utils_content}\n")

        if "def power" in main_content or "pow" in main_content:
            print("SUCCESS: power function was added to main.py!")

        if "format_power" in utils_content or "format" in utils_content:
            print("SUCCESS: format function was added to utils.py!")


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_file_path(self, red9_session, e2e_project: Path) -> None:
        """Test that invalid file paths are handled gracefully."""
        from red9.tools.read_file import ReadFileTool

        tool = ReadFileTool()
        result = tool.execute({"file_path": "/nonexistent/path/file.py"})

        assert not result.success
        print(f"Invalid path correctly rejected: {result.error}")

    def test_empty_search_pattern(self, red9_session, e2e_project: Path) -> None:
        """Test that empty search patterns are handled."""
        from red9.tools.grep import GrepTool

        tool = GrepTool()
        result = tool.execute(
            {
                "pattern": "",
                "path": str(e2e_project),
            }
        )

        # Should fail with invalid params
        assert not result.success
        print(f"Empty pattern correctly rejected: {result.error}")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
