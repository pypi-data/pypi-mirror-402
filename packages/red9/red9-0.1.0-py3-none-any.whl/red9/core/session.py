"""Core engine session for Red9."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from red9.config import Red9Config, config_exists, ensure_red9_dir, load_config, save_config
from red9.core.git_utils import GitRepository
from red9.core.mode_classifier import ModeClassifier
from red9.files.backup import BackupManager
from red9.indexing import IndexManager
from red9.indexing.repomap import RepoMap
from red9.providers.ollama import OllamaProvider
from red9.sandbox import LocalSandbox, Sandbox
from red9.security import create_default_security_hooks
from red9.telemetry import TelemetryService, get_telemetry
from red9.tools.apply_diff import ApplyDiffTool
from red9.tools.ast_grep import ASTGrepTool
from red9.tools.base import ToolRegistry, set_project_root
from red9.tools.batch_edit import BatchEditTool
from red9.tools.complete_task import CompleteTaskTool
from red9.tools.diagnostics import DiagnosticsTool
from red9.tools.edit_file import EditFileTool
from red9.tools.github import GitHubCloneTool, GitHubRepoSearchTool
from red9.tools.glob import GlobTool
from red9.tools.grep import GrepTool
from red9.tools.lint import LinterTool
from red9.tools.patch import ApplyPatchTool

# Import all tools for registry
from red9.tools.read_file import ReadFileTool
from red9.tools.review import ReviewSpecTool
from red9.tools.semantic_search import SemanticSearchTool
from red9.tools.shell import ShellTool
from red9.tools.write_file import WriteFileTool

logger = logging.getLogger(__name__)


class Red9Session:
    """Core session managing configuration, tools, and workflow execution."""

    def __init__(
        self,
        project_root: Path,
        sandbox: Sandbox | None = None,
        approval_mode: str = "default",
    ) -> None:
        """Initialize session.

        Args:
            project_root: Root directory of the project.
            sandbox: Optional sandbox for execution. Defaults to None (Direct Execution).
            approval_mode: Approval mode for workflow gates ("default", "auto", "yolo").
        """
        self.project_root = project_root.resolve()
        set_project_root(self.project_root)  # Ensure global state is set

        # DISABLE SANDBOX BY DEFAULT as requested for debugging
        self.sandbox = sandbox or LocalSandbox(self.project_root)
        self.approval_mode = approval_mode

        self.config: Red9Config | None = None

        # Components loaded on demand
        self.infrastructure: Any | None = None
        self.rag_assistant: Any | None = None
        self.tool_registry: Any | None = None
        self.index_manager: IndexManager | None = None
        self.repo_map: RepoMap | None = None
        self.backup_manager: BackupManager | None = None
        self.git: GitRepository = GitRepository(self.project_root)
        self.telemetry: TelemetryService = get_telemetry()
        self.classifier: ModeClassifier | None = None

        if config_exists(self.project_root):
            self.load_config()

    def load_config(self) -> None:
        """Load configuration from project root."""
        self.config = load_config(self.project_root)
        self.index_manager = IndexManager(self.project_root, self.config)
        self.repo_map = RepoMap(self.project_root)

        # Initialize mode classifier with fast model
        self.classifier = ModeClassifier(
            base_url=self.config.provider.base_url,
            model=self.config.provider.model,  # Fast generic model
        )

        # Enable telemetry if configured
        if self.config.telemetry.enabled:
            log_dir = self.project_root / self.config.telemetry.log_dir
            self.telemetry.enable(log_dir)

    def get_repo_map(self) -> str:
        """Get the current repository map."""
        if not self.repo_map:
            self.repo_map = RepoMap(self.project_root)
        return self.repo_map.get_map()

    def initialize_project(
        self,
        provider: str = "ollama",
        model: str | None = None,
        embedding_model: str | None = None,
    ) -> Path:
        """Initialize Red9 in the project directory.

        Args:
            provider: LLM provider type.
            model: Model name.
            embedding_model: Embedding model name.

        Returns:
            Path to created configuration file.
        """
        ensure_red9_dir(self.project_root)

        config = Red9Config()
        config.provider.type = provider  # type: ignore
        if model:
            config.provider.model = model
            # Override specialized models with the specific ones requested by user
            # unless the user provided a different one via CLI
            config.provider.code_model = "qwen3-coder:480b-cloud"
            config.provider.review_model = "devstral-small-2:24b-cloud"
            config.provider.agent_model = "nemotron-3-nano:30b-cloud"

            # If user specified --model, use it for agent tasks
            if model != "nemotron-3-nano:30b-cloud":
                config.provider.agent_model = model

        config_path = save_config(config, self.project_root)
        self.config = config
        self.index_manager = IndexManager(self.project_root, self.config)

        # Initialize IssueDB
        self._init_issuedb()

        return config_path

    def _init_issuedb(self) -> None:
        """Initialize IssueDB with default memories."""
        if not self.config:
            raise RuntimeError("Config not loaded")

        try:
            from issuedb.models import Memory
            from issuedb.repository import IssueRepository

            db_path = self.project_root / ".red9" / ".issue.db"
            repo = IssueRepository(db_path=str(db_path))

            default_memories = [
                Memory(
                    key="coding_style",
                    value=(
                        "Use type hints for all function signatures. "
                        "Prefer dataclasses and Pydantic models over dicts. "
                        "Use pathlib.Path instead of string paths."
                    ),
                    category="conventions",
                ),
                Memory(
                    key="error_handling",
                    value=(
                        "Provide actionable error messages with file paths and line numbers. "
                        "Log errors before raising exceptions."
                    ),
                    category="workflow",
                ),
                Memory(
                    key="testing",
                    value="Write unit tests for new functionality. Use pytest. Mock external deps.",
                    category="workflow",
                ),
            ]

            for mem in default_memories:
                try:
                    repo.add_memory(mem.key, mem.value, category=mem.category)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Failed to initialize IssueDB: {e}")

    def index_codebase(self) -> int:
        """Index the codebase.

        Returns:
            Number of indexed files.
        """
        if not self.index_manager:
            raise RuntimeError("Session not initialized")

        return self.index_manager.full_reindex(provider=None)

    def load_rag(self) -> None:
        """Initialize RAG assistant."""
        if not self.index_manager:
            return

        try:
            self.rag_assistant = self.index_manager.get_rag_assistant(provider=None)
        except Exception as e:
            logger.warning(f"Failed to load RAG: {e}")

    def execute_task(
        self,
        request: str,
        parallel: bool = False,
        issue_id: int | None = None,
        workflow_mode: str = "enterprise",
        fast_mode: bool = False,
        on_token: Any | None = None,
        on_ui_event: Any | None = None,
    ) -> bool:
        """Execute a task.

        Args:
            request: Task description.
            parallel: Whether to use parallel execution.
            issue_id: Optional existing issue ID.
            workflow_mode: Workflow mode - "enterprise" (default), "swarm", or "v1".
            fast_mode: If True, use single-agent fast mode (no exploration/review).
            on_token: Optional callback for streaming tokens. Called with each token as it arrives.
            on_ui_event: Optional callback for UI events.

        Returns:
            True if successful.
        """
        if not self.config:
            raise RuntimeError("Project not initialized")

        start_time = time.time()

        # 1. Ensure IssueDB entry
        if not issue_id:
            issue_id = self._create_issue(request)

        # 2. Prepare Infrastructure
        self._prepare_infrastructure()

        # Auto-detect fast mode if not explicitly set
        if not fast_mode and workflow_mode == "enterprise":
            complexity = self.get_task_complexity(request)
            if complexity == "simple":
                fast_mode = True
                logger.info("Auto-switching to FAST mode (simple task)")

        # 3. Build Workflow based on mode
        mentioned_files = []
        if fast_mode:
            from red9.core.mentions import extract_mentions

            mentioned_files = extract_mentions(request, self.project_root)
            if mentioned_files:
                logger.info(f"Fast mode: extracted mentions: {mentioned_files}")

        workflow = self._build_workflow(
            request, issue_id or 0, parallel, workflow_mode, fast_mode, mentioned_files
        )
        workflow_id = str(workflow.id)

        self.telemetry.track_workflow_start(workflow_id, len(request))

        # 5. Run
        from red9.workflows import run_workflow

        timeout = float(self.config.workflow.stage_timeout_minutes * 60)

        try:
            result = run_workflow(
                self.infrastructure,
                workflow,
                timeout=timeout,
                on_token=on_token,
                on_ui_event=on_ui_event,
            )
            status = result.status.name

            # Only true success is SUCCEEDED - no partial success masking
            success = status == "SUCCEEDED"

            if not success:
                # Log which stage failed for debugging
                for stage in result.stages:
                    if stage.status.name not in ("SUCCEEDED", "PENDING"):
                        logger.error(
                            f"Stage {stage.ref_id} failed with status: {stage.status.name}"
                        )

            self.telemetry.track_workflow_end(workflow_id, status, time.time() - start_time)

            return success
        except Exception as e:
            self.telemetry.track_workflow_end(workflow_id, "ERROR", time.time() - start_time)
            raise e

    def rollback(self, workflow_id: str) -> bool:
        """Rollback changes from a specific workflow."""
        try:
            # Re-initialize backup manager pointing to the workflow's backup dir
            bm = BackupManager(self.project_root, workflow_id)
            bm.restore_all()
            logger.info(f"Rolled back changes for workflow {workflow_id}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def simple_chat(
        self,
        message: str,
        on_token: Any | None = None,
    ) -> str:
        """Chat with Ragit context - for questions and conversations.

        Uses Ragit to fetch relevant codebase context and answers
        questions without running the full swarm workflow.

        Args:
            message: User message.
            on_token: Optional callback for streaming tokens.

        Returns:
            Assistant response.
        """
        if not self.config:
            raise RuntimeError("Project not initialized")

        provider = OllamaProvider(
            model=self.config.provider.model,
            base_url=self.config.provider.base_url,
        )

        # Get Ragit context for the message
        ragit_context = ""
        if self.index_manager:
            try:
                ragit_context = self.index_manager.get_context(message, top_k=5)
                logger.debug(f"Got Ragit context: {len(ragit_context)} chars")
            except Exception as e:
                logger.warning(f"Failed to get Ragit context: {e}")

        from red9.providers.base import Message

        # Build system prompt with context
        if ragit_context:
            system_prompt = f"""You are Red9, a helpful coding assistant.

## Codebase Context
{ragit_context}

Answer the user's question based on the codebase context above.
Be concise and helpful. If the context doesn't contain relevant information,
say so and suggest what might help.

For tasks that require code changes, suggest using:
  red9 task "your task description"
"""
        else:
            system_prompt = """You are Red9, a helpful coding assistant.

The codebase index is empty or unavailable. Answer based on general knowledge.

For tasks that require code changes, suggest using:
  red9 task "your task description"
"""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=message),
        ]

        try:
            if on_token and hasattr(provider, "stream_chat"):
                response_content = ""
                for event in provider.stream_chat(messages=messages):
                    if event.type == "delta" and event.content:
                        on_token(event.content)
                        response_content += event.content
                return response_content
            else:
                response = provider.chat(messages=messages)
                return response.message.content or ""
        except KeyboardInterrupt:
            return "[Interrupted]"

    def classify_request(self, message: str) -> str:
        """Classify a request using LLM to determine chat vs swarm mode.

        Makes an actual LLM call to the fast generic model to classify
        whether this request should be handled by chat mode (questions,
        explanations) or swarm mode (code changes, implementations).

        Args:
            message: The user's request.

        Returns:
            "chat" for questions/conversations.
            "swarm" for software engineering tasks.
        """
        if not self.classifier:
            # Fallback: if classifier not initialized, assume swarm
            logger.warning("Classifier not initialized, defaulting to swarm")
            return "swarm"

        return self.classifier.classify(message)

    def get_task_complexity(self, request: str) -> str:
        """Get task complexity for display purposes.

        Args:
            request: The user's request.

        Returns:
            "simple", "medium", or "complex".
        """
        if self.classifier:
            return self.classifier.classify_complexity(request)
        return "medium"

    def classify_complexity_fast(self, request: str) -> str | None:
        """Heuristic fast classification without LLM call.

        Instantly classifies obvious simple tasks using pattern matching.
        Returns None if the task requires LLM classification.

        Args:
            request: The user's request.

        Returns:
            "simple" if heuristic matches, None otherwise.
        """
        if self.classifier:
            return self.classifier.classify_complexity_fast(request)
        return None

    def _create_issue(self, request: str) -> int | None:
        """Create an issue in IssueDB."""
        if not self.config:
            return None

        try:
            from issuedb.models import Issue, Priority, Status
            from issuedb.repository import IssueRepository

            db_path = self.project_root / self.config.issuedb.db_path
            repo = IssueRepository(db_path=str(db_path))

            issue = Issue(
                title=request[:100],
                description=request,
                priority=Priority.MEDIUM,
                status=Status.OPEN,
            )
            created = repo.create_issue(issue)
            return created.id
        except Exception as e:
            logger.warning(f"Failed to create issue: {e}")
            return None

    def _prepare_infrastructure(self) -> None:
        """Setup infrastructure components."""
        if not self.config:
            return

        from red9.workflows import create_infrastructure

        # Providers
        # Default
        provider = OllamaProvider(
            base_url=self.config.provider.base_url,
            model=self.config.provider.model,
            embedding_model=self.config.provider.embedding_model,
        )

        # Get reasoning model (fallback to agent model if not configured)
        reasoning_model = getattr(
            self.config.provider, "reasoning_model", self.config.provider.agent_model
        )

        # Specific roles
        providers = {
            "code": OllamaProvider(
                base_url=self.config.provider.base_url,
                model=self.config.provider.code_model,
                embedding_model=self.config.provider.embedding_model,
            ),
            "review": OllamaProvider(
                base_url=self.config.provider.base_url,
                model=self.config.provider.review_model,
                embedding_model=self.config.provider.embedding_model,
            ),
            "agentic": OllamaProvider(
                base_url=self.config.provider.base_url,
                model=self.config.provider.agent_model,
                embedding_model=self.config.provider.embedding_model,
            ),
            "reasoning": OllamaProvider(
                base_url=self.config.provider.base_url,
                model=reasoning_model,
                embedding_model=self.config.provider.embedding_model,
            ),
        }

        # Security hooks
        security_hooks = None
        if self.config.security.enabled:
            security_hooks = create_default_security_hooks(self.config.security.hooks)
            logger.info(f"Security hooks enabled: {list(self.config.security.hooks.keys())}")

        # Tools
        registry = ToolRegistry(security_hooks=security_hooks)
        registry.register(ReadFileTool())
        registry.register(WriteFileTool())
        registry.register(EditFileTool())
        registry.register(ApplyDiffTool())  # Register ApplyDiff
        registry.register(ApplyPatchTool())  # Register Patch
        registry.register(BatchEditTool())
        registry.register(LinterTool(self.project_root))
        registry.register(DiagnosticsTool(self.project_root))
        registry.register(ASTGrepTool(self.project_root))
        registry.register(ReviewSpecTool())
        registry.register(GitHubCloneTool())
        registry.register(GitHubRepoSearchTool())
        registry.register(GlobTool())
        registry.register(GrepTool())

        # Inject Sandbox into ShellTool
        registry.register(ShellTool(self.project_root, sandbox=self.sandbox))

        semantic_search = SemanticSearchTool()
        if self.rag_assistant:
            semantic_search.set_assistant(self.rag_assistant)
        registry.register(semantic_search)

        registry.register(CompleteTaskTool())
        self.tool_registry = registry

        # Infrastructure
        self.infrastructure = create_infrastructure(
            project_root=self.project_root,
            provider=provider,
            tool_registry=registry,
            rag_assistant=self.rag_assistant,
            approval_mode=self.approval_mode,
            providers=providers,
        )

        # Check for and recover any pending workflows from previous crash
        from red9.workflows.runner import recover_pending_workflows

        recovered = recover_pending_workflows(self.infrastructure, max_age_hours=24.0)
        if recovered > 0:
            logger.info(f"Auto-recovered {recovered} workflows from previous session")

    def _build_workflow(
        self,
        request: str,
        issue_id: int,
        parallel: bool,
        workflow_mode: str = "v2",
        fast_mode: bool = False,
        mentioned_files: list[str] | None = None,
    ) -> object:
        """Build the appropriate workflow based on task complexity.

        Args:
            request: Task description.
            issue_id: IssueDB issue ID.
            parallel: Whether to use parallel execution (for v1 mode).
            workflow_mode: Workflow mode - "v2" (default), "enterprise", "swarm", or "v1".
            fast_mode: If True, use single-agent fast mode (no exploration/review).
            mentioned_files: List of files mentioned in the request (for fast mode).

        Returns:
            Configured workflow object.
        """
        from red9.workflows.builder import (
            build_enterprise_workflow,
            build_simple_workflow,
            build_swarm_workflow,
            build_task_workflow,
            build_v2_workflow,
        )

        # V2 workflow (new default - autonomous, no approval gates)
        if workflow_mode == "v2":
            if fast_mode:
                # Fast mode: single agent, minimal overhead
                logger.info("Using FAST workflow (single agent, --fast flag)")
                return build_simple_workflow(
                    request, self.project_root, mentioned_files=mentioned_files
                )

            # V2 spec-first autonomous workflow
            logger.info("Using V2 workflow (spec-first, autonomous)")
            return build_v2_workflow(request, self.project_root)

        # Enterprise workflow (with approval gates)
        elif workflow_mode == "enterprise":
            # Use complexity classifier to determine workflow configuration
            complexity = "medium"  # Default
            if self.classifier:
                complexity = self.classifier.classify_complexity(request)
                logger.info(f"Task complexity: {complexity}")

            if fast_mode:
                # Fast mode: single agent, minimal overhead
                logger.info("Using FAST workflow (single agent, --fast flag)")
                return build_simple_workflow(
                    request, self.project_root, mentioned_files=mentioned_files
                )

            # Enterprise workflow with complexity-based configuration
            logger.info(f"Using ENTERPRISE workflow (complexity: {complexity})")
            return build_enterprise_workflow(
                request=request,
                project_root=self.project_root,
                complexity=complexity,
                fast_mode=False,
            )

        # Iterative workflow with quality gates
        elif workflow_mode == "iterative":
            # Iterative workflow: DDD + Review loop until quality gates pass
            from red9.workflows.builder import build_iterative_workflow

            logger.info("Using ITERATIVE workflow (quality-gated loop)")
            return build_iterative_workflow(
                request=request,
                project_root=self.project_root,
                max_iterations=10,
            )

        # Swarm mode - user explicitly requested swarm workflow
        elif workflow_mode == "swarm":
            if fast_mode:
                # Fast mode overrides swarm
                logger.info("Using SIMPLE workflow (fast mode)")
                return build_simple_workflow(request, self.project_root)
            else:
                # User explicitly requested swarm - use it
                logger.info("Using SWARM workflow (full multi-agent)")
                return build_swarm_workflow(request, self.project_root)

        else:  # v1
            # V1 TDD Workflow
            # Setup → Plan → Test → Code → Verify → Complete
            if parallel:
                return self._build_parallel_workflow_if_beneficial(request, issue_id)
            return build_task_workflow(
                request=request,
                issue_id=issue_id,
                plan=None,
                project_root=self.project_root,
            )

    def _build_parallel_workflow_if_beneficial(
        self,
        request: str,
        issue_id: int,
    ) -> object:
        """Build a parallel workflow if beneficial."""
        if not self.config:
            raise RuntimeError("Config not loaded")

        from red9.agents.tasks.decompose import analyze_parallel_potential
        from red9.workflows.builder import (
            build_parallel_workflow,
            build_task_workflow,
        )
        from red9.workflows.models import PlanOutput

        # Create initial plan output for analysis
        initial_plan = PlanOutput(
            summary=request,
            files_to_modify=[],
            files_to_create=[],
            estimated_complexity="medium",
        )

        # Use analyze_parallel_potential for quick (non-LLM) analysis
        decomposition = analyze_parallel_potential(initial_plan, min_files_for_parallel=2)

        # Check complexity indicators in the request itself
        complexity_indicators = [
            "multiple",
            "several",
            "components",
            "modules",
            "refactor",
            "both",
            "all",
        ]
        request_lower = request.lower()
        complexity_score = sum(1 for ind in complexity_indicators if ind in request_lower)

        use_parallel = decomposition.can_parallelize or complexity_score >= 2

        if use_parallel:
            logger.info("Parallel execution enabled")
            return build_parallel_workflow(
                request=request,
                issue_id=issue_id,
                plan_output=initial_plan,
                project_root=self.project_root,
                max_parallel_stages=self.config.workflow.max_parallel_stages,
            )

        return build_task_workflow(
            request=request,
            issue_id=issue_id,
            plan=None,
            project_root=self.project_root,
        )
