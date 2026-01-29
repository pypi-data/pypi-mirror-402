"""Verify MCP Server."""

import json
import subprocess
import sys
from pathlib import Path

# Create a temporary project for testing
PROJECT_DIR = Path("/tmp/red9-mcp-test")
PROJECT_DIR.mkdir(parents=True, exist_ok=True)


def test_mcp_capabilities():
    """Test MCP server capabilities via stdin/stdout."""

    # Start the server process
    process = subprocess.Popen(
        [sys.executable, "-m", "red9.server", str(PROJECT_DIR)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        bufsize=0,  # Unbuffered
    )

    # 1. Send Initialize Request
    init_request = {"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {}}

    print(f"Sending: {json.dumps(init_request)}")
    process.stdin.write(json.dumps(init_request) + "\n")
    process.stdin.flush()

    response_line = process.stdout.readline()
    print(f"Received: {response_line}")
    response = json.loads(response_line)

    assert response["id"] == 1
    assert "serverInfo" in response["result"]
    assert response["result"]["serverInfo"]["name"] == "red9-mcp"

    # 2. List Tools
    list_request = {"jsonrpc": "2.0", "method": "tools/list", "id": 2, "params": {}}

    print(f"Sending: {json.dumps(list_request)}")
    process.stdin.write(json.dumps(list_request) + "\n")
    process.stdin.flush()

    response_line = process.stdout.readline()
    print(f"Received: {response_line}")
    response = json.loads(response_line)

    assert response["id"] == 2
    tools = response["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    print(f"Available tools: {tool_names}")

    assert "read_file" in tool_names
    assert "run_command" in tool_names

    # Terminate
    process.terminate()
    print("MCP Server verification PASSED")


if __name__ == "__main__":
    test_mcp_capabilities()
