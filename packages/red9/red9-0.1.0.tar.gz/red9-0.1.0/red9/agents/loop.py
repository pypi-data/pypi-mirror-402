"""Core agent execution loop with tool calling.

Note: LLM errors are NOT caught here - they bubble up to the Task layer
where Stabilize's TransientError/PermanentError mechanism handles retries.

Supports parallel execution of independent read-only tool calls.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from red9.agents.loop_detector import LoopDetector
from red9.errors import is_transient_error
from red9.logging import get_logger, log_llm_call, log_tool_call
from red9.providers.base import LLMProvider, Message, ToolCall
from red9.tools.base import ToolRegistry, ToolResult

logger = get_logger(__name__)

# Message management constants
MAX_MESSAGES = 100  # Maximum messages before pruning
MAX_CONTEXT_TOKENS = 100000  # Approximate token limit
CONTEXT_PRUNE_THRESHOLD = 0.85  # Prune when reaching 85% of limit


@dataclass
class AgentResult:
    """Result of agent execution."""

    success: bool
    final_message: str = ""
    error: str | None = None
    messages: list[Message] = field(default_factory=list)
    tool_calls_made: int = 0
    files_modified: list[str] = field(default_factory=list)
    files_read: list[str] = field(default_factory=list)  # Track files read
    outputs: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolExecutionResult:
    """Result of a single tool execution with metadata."""

    tool_call: ToolCall
    result: ToolResult
    duration_ms: float
    arguments: dict[str, Any]


class AgentLoop:
    """Core agent execution loop with tool calling.

    Implements the agent loop pattern:
    1. Send messages to LLM with tool definitions
    2. Execute any tool calls returned (parallel for read-only tools)
    3. Add tool results to message history
    4. Repeat until LLM returns no tool calls or max iterations
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_registry: ToolRegistry,
        max_iterations: int = 50,
        parallel_tool_execution: bool = True,
        max_parallel_tools: int = 4,
        enable_loop_detection: bool = True,
        enable_compression: bool = True,
        model_name: str = "default",
        cancellation_check: Callable[[], bool] | None = None,
        file_read_cache: dict[str, tuple[str, float]] | None = None,
    ) -> None:
        """Initialize agent loop.

        Args:
            provider: LLM provider for chat completions.
            tool_registry: Registry of available tools.
            max_iterations: Maximum number of LLM calls before stopping.
            parallel_tool_execution: Enable parallel tool execution for read-only tools.
            max_parallel_tools: Maximum concurrent tool executions.
            enable_loop_detection: Enable loop detection for repetitive tool calls.
            enable_compression: Enable automatic chat compression.
            model_name: Model name for context limit estimation.
            cancellation_check: Optional callback that returns True if loop should cancel.
                If not provided, uses the global cancellation token.
            file_read_cache: Optional shared cache for file reads across iterations.
                Maps file_path -> (content, mtime). Pass the same dict across
                iterations to avoid re-reading unchanged files.
        """
        self.provider = provider
        self.tools = tool_registry
        self.max_iterations = max_iterations
        self.parallel_execution = parallel_tool_execution
        self.max_parallel_tools = max_parallel_tools
        self.enable_loop_detection = enable_loop_detection
        self.enable_compression = enable_compression
        self._loop_detector = LoopDetector() if enable_loop_detection else None

        # Use global cancellation token if no explicit check provided
        if cancellation_check is None:
            from red9.core.cancellation import is_cancelled

            self._check_cancelled = is_cancelled
        else:
            self._check_cancelled = cancellation_check

        # New: ChatCompressor (formerly ContextCompressor)
        from red9.agents.compression import ChatCompressor

        self._compressor = ChatCompressor(provider) if enable_compression else None

        # Message bounds tracking
        self._max_messages = MAX_MESSAGES
        self._max_context_tokens = MAX_CONTEXT_TOKENS

        # Track files read to avoid duplicate reads
        # Can be shared across iterations by passing the same dict
        self._files_read_cache: dict[str, tuple[str, float]] = (
            file_read_cache if file_read_cache is not None else {}
        )

    def _estimate_tokens(self, messages: list[Message]) -> int:
        """Estimate token count for messages.

        Uses a simple heuristic of ~4 characters per token, which is
        conservative for most models.

        Args:
            messages: List of messages to estimate.

        Returns:
            Estimated token count.
        """
        total_chars = 0
        for msg in messages:
            if msg.content:
                total_chars += len(msg.content)
            # Account for tool calls
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    total_chars += len(tc.arguments) + len(tc.name) + 50  # Overhead
        # ~4 chars per token is conservative
        return total_chars // 4

    def _prune_messages(self, messages: list[Message]) -> list[Message]:
        """Prune messages when approaching context limits.

        Keeps:
        - System message (first)
        - First 5 messages (initial context)
        - Last 30 messages (recent context)
        - Injects a summary note about pruned content

        Args:
            messages: Full message list.

        Returns:
            Pruned message list.
        """
        if len(messages) <= self._max_messages:
            return messages

        # Separate system message
        system_msg = messages[0] if messages and messages[0].role == "system" else None
        other_messages = messages[1:] if system_msg else messages

        # Keep initial and recent context
        initial_count = 5
        recent_count = 30

        if len(other_messages) <= initial_count + recent_count:
            return messages

        initial_msgs = other_messages[:initial_count]
        recent_msgs = other_messages[-recent_count:]
        pruned_count = len(other_messages) - initial_count - recent_count

        # Create summary message about pruned content
        summary_msg = Message(
            role="user",
            content=f"[Context note: {pruned_count} intermediate messages were pruned "
            f"to manage context size. Recent messages and initial context preserved.]",
        )

        # Reconstruct message list
        result = []
        if system_msg:
            result.append(system_msg)
        result.extend(initial_msgs)
        result.append(summary_msg)
        result.extend(recent_msgs)

        logger.info(f"Pruned {pruned_count} messages, new count: {len(result)}")
        return result

    def run(
        self,
        system_prompt: str,
        user_message: str,
        context: str | None = None,
        error_history: list[dict[str, Any]] | None = None,
        on_token: Callable[[str], None] | None = None,
        on_ui_event: Callable[[dict[str, Any]], None] | None = None,
    ) -> AgentResult:
        """Execute the agent loop.

        Args:
            system_prompt: System prompt defining agent behavior.
            user_message: User's request or task.
            context: Optional context (e.g., RAG results) to include.
            error_history: Optional list of previous error attempts for retry context.
            on_token: Optional callback for streaming tokens. Called with each token as it arrives.
            on_ui_event: Optional callback for UI events.

        Returns:
            AgentResult with execution details.
        """
        # Build initial messages
        messages: list[Message] = []

        # Add system prompt
        full_system = system_prompt
        if context:
            full_system += f"\n\n## Relevant Context\n\n{context}"

        # Inject error history for retries
        if error_history:
            error_summary = "\n".join(
                f"- Attempt {e.get('attempt', '?')}: {e.get('error', 'Unknown error')}"
                for e in error_history
            )
            full_system += (
                f"\n\n## Previous Errors (LEARN FROM THESE - DO NOT REPEAT)\n\n"
                f"This task has failed {len(error_history)} time(s) before. "
                f"Review the errors and adjust your approach:\n{error_summary}"
            )
            logger.info(f"Injecting {len(error_history)} previous errors into prompt")

        messages.append(Message(role="system", content=full_system))

        # Add user message
        messages.append(Message(role="user", content=user_message))

        # Get tool definitions
        tool_definitions = self.tools.get_definitions()

        # Track execution
        tool_calls_made = 0
        files_modified: list[str] = []
        files_read: list[str] = []  # Track files read for context accumulation
        outputs: dict[str, Any] = {}

        logger.info(f"Starting agent loop, max_iterations={self.max_iterations}")

        # Track unresolved tool errors to block premature completion
        unresolved_errors: list[str] = []

        for iteration in range(self.max_iterations):
            # Check for external cancellation (e.g., stage failed)
            if self._check_cancelled():
                logger.info("Agent loop cancelled by external signal")
                return AgentResult(
                    success=False,
                    error="Cancelled by external signal",
                    messages=messages,
                    tool_calls_made=tool_calls_made,
                    files_modified=files_modified,
                    files_read=files_read,
                    outputs=outputs,
                )

            try:
                # Check message bounds and prune if needed
                estimated_tokens = self._estimate_tokens(messages)
                if (
                    len(messages) > self._max_messages
                    or estimated_tokens > self._max_context_tokens * CONTEXT_PRUNE_THRESHOLD
                ):
                    messages = self._prune_messages(messages)
                    logger.info(
                        f"Context pruned: {len(messages)} messages, "
                        f"~{self._estimate_tokens(messages)} tokens"
                    )

                # Check if compression is needed
                if self._compressor:
                    # Convert Message objects to dicts for compression
                    msg_dicts = [m.to_dict() for m in messages]
                    compressed_dicts, comp_result = self._compressor.compress(msg_dicts)

                    # If compression happened (length changed), rebuild Message list
                    if comp_result.compressed:
                        messages = [Message.from_dict(m) for m in compressed_dicts]
                        logger.info("Context compressed")

                # Get LLM response (streaming if callback provided)
                llm_start = time.time()

                # Get model name for UI
                model_name = getattr(self.provider, "model", "unknown")

                # Emit response_start event for UI state coordination
                if on_ui_event:
                    on_ui_event(
                        {"type": "response_start", "streaming": bool(on_token), "model": model_name}
                    )

                if on_token and hasattr(self.provider, "stream_chat"):
                    # Use streaming chat
                    from red9.providers.base import ChatResponse

                    accumulated_content = ""
                    tool_calls = None

                    for event in self.provider.stream_chat(
                        messages=messages,
                        tools=tool_definitions if tool_definitions else None,
                    ):
                        if event.type == "delta" and event.content:
                            on_token(event.content)
                            accumulated_content += event.content
                        if event.done:
                            tool_calls = event.tool_calls

                    response = ChatResponse(
                        message=Message(
                            role="assistant",
                            content=accumulated_content,
                            tool_calls=tool_calls,
                        )
                    )
                else:
                    # Use blocking chat
                    response = self.provider.chat(
                        messages=messages,
                        tools=tool_definitions if tool_definitions else None,
                    )

                llm_duration = (time.time() - llm_start) * 1000

                # Track telemetry
                from red9.telemetry import get_telemetry

                get_telemetry().track_llm_call(
                    model=getattr(self.provider, "model", "unknown"), duration_ms=llm_duration
                )

                log_llm_call(
                    logger,
                    provider=self.provider.__class__.__name__,
                    model=getattr(self.provider, "model", "unknown"),
                    duration_ms=llm_duration,
                )

                # Add assistant response to history
                messages.append(response.message)

                # Emit response_end event for UI state coordination
                if on_ui_event:
                    on_ui_event(
                        {
                            "type": "response_end",
                            "has_tool_calls": bool(response.message.tool_calls),
                        }
                    )

                # Check if done (no tool calls)
                if not response.message.tool_calls:
                    logger.info(
                        f"Agent completed after {iteration + 1} iterations, "
                        f"{tool_calls_made} tool calls"
                    )
                    return AgentResult(
                        success=True,
                        final_message=response.message.content or "",
                        messages=messages,
                        tool_calls_made=tool_calls_made,
                        files_modified=files_modified,
                        files_read=files_read,
                        outputs=outputs,
                    )

                # Execute tool calls (parallel for read-only, sequential for write)
                execution_results = self._execute_tool_calls(
                    response.message.tool_calls, on_ui_event
                )

                # Track loop detection state
                loop_warning: str | None = None

                for exec_result in execution_results:
                    tool_calls_made += 1

                    log_tool_call(
                        logger,
                        tool_name=exec_result.tool_call.name,
                        params=exec_result.arguments,
                        result=exec_result.result.success,
                        error=exec_result.result.error,
                        duration_ms=exec_result.duration_ms,
                    )

                    # Track tool errors for completion blocking
                    if not exec_result.result.success:
                        error_desc = (
                            f"{exec_result.tool_call.name}: "
                            f"{exec_result.result.error or 'Unknown error'}"
                        )
                        unresolved_errors.append(error_desc)
                        # Debug level - errors shown via UI
                        logger.debug(f"Tool error recorded: {error_desc}")

                    # Check for loops
                    if self._loop_detector:
                        loop_result = self._loop_detector.record_call(
                            exec_result.tool_call.name,
                            exec_result.arguments,
                        )
                        if loop_result.is_loop and not loop_warning:
                            loop_warning = self._loop_detector.inject_loop_warning(loop_result)

                    # Track file modifications and reads
                    tool = self.tools.get(exec_result.tool_call.name)
                    tool_name = exec_result.tool_call.name

                    if exec_result.result.success and tool:
                        if not tool.read_only:
                            # Track file modifications
                            if "file_path" in exec_result.arguments:
                                files_modified.append(exec_result.arguments["file_path"])
                            # Clear errors when successful write completes (agent fixed issue)
                            unresolved_errors.clear()
                        elif tool_name in ("read_file", "read_many_files"):
                            # Track files read for context accumulation
                            if "file_path" in exec_result.arguments:
                                files_read.append(exec_result.arguments["file_path"])
                            elif "paths" in exec_result.arguments:
                                files_read.extend(exec_result.arguments["paths"])

                    # Add result to history
                    tool_result_content = self._format_tool_result(exec_result.result)
                    messages.append(
                        Message(
                            role="tool",
                            content=tool_result_content,
                            tool_call_id=exec_result.tool_call.id,
                            name=exec_result.tool_call.name,
                        )
                    )

                    # Check for task completion
                    if exec_result.tool_call.name == "complete_task":
                        # Block completion if there are unresolved errors
                        if unresolved_errors:
                            error_list = "\n".join(f"- {e}" for e in unresolved_errors)
                            warning_msg = (
                                f"BLOCKED: Cannot complete task with unresolved errors:\n"
                                f"{error_list}\n\n"
                                f"Fix these errors first, then try complete_task again."
                            )
                            logger.warning(
                                f"Blocking complete_task: {len(unresolved_errors)} errors"
                            )
                            messages.append(Message(role="user", content=warning_msg))
                            # Don't return - let agent try again
                            continue

                        if exec_result.result.success and exec_result.result.output:
                            outputs.update(exec_result.result.output)
                        output = exec_result.result.output
                        summary = output.get("summary", "") if output else ""
                        return AgentResult(
                            success=True,
                            final_message=summary,
                            messages=messages,
                            tool_calls_made=tool_calls_made,
                            files_modified=files_modified,
                            files_read=files_read,
                            outputs=outputs,
                        )

                # Inject loop warning if detected
                if loop_warning:
                    messages.append(
                        Message(
                            role="user",
                            content=loop_warning,
                        )
                    )
                    logger.debug("Loop warning injected into agent context")

            except KeyboardInterrupt:
                # Re-raise KeyboardInterrupt - do NOT convert to AgentResult
                # This ensures the interrupt propagates up to the workflow level
                # and properly terminates the workflow instead of triggering retries
                logger.info("Agent loop interrupted by user - propagating interrupt")
                raise

            except Exception as e:
                # Let transient errors bubble up to Task layer for Stabilize retry
                if is_transient_error(e):
                    # Wrap in TransientError for proper Stabilize retry handling
                    from stabilize.errors import TransientError

                    raise TransientError(
                        f"Agent loop transient error at iteration {iteration}: {e}",
                        retry_after=5,
                        cause=e,
                    ) from e

                # Non-transient errors return failure result
                return AgentResult(
                    success=False,
                    error=f"Agent loop error at iteration {iteration}: {e}",
                    messages=messages,
                    tool_calls_made=tool_calls_made,
                    files_modified=files_modified,
                    files_read=files_read,
                    outputs=outputs,
                )

        # Max iterations reached
        return AgentResult(
            success=False,
            error=f"Max iterations ({self.max_iterations}) reached without completion",
            messages=messages,
            tool_calls_made=tool_calls_made,
            files_modified=files_modified,
            files_read=files_read,
            outputs=outputs,
        )

    def _execute_tool_calls(
        self,
        tool_calls: list[ToolCall],
        on_ui_event: Callable[[dict[str, Any]], None] | None = None,
    ) -> list[ToolExecutionResult]:
        """Execute tool calls with parallel support for read-only tools.

        Read-only tools (grep, glob, read_file, semantic_search) are executed
        in parallel. Write tools are executed sequentially to maintain order.

        Args:
            tool_calls: List of tool calls from LLM response.
            on_ui_event: Optional callback for UI events.

        Returns:
            List of execution results in order.
        """
        if not tool_calls:
            return []

        # Parse arguments for all tool calls
        parsed_calls: list[tuple[ToolCall, dict[str, Any]]] = []
        for tc in tool_calls:
            try:
                args = json.loads(tc.arguments) if tc.arguments else {}
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Malformed JSON in tool call '{tc.name}': {e}. "
                    f"Arguments: {tc.arguments[:100]}..."
                )
                args = {}
            parsed_calls.append((tc, args))

        # If parallel execution is disabled, run sequentially
        if not self.parallel_execution:
            return self._execute_sequentially(parsed_calls, on_ui_event)

        # Partition into read-only and write groups, tracking original indices
        # Also handle unknown tools by returning error results immediately
        read_only_calls: list[tuple[int, ToolCall, dict[str, Any]]] = []
        write_calls: list[tuple[int, ToolCall, dict[str, Any]]] = []
        # Results dict keyed by original index for proper ordering
        results_by_idx: dict[int, ToolExecutionResult] = {}

        for idx, (tc, args) in enumerate(parsed_calls):
            tool = self.tools.get(tc.name)
            if tool is None:
                # Unknown tool - return error result immediately
                logger.warning(f"Unknown tool requested: '{tc.name}'")
                results_by_idx[idx] = ToolExecutionResult(
                    tool_call=tc,
                    result=ToolResult(
                        success=False,
                        output=None,
                        error=f"Unknown tool: '{tc.name}'",
                    ),
                    duration_ms=0,
                    arguments=args,
                )
            elif tool.read_only:
                read_only_calls.append((idx, tc, args))
            else:
                write_calls.append((idx, tc, args))

        # Execute read-only tools in parallel
        if read_only_calls:
            # Strip indices for parallel execution
            calls_only = [(tc, args) for _, tc, args in read_only_calls]
            parallel_results = self._execute_parallel(calls_only, on_ui_event)
            # Map results back to original indices
            for (idx, _, _), result in zip(read_only_calls, parallel_results):
                results_by_idx[idx] = result

        # Execute write tools sequentially (order matters for file writes)
        if write_calls:
            # Strip indices for sequential execution
            calls_only = [(tc, args) for _, tc, args in write_calls]
            sequential_results = self._execute_sequentially(calls_only, on_ui_event)
            # Map results back to original indices
            for (idx, _, _), result in zip(write_calls, sequential_results):
                results_by_idx[idx] = result

        # Reconstruct results in original order
        return [results_by_idx[i] for i in range(len(parsed_calls))]

    def _execute_parallel(
        self,
        calls: list[tuple[ToolCall, dict[str, Any]]],
        on_ui_event: Callable[[dict[str, Any]], None] | None = None,
    ) -> list[ToolExecutionResult]:
        """Execute tool calls in parallel using thread pool.

        Args:
            calls: List of (tool_call, arguments) tuples.
            on_ui_event: Optional callback for UI events.

        Returns:
            List of execution results.
        """
        results: list[ToolExecutionResult] = []

        if not calls:
            return results

        # Limit concurrent executions
        max_workers = min(len(calls), self.max_parallel_tools)

        logger.debug(f"Executing {len(calls)} read-only tools in parallel (max={max_workers})")

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_call = {
                    executor.submit(self._execute_single_tool, tc, args, on_ui_event): (tc, args)
                    for tc, args in calls
                }

                # Collect results as they complete
                call_results: dict[str, ToolExecutionResult] = {}
                try:
                    for future in as_completed(future_to_call):
                        tc, args = future_to_call[future]
                        try:
                            exec_result = future.result()
                            call_results[tc.id] = exec_result
                        except Exception as e:
                            # Handle execution errors
                            call_results[tc.id] = ToolExecutionResult(
                                tool_call=tc,
                                result=ToolResult(success=False, output=None, error=str(e)),
                                duration_ms=0,
                                arguments=args,
                            )
                except KeyboardInterrupt:
                    # Cancel pending futures on interrupt
                    for future in future_to_call:
                        future.cancel()
                    raise
        except RuntimeError as e:
            # Handle "cannot schedule new futures after interpreter shutdown"
            if "shutdown" in str(e).lower():
                logger.warning(f"Executor shutdown during parallel execution: {e}")
                raise KeyboardInterrupt("Interpreter shutting down") from e
            raise

        # Return results in original order
        for tc, args in calls:
            if tc.id in call_results:
                results.append(call_results[tc.id])

        return results

    def _execute_sequentially(
        self,
        calls: list[tuple[ToolCall, dict[str, Any]]],
        on_ui_event: Callable[[dict[str, Any]], None] | None = None,
    ) -> list[ToolExecutionResult]:
        """Execute tool calls sequentially.

        Args:
            calls: List of (tool_call, arguments) tuples.
            on_ui_event: Optional callback for UI events.

        Returns:
            List of execution results in order.
        """
        results: list[ToolExecutionResult] = []

        for tc, args in calls:
            exec_result = self._execute_single_tool(tc, args, on_ui_event)
            results.append(exec_result)

        return results

    def _execute_single_tool(
        self,
        tool_call: ToolCall,
        arguments: dict[str, Any],
        on_ui_event: Callable[[dict[str, Any]], None] | None = None,
    ) -> ToolExecutionResult:
        """Execute a single tool call with timing.

        Args:
            tool_call: The tool call to execute.
            arguments: Parsed arguments.
            on_ui_event: Optional callback for UI events.

        Returns:
            Execution result with timing metadata.
        """
        # Notify UI of tool start
        if on_ui_event:
            on_ui_event({"type": "tool_start", "tool": tool_call.name, "args": arguments})

        tool_start = time.time()

        # Check for duplicate file read (optimization to reduce LLM calls)
        if tool_call.name == "read_file" and "file_path" in arguments:
            cached_result = self._check_file_read_cache(arguments["file_path"])
            if cached_result is not None:
                duration_ms = (time.time() - tool_start) * 1000
                logger.debug(f"Returning cached read for {arguments['file_path']}")
                if on_ui_event:
                    on_ui_event(
                        {
                            "type": "tool_end",
                            "tool": tool_call.name,
                            "duration_ms": duration_ms,
                            "success": True,
                            "cached": True,
                        }
                    )
                return ToolExecutionResult(
                    tool_call=tool_call,
                    result=cached_result,
                    duration_ms=duration_ms,
                    arguments=arguments,
                )

        result = self.tools.execute(tool_call.name, arguments)
        duration_ms = (time.time() - tool_start) * 1000

        # Cache successful file reads
        if tool_call.name == "read_file" and result.success and "file_path" in arguments:
            self._cache_file_read(arguments["file_path"], result)

        # Notify UI of tool end - include diff for file modification tools
        if on_ui_event:
            event_data = {
                "type": "tool_end",
                "tool": tool_call.name,
                "duration_ms": duration_ms,
                "success": result.success,
            }
            # Include diff if present (for write_file, edit_file, apply_diff)
            if result.diff:
                event_data["diff"] = result.diff
            # Include output for file path extraction
            if result.success and isinstance(result.output, dict):
                event_data["output"] = result.output
            if not result.success and result.error:
                event_data["error"] = result.error
            on_ui_event(event_data)

        return ToolExecutionResult(
            tool_call=tool_call,
            result=result,
            duration_ms=duration_ms,
            arguments=arguments,
        )

    def _format_tool_result(self, result: ToolResult) -> str:
        """Format tool result for message history.

        Args:
            result: Tool execution result.

        Returns:
            Formatted string for LLM consumption.
        """
        if not result.success:
            return f"Error: {result.error or 'Unknown error'}"

        if result.output is None:
            return "Success (no output)"

        if isinstance(result.output, str):
            return result.output

        if isinstance(result.output, dict):
            # Handle cached file read specially
            if result.output.get("cached") and "content" in result.output:
                content = result.output["content"]
                return (
                    f"{content}\n\n"
                    "[CACHED: This file was already read earlier in this conversation. "
                    "DO NOT read this file again - the content is already in your context.]"
                )

            # Include diff if available
            output_str = json.dumps(result.output, indent=2, default=str)
            if result.diff:
                output_str += f"\n\n--- Diff ---\n{result.diff}"
            return output_str

        return str(result.output)

    def _check_file_read_cache(self, file_path: str) -> ToolResult | None:
        """Check if a file was already read and return cached result if unchanged.

        Args:
            file_path: Path to the file (can be relative or absolute).

        Returns:
            Cached ToolResult if file unchanged, None otherwise.
        """
        from pathlib import Path

        from red9.tools.base import get_project_root

        # Resolve to absolute path for consistent cache keys
        # Use project_root for relative paths (not CWD)
        try:
            path_obj = Path(file_path)
            if path_obj.is_absolute():
                abs_path = str(path_obj.resolve())
            else:
                # Relative path - resolve relative to project root
                abs_path = str((get_project_root() / file_path).resolve())
        except Exception:
            abs_path = file_path

        if abs_path not in self._files_read_cache:
            return None

        cached_content, cached_mtime = self._files_read_cache[abs_path]

        # Check if file still exists and has same mtime
        # Use single stat() call to avoid TOCTOU race between exists() and stat()
        try:
            path = Path(abs_path)
            current_mtime = path.stat().st_mtime
            if current_mtime != cached_mtime:
                # File modified - invalidate cache
                del self._files_read_cache[abs_path]
                return None

            # File unchanged - return cached content with a note
            logger.debug(f"Cache hit for {file_path} (returning cached content)")
            return ToolResult(
                success=True,
                output={"content": cached_content, "cached": True},
                error=None,
            )
        except (FileNotFoundError, OSError):
            # File deleted or inaccessible - invalidate cache
            if abs_path in self._files_read_cache:
                del self._files_read_cache[abs_path]
            return None
        except Exception:
            # On any error, invalidate cache and let fresh read happen
            self._files_read_cache.pop(abs_path, None)
            return None

    def _cache_file_read(self, file_path: str, result: ToolResult) -> None:
        """Cache a successful file read result.

        Args:
            file_path: Path to the file (can be relative or absolute).
            result: Successful read result.
        """
        from pathlib import Path

        from red9.tools.base import get_project_root

        try:
            # Use resolved path from result if available (most accurate)
            if isinstance(result.output, dict) and "file_path" in result.output:
                abs_path = result.output["file_path"]
            else:
                # Resolve relative paths using project root (not CWD)
                path_obj = Path(file_path)
                if path_obj.is_absolute():
                    abs_path = str(path_obj.resolve())
                else:
                    abs_path = str((get_project_root() / file_path).resolve())

            path = Path(abs_path)
            if not path.exists():
                return

            mtime = path.stat().st_mtime

            # Extract content from result
            content = ""
            if isinstance(result.output, dict):
                content = result.output.get("content", "")
            elif isinstance(result.output, str):
                content = result.output

            if content:
                self._files_read_cache[abs_path] = (content, mtime)
                logger.debug(f"Cached file read: {abs_path}")
        except Exception as e:
            logger.debug(f"Failed to cache file read {file_path}: {e}")


def load_agent_context(
    db_path: str,
    categories: list[str] | None = None,
) -> dict[str, str]:
    """Load relevant memories for agent guidelines from IssueDB.

    Args:
        db_path: Path to IssueDB database.
        categories: Categories to load (None = all).

    Returns:
        Dictionary of key-value guidelines.
    """
    try:
        from issuedb.repository import IssueRepository

        repo = IssueRepository(db_path=db_path)
        context: dict[str, str] = {}

        if categories:
            for category in categories:
                memories = repo.list_memory(category=category)
                for mem in memories:
                    context[f"[{category}] {mem.key}"] = mem.value
        else:
            # Load all memories
            memories = repo.list_memory()
            for mem in memories:
                cat = mem.category or "general"
                context[f"[{cat}] {mem.key}"] = mem.value

        return context

    except ImportError:
        logger.debug("IssueDB not available for agent context loading")
        return {}
    except Exception as e:
        logger.warning(f"Failed to load agent context from IssueDB: {e}")
        return {}


def format_guidelines(context: dict[str, str]) -> str:
    """Format guidelines dictionary as readable text.

    Args:
        context: Dictionary of guidelines.

    Returns:
        Formatted string.
    """
    if not context:
        return "No project guidelines available."

    lines = ["Project Guidelines:"]
    for key, value in context.items():
        lines.append(f"- {key}: {value}")

    return "\n".join(lines)
