"""Pytest configuration and fixtures for RED9 tests."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def project_dir(temp_dir: Path) -> Path:
    """Create a mock project directory structure."""
    # Create .red9 directory
    red9_dir = temp_dir / ".red9"
    red9_dir.mkdir()

    # Create a simple config
    config_file = red9_dir / "config.yaml"
    config_file.write_text("""
version: 1
provider:
  type: ollama
  model: llama3.1:8b
""")

    # Create some source files
    src_dir = temp_dir / "src"
    src_dir.mkdir()

    (src_dir / "main.py").write_text('print("Hello, World!")\n')
    (src_dir / "utils.py").write_text("def add(a, b):\n    return a + b\n")

    return temp_dir


@pytest.fixture
def sample_file(temp_dir: Path) -> Path:
    """Create a sample file for testing."""
    file_path = temp_dir / "sample.py"
    file_path.write_text("""def hello():
    print("Hello")

def goodbye():
    print("Goodbye")
""")
    return file_path


@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry for testing."""
    from red9.tools.base import Tool, ToolDefinition, ToolRegistry, ToolResult

    class MockTool(Tool):
        @property
        def name(self) -> str:
            return "mock_tool"

        @property
        def description(self) -> str:
            return "A mock tool for testing"

        def get_definition(self) -> ToolDefinition:
            return ToolDefinition(
                name=self.name,
                description=self.description,
                parameters={"type": "object", "properties": {}},
            )

        def execute(self, params: dict) -> ToolResult:
            return ToolResult.ok({"status": "success"})

    registry = ToolRegistry()
    registry.register(MockTool())
    return registry
