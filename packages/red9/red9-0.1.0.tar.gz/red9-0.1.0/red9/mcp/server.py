"MCP Server implementation exposing Red9 tools."

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any

from red9.core.session import Red9Session
from red9.mcp.protocol import (
    JsonRpcRequest,
    JsonRpcResponse,
    MCPCallToolResult,
    MCPListToolsResult,
    MCPTool,
)

logger = logging.getLogger(__name__)


class MCPServer:
    """Model Context Protocol Server for Red9.

    Exposes Red9's internal tools to external MCP clients (like IDEs or other agents).
    Operates over stdio by default.
    """

    def __init__(self, session: Red9Session) -> None:
        """Initialize MCP Server.

        Args:
            session: Active Red9 session containing tools to expose.
        """
        self.session = session
        # Ensure infrastructure is ready to get tools
        if not self.session.tool_registry:
            self.session._prepare_infrastructure()

    async def run_stdio(self) -> None:
        """Run the server loop over stdin/stdout."""
        logger.info("Starting MCP Server on stdio...")

        # Disable other logging to stdout to avoid corrupting JSON-RPC
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                root_logger.removeHandler(handler)

        # Add file handler for debugging if needed, or stderr
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        root_logger.addHandler(stderr_handler)

        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break

                request = json.loads(line)
                response = await self.handle_request(request)

                if response:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()

            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
            except Exception as e:
                logger.error(f"MCP Server Error: {e}")

    async def handle_request(self, request: JsonRpcRequest) -> JsonRpcResponse | None:
        """Handle incoming JSON-RPC request."""
        method = request.get("method")
        msg_id = request.get("id")
        params = request.get("params", {})

        result: Any = None
        error: dict[str, Any] | None = None

        try:
            if method == "tools/list":
                result = self._list_tools()
            elif method == "tools/call":
                result = await self._call_tool(params)
            elif method == "initialize":
                result = {
                    "protocolVersion": "0.1.0",
                    "serverInfo": {"name": "red9-mcp", "version": "0.1.0"},
                    "capabilities": {"tools": {}},
                }
            elif method == "notifications/initialized":
                # No response needed for notifications
                return None
            else:
                error = {"code": -32601, "message": "Method not found"}

        except Exception as e:
            logger.exception(f"Error handling method {method}")
            error = {"code": -32603, "message": str(e)}

        return {
            "jsonrpc": "2.0",
            "result": result,
            "error": error,
            "id": msg_id,
        }

    def _list_tools(self) -> MCPListToolsResult:
        """List available tools in MCP format."""
        if not self.session.tool_registry:
            return {"tools": []}

        tools: list[MCPTool] = []
        for tool in self.session.tool_registry.get_all():
            definition = tool.get_definition()
            tools.append(
                {
                    "name": definition.name,
                    "description": definition.description,
                    "inputSchema": definition.parameters,
                }
            )
        return {"tools": tools}

    async def _call_tool(self, params: dict[str, Any] | None) -> MCPCallToolResult:
        """Execute a tool via the registry."""
        if not params or "name" not in params or not self.session.tool_registry:
            raise ValueError("Invalid parameters or registry not initialized")

        name = params["name"]
        arguments = params.get("arguments", {})

        logger.info(f"MCP executing tool: {name}")

        # Tools in red9 are synchronous, but we wrap them for async handling
        result = await asyncio.get_event_loop().run_in_executor(
            None, self.session.tool_registry.execute, name, arguments
        )

        if not result.success:
            return {
                "content": [{"type": "text", "text": result.error or "Unknown error"}],
                "isError": True,
            }

        # Format output
        text_content = ""
        if isinstance(result.output, dict):
            text_content = json.dumps(result.output, indent=2)
        else:
            text_content = str(result.output)

        return {
            "content": [{"type": "text", "text": text_content}],
            "isError": False,
        }
