"""End-to-end tests for edit tools and RAG change detection.

This test module exercises RED9's edit tools (edit_file, apply_diff, batch_edit)
and RAG indexing change detection in comprehensive workflows.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from red9.indexing.tracker import IndexTracker
from red9.tools.apply_diff import ApplyDiffTool
from red9.tools.base import ToolErrorType, set_project_root
from red9.tools.batch_edit import BatchEditTool
from red9.tools.edit_file import EditFileTool

# =============================================================================
# File Content Templates
# =============================================================================

APP_INIT_CONTENT = '''"""FastAPI Todo Application."""
__version__ = "1.0.0"
'''

APP_MODELS_CONTENT = '''"""Todo data models."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Todo:
    """Todo item model."""

    id: str
    title: str
    description: Optional[str] = None
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
        }
'''

APP_DATABASE_CONTENT = '''"""In-memory todo database."""
from typing import Optional

from app.models import Todo


class TodoDatabase:
    """Simple in-memory database for todos."""

    def __init__(self):
        self.todos: dict[str, Todo] = {}

    def add_todo(self, todo: Todo) -> Todo:
        """Add a new todo."""
        self.todos[todo.id] = todo
        return todo

    def get_todo(self, todo_id: str) -> Optional[Todo]:
        """Get a todo by ID."""
        return self.todos.get(todo_id)

    def get_all_todos(self) -> list[Todo]:
        """Get all todos."""
        return list(self.todos.values())

    def update_todo(self, todo_id: str, **kwargs) -> Optional[Todo]:
        """Update a todo."""
        todo = self.todos.get(todo_id)
        if todo:
            for key, value in kwargs.items():
                if hasattr(todo, key):
                    setattr(todo, key, value)
        return todo

    def delete_todo(self, todo_id: str) -> bool:
        """Delete a todo."""
        if todo_id in self.todos:
            del self.todos[todo_id]
            return True
        return False
'''

APP_UTILS_CONTENT = '''"""Utility functions for todo operations."""
import uuid
from typing import Optional

from app.models import Todo


def validate_todo_title(title: str) -> tuple[bool, Optional[str]]:
    """Validate a todo title.

    Args:
        title: The title to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not title:
        return False, "Title cannot be empty"
    if len(title) > 200:
        return False, "Title must be 200 characters or less"
    return True, None


def format_todo_output(todo: Todo) -> str:
    """Format a todo for display.

    Args:
        todo: The todo to format.

    Returns:
        Formatted string representation.
    """
    status = "[x]" if todo.completed else "[ ]"
    return f"{status} {todo.title} (ID: {todo.id})"


def generate_todo_id() -> str:
    """Generate a unique todo ID."""
    return str(uuid.uuid4())[:8]
'''

APP_MAIN_CONTENT = '''"""FastAPI application main module."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.database import TodoDatabase
from app.models import Todo
from app.utils import validate_todo_title, generate_todo_id

app = FastAPI(title="Todo API", version="1.0.0")
db = TodoDatabase()


class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


@app.get("/todos")
def list_todos():
    """List all todos."""
    return [todo.to_dict() for todo in db.get_all_todos()]


@app.get("/todos/{todo_id}")
def get_todo(todo_id: str):
    """Get a single todo."""
    todo = db.get_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo.to_dict()


@app.post("/todos", status_code=201)
def create_todo(data: TodoCreate):
    """Create a new todo."""
    is_valid, error = validate_todo_title(data.title)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    todo = Todo(
        id=generate_todo_id(),
        title=data.title,
        description=data.description,
    )
    db.add_todo(todo)
    return todo.to_dict()


@app.put("/todos/{todo_id}")
def update_todo(todo_id: str, data: TodoUpdate):
    """Update an existing todo."""
    todo = db.get_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    if data.title is not None:
        is_valid, error = validate_todo_title(data.title)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = db.update_todo(todo_id, **updates)
    return updated.to_dict()


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: str):
    """Delete a todo."""
    if not db.delete_todo(todo_id):
        raise HTTPException(status_code=404, detail="Todo not found")
'''

TESTS_INIT_CONTENT = '''"""Tests for todo app."""
'''

TEST_API_CONTENT = '''"""Basic API tests."""
import pytest


def test_placeholder():
    """Placeholder test."""
    assert True
'''

CONFIG_CONTENT = """version: "1"
provider:
  type: ollama
  model: nemotron-3-nano:30b-cloud
  code_model: qwen3-coder:480b-cloud
  review_model: devstral-small-2:24b-cloud
  agent_model: nemotron-3-nano:30b-cloud
  embedding_model: nomic-embed-text
indexing:
  include:
    - "**/*.py"
  exclude:
    - "**/__pycache__/**"
    - "**/tests/**"
  chunk_size: 256
  chunk_overlap: 25
  num_chunks: 3
"""


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def e2e_project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a complete FastAPI todo application project."""
    project_root = tmp_path / "todo_project"
    project_root.mkdir()

    # Create app directory
    app_dir = project_root / "app"
    app_dir.mkdir()
    (app_dir / "__init__.py").write_text(APP_INIT_CONTENT)
    (app_dir / "models.py").write_text(APP_MODELS_CONTENT)
    (app_dir / "database.py").write_text(APP_DATABASE_CONTENT)
    (app_dir / "utils.py").write_text(APP_UTILS_CONTENT)
    (app_dir / "main.py").write_text(APP_MAIN_CONTENT)

    # Create tests directory
    tests_dir = project_root / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text(TESTS_INIT_CONTENT)
    (tests_dir / "test_api.py").write_text(TEST_API_CONTENT)

    # Create .red9 directory
    red9_dir = project_root / ".red9"
    red9_dir.mkdir()
    (red9_dir / "config.yaml").write_text(CONFIG_CONTENT)

    # Set project root for path validation
    set_project_root(project_root)

    yield project_root


@pytest.fixture
def index_tracker(e2e_project_dir: Path) -> IndexTracker:
    """Create IndexTracker for change detection tests."""
    state_path = e2e_project_dir / ".red9" / "index_state.json"
    return IndexTracker(e2e_project_dir, state_path)


@pytest.fixture
def edit_file_tool() -> EditFileTool:
    """Create EditFileTool instance."""
    return EditFileTool()


@pytest.fixture
def apply_diff_tool() -> ApplyDiffTool:
    """Create ApplyDiffTool instance."""
    return ApplyDiffTool()


@pytest.fixture
def batch_edit_tool() -> BatchEditTool:
    """Create BatchEditTool instance."""
    return BatchEditTool()


# =============================================================================
# EditFileTool Tests
# =============================================================================


class TestEditFileTool:
    """Tests for the EditFileTool."""

    def test_edit_file_exact_match(
        self, e2e_project_dir: Path, edit_file_tool: EditFileTool
    ) -> None:
        """Test edit_file with exact string match - single occurrence."""
        utils_file = e2e_project_dir / "app" / "utils.py"

        result = edit_file_tool.execute(
            {
                "file_path": str(utils_file),
                "old_string": 'return False, "Title cannot be empty"',
                "new_string": 'return False, "Title is required"',
            }
        )

        assert result.success
        assert result.output["occurrences_replaced"] == 1
        assert result.output["match_type"] == "exact"
        assert result.output["is_new_file"] is False

        # Verify file content changed
        content = utils_file.read_text()
        assert 'return False, "Title is required"' in content
        assert 'return False, "Title cannot be empty"' not in content

    def test_edit_file_replace_all(
        self, e2e_project_dir: Path, edit_file_tool: EditFileTool
    ) -> None:
        """Test edit_file with replace_all=True for multiple occurrences."""
        database_file = e2e_project_dir / "app" / "database.py"

        # Count occurrences before
        original_content = database_file.read_text()
        original_count = original_content.count("self.todos")

        result = edit_file_tool.execute(
            {
                "file_path": str(database_file),
                "old_string": "self.todos",
                "new_string": "self._todos",
                "replace_all": True,
            }
        )

        assert result.success
        assert result.output["occurrences_replaced"] == original_count
        assert result.output["occurrences_replaced"] > 1  # Multiple replacements

        # Verify file content
        new_content = database_file.read_text()
        assert "self._todos" in new_content
        assert new_content.count("self._todos") == original_count

    def test_edit_file_fuzzy_match_whitespace(
        self, e2e_project_dir: Path, edit_file_tool: EditFileTool
    ) -> None:
        """Test edit_file falls back to fuzzy matching for whitespace differences."""
        utils_file = e2e_project_dir / "app" / "utils.py"

        # Provide old_string with slightly different indentation (tabs vs spaces)
        # The original uses 4 spaces, we'll provide with 2 spaces
        old_str = (
            "def generate_todo_id() -> str:\n"
            '  """Generate a unique todo ID."""\n'
            "  return str(uuid.uuid4())[:8]"
        )
        new_str = (
            "def generate_todo_id() -> str:\n"
            '    """Generate a unique todo ID."""\n'
            "    return str(uuid.uuid4())[:12]"
        )
        result = edit_file_tool.execute(
            {
                "file_path": str(utils_file),
                "old_string": old_str,
                "new_string": new_str,
            }
        )

        assert result.success
        # Fuzzy match should have been used
        assert result.output.get("fuzzy_match") is True or result.output["match_type"] == "exact"
        if result.output.get("fuzzy_match"):
            assert result.output["similarity"] >= 0.8

    def test_edit_file_create_new_file(
        self, e2e_project_dir: Path, edit_file_tool: EditFileTool
    ) -> None:
        """Test edit_file creates new file when old_string is empty."""
        new_file = e2e_project_dir / "app" / "constants.py"

        new_content = (
            '"""Application constants."""\n\nMAX_TITLE_LENGTH = 200\nDEFAULT_PAGE_SIZE = 10\n'
        )
        result = edit_file_tool.execute(
            {
                "file_path": str(new_file),
                "old_string": "",
                "new_string": new_content,
            }
        )

        assert result.success
        assert result.output["is_new_file"] is True
        assert new_file.exists()
        assert "MAX_TITLE_LENGTH = 200" in new_file.read_text()

    def test_edit_file_error_no_occurrence(
        self, e2e_project_dir: Path, edit_file_tool: EditFileTool
    ) -> None:
        """Test edit_file fails when string not found."""
        utils_file = e2e_project_dir / "app" / "utils.py"

        result = edit_file_tool.execute(
            {
                "file_path": str(utils_file),
                "old_string": "this_string_does_not_exist_anywhere",
                "new_string": "replacement",
            }
        )

        assert not result.success
        assert result.error_type == ToolErrorType.EDIT_NO_OCCURRENCE_FOUND

    def test_edit_file_error_multiple_occurrences_without_replace_all(
        self, e2e_project_dir: Path, edit_file_tool: EditFileTool
    ) -> None:
        """Test edit_file fails with multiple matches when replace_all=False."""
        database_file = e2e_project_dir / "app" / "database.py"

        result = edit_file_tool.execute(
            {
                "file_path": str(database_file),
                "old_string": "self.todos",  # Appears multiple times
                "new_string": "self._data",
                "replace_all": False,
            }
        )

        assert not result.success
        assert result.error_type == ToolErrorType.EDIT_MULTIPLE_OCCURRENCES


# =============================================================================
# ApplyDiffTool Tests
# =============================================================================


class TestApplyDiffTool:
    """Tests for the ApplyDiffTool."""

    def test_apply_diff_exact_match(
        self, e2e_project_dir: Path, apply_diff_tool: ApplyDiffTool
    ) -> None:
        """Test apply_diff with exact SEARCH/REPLACE block."""
        models_file = e2e_project_dir / "app" / "models.py"

        search_block = '    def to_dict(self) -> dict:\n        """Convert to dictionary."""'
        replace_block = (
            "    def to_dict(self) -> dict[str, any]:\n"
            '        """Convert todo to dictionary representation."""'
        )
        result = apply_diff_tool.execute(
            {
                "file_path": str(models_file),
                "search": search_block,
                "replace": replace_block,
            }
        )

        assert result.success
        content = models_file.read_text()
        assert "def to_dict(self) -> dict[str, any]:" in content
        assert "Convert todo to dictionary representation" in content

    def test_apply_diff_add_method(
        self, e2e_project_dir: Path, apply_diff_tool: ApplyDiffTool
    ) -> None:
        """Test apply_diff to add a new method to existing class."""
        database_file = e2e_project_dir / "app" / "database.py"

        # Add a complete_todo method after delete_todo
        result = apply_diff_tool.execute(
            {
                "file_path": str(database_file),
                "search": '''    def delete_todo(self, todo_id: str) -> bool:
        """Delete a todo."""
        if todo_id in self.todos:
            del self.todos[todo_id]
            return True
        return False''',
                "replace": '''    def delete_todo(self, todo_id: str) -> bool:
        """Delete a todo."""
        if todo_id in self.todos:
            del self.todos[todo_id]
            return True
        return False

    def complete_todo(self, todo_id: str) -> bool:
        """Mark a todo as completed."""
        todo = self.todos.get(todo_id)
        if todo:
            todo.completed = True
            return True
        return False''',
            }
        )

        assert result.success
        content = database_file.read_text()
        assert "def complete_todo(self, todo_id: str) -> bool:" in content
        assert "Mark a todo as completed" in content


# =============================================================================
# BatchEditTool Tests
# =============================================================================


class TestBatchEditTool:
    """Tests for the BatchEditTool."""

    def test_batch_edit_coordinated_rename(
        self, e2e_project_dir: Path, batch_edit_tool: BatchEditTool
    ) -> None:
        """Test batch_edit for renaming function across multiple files."""
        utils_file = e2e_project_dir / "app" / "utils.py"
        main_file = e2e_project_dir / "app" / "main.py"

        result = batch_edit_tool.execute(
            {
                "edits": [
                    {
                        "file_path": str(utils_file),
                        "old_string": "def validate_todo_title(title: str)",
                        "new_string": "def validate_title(title: str)",
                    },
                    {
                        "file_path": str(main_file),
                        "old_string": "from app.utils import validate_todo_title, generate_todo_id",
                        "new_string": "from app.utils import validate_title, generate_todo_id",
                    },
                    {
                        "file_path": str(main_file),
                        "old_string": "is_valid, error = validate_todo_title(data.title)",
                        "new_string": "is_valid, error = validate_title(data.title)",
                        "replace_all": True,
                    },
                ]
            }
        )

        assert result.success

        # Verify both files updated
        utils_content = utils_file.read_text()
        main_content = main_file.read_text()

        assert "def validate_title(title: str)" in utils_content
        assert "def validate_todo_title" not in utils_content

        assert "import validate_title" in main_content
        assert "validate_title(data.title)" in main_content

    def test_batch_edit_rollback_on_failure(
        self, e2e_project_dir: Path, batch_edit_tool: BatchEditTool
    ) -> None:
        """Test batch_edit rolls back all changes if one fails."""
        utils_file = e2e_project_dir / "app" / "utils.py"
        models_file = e2e_project_dir / "app" / "models.py"

        # Save original content for verification
        original_utils = utils_file.read_text()

        # Second edit has invalid old_string
        result = batch_edit_tool.execute(
            {
                "edits": [
                    {
                        "file_path": str(utils_file),
                        "old_string": "def generate_todo_id() -> str:",
                        "new_string": "def create_todo_id() -> str:",
                    },
                    {
                        "file_path": str(models_file),
                        "old_string": "this_does_not_exist_anywhere_in_file",
                        "new_string": "replacement",
                    },
                ]
            }
        )

        assert not result.success
        assert result.error_type == ToolErrorType.EDIT_NO_OCCURRENCE_FOUND

        # Verify first file was NOT changed (rolled back)
        current_utils = utils_file.read_text()
        assert current_utils == original_utils
        assert "def generate_todo_id() -> str:" in current_utils

    def test_batch_edit_multiple_edits_same_file(
        self, e2e_project_dir: Path, batch_edit_tool: BatchEditTool
    ) -> None:
        """Test batch_edit with multiple edits to same file."""
        main_file = e2e_project_dir / "app" / "main.py"

        result = batch_edit_tool.execute(
            {
                "edits": [
                    {
                        "file_path": str(main_file),
                        "old_string": 'title="Todo API"',
                        "new_string": 'title="My Todo API"',
                    },
                    {
                        "file_path": str(main_file),
                        "old_string": 'version="1.0.0"',
                        "new_string": 'version="2.0.0"',
                    },
                ]
            }
        )

        assert result.success

        content = main_file.read_text()
        assert 'title="My Todo API"' in content
        assert 'version="2.0.0"' in content


# =============================================================================
# IndexTracker Change Detection Tests
# =============================================================================


class TestIndexTrackerChangeDetection:
    """Tests for IndexTracker file change detection."""

    def test_tracker_initial_state_empty(
        self, e2e_project_dir: Path, index_tracker: IndexTracker
    ) -> None:
        """Test IndexTracker starts with empty state."""
        assert index_tracker.has_indexed_files() is False
        assert index_tracker.get_indexed_count() == 0

    def test_tracker_detect_added_files(
        self, e2e_project_dir: Path, index_tracker: IndexTracker
    ) -> None:
        """Test IndexTracker detects all project files as 'added' on first scan."""
        patterns = ["**/*.py"]
        excludes = ["**/tests/**", "**/__pycache__/**"]

        added, modified, deleted = index_tracker.get_changed_files(patterns, excludes)

        # Should detect app/*.py files as added
        assert len(added) >= 5  # __init__, models, database, utils, main
        assert len(modified) == 0
        assert len(deleted) == 0

        # Verify expected files are in added
        added_names = {p.name for p in added}
        assert "models.py" in added_names
        assert "database.py" in added_names
        assert "utils.py" in added_names
        assert "main.py" in added_names

    def test_tracker_update_state_tracks_files(
        self, e2e_project_dir: Path, index_tracker: IndexTracker
    ) -> None:
        """Test update_state properly tracks files with content hashes."""
        patterns = ["**/*.py"]
        excludes = ["**/tests/**", "**/__pycache__/**"]

        added, _, _ = index_tracker.get_changed_files(patterns, excludes)

        # Update state for all added files
        index_tracker.update_state(added)
        index_tracker.save()

        # Verify tracking
        assert index_tracker.has_indexed_files() is True
        assert index_tracker.get_indexed_count() == len(added)

        # Verify hashes exist
        hashes = index_tracker.get_file_hashes()
        assert len(hashes) == len(added)
        for rel_path, hash_value in hashes.items():
            assert len(hash_value) == 32  # MD5 hash length

    def test_tracker_detect_modified_after_edit(
        self, e2e_project_dir: Path, index_tracker: IndexTracker, edit_file_tool: EditFileTool
    ) -> None:
        """Test IndexTracker detects file as 'modified' after edit tool changes it."""
        patterns = ["**/*.py"]
        excludes = ["**/tests/**", "**/__pycache__/**"]

        # Initial index
        added, _, _ = index_tracker.get_changed_files(patterns, excludes)
        index_tracker.update_state(added)
        index_tracker.save()

        # Edit a file - use a string that actually exists in utils.py
        utils_file = e2e_project_dir / "app" / "utils.py"
        result = edit_file_tool.execute(
            {
                "file_path": str(utils_file),
                "old_string": "if len(title) > 200:",
                "new_string": "if len(title) > 300:",
            }
        )
        assert result.success, f"Edit failed: {result.error}"

        # Check for changes - need to reload tracker to clear cached state
        new_tracker = IndexTracker(e2e_project_dir, index_tracker.state_path)
        added2, modified, deleted = new_tracker.get_changed_files(patterns, excludes)

        assert len(added2) == 0
        assert len(modified) >= 1
        assert len(deleted) == 0

        modified_names = {p.name for p in modified}
        assert "utils.py" in modified_names

    def test_tracker_detect_deleted_file(
        self, e2e_project_dir: Path, index_tracker: IndexTracker
    ) -> None:
        """Test IndexTracker detects deleted files."""
        patterns = ["**/*.py"]
        excludes = ["**/tests/**", "**/__pycache__/**"]

        # Initial index
        added, _, _ = index_tracker.get_changed_files(patterns, excludes)
        index_tracker.update_state(added)
        index_tracker.save()

        # Delete a file
        init_file = e2e_project_dir / "app" / "__init__.py"
        init_file.unlink()

        # Check for changes
        new_tracker = IndexTracker(e2e_project_dir, index_tracker.state_path)
        added2, modified, deleted = new_tracker.get_changed_files(patterns, excludes)

        assert len(deleted) >= 1
        deleted_names = {p.name for p in deleted}
        assert "__init__.py" in deleted_names

    def test_tracker_no_changes_after_reindex(
        self, e2e_project_dir: Path, index_tracker: IndexTracker, edit_file_tool: EditFileTool
    ) -> None:
        """Test IndexTracker reports no changes after re-indexing modified files."""
        patterns = ["**/*.py"]
        excludes = ["**/tests/**", "**/__pycache__/**"]

        # Initial index
        added, _, _ = index_tracker.get_changed_files(patterns, excludes)
        index_tracker.update_state(added)
        index_tracker.save()

        # Edit a file
        utils_file = e2e_project_dir / "app" / "utils.py"
        edit_file_tool.execute(
            {
                "file_path": str(utils_file),
                "old_string": "return True, None",
                "new_string": 'return True, ""',
            }
        )

        # Update tracker state for the modified file
        new_tracker = IndexTracker(e2e_project_dir, index_tracker.state_path)
        _, modified, _ = new_tracker.get_changed_files(patterns, excludes)
        new_tracker.update_state(modified)
        new_tracker.save()

        # Now check again - should be no changes
        final_tracker = IndexTracker(e2e_project_dir, new_tracker.state_path)
        added3, modified3, deleted3 = final_tracker.get_changed_files(patterns, excludes)

        assert len(added3) == 0
        assert len(modified3) == 0
        assert len(deleted3) == 0


# =============================================================================
# E2E Workflow Tests
# =============================================================================


class TestE2EWorkflows:
    """End-to-end workflow tests combining edit tools and change detection."""

    def test_e2e_edit_triggers_reindex_cycle(
        self, e2e_project_dir: Path, index_tracker: IndexTracker, edit_file_tool: EditFileTool
    ) -> None:
        """Full E2E: edit file -> detect change -> update index -> verify no changes."""
        patterns = ["**/*.py"]
        excludes = ["**/tests/**", "**/__pycache__/**"]

        # Step 1: Initial index
        added, _, _ = index_tracker.get_changed_files(patterns, excludes)
        initial_count = len(added)
        assert initial_count >= 5

        index_tracker.update_state(added)
        index_tracker.save()

        # Step 2: Edit utils.py
        utils_file = e2e_project_dir / "app" / "utils.py"
        result = edit_file_tool.execute(
            {
                "file_path": str(utils_file),
                "old_string": "def generate_todo_id() -> str:",
                "new_string": "def create_unique_id() -> str:",
            }
        )
        assert result.success

        # Step 3: Verify IndexTracker detects the change
        tracker2 = IndexTracker(e2e_project_dir, index_tracker.state_path)
        added2, modified2, deleted2 = tracker2.get_changed_files(patterns, excludes)

        assert len(added2) == 0
        assert len(modified2) == 1
        assert len(deleted2) == 0
        assert modified2[0].name == "utils.py"

        # Step 4: Update index
        tracker2.update_state(modified2)
        tracker2.save()

        # Step 5: Verify no more changes
        tracker3 = IndexTracker(e2e_project_dir, tracker2.state_path)
        added3, modified3, deleted3 = tracker3.get_changed_files(patterns, excludes)

        assert len(added3) == 0
        assert len(modified3) == 0
        assert len(deleted3) == 0

    def test_e2e_batch_edit_triggers_multiple_file_reindex(
        self, e2e_project_dir: Path, index_tracker: IndexTracker, batch_edit_tool: BatchEditTool
    ) -> None:
        """Full E2E: batch edit multiple files -> detect all changes."""
        patterns = ["**/*.py"]
        excludes = ["**/tests/**", "**/__pycache__/**"]

        # Initial index
        added, _, _ = index_tracker.get_changed_files(patterns, excludes)
        index_tracker.update_state(added)
        index_tracker.save()

        # Batch edit both utils.py and models.py
        utils_file = e2e_project_dir / "app" / "utils.py"
        models_file = e2e_project_dir / "app" / "models.py"

        result = batch_edit_tool.execute(
            {
                "edits": [
                    {
                        "file_path": str(utils_file),
                        "old_string": '"""Utility functions for todo operations."""',
                        "new_string": '"""Helper functions for todo operations."""',
                    },
                    {
                        "file_path": str(models_file),
                        "old_string": '"""Todo data models."""',
                        "new_string": '"""Data models for todo items."""',
                    },
                ]
            }
        )
        assert result.success

        # Verify both files detected as modified
        tracker2 = IndexTracker(e2e_project_dir, index_tracker.state_path)
        added2, modified2, deleted2 = tracker2.get_changed_files(patterns, excludes)

        assert len(added2) == 0
        assert len(modified2) == 2
        assert len(deleted2) == 0

        modified_names = {p.name for p in modified2}
        assert "utils.py" in modified_names
        assert "models.py" in modified_names

    def test_e2e_new_content_indexed(
        self, e2e_project_dir: Path, index_tracker: IndexTracker, edit_file_tool: EditFileTool
    ) -> None:
        """Full E2E: add new function -> reindex -> verify hash updated."""
        patterns = ["**/*.py"]
        excludes = ["**/tests/**", "**/__pycache__/**"]

        # Initial index
        added, _, _ = index_tracker.get_changed_files(patterns, excludes)
        index_tracker.update_state(added)
        index_tracker.save()

        # Get original hash for utils.py
        original_hashes = index_tracker.get_file_hashes()
        utils_rel_path = "app/utils.py"
        original_hash = original_hashes.get(utils_rel_path)
        assert original_hash is not None

        # Add new function to utils.py using edit_file
        utils_file = e2e_project_dir / "app" / "utils.py"
        result = edit_file_tool.execute(
            {
                "file_path": str(utils_file),
                "old_string": "    return str(uuid.uuid4())[:8]",
                "new_string": '''    return str(uuid.uuid4())[:8]


def calculate_priority(todo_count: int, completed_count: int) -> float:
    """Calculate todo priority based on completion rate.

    Args:
        todo_count: Total number of todos.
        completed_count: Number of completed todos.

    Returns:
        Priority score between 0 and 1.
    """
    if todo_count == 0:
        return 0.0
    return 1.0 - (completed_count / todo_count)''',
            }
        )
        assert result.success

        # Reindex
        tracker2 = IndexTracker(e2e_project_dir, index_tracker.state_path)
        _, modified, _ = tracker2.get_changed_files(patterns, excludes)
        tracker2.update_state(modified)
        tracker2.save()

        # Verify hash changed
        new_hashes = tracker2.get_file_hashes()
        new_hash = new_hashes.get(utils_rel_path)

        assert new_hash is not None
        assert new_hash != original_hash  # Hash should be different after adding content

        # Verify content includes new function
        content = utils_file.read_text()
        assert "def calculate_priority(" in content
        assert "Priority score between 0 and 1" in content
