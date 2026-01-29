"""Context compression and summarization for agent loops."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from red9.logging import get_logger
from red9.providers.base import LLMProvider, Message

logger = get_logger(__name__)


@dataclass
class CompressionResult:
    compressed: bool
    original_count: int
    new_count: int
    original_tokens: int
    new_tokens: int


class ChatCompressor:
    """Manages conversation history compression."""

    def __init__(self, provider: LLMProvider, max_tokens: int = 8000, target_tokens: int = 4000):
        self.provider = provider
        self.max_tokens = max_tokens
        self.target_tokens = target_tokens

    def should_compress(self, messages: list[dict[str, Any]]) -> bool:
        """Check if compression is needed."""
        # Simple estimation (4 chars per token)
        total_chars = sum(len(str(m.get("content", ""))) for m in messages)
        est_tokens = total_chars / 4
        return est_tokens > self.max_tokens

    def compress(
        self, messages: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], CompressionResult]:
        """Compress messages if they exceed the token limit."""
        original_len = len(messages)
        # Recalculate estimated tokens
        total_chars = sum(len(str(m.get("content", ""))) for m in messages)
        est_tokens = int(total_chars / 4)

        if not self.should_compress(messages):
            return messages, CompressionResult(
                False, original_len, original_len, est_tokens, est_tokens
            )

        logger.info(f"Compressing context: ~{est_tokens} tokens -> target {self.target_tokens}")

        # Keep system prompt and recent messages intact
        if len(messages) < 4:
            return messages, CompressionResult(
                False, original_len, original_len, est_tokens, est_tokens
            )

        system_msgs = [m for m in messages if m["role"] == "system"]
        history = [m for m in messages if m["role"] != "system"]

        # Keep the last 5 turns (10 messages)
        recent = history[-10:]
        older = history[:-10]

        if not older:
            return messages, CompressionResult(
                False, original_len, original_len, est_tokens, est_tokens
            )

        # Summarize older messages
        summary_prompt = "Summarize the key actions and decisions from this conversation history:"
        history_text = "\n".join([f"{m['role']}: {m.get('content', '')}" for m in older])

        try:
            summary_response = self.provider.chat(
                messages=[
                    Message(role="system", content="You are a helpful assistant."),
                    Message(role="user", content=f"{summary_prompt}\n\n{history_text}"),
                ]
            )
            summary = summary_response.message.content

            compressed_msg = {
                "role": "user",
                "content": f"[Previous Conversation Summary]: {summary}",
            }

            new_history = system_msgs + [compressed_msg] + recent

            new_chars = sum(len(str(m.get("content", ""))) for m in new_history)
            new_tokens = int(new_chars / 4)

            return new_history, CompressionResult(
                True, original_len, len(new_history), est_tokens, new_tokens
            )

        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            # Fallback: simple truncation
            truncated = system_msgs + messages[-20:]
            new_chars = sum(len(str(m.get("content", ""))) for m in truncated)
            new_tokens = int(new_chars / 4)
            return truncated, CompressionResult(
                True, original_len, len(truncated), est_tokens, new_tokens
            )


def create_compressor(provider: LLMProvider, model_name: str = "default") -> ChatCompressor:
    """Factory to create a compressor instance."""
    # Logic to adjust max_tokens based on model could go here
    return ChatCompressor(provider)
