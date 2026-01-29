"""Write file tool implementation."""

from __future__ import annotations

import base64
import re
from typing import Any

from red9.files.diff import generate_unified_diff
from red9.files.lock import FileLockTimeoutError, get_file_manager
from red9.logging import get_logger
from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult, validate_path

logger = get_logger(__name__)

# Secret detection patterns
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "API key assignment",
        re.compile(r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}"),
    ),
    (
        "Secret assignment",
        re.compile(r"(?i)(secret|password|passwd|pwd)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    ),
    (
        "Token assignment",
        re.compile(r"(?i)(token|auth_token|access_token)\s*[:=]\s*['\"]?[\w\-]{16,}"),
    ),
    ("Private key", re.compile(r"-----BEGIN [A-Z]+ PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"ghp_[a-zA-Z0-9]{36}")),
    ("GitHub OAuth", re.compile(r"gho_[a-zA-Z0-9]{36}")),
    ("OpenAI key", re.compile(r"sk-[a-zA-Z0-9]{48}")),
    ("AWS key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Anthropic key", re.compile(r"sk-ant-[a-zA-Z0-9\-]{40,}")),
    (
        "Generic credential",
        re.compile(r"(?i)credential[s]?\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    ),
]


def _detect_secrets(content: str) -> list[str]:
    """Detect potential secrets in content.

    Args:
        content: Content to scan for secrets.

    Returns:
        List of detected secret descriptions.
    """
    findings: list[str] = []

    # Check raw content
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(content):
            findings.append(f"{name} detected")

    # Check for base64-encoded secrets
    # Look for long base64 strings that might contain encoded secrets
    b64_pattern = re.compile(r"[A-Za-z0-9+/=]{40,}")
    for match in b64_pattern.finditer(content):
        try:
            # Try to decode and check for secrets
            decoded = base64.b64decode(match.group()).decode("utf-8", errors="ignore")
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(decoded):
                    findings.append(f"Base64-encoded {name.lower()}")
                    break
        except Exception:
            # Not valid base64 or not decodable - skip
            pass

    return findings


class WriteFileTool(Tool):
    """Write content to a file (creates or overwrites)."""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return """Write content to a file, creating it if it doesn't exist.
If the file exists, it will be overwritten.
Parent directories are created automatically.
Prefer edit_file for targeted changes to existing files."""

    @property
    def read_only(self) -> bool:
        return False

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                },
                "required": ["file_path", "content"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        raw_path = params.get("file_path", "")
        content = params.get("content", "")

        if not raw_path:
            return ToolResult.fail(
                "file_path is required",
                error_type=ToolErrorType.INVALID_PARAMS,
            )

        # Validate path for security (don't require existence for new files)
        file_path, error = validate_path(raw_path, must_exist=False)
        if error:
            return ToolResult.fail(error, error_type=ToolErrorType.PERMISSION_DENIED)

        # Check for potential secrets in content
        secrets_found = _detect_secrets(content)
        if secrets_found:
            secrets_list = ", ".join(secrets_found[:3])
            if len(secrets_found) > 3:
                secrets_list += f" (+{len(secrets_found) - 3} more)"
            logger.warning(f"Potential secrets detected in {raw_path}: {secrets_list}")
            return ToolResult.fail(
                f"Security warning: Potential secrets detected ({secrets_list}). "
                f"Secrets should not be written to source files. "
                f"Use environment variables or a secrets manager instead.",
                error_type=ToolErrorType.SECURITY_VIOLATION,
            )

        try:
            # Acquire file lock for thread-safe writing
            file_manager = get_file_manager()

            with file_manager.locked(file_path, timeout=30.0):
                # Read original content for diff (if exists)
                original_content = ""
                is_new_file = True

                if file_path.exists():
                    try:
                        original_content = file_path.read_text()
                        is_new_file = False
                    except Exception:
                        pass

                # Generate diff
                diff = generate_unified_diff(original_content, content, str(file_path))

                # Validate syntax for Python files BEFORE writing
                if file_path.suffix == ".py":
                    import ast

                    try:
                        ast.parse(content, filename=str(file_path))
                    except SyntaxError as e:
                        # Reject the write - don't create files with invalid syntax
                        logger.warning(
                            f"Write rejected: invalid Python syntax at line {e.lineno}: {e.msg}"
                        )
                        return ToolResult.fail(
                            f"Write rejected: invalid Python syntax at "
                            f"line {e.lineno}: {e.msg}. "
                            f"Please fix your code before writing.",
                            error_type=ToolErrorType.EDIT_VALIDATION_FAILED,
                        )

                # Create parent directories
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                file_path.write_text(content)

                return ToolResult.ok(
                    {
                        "file_path": str(file_path),
                        "bytes_written": len(content),
                        "is_new_file": is_new_file,
                        "lines_written": len(content.splitlines()),
                    },
                    diff=diff,
                )

        except FileLockTimeoutError as e:
            return ToolResult.fail(
                f"Could not acquire file lock: {e}",
                error_type=ToolErrorType.FILE_WRITE_FAILURE,
            )
        except PermissionError:
            return ToolResult.fail(
                f"Permission denied: {file_path}",
                error_type=ToolErrorType.PERMISSION_DENIED,
            )
        except OSError as e:
            if "No space left" in str(e):
                return ToolResult.fail(
                    f"No space left on device: {file_path}",
                    error_type=ToolErrorType.NO_SPACE_LEFT,
                )
            return ToolResult.fail(
                f"Failed to write file: {e}",
                error_type=ToolErrorType.FILE_WRITE_FAILURE,
            )
        except Exception as e:
            return ToolResult.fail(
                f"Failed to write file: {e}",
                error_type=ToolErrorType.FILE_WRITE_FAILURE,
            )
