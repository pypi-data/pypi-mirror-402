"""Red9 server entry point (headless)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from red9.core.session import Red9Session
from red9.mcp.server import MCPServer


async def run_server(project_root: str = ".") -> None:
    """Run the Red9 MCP Server."""
    root_path = Path(project_root).resolve()

    # Initialize session
    session = Red9Session(root_path)
    if not session.config:
        # Auto-initialize with defaults if not present
        session.initialize_project()

    # Start MCP server
    server = MCPServer(session)
    await server.run_stdio()


def main() -> None:
    """Entry point for python -m red9.server."""
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    asyncio.run(run_server(root))


if __name__ == "__main__":
    main()
