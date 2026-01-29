"""Token estimation utilities for context management.

Provides approximate token counting for chat messages without requiring
external tokenizer libraries like tiktoken.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from red9.logging import get_logger

if TYPE_CHECKING:
    from red9.providers.base import Message

logger = get_logger(__name__)

# Approximate tokens per character for different content types
# These are rough estimates based on common tokenizer behavior
CHARS_PER_TOKEN_CODE = 3.5  # Code tends to have more tokens per char
CHARS_PER_TOKEN_TEXT = 4.0  # Natural language
CHARS_PER_TOKEN_JSON = 3.0  # JSON has many special chars

# Message overhead (role tags, formatting)
MESSAGE_OVERHEAD_TOKENS = 4

# Default context limits for common models
DEFAULT_CONTEXT_LIMITS = {
    "gpt-4": 8192,
    "gpt-4-turbo": 128000,
    "gpt-4o": 128000,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    "llama3": 8192,
    "llama3.1": 128000,
    "qwen2.5-coder": 32768,
    "deepseek-coder": 16384,
    "default": 32768,
}


@dataclass
class TokenEstimate:
    """Token count estimate for content."""

    total_tokens: int
    char_count: int
    content_type: str  # "code", "text", "json", "mixed"
    confidence: str  # "high", "medium", "low"


def estimate_tokens(text: str, content_type: str = "mixed") -> TokenEstimate:
    """Estimate token count for text content.

    Uses character-based heuristics for fast estimation without
    requiring external tokenizer libraries.

    Args:
        text: Text content to estimate.
        content_type: Type of content ("code", "text", "json", "mixed").

    Returns:
        TokenEstimate with count and metadata.
    """
    if not text:
        return TokenEstimate(
            total_tokens=0,
            char_count=0,
            content_type=content_type,
            confidence="high",
        )

    char_count = len(text)

    # Select chars per token based on content type
    if content_type == "code":
        chars_per_token = CHARS_PER_TOKEN_CODE
    elif content_type == "json":
        chars_per_token = CHARS_PER_TOKEN_JSON
    elif content_type == "text":
        chars_per_token = CHARS_PER_TOKEN_TEXT
    else:
        # Mixed: analyze content to estimate
        chars_per_token = _estimate_chars_per_token(text)

    tokens = int(char_count / chars_per_token)

    # Confidence based on content type
    confidence = "medium" if content_type == "mixed" else "high"

    return TokenEstimate(
        total_tokens=tokens,
        char_count=char_count,
        content_type=content_type,
        confidence=confidence,
    )


def estimate_message_tokens(message: Message) -> int:
    """Estimate tokens for a single message.

    Args:
        message: Chat message.

    Returns:
        Estimated token count.
    """
    tokens = MESSAGE_OVERHEAD_TOKENS

    if message.content:
        content_type = _detect_content_type(message.content)
        tokens += estimate_tokens(message.content, content_type).total_tokens

    # Tool calls add tokens
    if message.tool_calls:
        for tc in message.tool_calls:
            tokens += estimate_tokens(tc.name, "text").total_tokens
            tokens += estimate_tokens(tc.arguments, "json").total_tokens

    return tokens


def estimate_messages_tokens(messages: list[Message]) -> int:
    """Estimate total tokens for a list of messages.

    Args:
        messages: List of chat messages.

    Returns:
        Estimated total token count.
    """
    return sum(estimate_message_tokens(msg) for msg in messages)


def get_model_context_limit(model_name: str) -> int:
    """Get the context limit for a model.

    Args:
        model_name: Model name or identifier.

    Returns:
        Context limit in tokens.
    """
    model_lower = model_name.lower()

    # Check for exact match
    if model_lower in DEFAULT_CONTEXT_LIMITS:
        return DEFAULT_CONTEXT_LIMITS[model_lower]

    # Check for partial match
    for key, limit in DEFAULT_CONTEXT_LIMITS.items():
        if key in model_lower:
            return limit

    return DEFAULT_CONTEXT_LIMITS["default"]


def should_compress(
    messages: list[Message],
    model_name: str = "default",
    threshold_ratio: float = 0.7,
) -> tuple[bool, int, int]:
    """Check if message history should be compressed.

    Args:
        messages: Current message history.
        model_name: Model name for context limit.
        threshold_ratio: Trigger compression at this ratio of context.

    Returns:
        Tuple of (should_compress, current_tokens, context_limit).
    """
    context_limit = get_model_context_limit(model_name)
    current_tokens = estimate_messages_tokens(messages)
    threshold = int(context_limit * threshold_ratio)

    should = current_tokens > threshold

    if should:
        logger.info(
            f"Compression recommended: {current_tokens}/{context_limit} tokens "
            f"({current_tokens / context_limit:.0%} of context)"
        )

    return should, current_tokens, context_limit


def _estimate_chars_per_token(text: str) -> float:
    """Estimate chars per token based on content analysis.

    Args:
        text: Text to analyze.

    Returns:
        Estimated chars per token.
    """
    # Heuristics based on content characteristics
    code_indicators = [
        "def ",
        "class ",
        "import ",
        "function ",
        "const ",
        "let ",
        "var ",
        "if (",
        "for (",
        "while (",
        "return ",
        "=>",
        "->",
        "{ }",
        "[]",
    ]

    json_indicators = ['{"', '": "', '": {', "null", "true", "false"]

    # Count indicators
    code_score = sum(1 for ind in code_indicators if ind in text)
    json_score = sum(1 for ind in json_indicators if ind in text)

    # Determine content type
    if json_score > code_score and json_score > 2:
        return CHARS_PER_TOKEN_JSON
    elif code_score > 3:
        return CHARS_PER_TOKEN_CODE
    else:
        return CHARS_PER_TOKEN_TEXT


def _detect_content_type(content: str) -> str:
    """Detect the content type of text.

    Args:
        content: Text content.

    Returns:
        Content type string.
    """
    if not content:
        return "text"

    # Check for JSON
    stripped = content.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"

    # Check for code patterns
    code_patterns = [
        "def ",
        "class ",
        "import ",
        "from ",
        "function ",
        "const ",
        "let ",
        "var ",
        "if (",
        "for (",
    ]

    code_count = sum(1 for p in code_patterns if p in content)
    if code_count >= 2:
        return "code"

    return "text"
