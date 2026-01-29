"""Ollama LLM provider implementation.

This provider is a thin wrapper - retry/compensation is handled by Stabilize.
When errors occur, they bubble up to the Task layer where Stabilize's
built-in retry with exponential backoff (TransientError) handles them.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from typing import Any
from uuid import uuid4

import requests

from red9.providers.base import (
    ChatResponse,
    ChatStreamEvent,
    EmbeddingResponse,
    GenerationConfig,
    LLMProvider,
    Message,
    ToolCall,
)

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """LLM provider using Ollama for local inference.

    Note: This provider does NOT implement retry logic. Retry/backoff is
    handled at the Stabilize Task level using TransientError/PermanentError.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nemotron-3-nano:30b-cloud",
        embedding_model: str = "nomic-embed-text",
        timeout: int = 120,
    ) -> None:
        """Initialize Ollama provider.

        Args:
            base_url: Ollama server URL.
            model: Model to use for generation.
            embedding_model: Model to use for embeddings.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.embedding_model = embedding_model
        self.timeout = timeout

        # Lazy import to avoid dependency issues
        self._ragit_provider = None

    @property
    def ragit_provider(self) -> Any:
        """Get or create the Ragit Ollama provider."""
        if self._ragit_provider is None:
            from ragit.providers import OllamaProvider as RagitOllamaProvider

            self._ragit_provider = RagitOllamaProvider(
                base_url=self.base_url,
                embedding_url=self.base_url,
                timeout=self.timeout,
            )
        return self._ragit_provider

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
        config = config or GenerationConfig()

        try:
            start_time = time.time()
            response = self.ragit_provider.generate(
                prompt=prompt,
                model=self.model,
                system_prompt=system_prompt,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            duration_ms = (time.time() - start_time) * 1000

            from red9.telemetry import get_telemetry

            get_telemetry().track_llm_call(model=self.model, duration_ms=duration_ms)

            return response.text
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {e}") from e

    def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        config: GenerationConfig | None = None,
    ) -> ChatResponse:
        """Chat completion with optional tool calling.

        Note: Errors bubble up to Stabilize Task layer for retry handling.

        Args:
            messages: Conversation history.
            tools: Available tools in OpenAI function format.
            config: Generation configuration.

        Returns:
            Chat response with message and optional tool calls.
        """
        config = config or GenerationConfig()

        # Convert messages to Ollama format
        ollama_messages = [msg.to_dict(provider="ollama") for msg in messages]

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
                "top_p": config.top_p,
            },
        }

        if tools:
            payload["tools"] = tools

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()

        # Parse response
        msg_data = data.get("message", {})
        content = msg_data.get("content", "")
        tool_calls = None

        # 1. Try native Ollama tool calls
        if "tool_calls" in msg_data:
            tool_calls = [
                ToolCall(
                    id=tc.get("id", str(uuid4())),
                    name=tc["function"]["name"],
                    arguments=json.dumps(tc["function"].get("arguments", {}))
                    if isinstance(tc["function"].get("arguments"), dict)
                    else tc["function"].get("arguments", "{}"),
                )
                for tc in msg_data["tool_calls"]
            ]

        # 2. Fallback: Manual Parsing (Markdown/XML style)
        # Some models emit <tool_call> or similar when native fails
        if not tool_calls and content:
            import re

            # Look for <tool_call name="xyz">params</tool_call>
            xml_matches = re.findall(r'<tool_call\s+name="([^"]+)">([\s\S]*?)</tool_call>', content)
            if xml_matches:
                tool_calls = []
                for name, args in xml_matches:
                    tool_calls.append(ToolCall(id=str(uuid4()), name=name, arguments=args.strip()))

            # Look for ```json (tool call) style if model is prone to it
            # (Heuristic: common in qwen/deepseek)

        message = Message(
            role=msg_data.get("role", "assistant"),
            content=content,
            tool_calls=tool_calls,
        )

        return ChatResponse(
            message=message,
            finish_reason=data.get("done_reason"),
        )

    def stream_chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        config: GenerationConfig | None = None,
    ) -> Iterator[ChatStreamEvent]:
        """Stream chat completion with optional tool calling.

        Uses Ollama's streaming API to yield content tokens as they arrive.
        Tool calls are accumulated and yielded in the final event.

        Args:
            messages: Conversation history.
            tools: Available tools in OpenAI function format.
            config: Generation configuration.

        Yields:
            ChatStreamEvent objects with content deltas and final tool calls.
        """
        config = config or GenerationConfig()
        ollama_messages = [msg.to_dict(provider="ollama") for msg in messages]

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,  # ENABLE STREAMING
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
                "top_p": config.top_p,
            },
        }

        if tools:
            payload["tools"] = tools

        try:
            with requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
                stream=True,
            ) as response:
                response.raise_for_status()
                accumulated_content = ""
                tool_calls: list[ToolCall] | None = None

                try:
                    for line in response.iter_lines():
                        if not line:
                            continue

                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        msg = data.get("message", {})

                        # Yield content deltas as they arrive
                        content = msg.get("content", "")
                        if content:
                            accumulated_content += content
                            yield ChatStreamEvent(type="delta", content=content)

                        # Tool calls typically come at end in Ollama's response
                        if "tool_calls" in msg:
                            tool_calls = [
                                ToolCall(
                                    id=tc.get("id", str(uuid4())),
                                    name=tc["function"]["name"],
                                    arguments=json.dumps(tc["function"].get("arguments", {}))
                                    if isinstance(tc["function"].get("arguments"), dict)
                                    else tc["function"].get("arguments", "{}"),
                                )
                                for tc in msg["tool_calls"]
                            ]

                        # Check for completion
                        if data.get("done"):
                            # Fallback: Manual parsing for models that emit tool calls in content
                            if not tool_calls and accumulated_content:
                                import re

                                xml_matches = re.findall(
                                    r'<tool_call\s+name="([^"]+)">([\s\S]*?)</tool_call>',
                                    accumulated_content,
                                )
                                if xml_matches:
                                    tool_calls = [
                                        ToolCall(id=str(uuid4()), name=name, arguments=args.strip())
                                        for name, args in xml_matches
                                    ]

                            yield ChatStreamEvent(
                                type="done",
                                content=accumulated_content,
                                tool_calls=tool_calls,
                                done=True,
                            )
                            return
                except KeyboardInterrupt:
                    # Clean exit on Ctrl+C - connection closes via context manager
                    raise

        except KeyboardInterrupt:
            # Re-raise for proper handling by caller
            raise
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama streaming chat failed: {e}") from e

    def embed(self, texts: list[str]) -> EmbeddingResponse:
        """Generate embeddings for texts using ragit's OllamaProvider.

        Uses ragit's smart batch embedding with native /api/embed endpoint,
        LRU caching, and connection pooling.

        Args:
            texts: List of texts to embed.

        Returns:
            Embedding response with vectors.
        """
        try:
            # Use ragit's OllamaProvider for smart batch embedding
            responses = self.ragit_provider.embed_batch(texts, model=self.embedding_model)

            # Extract embedding vectors from EmbeddingResponse objects
            # Convert tuples to lists for our EmbeddingResponse format
            embeddings = [list(resp.embedding) for resp in responses]
            dimensions = len(embeddings[0]) if embeddings else 0

            return EmbeddingResponse(
                embeddings=embeddings,
                dimensions=dimensions,
                model=self.embedding_model,
            )
        except Exception as e:
            raise RuntimeError(f"Embedding failed: {e}") from e

    def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        config: GenerationConfig | None = None,
    ) -> Iterator[str]:
        """Stream generated text token by token.

        Args:
            prompt: The input prompt.
            system_prompt: Optional system prompt.
            config: Generation configuration.

        Yields:
            Generated text tokens.
        """
        config = config or GenerationConfig()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
            },
        }

        try:
            with requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
                stream=True,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama streaming failed: {e}") from e

    def is_available(self) -> bool:
        """Check if Ollama server is available.

        Returns:
            True if Ollama is running and accessible.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> list[dict[str, Any]]:
        """List available models.

        Returns:
            List of model information dictionaries.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except requests.RequestException:
            return []
