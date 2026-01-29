"""Web fetch tool with optional Playwright support.

Fetches web content with automatic retry, timeout handling, and
HTML-to-markdown conversion. Falls back to Stabilize's HTTPTask if
Playwright is unavailable.
"""

from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import urlparse

from stabilize import HTTPTask, StageExecution

from red9.logging import get_logger
from red9.tools.base import Tool, ToolDefinition, ToolErrorType, ToolResult

logger = get_logger(__name__)

# Security: URL allowlist patterns (can be configured)
DEFAULT_ALLOWED_DOMAINS: set[str] = set()  # Empty = allow all
BLOCKED_DOMAINS: set[str] = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "169.254.169.254",  # AWS metadata
    "metadata.google.internal",  # GCP metadata
}

# Limits
MAX_RESPONSE_SIZE = 1_000_000  # 1MB
DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 120


class WebFetchTool(Tool):
    """Fetch web content using Playwright or Stabilize's HTTPTask."""

    def __init__(
        self,
        allowed_domains: set[str] | None = None,
        blocked_domains: set[str] | None = None,
    ) -> None:
        """Initialize web fetch tool.

        Args:
            allowed_domains: If set, only these domains are allowed.
            blocked_domains: Domains to block (merged with defaults).
        """
        self._allowed_domains = allowed_domains or DEFAULT_ALLOWED_DOMAINS
        self._blocked_domains = (blocked_domains or set()) | BLOCKED_DOMAINS
        self._playwright_available = self._check_playwright()

    def _check_playwright(self) -> bool:
        """Check if playwright is installed and available."""
        try:
            import playwright  # noqa: F401
            from playwright.sync_api import sync_playwright  # noqa: F401

            return True
        except ImportError:
            return False

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        backend = "Playwright" if self._playwright_available else "HTTP"
        return f"""Fetch content from a URL using {backend}.

Returns the page content converted to markdown for easy reading.
Supports automatic retry on transient failures.

Use this tool to:
- Read documentation from URLs
- Fetch API responses
- Get content from web pages

Note: Some domains may be blocked for security."""

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
                    "url": {
                        "type": "string",
                        "description": "URL to fetch (must be http:// or https://)",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": (
                            f"Timeout in seconds (default: {DEFAULT_TIMEOUT}, max: {MAX_TIMEOUT})"
                        ),
                        "default": DEFAULT_TIMEOUT,
                    },
                    "include_headers": {
                        "type": "boolean",
                        "description": "Include response headers in output",
                        "default": False,
                    },
                    "raw": {
                        "type": "boolean",
                        "description": "Return raw content without markdown conversion",
                        "default": False,
                    },
                    "use_browser": {
                        "type": "boolean",
                        "description": "Force use of browser (Playwright) if available",
                        "default": False,
                    },
                },
                "required": ["url"],
            },
        )

    def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute web fetch.

        Args:
            params: Tool parameters.

        Returns:
            ToolResult with fetched content.
        """
        url = params.get("url", "")
        timeout = min(params.get("timeout", DEFAULT_TIMEOUT), MAX_TIMEOUT)
        include_headers = params.get("include_headers", False)
        raw = params.get("raw", False)
        use_browser = params.get("use_browser", False)

        # Validate URL
        validation_error = self._validate_url(url)
        if validation_error:
            return ToolResult.fail(validation_error, error_type=ToolErrorType.INVALID_PARAMS)

        # Use Playwright if requested or if it's the default and available
        if (use_browser or self._playwright_available) and self._playwright_available:
            try:
                return self._fetch_with_playwright(url, timeout, raw)
            except Exception as e:
                logger.warning(f"Playwright failed: {e}. Falling back to HTTP.")
                # Fallthrough to HTTP

        # Fallback to Stabilize HTTPTask
        return self._fetch_with_http(url, timeout, include_headers, raw)

    def _fetch_with_playwright(self, url: str, timeout: int, raw: bool) -> ToolResult:
        """Fetch URL using Playwright."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
                content = page.content()

                if raw:
                    result = content
                else:
                    # Use readability/markdown conversion on the rendered HTML
                    result = self._html_to_markdown(content)

                return ToolResult.ok({"url": url, "content": result, "backend": "playwright"})
            finally:
                browser.close()

    def _fetch_with_http(
        self, url: str, timeout: int, include_headers: bool, raw: bool
    ) -> ToolResult:
        """Fetch using Stabilize HTTPTask."""
        # Create StageExecution for HTTPTask
        stage = StageExecution(
            ref_id="web_fetch",
            type="http",
            name="Web Fetch",
            context={
                "url": url,
                "method": "GET",
                "timeout": timeout,
                "retries": 2,
                "retry_delay": 1.0,
                "retry_on_status": [502, 503, 504, 429],
                "max_response_size": MAX_RESPONSE_SIZE,
                "verify_ssl": True,
            },
        )

        # Execute HTTPTask
        http_task = HTTPTask()
        try:
            result = http_task.execute(stage)
        except Exception as e:
            logger.error(f"HTTPTask execution failed: {e}")
            return ToolResult.fail(
                f"Failed to fetch URL: {e}",
                error_type=ToolErrorType.NETWORK_ERROR,
            )

        # Check result status
        # Note: stabilize TaskResult.status is an Enum
        if result.status.name != "SUCCEEDED":
            error_msg = result.error or "Request failed"
            return ToolResult.fail(
                f"HTTP request failed: {error_msg}",
                error_type=ToolErrorType.NETWORK_ERROR,
            )

        outputs = result.outputs or {}
        status_code = outputs.get("status_code", 0)
        body = outputs.get("body", "")
        content_type = outputs.get("content_type", "")
        headers = outputs.get("headers", {})

        # Check status code
        if status_code >= 400:
            return ToolResult.fail(
                f"HTTP {status_code}: {body[:200] if body else 'No response body'}",
                error_type=ToolErrorType.NETWORK_ERROR,
            )

        # Convert content based on type
        if raw:
            content = body
        elif "html" in content_type.lower():
            content = self._html_to_markdown(body)
        elif "json" in content_type.lower():
            content = f"```json\n{body}\n```"
        else:
            content = body

        # Truncate if too long
        if len(content) > 50000:
            content = content[:50000] + "\n\n... [truncated, content too long]"

        result_output: dict[str, Any] = {
            "url": url,
            "status_code": status_code,
            "content_type": content_type,
            "content_length": len(body),
            "content": content,
            "backend": "http",
        }

        if include_headers:
            result_output["headers"] = headers

        return ToolResult.ok(result_output)

    def _validate_url(self, url: str) -> str | None:
        """Validate URL for security.

        Args:
            url: URL to validate.

        Returns:
            Error message if invalid, None if valid.
        """
        if not url:
            return "URL is required"

        try:
            parsed = urlparse(url)
        except Exception:
            return "Invalid URL format"

        # Check scheme
        if parsed.scheme not in ("http", "https"):
            return "URL must use http:// or https://"

        # Check hostname
        hostname = parsed.hostname
        if not hostname:
            return "URL must have a hostname"

        # Check blocked domains
        hostname_lower = hostname.lower()
        for blocked in self._blocked_domains:
            if hostname_lower == blocked or hostname_lower.endswith(f".{blocked}"):
                return f"Domain '{hostname}' is blocked for security"

        # Check allowed domains (if configured)
        if self._allowed_domains:
            allowed = False
            for domain in self._allowed_domains:
                if hostname_lower == domain or hostname_lower.endswith(f".{domain}"):
                    allowed = True
                    break
            if not allowed:
                return f"Domain '{hostname}' is not in the allowed list"

        return None

    def _html_to_markdown(self, html_content: str) -> str:
        """Convert HTML to markdown-like text.

        Simple conversion without external dependencies.

        Args:
            html_content: HTML content.

        Returns:
            Markdown-like text.
        """
        text = html_content

        # Remove script and style tags
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Convert headers
        for i in range(6, 0, -1):
            text = re.sub(
                rf"<h{i}[^>]*>(.*?)</h{i}>",
                r"\n" + "#" * i + r" \1\n",
                text,
                flags=re.DOTALL | re.IGNORECASE,
            )

        # Convert paragraphs
        text = re.sub(r"<p[^>]*>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)

        # Convert line breaks
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

        # Convert links
        text = re.sub(
            r'<a[^>]*href=["\']([^"\\]*)["\'][^>]*>(.*?)</a>',
            r"[\2](\1)",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Convert bold/strong
        text = re.sub(
            r"<(b|strong)[^>]*>(.*?)</\1>", r"**\2**", text, flags=re.DOTALL | re.IGNORECASE
        )

        # Convert italic/em
        text = re.sub(r"<(i|em)[^>]*>(.*?)</\1>", r"*\2*", text, flags=re.DOTALL | re.IGNORECASE)

        # Convert code
        text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(
            r"<pre[^>]*>(.*?)</pre>", r"```\n\1\n```", text, flags=re.DOTALL | re.IGNORECASE
        )

        # Convert lists
        text = re.sub(r"<li[^>]*>", "\n- ", text, flags=re.IGNORECASE)
        text = re.sub(r"</li>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"</?[ou]l[^>]*>", "\n", text, flags=re.IGNORECASE)

        # Remove remaining HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode HTML entities
        text = html.unescape(text)

        # Clean up whitespace
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()
