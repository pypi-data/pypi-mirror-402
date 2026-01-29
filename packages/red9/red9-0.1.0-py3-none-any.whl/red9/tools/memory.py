"""Memory tool for persistent storage using IssueDB.

Allows agents to store and recall information across sessions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from red9.logging import get_logger
from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult, get_project_root

logger = get_logger(__name__)

# Default memory categories
DEFAULT_CATEGORIES = [
    "guidelines",  # Project-specific guidelines
    "preferences",  # User preferences
    "context",  # Context about the codebase
    "lessons",  # Lessons learned from errors
]


class MemoryTool(Tool):
    """Store and recall information using IssueDB memory system.

    Operations:
    - store: Save a key-value pair with optional category
    - recall: Retrieve a value by key
    - list: List all memories, optionally filtered by category
    - delete: Remove a memory by key
    - search: Search memories by value content
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        """Initialize memory tool.

        Args:
            db_path: Path to IssueDB database. Defaults to project .red9/.issue.db
        """
        self._db_path = db_path
        self._repo = None

    @property
    def name(self) -> str:
        return "memory"

    @property
    def description(self) -> str:
        return """Store and recall persistent information.

Use this tool to:
- Save important context for future reference
- Store project guidelines and conventions
- Remember lessons learned from errors
- Track user preferences

Operations:
- store: Save key=value with optional category
- recall: Get value by key
- list: List all memories (optionally by category)
- delete: Remove a memory
- search: Search memories by content"""

    @property
    def read_only(self) -> bool:
        # Memory operations can write
        return False

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["store", "recall", "list", "delete", "search"],
                        "description": "Action to perform",
                    },
                    "key": {
                        "type": "string",
                        "description": "Memory key (required for store/recall/delete)",
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to store (required for store action)",
                    },
                    "category": {
                        "type": "string",
                        "description": (
                            f"Category for organization. Common: {', '.join(DEFAULT_CATEGORIES)}"
                        ),
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query (for search action)",
                    },
                },
                "required": ["action"],
            },
        )

    def _get_repo(self) -> Any:
        """Get or create IssueDB repository.

        Returns:
            IssueRepository instance.
        """
        if self._repo is not None:
            return self._repo

        try:
            from issuedb.repository import IssueRepository
        except ImportError:
            raise RuntimeError("IssueDB is not installed. Run: pip install issuedb")

        # Determine database path
        if self._db_path:
            db_path = Path(self._db_path)
        else:
            project_root = get_project_root()
            db_path = project_root / ".red9" / ".issue.db"

        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._repo = IssueRepository(db_path=str(db_path))
        return self._repo

    def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute memory operation.

        Args:
            params: Tool parameters.

        Returns:
            ToolResult with operation result.
        """
        action = params.get("action", "")
        key = params.get("key", "")
        value = params.get("value", "")
        category = params.get("category", "")
        query = params.get("query", "")

        if not action:
            return ToolResult.fail(
                "action is required",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        try:
            repo = self._get_repo()
        except RuntimeError as e:
            return ToolResult.fail(str(e), error_type=ToolErrorType.NOT_INITIALIZED)
        except Exception as e:
            return ToolResult.fail(
                f"Failed to initialize memory storage: {e}",
                error_type=ToolErrorType.EXECUTION_ERROR,
            )

        try:
            if action == "store":
                return self._store(repo, key, value, category)
            elif action == "recall":
                return self._recall(repo, key)
            elif action == "list":
                return self._list(repo, category)
            elif action == "delete":
                return self._delete(repo, key)
            elif action == "search":
                return self._search(repo, query)
            else:
                return ToolResult.fail(
                    f"Unknown action: {action}",
                    error_type=ToolErrorType.INVALID_PARAMS,
                )
        except Exception as e:
            logger.error(f"Memory operation failed: {e}")
            return ToolResult.fail(
                f"Memory operation failed: {e}",
                error_type=ToolErrorType.EXECUTION_ERROR,
            )

    def _store(self, repo: Any, key: str, value: str, category: str) -> ToolResult:
        """Store a memory.

        Args:
            repo: IssueRepository instance.
            key: Memory key.
            value: Memory value.
            category: Optional category.

        Returns:
            ToolResult.
        """
        if not key:
            return ToolResult.fail(
                "key is required for store action",
                error_type=ToolErrorType.INVALID_PARAMS,
            )
        if not value:
            return ToolResult.fail(
                "value is required for store action",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        repo.store_memory(key=key, value=value, category=category or None)
        logger.info(f"Stored memory: {key} (category: {category or 'none'})")

        return ToolResult.ok(
            {
                "stored": True,
                "key": key,
                "category": category or None,
            }
        )

    def _recall(self, repo: Any, key: str) -> ToolResult:
        """Recall a memory.

        Args:
            repo: IssueRepository instance.
            key: Memory key.

        Returns:
            ToolResult.
        """
        if not key:
            return ToolResult.fail(
                "key is required for recall action",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        memory = repo.get_memory(key=key)
        if memory is None:
            return ToolResult.ok(
                {
                    "found": False,
                    "key": key,
                    "value": None,
                }
            )

        return ToolResult.ok(
            {
                "found": True,
                "key": memory.key,
                "value": memory.value,
                "category": memory.category,
            }
        )

    def _list(self, repo: Any, category: str) -> ToolResult:
        """List memories.

        Args:
            repo: IssueRepository instance.
            category: Optional category filter.

        Returns:
            ToolResult.
        """
        memories = repo.list_memory(category=category or None)

        items = []
        for mem in memories:
            items.append(
                {
                    "key": mem.key,
                    "value": mem.value[:100] + "..." if len(mem.value) > 100 else mem.value,
                    "category": mem.category,
                }
            )

        return ToolResult.ok(
            {
                "count": len(items),
                "category_filter": category or None,
                "memories": items,
            }
        )

    def _delete(self, repo: Any, key: str) -> ToolResult:
        """Delete a memory.

        Args:
            repo: IssueRepository instance.
            key: Memory key.

        Returns:
            ToolResult.
        """
        if not key:
            return ToolResult.fail(
                "key is required for delete action",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        # Check if exists first
        memory = repo.get_memory(key=key)
        if memory is None:
            return ToolResult.ok(
                {
                    "deleted": False,
                    "key": key,
                    "reason": "Memory not found",
                }
            )

        repo.delete_memory(key=key)
        logger.info(f"Deleted memory: {key}")

        return ToolResult.ok(
            {
                "deleted": True,
                "key": key,
            }
        )

    def _search(self, repo: Any, query: str) -> ToolResult:
        """Search memories by content.

        Args:
            repo: IssueRepository instance.
            query: Search query.

        Returns:
            ToolResult.
        """
        if not query:
            return ToolResult.fail(
                "query is required for search action",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        # Get all memories and filter by query
        all_memories = repo.list_memory()
        query_lower = query.lower()

        matches = []
        for mem in all_memories:
            if query_lower in mem.key.lower() or query_lower in mem.value.lower():
                matches.append(
                    {
                        "key": mem.key,
                        "value": mem.value[:200] + "..." if len(mem.value) > 200 else mem.value,
                        "category": mem.category,
                    }
                )

        return ToolResult.ok(
            {
                "query": query,
                "count": len(matches),
                "matches": matches,
            }
        )
