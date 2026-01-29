"""Pydantic configuration models for RED9."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """LLM provider configuration.

    Multi-model strategy for swarm workflows:
    - model: General purpose (default for non-specialized tasks)
    - agent_model: Agentic tasks (fast, reliable)
    - code_model: Code reading/writing (specialized for code)
    - review_model: Code review (specialized for code analysis)
    - reasoning_model: Architecture/planning (deep reasoning)
    """

    type: Literal["ollama"] = "ollama"
    base_url: str = "http://localhost:11434"

    # General purpose model
    model: str = "nemotron-3-nano:30b-cloud"

    # Specialized models for swarm workflow
    agent_model: str = "nemotron-3-nano:30b-cloud"  # Agentic: fast, reliable
    code_model: str = "qwen3-coder:480b-cloud"  # Coding: reading/writing code
    review_model: str = "qwen3-coder:480b-cloud"  # Review: code analysis (same as code_model)
    reasoning_model: str = "gpt-oss:120b-cloud"  # Reasoning: architecture, planning

    # Embeddings
    embedding_model: str = "nomic-embed-text"

    timeout: int = 120  # Request timeout in seconds
    # NOTE: Retry/backoff is handled by Stabilize's Task layer using TransientError


class IndexingConfig(BaseModel):
    """Codebase indexing configuration."""

    include: list[str] = Field(default_factory=lambda: ["**/*.py", "**/*.ts", "**/*.js", "**/*.md"])
    exclude: list[str] = Field(
        default_factory=lambda: [
            "**/node_modules/**",
            "**/.venv/**",
            "**/venv/**",
            "**/dist/**",
            "**/build/**",
            "**/__pycache__/**",
            "**/.git/**",
            "**/.red9/**",
        ]
    )
    chunk_size: int = 512
    chunk_overlap: int = 50
    num_chunks: int = 5  # Number of chunks to retrieve (top_k)
    chunk_separator: str | None = None  # Optional separator for code-aware chunking


class WorkflowConfig(BaseModel):
    """Stabilize workflow configuration."""

    max_parallel_stages: int = 4
    stage_timeout_minutes: int = 30
    db_path: str = ".red9/workflows.db"


class IssueDBConfig(BaseModel):
    """IssueDB configuration."""

    db_path: str = ".red9/.issue.db"  # Store in .red9/ folder for cleaner project root
    auto_create_issues: bool = True
    capture_lessons: bool = True


class SandboxConfig(BaseModel):
    """Sandbox configuration."""

    enabled: bool = False  # Disabled by default for now
    mode: Literal["local", "docker"] = "local"
    # Docker specific settings could go here in future


class TelemetryConfig(BaseModel):
    """Telemetry configuration."""

    enabled: bool = True
    log_dir: str = ".red9/telemetry"


class TaskTimeoutConfig(BaseModel):
    """Per-task timeout and retry configuration.

    These settings override Stabilize's defaults for specific task types,
    allowing fine-grained control over execution behavior.
    """

    timeout_seconds: int = 300
    max_retries: int = 3
    retry_backoff_base: float = 2.0


class AgentConfig(BaseModel):
    """Agent execution configuration.

    Controls behavior of AgentLoop including context management,
    iteration limits, and parallel execution.
    """

    max_iterations: int = 50
    max_parallel_tools: int = 4
    enable_loop_detection: bool = True
    enable_compression: bool = True
    max_messages: int = 100  # Message bound before pruning
    max_context_tokens: int = 100000  # Approximate token limit

    # Per-task timeout overrides
    task_timeouts: dict[str, TaskTimeoutConfig] = Field(
        default_factory=lambda: {
            "ddd": TaskTimeoutConfig(timeout_seconds=600, max_retries=5),
            "spec": TaskTimeoutConfig(timeout_seconds=300, max_retries=3),
            "context": TaskTimeoutConfig(timeout_seconds=180, max_retries=2),
            "iteration_loop": TaskTimeoutConfig(timeout_seconds=900, max_retries=10),
            "swarm": TaskTimeoutConfig(timeout_seconds=600, max_retries=3),
        }
    )


class TestConfig(BaseModel):
    """Testing configuration override."""

    # Map language/framework to test command
    # e.g., "python": "pytest"
    commands: dict[str, str] = Field(default_factory=dict)

    # Auto-discovery patterns
    discovery_patterns: list[str] = Field(
        default_factory=lambda: ["test_*.py", "*_test.py", "*.test.js"]
    )


class SecurityConfig(BaseModel):
    """Security hook configuration.

    Controls which security hooks are enabled and allows customization
    of patterns for dangerous command and secret detection.
    """

    enabled: bool = True
    hooks: dict[str, bool] = Field(
        default_factory=lambda: {
            "dangerous_commands": True,
            "secret_detection": True,
        }
    )
    # Additional patterns for dangerous command detection
    # Format: list of (pattern, description, severity) as JSON strings
    custom_dangerous_patterns: list[str] = Field(default_factory=list)
    # Additional patterns for secret detection
    # Format: list of (pattern, description, severity) as JSON strings
    custom_secret_patterns: list[str] = Field(default_factory=list)
    # Paths outside project that are allowed for tool access
    allowed_paths_outside_project: list[str] = Field(default_factory=list)


class Red9Config(BaseModel):
    """Main RED9 configuration."""

    version: str = "1"
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    issuedb: IssueDBConfig = Field(default_factory=IssueDBConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    tests: TestConfig = Field(default_factory=TestConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    approval_mode: Literal["default", "plan", "auto", "yolo"] = "default"

    def get_red9_dir(self, project_root: Path) -> Path:
        """Get the .red9 directory path."""
        return project_root / ".red9"

    def get_config_path(self, project_root: Path) -> Path:
        """Get the config.yaml path."""
        return self.get_red9_dir(project_root) / "config.yaml"

    def get_workflows_db_path(self, project_root: Path) -> Path:
        """Get the workflows database path."""
        return project_root / self.workflow.db_path

    def get_issuedb_path(self, project_root: Path) -> Path:
        """Get the IssueDB database path."""
        return project_root / self.issuedb.db_path
