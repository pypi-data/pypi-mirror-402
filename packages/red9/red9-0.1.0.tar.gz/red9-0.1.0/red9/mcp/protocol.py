"""Model Context Protocol (MCP) type definitions and schemas."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


class JsonRpcRequest(TypedDict):
    jsonrpc: Literal["2.0"]
    method: str
    params: dict[str, Any] | None
    id: int | str | None


class JsonRpcResponse(TypedDict):
    jsonrpc: Literal["2.0"]
    result: Any | None
    error: dict[str, Any] | None
    id: int | str | None


class MCPTool(TypedDict):
    name: str
    description: str
    inputSchema: dict[str, Any]


class MCPListToolsResult(TypedDict):
    tools: list[MCPTool]


class MCPCallToolResult(TypedDict):
    content: list[dict[str, Any]]
    isError: bool | None
