"""LLM-based mode classifier for Red9.

Uses the fast generic model to classify user requests into either:
- CHAT: Questions, explanations, greetings (answered with Ragit context)
- SWARM: Software engineering tasks requiring code changes

Also provides LLM-based task complexity classification:
- SIMPLE: Single file, no frameworks, trivial (fibonacci, hello world, fix typo)
- MEDIUM: Web app, database, API, requires spec and testing
- COMPLEX: Multi-service, architecture changes, distributed systems
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Literal

from red9.providers.base import Message
from red9.providers.ollama import OllamaProvider

logger = logging.getLogger(__name__)


# Heuristic patterns for instant simple task detection (no LLM call needed)
SIMPLE_TASK_PATTERNS = [
    # Trivial coding exercises
    r"^(write|create|make|implement)\s+(a\s+)?(simple\s+)?(hello\s*world|fibonacci|fizzbuzz|factorial)",
    r"^(write|create|make)\s+(a\s+)?script\s+that\s+prints",
    # Typo/comment fixes
    r"^fix\s+(a\s+|the\s+)?typo",
    r"^add\s+(a\s+)?comment",
    r"^remove\s+(the\s+)?comment",
    r"^update\s+(the\s+)?comment",
    # Simple renames
    r"^rename\s+\w+\s+to\s+\w+",
    r"^change\s+\w+\s+to\s+\w+",
    # Single constant/config changes
    r"^add\s+(a\s+)?constant",
    r"^change\s+(the\s+)?value",
    r"^update\s+(the\s+)?config",
    r"^set\s+\w+\s+to\s+",
    # Print/log statements
    r"^add\s+(a\s+)?print\s+statement",
    r"^add\s+(a\s+)?log\s+statement",
    # Simple formatting
    r"^format\s+(the\s+)?code",
    r"^fix\s+(the\s+)?indentation",
]

# Keywords that indicate NON-simple tasks (should trigger LLM classification)
COMPLEX_KEYWORDS = [
    # Frameworks
    "flask",
    "django",
    "fastapi",
    "falcon",
    "express",
    "react",
    "vue",
    "angular",
    # Databases
    "database",
    "sqlite",
    "postgres",
    "mysql",
    "mongodb",
    "redis",
    # APIs
    "api",
    "rest",
    "graphql",
    "endpoint",
    "crud",
    "http",
    # Authentication
    "auth",
    "login",
    "oauth",
    "jwt",
    "session",
    "cookie",
    # Architecture
    "architecture",
    "microservice",
    "distributed",
    "scalable",
    "migration",
    # Testing
    "test",
    "unit test",
    "integration",
    "pytest",
    "jest",
    # Multi-component
    "full stack",
    "frontend",
    "backend",
    "server",
    "client",
]


class ModeClassifier:
    """Classifies user requests using LLM inference.

    NO pattern matching - this makes actual LLM calls to determine:
    1. If a request should be handled by chat mode or swarm mode
    2. Task complexity (simple, medium, complex) for workflow routing
    """

    SYSTEM_PROMPT = """You are a request classifier for a coding assistant.

Classify the user's request into ONE of these modes:

CHAT - Use for:
- Greetings (hi, hello, hey)
- Questions about the codebase ("what's in this repo?", "how does X work?")
- Explanations ("explain the architecture", "what does this file do?")
- Help requests ("help", "what can you do?")
- General questions that can be answered by looking at code

SWARM - Use for:
- Code changes ("add a feature", "implement X")
- Bug fixes ("fix the bug in Y", "resolve the error")
- Refactoring ("refactor Z", "improve the code")
- Creating files ("create a new module", "write a script")
- Test writing ("write tests for X", "add unit tests")
- Any task that requires MODIFYING or CREATING code

Reply with ONLY one word: CHAT or SWARM"""

    COMPLEXITY_PROMPT = """You are a task complexity classifier for a coding assistant.

Classify the task complexity as ONE of:

SIMPLE - Single file, no frameworks, no databases, trivial tasks:
- "write fibonacci function"
- "create hello world"
- "fix typo in file X"
- "write factorial function"
- "add a constant to config"

MEDIUM - Web app, database, API, requires spec and testing:
- "build a todo app with flask and sqlite"
- "create CRUD endpoints for users"
- "add authentication to the API"
- "implement a REST endpoint"
- Any task mentioning: flask, django, falcon, fastapi, database, sqlite,
  postgres, mysql, api, server, web app, crud, rest, endpoint, model,
  schema, auth, login

COMPLEX - Multi-service, architecture changes, distributed systems:
- "refactor entire codebase to microservices"
- "implement payment processing system"
- "design distributed cache architecture"
- "migrate database schema with zero downtime"
- Any task mentioning: architecture, migration, microservices, distributed,
  scalable, multiple components, full stack, security system

IMPORTANT: When in doubt, classify as MEDIUM.
Never classify tasks with frameworks, databases, or APIs as SIMPLE.

Task: {request}

Reply with ONLY one word: SIMPLE, MEDIUM, or COMPLEX"""

    def __init__(self, base_url: str, model: str, project_root: Path | None = None) -> None:
        """Initialize classifier with LLM provider.

        Args:
            base_url: Ollama API base URL.
            model: Model name (should be fast, e.g., nemotron-3-nano).
            project_root: Optional project root for file mention extraction.
        """
        self.provider = OllamaProvider(base_url=base_url, model=model)
        self._model = model
        self.project_root = project_root

    def classify_complexity_fast(
        self, request: str
    ) -> Literal["simple", "medium", "complex"] | None:
        """Heuristic pre-classification without LLM call.

        Instantly classifies obvious simple tasks using pattern matching.
        Returns None if the task requires LLM classification.

        This provides instant feedback for trivial tasks like:
        - "write hello world"
        - "fix typo in README.md"
        - "add a comment to function X"

        Args:
            request: The user's task request.

        Returns:
            "simple" if heuristic matches a trivial task.
            None if LLM classification is needed.
        """
        if not request.strip():
            return "simple"

        request_lower = request.lower().strip()

        # First, check for complex keywords that should trigger LLM classification
        for keyword in COMPLEX_KEYWORDS:
            if keyword in request_lower:
                logger.debug(f"Complex keyword '{keyword}' found, deferring to LLM")
                return None  # Defer to LLM

        # Check simple task patterns
        for pattern in SIMPLE_TASK_PATTERNS:
            if re.match(pattern, request_lower, re.IGNORECASE):
                logger.info("Heuristic: Task classified as SIMPLE (pattern match)")
                return "simple"

        # Check for single file mention with short request
        # Pattern: mentions exactly one file and request is short
        file_mentions = self._extract_file_mentions(request)
        word_count = len(request.split())

        if len(file_mentions) == 1 and word_count < 15:
            # Single file + short request = likely simple
            logger.info("Heuristic: Task classified as SIMPLE (single file)")
            return "simple"

        # Cannot determine heuristically, need LLM
        return None

    def _extract_file_mentions(self, request: str) -> list[str]:
        """Extract file path mentions from request.

        Looks for patterns like:
        - file.py, path/to/file.js
        - @file.py (explicit mention syntax)

        Args:
            request: The user's request text.

        Returns:
            List of file paths mentioned.
        """
        mentions = []

        # Pattern 1: @filename syntax
        at_pattern = r"@([\w./\-]+\.\w+)"
        mentions.extend(re.findall(at_pattern, request))

        # Pattern 2: Common file extensions
        extensions = "py|js|ts|tsx|jsx|go|rs|java|rb|cpp|c|h|md|txt|yaml|yml|json|toml"
        file_pattern = rf"\b([\w./\-]+\.(?:{extensions}))\b"
        mentions.extend(re.findall(file_pattern, request))

        # Deduplicate
        return list(set(mentions))

    def classify(self, request: str) -> Literal["chat", "swarm"]:
        """Classify a user request using LLM inference.

        Makes an actual LLM call to determine the appropriate mode.

        Args:
            request: The user's request text.

        Returns:
            "chat" for conversational/question requests.
            "swarm" for software engineering tasks.
        """
        if not request.strip():
            return "chat"

        try:
            messages = [
                Message(role="system", content=self.SYSTEM_PROMPT),
                Message(role="user", content=request),
            ]

            logger.debug(f"Classifying request with LLM: {request[:50]}...")
            response = self.provider.chat(messages=messages)
            result = (response.message.content or "").strip().upper()

            logger.debug(f"LLM classification response: {result}")

            # Parse LLM response - look for SWARM keyword
            if "SWARM" in result:
                logger.info(f"Request classified as SWARM: {request[:50]}...")
                return "swarm"

            # Default to chat for anything else
            logger.info(f"Request classified as CHAT: {request[:50]}...")
            return "chat"

        except Exception as e:
            # On any error, default to chat mode (safer)
            logger.warning(f"Mode classification failed, defaulting to chat: {e}")
            return "chat"

    def classify_complexity(self, request: str) -> Literal["simple", "medium", "complex"]:
        """Classify task complexity using LLM inference.

        Makes an actual LLM call to determine task complexity for proper
        workflow routing. This replaces pattern matching which incorrectly
        classified tasks like "todo app with sqlite" as simple.

        Args:
            request: The user's task request.

        Returns:
            "simple" - Single file, clear output (use single agent)
            "medium" - Multi-file, requires spec (use v2 workflow)
            "complex" - Architectural changes (use full swarm)
        """
        if not request.strip():
            return "simple"

        try:
            # Format the prompt with the request
            prompt = self.COMPLEXITY_PROMPT.format(request=request)

            messages = [
                Message(role="user", content=prompt),
            ]

            logger.debug(f"Classifying complexity with LLM: {request[:50]}...")
            response = self.provider.chat(messages=messages)
            result = (response.message.content or "").strip().upper()

            logger.debug(f"LLM complexity response: {result}")

            # Parse LLM response
            if "SIMPLE" in result:
                logger.info(f"Task classified as SIMPLE: {request[:50]}...")
                return "simple"
            elif "COMPLEX" in result:
                logger.info(f"Task classified as COMPLEX: {request[:50]}...")
                return "complex"
            else:
                # Default to medium (covers MEDIUM and any other response)
                logger.info(f"Task classified as MEDIUM: {request[:50]}...")
                return "medium"

        except Exception as e:
            # On any error, default to medium (safest choice)
            logger.warning(f"Complexity classification failed, defaulting to medium: {e}")
            return "medium"
