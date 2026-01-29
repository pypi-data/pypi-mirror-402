"""Error classification and handling for RED9.

Provides robust error classification for retry logic and error handling.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from red9.logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


# HTTP status codes that indicate transient errors
TRANSIENT_HTTP_CODES = {
    408,  # Request Timeout
    429,  # Too Many Requests
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
    529,  # Site is overloaded (Cloudflare)
}

# Permanent HTTP error codes (should not retry)
PERMANENT_HTTP_CODES = {
    400,  # Bad Request
    401,  # Unauthorized
    403,  # Forbidden
    404,  # Not Found
    405,  # Method Not Allowed
    410,  # Gone
    422,  # Unprocessable Entity
}

# Error message patterns that indicate transient errors
TRANSIENT_PATTERNS = [
    re.compile(r"timeout", re.I),
    re.compile(r"timed?\s*out", re.I),
    re.compile(r"connection\s*(error|refused|reset|closed)", re.I),
    re.compile(r"temporary\s*(failure|error|unavailable)", re.I),
    re.compile(r"service\s*unavailable", re.I),
    re.compile(r"server\s*(busy|overloaded)", re.I),
    re.compile(r"rate\s*limit", re.I),
    re.compile(r"throttl", re.I),
    re.compile(r"too\s*many\s*requests", re.I),
    re.compile(r"retry\s*(after|later)", re.I),
    re.compile(r"503|504|529", re.I),
    re.compile(r"ECONNREFUSED|ECONNRESET|ETIMEDOUT", re.I),
    re.compile(r"network\s*(error|unreachable)", re.I),
    re.compile(r"dns\s*(error|failure)", re.I),
]

# Error message patterns that indicate permanent errors
PERMANENT_PATTERNS = [
    re.compile(r"invalid\s*(api\s*)?key", re.I),
    re.compile(r"authentication\s*(failed|error)", re.I),
    re.compile(r"unauthorized", re.I),
    re.compile(r"forbidden", re.I),
    re.compile(r"not\s*found", re.I),
    re.compile(r"invalid\s*(request|parameter|argument)", re.I),
    re.compile(r"malformed", re.I),
    re.compile(r"unsupported", re.I),
    re.compile(r"model\s*not\s*(found|available)", re.I),
    re.compile(r"content\s*policy", re.I),
    re.compile(r"safety\s*(filter|block)", re.I),
]


def is_transient_error(error: Exception) -> bool:
    """Check if an error is transient and should be retried.

    Uses a multi-layered approach:
    1. Check exception type hierarchy
    2. Check HTTP status codes for HTTP errors
    3. Check error message patterns

    Args:
        error: The exception to classify.

    Returns:
        True if the error is transient and should be retried.
    """
    # Layer 1: Check exception types
    if _is_transient_by_type(error):
        logger.debug(f"Error classified as transient by type: {type(error).__name__}")
        return True

    # Layer 2: Check HTTP status codes
    http_result = _check_http_status(error)
    if http_result is not None:
        logger.debug(f"Error classified by HTTP status: transient={http_result}")
        return http_result

    # Layer 3: Check error message patterns
    error_str = str(error)

    # Check permanent patterns first (takes precedence)
    for pattern in PERMANENT_PATTERNS:
        if pattern.search(error_str):
            logger.debug(f"Error classified as permanent by pattern: {pattern.pattern}")
            return False

    # Check transient patterns
    for pattern in TRANSIENT_PATTERNS:
        if pattern.search(error_str):
            logger.debug(f"Error classified as transient by pattern: {pattern.pattern}")
            return True

    # Default: not transient (fail fast for unknown errors)
    logger.debug(f"Error not classified as transient: {type(error).__name__}: {str(error)[:100]}")
    return False


def _is_transient_by_type(error: Exception) -> bool:
    """Check if error is transient based on exception type."""
    # Import here to avoid dependencies if not installed
    try:
        import requests.exceptions

        transient_types = (
            requests.exceptions.Timeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        )
        if isinstance(error, transient_types):
            return True
    except ImportError:
        pass

    # Standard library exceptions
    import socket
    import ssl

    if isinstance(
        error,
        (
            TimeoutError,
            ConnectionError,
            ConnectionRefusedError,
            ConnectionResetError,
            BrokenPipeError,
            socket.timeout,
            socket.gaierror,
            ssl.SSLError,
        ),
    ):
        return True

    # Check for OSError with transient errno
    if isinstance(error, OSError):
        import errno

        transient_errnos = {
            errno.ETIMEDOUT,
            errno.ECONNREFUSED,
            errno.ECONNRESET,
            errno.ECONNABORTED,
            errno.ENETUNREACH,
            errno.EHOSTUNREACH,
            errno.EPIPE,
        }
        if hasattr(error, "errno") and error.errno in transient_errnos:
            return True

    return False


def _check_http_status(error: Exception) -> bool | None:
    """Check HTTP status code if available.

    Returns:
        True if transient, False if permanent, None if not an HTTP error.
    """
    # Try to get status code from various error types
    status_code = None

    # requests library HTTPError
    if hasattr(error, "response") and error.response is not None:
        response = error.response
        if hasattr(response, "status_code"):
            status_code = response.status_code

    # httpx library
    if hasattr(error, "response") and hasattr(error.response, "status_code"):
        status_code = error.response.status_code

    # aiohttp
    if hasattr(error, "status"):
        status_code = error.status

    # Check status code
    if status_code is not None:
        if status_code in TRANSIENT_HTTP_CODES:
            return True
        if status_code in PERMANENT_HTTP_CODES:
            return False
        # 5xx errors are generally transient
        if 500 <= status_code < 600:
            return True

    return None


def get_retry_after(error: Exception) -> int | None:
    """Extract retry-after value from error if available.

    Args:
        error: The exception to check.

    Returns:
        Retry delay in seconds, or None if not available.
    """
    # Check for Retry-After header in HTTP response
    if hasattr(error, "response") and error.response is not None:
        response = error.response
        if hasattr(response, "headers"):
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return int(retry_after)
                except ValueError:
                    pass

    # Check error message for retry hints
    error_str = str(error)
    match = re.search(r"retry\s*(?:after|in)\s*(\d+)\s*(?:seconds?|s)?", error_str, re.I)
    if match:
        return int(match.group(1))

    return None


class Red9Error(Exception):
    """Base exception for RED9 errors."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause


class ProviderError(Red9Error):
    """Error from LLM provider."""

    def __init__(
        self,
        message: str,
        provider: str,
        cause: Exception | None = None,
        is_transient: bool = False,
    ):
        super().__init__(message, cause)
        self.provider = provider
        self.is_transient = is_transient


class ToolError(Red9Error):
    """Error from tool execution."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        cause: Exception | None = None,
    ):
        super().__init__(message, cause)
        self.tool_name = tool_name
