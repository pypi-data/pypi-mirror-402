"""Verification script for IssueDB Notepad integration."""

import shutil
import sys
from pathlib import Path

# Ensure red9 is in path
sys.path.insert(0, str(Path.cwd()))

from issuedb.repository import IssueRepository

from red9.agents.notepad import Notepad


def test_issuedb_notepad():
    print("\n--- Testing IssueDB Notepad ---")

    # Setup temp project
    test_root = Path("/tmp/red9-notepad-test")
    if test_root.exists():
        shutil.rmtree(test_root)
    test_root.mkdir(parents=True)

    # Initialize DB (Notepad does this implicitly if missing? No, assumes .red9 exists)
    red9_dir = test_root / ".red9"
    red9_dir.mkdir()

    # Create DB explicitly first to ensure it's valid
    db_path = str(red9_dir / ".issue.db")
    repo = IssueRepository(db_path=db_path)

    # Initialize Notepad
    notepad = Notepad(test_root, workflow_id="wf-123")

    # 1. Add Entry
    print("Adding memory entry...")
    notepad.add_entry("learning", "This is a test learning", "TestTask")

    # 2. Verify in DB directly
    memories = repo.list_memory(category="learning")
    if memories and "This is a test learning" in memories[0].value:
        print("✅ Entry found in IssueDB")
    else:
        print("❌ Entry NOT found in IssueDB")
        print(f"Memories found: {memories}")
        sys.exit(1)

    # 3. Verify Summary
    print("Getting summary...")
    summary = notepad.get_summary()
    print(f"Summary output:\n{summary}")

    if "INHERITED WISDOM" in summary and "This is a test learning" in summary:
        print("✅ Summary generated correctly")
    else:
        print("❌ Summary generation failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        test_issuedb_notepad()
        print("\nALL CHECKS PASSED")
    except Exception as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
