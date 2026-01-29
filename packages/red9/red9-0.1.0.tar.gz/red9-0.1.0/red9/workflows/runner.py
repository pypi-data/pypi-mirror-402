"""Stabilize infrastructure setup and processor creation."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from stabilize import (
    CompleteStageHandler,
    CompleteTaskHandler,
    CompleteWorkflowHandler,
    Orchestrator,
    QueueProcessor,
    RunTaskHandler,
    SqliteQueue,
    SqliteWorkflowStore,
    StabilizeHandler,
    StartStageHandler,
    StartTaskHandler,
    StartWorkflowHandler,
    TaskRegistry,
)
from stabilize.queue import CancelStage
from stabilize.recovery import recover_on_startup

from red9.approval import configure_approval
from red9.logging import get_logger, log_workflow_event, set_workflow_context


class CancelStageHandler(StabilizeHandler):
    """Handler for CancelStage messages - acknowledges stage cancellation."""

    def __init__(self, queue: SqliteQueue, store: SqliteWorkflowStore) -> None:
        super().__init__(queue, store)

    @property
    def message_type(self) -> type:
        return CancelStage

    def handle(self, message: CancelStage) -> None:
        """Handle stage cancellation - just acknowledge it."""
        # The framework handles the status update, we just need to process the message
        pass


logger = get_logger(__name__)

if TYPE_CHECKING:
    from red9.providers.base import LLMProvider
    from red9.tools.base import ToolRegistry as Red9ToolRegistry


@dataclass
class WorkflowInfrastructure:
    """Container for Stabilize infrastructure components."""

    store: SqliteWorkflowStore
    queue: SqliteQueue
    processor: QueueProcessor
    orchestrator: Orchestrator
    registry: TaskRegistry
    on_token: Callable[[str], None] | None = None
    on_ui_event: Callable[[dict[str, Any]], None] | None = None

    def set_stream_callback(self, callback: Callable[[str], None] | None) -> None:
        """Set the streaming token callback for all agent tasks.

        Args:
            callback: Function called with each token during LLM streaming.
        """
        self.on_token = callback

    def set_ui_event_callback(self, callback: Callable[[dict[str, Any]], None] | None) -> None:
        """Set the UI event callback for all agent tasks.

        Args:
            callback: Function called with structured UI events.
        """
        self.on_ui_event = callback


from red9.core.signals import token_stream, ui_event

# Module-level reference to current infrastructure's callback for tasks to access
_current_stream_callback: Callable[[str], None] | None = None
_current_ui_event_callback: Callable[[dict[str, Any]], None] | None = None


def _stream_wrapper(token: str) -> None:
    """Signal wrapper for streaming tokens."""
    token_stream.send(None, token=token)


def _ui_event_wrapper(event: dict[str, Any]) -> None:
    """Signal wrapper for UI events."""
    ui_event.send(None, event=event)


def get_stream_callback() -> Callable[[str], None] | None:
    """Get the current streaming callback if set, or signal wrapper.

    Returns:
        The callback function or signal wrapper.
    """
    if _current_stream_callback:
        return _current_stream_callback
    return _stream_wrapper


def get_ui_event_callback() -> Callable[[dict[str, Any]], None] | None:
    """Get the current UI event callback if set, or signal wrapper.

    Returns:
        The callback function or signal wrapper.
    """
    if _current_ui_event_callback:
        return _current_ui_event_callback
    return _ui_event_wrapper


def emit_phase_start(stage: Any) -> None:
    """Emit phase_start event from a Stabilize stage.

    Call this at the start of agent task execute() methods to show
    phase headers in the UI.

    Args:
        stage: StageExecution instance with name and context.
    """
    callback = get_ui_event_callback()
    if not callback:
        return

    # Extract phase number and total from context
    phase_number = 0
    total_phases = 0
    if hasattr(stage, "context") and stage.context:
        phase_number = stage.context.get("phase_number", 0)
        total_phases = stage.context.get("total_phases", 0)

    # Extract phase name from stage name (e.g., "Phase 1: Discovery" -> "Discovery")
    name = getattr(stage, "name", "")
    if ": " in name:
        name = name.split(": ", 1)[1]

    callback(
        {
            "type": "phase_start",
            "phase": name,
            "phase_number": phase_number,
            "total_phases": total_phases,
        }
    )


def set_stream_callback(callback: Callable[[str], None] | None) -> None:
    """Set the current streaming callback.

    Args:
        callback: Function called with each token during LLM streaming.
    """
    global _current_stream_callback
    _current_stream_callback = callback


def set_ui_event_callback(callback: Callable[[dict[str, Any]], None] | None) -> None:
    """Set the current UI event callback.

    Args:
        callback: Function called with structured UI events.
    """
    global _current_ui_event_callback
    _current_ui_event_callback = callback


def create_infrastructure(
    project_root: Path,
    provider: LLMProvider | None = None,
    tool_registry: Red9ToolRegistry | None = None,
    rag_assistant: object | None = None,
    approval_mode: str = "default",
    providers: dict[str, LLMProvider] | None = None,
) -> WorkflowInfrastructure:
    """Create Stabilize infrastructure for workflow execution.

    Args:
        project_root: Root directory of the project.
        provider: Default LLM provider for agent tasks.
        tool_registry: Tool registry for agent tasks.
        rag_assistant: Ragit RAGAssistant for semantic search.
        approval_mode: Approval mode ("default", "plan", "auto", "yolo").
        providers: Role-based LLM providers (code, review, agentic).

    Returns:
        WorkflowInfrastructure containing all components.
    """
    # Configure global approval manager
    configure_approval(mode=approval_mode)  # type: ignore[arg-type]
    logger.info(f"Approval mode configured: {approval_mode}")
    # Ensure .red9 directory exists
    red9_dir = project_root / ".red9"
    red9_dir.mkdir(parents=True, exist_ok=True)

    db_path = red9_dir / "workflows.db"
    db_url = f"sqlite:///{db_path}"

    # Create store and queue
    store = SqliteWorkflowStore(db_url, create_tables=True)
    queue = SqliteQueue(db_url, table_name="queue_messages")
    queue._create_table()

    # Create task registry with agent tasks
    registry = TaskRegistry()
    _register_tasks(registry, provider, tool_registry, rag_assistant, providers)

    # Create processor with handlers (needs registry for RunTaskHandler)
    processor = create_processor(queue, store, registry)

    # Create orchestrator
    orchestrator = Orchestrator(queue)

    return WorkflowInfrastructure(
        store=store,
        queue=queue,
        processor=processor,
        orchestrator=orchestrator,
        registry=registry,
    )


def create_processor(
    queue: SqliteQueue,
    store: SqliteWorkflowStore,
    registry: TaskRegistry,
) -> QueueProcessor:
    """Create queue processor with all standard handlers.

    Args:
        queue: Message queue for workflow events.
        store: Workflow state store.
        registry: Task registry for RunTaskHandler.

    Returns:
        Configured QueueProcessor.
    """
    # Create processor with optimized configuration
    from stabilize.queue.processor import QueueProcessorConfig

    # Optimize for latency and throughput
    processor_config = QueueProcessorConfig(
        poll_frequency_ms=10,  # Poll 10x faster (10ms)
        max_workers=20,  # Allow more concurrent agents
        retry_delay=timedelta(seconds=1),  # Retry fast
        enable_deduplication=True,
    )

    processor = QueueProcessor(queue, config=processor_config)

    # Configure resilience with larger timeouts for autonomous agents
    from stabilize.resilience.bulkheads import TaskBulkheadManager
    from stabilize.resilience.circuits import WorkflowCircuitFactory
    from stabilize.resilience.config import BulkheadConfig, ResilienceConfig

    # 1 hour timeout for coding tasks
    long_timeout = BulkheadConfig(max_concurrent=5, timeout_seconds=3600.0)

    # Iteration loop needs special config: single concurrent, long timeout, many retries
    # The iteration_loop task uses TransientError to signal retry for each iteration
    iteration_loop_bulkhead = BulkheadConfig(
        max_concurrent=1,  # Only one iteration at a time
        timeout_seconds=3600.0,  # 1 hour per iteration
    )

    resilience_config = ResilienceConfig(
        bulkheads={
            "default": long_timeout,  # Set default timeout for all unspecified tasks
            "shell": long_timeout,
            "python": long_timeout,
            "http": BulkheadConfig(max_concurrent=10, timeout_seconds=120.0),
            "docker": long_timeout,
            "swarm_agent": long_timeout,
            "agent_swarm": long_timeout,
            "stabilize_swarm_agent": long_timeout,
            "iteration_loop": iteration_loop_bulkhead,  # Quality-gated iteration loop
        }
    )

    bulkhead_manager = TaskBulkheadManager(resilience_config)
    circuit_factory = WorkflowCircuitFactory(resilience_config)

    # Register all standard handlers in order
    handlers = [
        StartWorkflowHandler(queue, store),
        StartStageHandler(queue, store),
        StartTaskHandler(queue, store, registry),  # Now requires registry
        RunTaskHandler(
            queue,
            store,
            registry,
            bulkhead_manager=bulkhead_manager,
            circuit_factory=circuit_factory,
        ),  # Needs registry to execute tasks
        CompleteTaskHandler(queue, store),
        CompleteStageHandler(queue, store),
        CompleteWorkflowHandler(queue, store),
        CancelStageHandler(queue, store),  # Handle stage cancellations
    ]

    for handler in handlers:
        processor.register_handler(handler)

    return processor


def _register_tasks(
    registry: TaskRegistry,
    provider: LLMProvider | None,
    tool_registry: Red9ToolRegistry | None,
    rag_assistant: object | None,
    providers: dict[str, LLMProvider] | None = None,
) -> None:
    """Register all agent tasks with the registry.

    Args:
        registry: Stabilize task registry.
        provider: Default LLM provider for agent tasks.
        tool_registry: Tool registry for agent tasks.
        rag_assistant: Ragit RAGAssistant instance.
        providers: Role-based LLM providers (code, review, agentic, reasoning).
    """
    # Import here to avoid circular imports
    from red9.agents.tasks.approval_gate import ApprovalGateTask, QuickApprovalGateTask
    from red9.agents.tasks.architect import ArchitectAgentTask
    from red9.agents.tasks.code import CodeAgentTask
    from red9.agents.tasks.compensation import CompensationTask
    from red9.agents.tasks.context import ContextAgentTask
    from red9.agents.tasks.ddd import DDDImplementationTask
    from red9.agents.tasks.ddd_retry import DDDRetryTask
    from red9.agents.tasks.decompose import DecomposeAgentTask
    from red9.agents.tasks.diagnosis import DiagnosisTask
    from red9.agents.tasks.docs_sync import DocSyncTask
    from red9.agents.tasks.explorer import ExplorerAgentTask
    from red9.agents.tasks.index_setup import IndexSetupTask
    from red9.agents.tasks.issue_complete import IssueCompleteTask
    from red9.agents.tasks.issue_setup import IssueSetupTask
    from red9.agents.tasks.iteration_loop import IterationLoopTask
    from red9.agents.tasks.merge import MergeAgentTask
    from red9.agents.tasks.plan import PlanAgentTask
    from red9.agents.tasks.reviewer import ReviewerAgentTask
    from red9.agents.tasks.simple_code import SimpleCodeAgentTask
    from red9.agents.tasks.spec import SpecAgentTask
    from red9.agents.tasks.swarm_agent import SwarmAgentTask
    from red9.agents.tasks.swarm_aggregator import SwarmAggregatorTask
    from red9.agents.tasks.test import TestAgentTask
    from red9.agents.tasks.test_run import TestRunAgentTask
    from red9.agents.tasks.test_write import TestWriteAgentTask

    # Resolve providers for specific roles
    providers = providers or {}
    code_provider = providers.get("code") or provider
    providers.get("review") or provider
    agentic_provider = providers.get("agentic") or provider
    reasoning_provider = providers.get("reasoning") or provider

    # Register infrastructure tasks (no LLM needed)
    registry.register("index_setup", IndexSetupTask())
    registry.register("issue_setup", IssueSetupTask())
    registry.register("issue_complete", IssueCompleteTask())
    registry.register("merge_agent", MergeAgentTask())
    registry.register("compensation_agent", CompensationTask())

    # Register agent tasks (require LLM provider)
    if tool_registry:
        # Context Agent (Phase 0) - Agentic
        if agentic_provider:
            registry.register(
                "context_agent",
                ContextAgentTask(agentic_provider, tool_registry),
            )
            registry.register(
                "spec_agent",
                SpecAgentTask(agentic_provider, tool_registry),
            )
            # Use agentic_provider (Nemotron) for speed/reliability, prompt handles git logic
            registry.register(
                "doc_sync_agent",
                DocSyncTask(agentic_provider, tool_registry),
            )
            registry.register(
                "plan_agent",
                PlanAgentTask(agentic_provider, tool_registry, rag_assistant),
            )
            registry.register(
                "test_agent",
                TestAgentTask(agentic_provider, tool_registry, rag_assistant),
            )
            registry.register(
                "test_write_agent",
                TestWriteAgentTask(agentic_provider, tool_registry, rag_assistant),
            )
            registry.register(
                "test_run_agent",
                TestRunAgentTask(agentic_provider, tool_registry, rag_assistant),
            )
            registry.register(
                "decompose_agent",
                DecomposeAgentTask(agentic_provider, tool_registry),
            )

        # DDD Agent (Phase 2) - Code generation
        if code_provider:
            registry.register(
                "ddd_agent",
                DDDImplementationTask(
                    code_provider, tool_registry, fallback_provider=agentic_provider or provider
                ),
            )
            registry.register(
                "code_agent",
                CodeAgentTask(code_provider, tool_registry, rag_assistant),
            )
            # Simple code agent for trivial tasks (no exploration, no analysis)
            registry.register(
                "simple_code_agent",
                SimpleCodeAgentTask(code_provider, tool_registry, rag_assistant),
            )
            # Autonomous recovery agents
            registry.register(
                "diagnosis_agent",
                DiagnosisTask(agentic_provider or code_provider),
            )
            registry.register(
                "ddd_retry_agent",
                DDDRetryTask(code_provider, tool_registry),
            )

            # Iteration loop task (for quality-gated completion)
            # Uses code_provider for DDD and agentic_provider for review
            review_provider = providers.get("review") or agentic_provider or code_provider
            registry.register(
                "iteration_loop",
                IterationLoopTask(
                    ddd_provider=code_provider,
                    review_provider=review_provider,
                    tool_registry=tool_registry,
                ),
            )

    # ==========================================================================
    # Swarm Infrastructure Tasks (7-Phase Workflow)
    # ==========================================================================

    # Approval gates (no LLM needed)
    registry.register("approval_gate", ApprovalGateTask())
    registry.register("quick_approval_gate", QuickApprovalGateTask())

    # Swarm aggregator (agentic provider)
    if agentic_provider:
        registry.register("swarm_aggregator", SwarmAggregatorTask(agentic_provider))

    # Agent swarm tasks (requires multi-model providers and tools)
    if tool_registry and provider:
        # Build providers dict for swarm tasks
        from red9.workflows.models import MODEL_AGENTIC, MODEL_CODING, MODEL_REASONING

        swarm_providers: dict[str, LLMProvider] = {
            "default": provider,
            MODEL_CODING: code_provider or provider,
            MODEL_AGENTIC: agentic_provider or provider,
            MODEL_REASONING: reasoning_provider or provider,
        }
        # SwarmAgentTask runs single agent as Stabilize stage (native parallelism)
        registry.register("swarm_agent", SwarmAgentTask(swarm_providers, tool_registry))

    # ==========================================================================
    # Enterprise Workflow Tasks (New Agent Personas)
    # ==========================================================================

    if tool_registry:
        # Explorer agents (use coding model for codebase analysis)
        if code_provider:
            registry.register(
                "explorer_agent",
                ExplorerAgentTask(code_provider, tool_registry),
            )

        # Architect agents (use reasoning model for design decisions)
        if reasoning_provider:
            registry.register(
                "architect_agent",
                ArchitectAgentTask(reasoning_provider, tool_registry),
            )

        # Reviewer agents (use coding model for code analysis)
        if code_provider:
            registry.register(
                "reviewer_agent",
                ReviewerAgentTask(code_provider, tool_registry),
            )


def run_workflow(
    infrastructure: WorkflowInfrastructure,
    workflow: object,
    timeout: float = 300.0,
    on_token: Callable[[str], None] | None = None,
    on_ui_event: Callable[[dict[str, Any]], None] | None = None,
) -> object:
    """Execute a workflow to completion.

    Args:
        infrastructure: Workflow infrastructure components.
        workflow: Stabilize Workflow to execute.
        timeout: Maximum execution time in seconds.
        on_token: Optional callback for streaming tokens.
        on_ui_event: Optional callback for UI events.

    Returns:
        Completed workflow.

    Raises:
        KeyboardInterrupt: If the user cancels with Ctrl+C.
    """
    from red9.core.cancellation import (
        CancellationToken,
        set_cancellation_token,
    )

    workflow_id = str(workflow.id)
    set_workflow_context(workflow_id)

    # Set streaming callback for this workflow execution
    set_stream_callback(on_token)
    infrastructure.set_stream_callback(on_token)

    # Set UI event callback
    set_ui_event_callback(on_ui_event)
    infrastructure.set_ui_event_callback(on_ui_event)

    logger.info(f"Starting workflow {workflow_id}")
    log_workflow_event(logger, "started", workflow_id, timeout=timeout)

    # Store the workflow
    infrastructure.store.store(workflow)

    # Start execution
    infrastructure.orchestrator.start(workflow)

    # Create cancellation token for graceful interruption
    cancellation_token = CancellationToken()
    set_cancellation_token(cancellation_token)

    # Start parallel processing with ThreadPoolExecutor
    try:
        with cancellation_token:  # Installs Ctrl+C handler
            infrastructure.processor.start()

            # Poll for workflow completion
            start_time = time.time()
            poll_interval = 0.05  # 50ms polling

            while time.time() - start_time < timeout:
                # Check for cancellation
                if cancellation_token.is_cancelled:
                    logger.info(f"Workflow {workflow_id} cancelled by user")
                    log_workflow_event(logger, "cancelled", workflow_id)
                    # Cancel workflow in database
                    try:
                        infrastructure.store.cancel(
                            workflow_id,
                            canceled_by="user",
                            reason="Cancelled by user",
                        )
                    except Exception as cancel_err:
                        logger.warning(f"Failed to cancel workflow: {cancel_err}")
                    break

                # Check workflow status
                current = infrastructure.store.retrieve(workflow.id)
                status = getattr(current, "status", None)

                if status and status.name in ("SUCCEEDED", "FAILED", "CANCELLED", "TERMINAL"):
                    logger.debug(f"Workflow {workflow_id} reached terminal state: {status.name}")
                    break

                time.sleep(poll_interval)
            else:
                # Timeout reached
                logger.warning(f"Workflow {workflow_id} timed out after {timeout}s")

    except KeyboardInterrupt:
        # User pressed Ctrl+C - graceful cancellation
        logger.info(f"Workflow {workflow_id} interrupted by user (Ctrl+C)")
        log_workflow_event(logger, "cancelled", workflow_id, reason="user_interrupt")

        # Cancel workflow in the database so it won't be resumed
        try:
            infrastructure.store.cancel(
                workflow_id,
                canceled_by="user",
                reason="Cancelled by user (Ctrl+C)",
            )
            logger.info(f"Workflow {workflow_id} marked as CANCELLED in database")
        except Exception as cancel_err:
            logger.warning(f"Failed to cancel workflow in database: {cancel_err}")

        # Clean up silently before re-raising
        _cleanup_quietly(infrastructure)
        raise  # Re-raise so the CLI can handle it

    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {e}")
        log_workflow_event(logger, "failed", workflow_id, error=str(e))
        raise

    finally:
        # Stop processor and clear callbacks - suppress any threading exceptions
        _cleanup_quietly(infrastructure)

    # Retrieve final state
    result = infrastructure.store.retrieve(workflow.id)

    status = getattr(result, "status", "unknown")
    logger.info(f"Workflow {workflow_id} completed with status: {status}")
    log_workflow_event(logger, "completed", workflow_id, status=str(status))

    return result


def _cleanup_quietly(infrastructure: WorkflowInfrastructure) -> None:
    """Clean up infrastructure without raising exceptions.

    Suppresses threading-related exceptions that occur during shutdown,
    which are normal when cancelling via Ctrl+C.
    """
    import threading

    # Set a silent excepthook - DON'T restore it, let it stay silent
    # because threads may still throw exceptions after this function returns
    def silent_excepthook(args: threading.ExceptHookArgs) -> None:
        # Silently ignore all thread exceptions during shutdown
        pass

    threading.excepthook = silent_excepthook

    # Stop processor without waiting
    try:
        infrastructure.processor.stop(wait=False)
    except Exception:
        pass  # Ignore errors during stop

    # Clear callbacks
    try:
        set_stream_callback(None)
        infrastructure.set_stream_callback(None)
        set_ui_event_callback(None)
        infrastructure.set_ui_event_callback(None)
    except Exception:
        pass

    try:
        from red9.core.cancellation import set_cancellation_token

        set_cancellation_token(None)
    except Exception:
        pass


def recover_pending_workflows(
    infrastructure: WorkflowInfrastructure,
    max_age_hours: float = 24.0,
) -> int:
    """Recover any pending workflows from a previous crash.

    This function should be called at application startup to resume
    any workflows that were interrupted.

    Args:
        infrastructure: Workflow infrastructure components.
        max_age_hours: Only recover workflows started within this window.

    Returns:
        Number of workflows recovered.
    """
    logger.info("Checking for workflows to recover...")

    try:
        results = recover_on_startup(
            store=infrastructure.store,
            queue=infrastructure.queue,
            application="red9",
            max_age_hours=max_age_hours,
        )

        recovered_count = sum(1 for r in results if r.status == "recovered")
        failed_count = sum(1 for r in results if r.status == "failed")

        if recovered_count > 0:
            logger.info(f"Recovered {recovered_count} workflows")
            for r in results:
                if r.status == "recovered":
                    log_workflow_event(
                        logger,
                        "recovered",
                        r.workflow_id,
                        stages_requeued=r.stages_requeued,
                    )

        if failed_count > 0:
            logger.warning(f"Failed to recover {failed_count} workflows")
            for r in results:
                if r.status == "failed":
                    logger.error(f"Recovery failed for {r.workflow_id}: {r.message}")

        return recovered_count

    except Exception as e:
        logger.warning(f"Workflow recovery check failed: {e}")
        return 0
