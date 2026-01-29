"""Curated examples for agent prompts.

Provides concrete tool calling examples that help agents understand
proper usage patterns, error recovery, and best practices.
"""

from __future__ import annotations

# ============================================================================
# TOOL CALLING EXAMPLES
# ============================================================================

READ_FILE_EXAMPLES = """
### read_file Examples

**Read a file to understand its structure:**
```json
{"name": "read_file", "arguments": {"file_path": "src/auth/login.py"}}
```

**Read specific lines (for large files):**
```json
{
  "name": "read_file",
  "arguments": {"file_path": "src/models.py", "start_line": 100, "end_line": 150}
}
```
"""

EDIT_FILE_EXAMPLES = """
### edit_file Examples

**Replace a single function:**
```json
{
  "name": "edit_file",
  "arguments": {
    "file_path": "src/utils.py",
    "old_string": "def calculate_total(items):\\n    return sum(items)",
    "new_string": "def calculate_total(items: list[int]) -> int:\\n    return sum(items)"
  }
}
```

**Add an import at the top:**
```json
{
  "name": "edit_file",
  "arguments": {
    "file_path": "src/main.py",
    "old_string": "from pathlib import Path",
    "new_string": "from pathlib import Path\\nfrom typing import Optional"
  }
}
```

**Replace all occurrences:**
```json
{
  "name": "edit_file",
  "arguments": {
    "file_path": "src/config.py",
    "old_string": "DEBUG = True",
    "new_string": "DEBUG = False",
    "replace_all": true
  }
}
```
"""

GREP_EXAMPLES = """
### grep Examples

**Find all usages of a function:**
```json
{"name": "grep", "arguments": {"pattern": "calculate_total\\\\(", "path": "src/"}}
```

**Search in specific file types:**
```json
{"name": "grep", "arguments": {"pattern": "import\\\\s+requests", "file_pattern": "*.py"}}
```

**Case-insensitive search:**
```json
{"name": "grep", "arguments": {"pattern": "todo|fixme", "case_sensitive": false}}
```
"""

SHELL_EXAMPLES = """
### shell Examples

**Run tests:**
```json
{"name": "shell", "arguments": {"command": "pytest -v tests/"}}
```

**Run linting:**
```json
{"name": "shell", "arguments": {"command": "ruff check src/"}}
```

**Check types:**
```json
{"name": "shell", "arguments": {"command": "mypy src/ --strict"}}
```
"""

COMPLETE_TASK_EXAMPLES = """
### complete_task Examples

**Successful completion with file modifications:**
```json
{
  "name": "complete_task",
  "arguments": {
    "summary": "Implemented user authentication with JWT tokens",
    "files_modified": ["src/auth/jwt.py", "src/routes/login.py", "tests/test_auth.py"],
    "outputs": {"feature": "jwt_auth", "tests_added": 5}
  }
}
```

**Completion with test results:**
```json
{
  "name": "complete_task",
  "arguments": {
    "summary": "All tests passed - 15 tests run, 0 failures",
    "outputs": {"tests_passed": true, "test_count": 15, "failures": 0}
  }
}
```
"""

# ============================================================================
# ERROR RECOVERY PATTERNS
# ============================================================================

ERROR_RECOVERY_GUIDE = """
## Common Errors and Recovery

### edit_file: "old_string not found"
**Cause**: The text you're trying to match doesn't exist exactly as specified.
**Recovery**:
1. Re-read the file with `read_file` to see current content
2. Copy the exact text including whitespace
3. Check for tabs vs spaces, trailing whitespace
4. The tool supports fuzzy matching for minor whitespace differences

### edit_file: "multiple occurrences"
**Cause**: The old_string appears more than once in the file.
**Recovery**:
1. Add more context (surrounding lines) to make the match unique
2. Use `replace_all: true` if you want to change all occurrences
3. Read the file to understand where duplicates are

### grep: No results found
**Cause**: Pattern doesn't match or search path is wrong.
**Recovery**:
1. Check regex syntax (escape special characters)
2. Try a simpler pattern first
3. Use `glob` to verify files exist in the path
4. Try case-insensitive search

### shell: Command failed
**Cause**: Command returned non-zero exit code.
**Recovery**:
1. Check the error output for details
2. Verify dependencies are installed
3. Check working directory context
4. Try running simpler commands first

### read_file: File not found
**Cause**: File doesn't exist at specified path.
**Recovery**:
1. Use `glob` to find similar files
2. Check for typos in the path
3. Verify the file exists in the project
"""

# ============================================================================
# OUTPUT FORMAT SPECIFICATIONS
# ============================================================================

PLAN_OUTPUT_FORMAT = """
## Plan Output Format

When completing your planning task, structure your output as:

```markdown
# Implementation Plan

## Files to Modify
- `path/to/file.py` - Description of changes

## Files to Create
- `path/to/new_file.py` - Description and purpose

## Implementation Steps
1. First step with details
2. Second step with details
...

## Test Requirements
- Test cases to add
- How to verify the changes

## Risks and Considerations
- Potential issues
- Edge cases to handle
```
"""

CODE_OUTPUT_FORMAT = """
## Code Implementation Output

When completing code implementation, report:

1. **Files modified** with brief description of changes
2. **New files created** with their purpose
3. **Tests updated** if any
4. **Verification** - any commands run to verify changes

Example completion:
```
Implemented JWT authentication:
- Modified src/auth/jwt.py: Added token generation and validation
- Created src/auth/middleware.py: New authentication middleware
- Updated tests/test_auth.py: Added 5 new test cases
- Ran: ruff check src/ - no errors
```
"""

TEST_OUTPUT_FORMAT = """
## Test Results Output

When reporting test results, include:

```json
{
  "tests_passed": true,
  "summary": "15 tests run, 15 passed, 0 failed",
  "test_count": 15,
  "passed": 15,
  "failed": 0,
  "skipped": 0,
  "failures": []
}
```

For failures, include details:
```json
{
  "tests_passed": false,
  "summary": "15 tests run, 13 passed, 2 failed",
  "failures": [
    {
      "test": "test_user_login",
      "file": "tests/test_auth.py",
      "error": "AssertionError: expected 200, got 401"
    }
  ]
}
```
"""

# ============================================================================
# COMBINED EXAMPLES BY AGENT TYPE
# ============================================================================


def get_examples_for_agent(agent_type: str) -> str:
    """Get relevant examples for an agent type.

    Args:
        agent_type: Type of agent (plan, code, test, etc.).

    Returns:
        Combined examples string.
    """
    common = f"{READ_FILE_EXAMPLES}\n{GREP_EXAMPLES}"

    if agent_type == "plan":
        return f"{common}\n{COMPLETE_TASK_EXAMPLES}\n{ERROR_RECOVERY_GUIDE}\n{PLAN_OUTPUT_FORMAT}"

    elif agent_type == "code":
        return (
            f"{common}\n{EDIT_FILE_EXAMPLES}\n{SHELL_EXAMPLES}"
            f"\n{COMPLETE_TASK_EXAMPLES}\n{ERROR_RECOVERY_GUIDE}\n{CODE_OUTPUT_FORMAT}"
        )

    elif agent_type in ("test", "test_run"):
        return (
            f"{common}\n{SHELL_EXAMPLES}\n{COMPLETE_TASK_EXAMPLES}"
            f"\n{ERROR_RECOVERY_GUIDE}\n{TEST_OUTPUT_FORMAT}"
        )

    elif agent_type == "test_write":
        return f"{common}\n{EDIT_FILE_EXAMPLES}\n{COMPLETE_TASK_EXAMPLES}\n{ERROR_RECOVERY_GUIDE}"

    elif agent_type == "fix":
        return (
            f"{common}\n{EDIT_FILE_EXAMPLES}\n{SHELL_EXAMPLES}"
            f"\n{COMPLETE_TASK_EXAMPLES}\n{ERROR_RECOVERY_GUIDE}"
        )

    else:
        return f"{common}\n{COMPLETE_TASK_EXAMPLES}\n{ERROR_RECOVERY_GUIDE}"
