"""Base LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    """A message in a conversation."""

    role: str  # "system", "user", "assistant", "tool"
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None  # For tool responses
    name: str | None = None  # For tool responses

    def to_dict(self, provider: str = "ollama") -> dict[str, Any]:
        """Convert to dictionary for API calls.

        Args:
            provider: The LLM provider ("ollama", "openai", etc.)

        Returns:
            Dictionary suitable for the provider's API.
        """
        d: dict[str, Any] = {"role": self.role}

        if self.content is not None:
            d["content"] = self.content

        if self.tool_calls:
            d["tool_calls"] = [tc.to_dict(provider=provider) for tc in self.tool_calls]

        # Ollama doesn't use tool_call_id in tool responses
        # OpenAI does, so only include for OpenAI-compatible APIs
        if provider != "ollama":
            if self.tool_call_id:
                d["tool_call_id"] = self.tool_call_id

            if self.name:
                d["name"] = self.name

        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Message:
        """Create from dictionary.

        Args:
            data: Dictionary representation of message.

        Returns:
            Message object.
        """
        tool_calls = None
        if "tool_calls" in data:
            tool_calls = []
            for tc_data in data["tool_calls"]:
                tool_calls.append(ToolCall.from_dict(tc_data))

        return cls(
            role=data["role"],
            content=data.get("content"),
            tool_calls=tool_calls,
            tool_call_id=data.get("tool_call_id"),
            name=data.get("name"),
        )


@dataclass
class ToolCall:
    """A tool call from the assistant."""

    id: str
    name: str
    arguments: str  # JSON string

    def to_dict(self, provider: str = "ollama") -> dict[str, Any]:
        """Convert to dictionary.

        Args:
            provider: The LLM provider ("ollama", "openai", etc.)

        Returns:
            Dictionary suitable for the provider's API.
        """
        import json

        # Parse arguments string to dict if possible
        try:
            args_dict = (
                json.loads(self.arguments) if isinstance(self.arguments, str) else self.arguments
            )
        except json.JSONDecodeError:
            args_dict = {}

        if provider == "ollama":
            # Ollama format - no id at top level, arguments as object
            return {
                "function": {
                    "name": self.name,
                    "arguments": args_dict,
                },
            }
        else:
            # OpenAI format
            return {
                "id": self.id,
                "type": "function",
                "function": {
                    "name": self.name,
                    "arguments": self.arguments,
                },
            }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolCall:
        """Create from dictionary.

        Args:
            data: Dictionary representation of tool call.

        Returns:
            ToolCall object.
        """
        import json
        from uuid import uuid4

        # Handle both OpenAI (type=function) and Ollama (function nested) formats
        if "function" in data:
            fn = data["function"]
            name = fn["name"]
            args = fn["arguments"]
            # Convert args back to string if it's a dict
            if isinstance(args, dict):
                args_str = json.dumps(args)
            else:
                args_str = str(args)

            # OpenAI has id at top level, Ollama doesn't
            tc_id = data.get("id", str(uuid4()))

            return cls(id=tc_id, name=name, arguments=args_str)

        # Fallback/Direct format
        return cls(
            id=data.get("id", str(uuid4())),
            name=data.get("name", "unknown"),
            arguments=data.get("arguments", "{}"),
        )


@dataclass
class GenerationConfig:
    """Configuration for text generation."""

    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    stop: list[str] | None = None


@dataclass
class ChatResponse:
    """Response from a chat completion."""

    message: Message
    finish_reason: str | None = None
    usage: dict[str, int] | None = None


@dataclass
class ChatStreamEvent:
    """Event from streaming chat completion.

    Attributes:
        type: Event type - "delta", "tool_call", or "done".
        content: Text content delta (for "delta" events).
        tool_calls: List of tool calls (for "done" events).
        done: Whether this is the final event.
    """

    type: str  # "delta", "tool_call", "done"
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    done: bool = False


@dataclass
class EmbeddingResponse:
    """Response from an embedding request."""

    embeddings: list[list[float]]
    dimensions: int
    model: str | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Providers handle text generation, chat completion with tool calling,
    and text embedding.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        config: GenerationConfig | None = None,
    ) -> str:
        """Generate text from a prompt.

        Args:
            prompt: The input prompt.
            system_prompt: Optional system prompt.
            config: Generation configuration.

        Returns:
            Generated text.
        """
        pass

    @abstractmethod
    def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        config: GenerationConfig | None = None,
    ) -> ChatResponse:
        """Chat completion with optional tool calling.

        Args:
            messages: Conversation history.
            tools: Available tools in OpenAI function format.
            config: Generation configuration.

        Returns:
            Chat response with message and optional tool calls.
        """
        pass

    @abstractmethod
    def embed(self, texts: list[str]) -> EmbeddingResponse:
        """Generate embeddings for texts.

        Args:
            texts: List of texts to embed.

        Returns:
            Embedding response with vectors.
        """
        pass

    def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        config: GenerationConfig | None = None,
    ) -> Iterator[str]:
        """Stream generated text token by token.

        Default implementation just yields the full response.
        Override for true streaming.

        Args:
            prompt: The input prompt.
            system_prompt: Optional system prompt.
            config: Generation configuration.

        Yields:
            Generated text tokens.
        """
        yield self.generate(prompt, system_prompt, config)

    def stream_chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        config: GenerationConfig | None = None,
    ) -> Iterator[ChatStreamEvent]:
        """Stream chat completion with optional tool calling.

        Default implementation falls back to blocking chat() and yields a single done event.
        Override for true streaming support.

        Args:
            messages: Conversation history.
            tools: Available tools in OpenAI function format.
            config: Generation configuration.

        Yields:
            ChatStreamEvent objects with content deltas and final tool calls.
        """
        response = self.chat(messages, tools, config)
        yield ChatStreamEvent(
            type="done",
            content=response.message.content,
            tool_calls=response.message.tool_calls,
            done=True,
        )

    def is_available(self) -> bool:
        """Check if the provider is available and configured.

        Returns:
            True if provider can be used.
        """
        return True
