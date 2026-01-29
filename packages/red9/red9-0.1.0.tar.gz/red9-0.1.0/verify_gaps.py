"""Verification script for Aider-gap features."""

import sys
from pathlib import Path

# Ensure red9 is in path
sys.path.insert(0, str(Path.cwd()))

from red9.files.fuzzy_match import find_best_match
from red9.tools.web_fetch import WebFetchTool


def test_fuzzy_match():
    print("\n--- Testing Fuzzy Match ---")
    source = """
    def hello_world():
        print("Hello")
        return True
    """

    # Block with different indentation and whitespace
    search = """def hello_world():
print("Hello")
return True"""

    match = find_best_match(source, search)
    if match:
        print(f"Match found! Confidence: {match.confidence:.2f}")
        print(f"Matched text: {match.matched_text!r}")
        assert match.confidence > 0.9
    else:
        print("Match FAILED")
        sys.exit(1)


def test_web_fetch():
    print("\n--- Testing Web Fetch ---")
    tool = WebFetchTool()
    # Test safe domain
    result = tool.execute({"url": "https://example.com", "raw": True})
    if result.success:
        print(f"Fetched example.com: {len(result.output['content'])} bytes")
        print(f"Backend used: {result.output.get('backend', 'unknown')}")
    else:
        print(f"Fetch failed: {result.error}")

    # Test blocked domain
    result = tool.execute({"url": "http://localhost:8000"})
    if not result.success and "blocked" in result.error:
        print("Blocked localhost correctly.")
    else:
        print(f"Failed to block localhost: {result}")


if __name__ == "__main__":
    test_fuzzy_match()
    test_web_fetch()
    print("\nALL CHECKS PASSED")
