"""Semantic search tool using RAG."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult

if TYPE_CHECKING:
    pass  # Future: import RAGAssistant when type stubs available


class RAGAssistantProtocol(Protocol):
    """Protocol for RAG assistant to enable proper type checking."""

    def retrieve(self, query: str, top_k: int = 5) -> list[tuple[Any, float]]:
        """Retrieve relevant chunks for a query."""
        ...

    def get_context(self, query: str, top_k: int = 5) -> str:
        """Get formatted context for a query."""
        ...


# Validation constants
MIN_TOP_K = 1
MAX_TOP_K = 100
DEFAULT_TOP_K = 5


class SemanticSearchTool(Tool):
    """Search codebase using semantic similarity (RAG)."""

    def __init__(self, assistant: RAGAssistantProtocol | None = None) -> None:
        """Initialize with optional RAG assistant.

        Args:
            assistant: Ragit RAGAssistant instance implementing RAGAssistantProtocol.
        """
        self._assistant: RAGAssistantProtocol | None = assistant

    @property
    def name(self) -> str:
        return "semantic_search"

    @property
    def description(self) -> str:
        return """Search codebase using semantic similarity.
Finds code relevant to natural language queries.
Returns relevant code chunks with similarity scores."""

    @property
    def read_only(self) -> bool:
        return True

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query about the code",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                    },
                },
                "required": ["query"],
            },
        )

    def set_assistant(self, assistant: RAGAssistantProtocol | None) -> None:
        """Set the RAG assistant.

        Args:
            assistant: Ragit RAGAssistant instance implementing RAGAssistantProtocol.
        """
        self._assistant = assistant

    def execute(self, params: dict[str, Any]) -> ToolResult:
        query = params.get("query", "")
        raw_top_k = params.get("top_k", DEFAULT_TOP_K)

        # Validate query
        if not query:
            return ToolResult.fail(
                "query is required",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        if not isinstance(query, str):
            return ToolResult.fail(
                "query must be a string",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        # Validate and clamp top_k
        try:
            top_k = int(raw_top_k)
        except (TypeError, ValueError):
            return ToolResult.fail(
                f"top_k must be an integer, got {type(raw_top_k).__name__}",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        if top_k < MIN_TOP_K:
            top_k = MIN_TOP_K
        elif top_k > MAX_TOP_K:
            top_k = MAX_TOP_K

        # Check assistant availability
        if not self._assistant:
            return ToolResult.fail(
                "Semantic search unavailable. Project may be empty or not indexed.",
                error_type=ToolErrorType.NOT_INITIALIZED,
            )

        try:
            # Use Ragit to retrieve relevant chunks
            results = self._assistant.retrieve(query, top_k=top_k)

            # Format results
            formatted_results = []
            for chunk, score in results:
                formatted_results.append(
                    {
                        "content": chunk.content[:500],  # Truncate long content
                        "doc_id": chunk.doc_id,
                        "chunk_index": chunk.chunk_index,
                        "similarity": round(score, 4),
                    }
                )

            # Also get formatted context
            context = self._assistant.get_context(query, top_k=top_k)

            return ToolResult.ok(
                {
                    "results": formatted_results,
                    "total_results": len(formatted_results),
                    "context": context,
                    "query": query,
                }
            )

        except ConnectionError as e:
            return ToolResult.fail(
                f"Connection error during semantic search: {e}",
                error_type=ToolErrorType.NETWORK_ERROR,
            )
        except TimeoutError as e:
            return ToolResult.fail(
                f"Timeout during semantic search: {e}",
                error_type=ToolErrorType.TIMEOUT,
            )
        except ValueError as e:
            return ToolResult.fail(
                f"Invalid value during semantic search: {e}",
                error_type=ToolErrorType.INVALID_PARAMS,
            )
        except Exception as e:
            # Log the error type for debugging
            error_type_name = type(e).__name__
            return ToolResult.fail(
                f"Semantic search failed ({error_type_name}): {e}",
                error_type=ToolErrorType.EXECUTION_ERROR,
            )
