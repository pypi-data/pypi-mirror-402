"""Ralph Loop - Autonomous execution loop with Circuit Breaker."""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Any

from loop.agent.client import LoopClient
from loop.core.errors import CircuitBreakerOpenError


class LoopPhase(Enum):
    """Ralph Loop execution phases."""

    PLANNING = "planning"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    HALTED = "halted"
    COMPLETED = "completed"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    HALF_OPEN = "half_open"  # Testing
    OPEN = "open"  # Blocked


@dataclass
class CircuitBreaker:
    """Circuit breaker for preventing infinite loops."""

    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    no_progress_count: int = 0
    same_error_count: int = 0
    last_error: Optional[str] = None
    history: list = field(default_factory=list)

    # Thresholds
    no_progress_threshold: int = 3
    same_error_threshold: int = 5

    def record_progress(self):
        """Record that progress was made."""
        self.no_progress_count = 0
        self.same_error_count = 0
        self.last_error = None
        self.state = CircuitBreakerState.CLOSED
        self.history.append(("progress", None))

    def record_no_progress(self):
        """Record that no progress was made."""
        self.no_progress_count += 1
        self.history.append(("no_progress", self.no_progress_count))

        if self.no_progress_count >= self.no_progress_threshold:
            self.state = CircuitBreakerState.OPEN

    def record_error(self, error: str):
        """Record an error."""
        if error == self.last_error:
            self.same_error_count += 1
        else:
            self.same_error_count = 1
            self.last_error = error

        self.history.append(("error", error))

        if self.same_error_count >= self.same_error_threshold:
            self.state = CircuitBreakerState.OPEN

    def should_halt(self) -> bool:
        """Check if execution should halt."""
        return self.state == CircuitBreakerState.OPEN

    def get_halt_reason(self) -> str:
        """Get reason for halting."""
        if self.no_progress_count >= self.no_progress_threshold:
            return f"No progress for {self.no_progress_count} iterations"
        if self.same_error_count >= self.same_error_threshold:
            return f"Same error repeated {self.same_error_count} times: {self.last_error}"
        return "Unknown"

    def reset(self):
        """Reset circuit breaker state."""
        self.state = CircuitBreakerState.CLOSED
        self.no_progress_count = 0
        self.same_error_count = 0
        self.last_error = None
        self.history.clear()


@dataclass
class LoopStatus:
    """Status of Ralph Loop execution."""

    phase: LoopPhase
    iteration: int
    max_iterations: int
    circuit_breaker_state: CircuitBreakerState
    last_response: Optional[str] = None
    error: Optional[str] = None


class RalphLoop:
    """Autonomous execution loop with circuit breaker protection."""

    def __init__(
        self,
        max_iterations: int = 100,
        no_progress_threshold: int = 3,
        same_error_threshold: int = 5,
        on_iteration: Optional[Callable[[LoopStatus], None]] = None,
        on_complete: Optional[Callable[[LoopStatus], None]] = None,
        on_tool_use: Optional[Callable[[str, dict], None]] = None,
        on_text: Optional[Callable[[str], None]] = None,
    ):
        self.max_iterations = max_iterations
        self.circuit_breaker = CircuitBreaker(
            no_progress_threshold=no_progress_threshold,
            same_error_threshold=same_error_threshold,
        )
        self.on_iteration = on_iteration
        self.on_complete = on_complete
        self.on_tool_use = on_tool_use
        self.on_text = on_text

        self._phase = LoopPhase.READY
        self._iteration = 0
        self._stop_requested = False
        self._last_response: Optional[str] = None

    @property
    def phase(self) -> LoopPhase:
        return self._phase

    @property
    def iteration(self) -> int:
        return self._iteration

    def get_status(self) -> LoopStatus:
        """Get current loop status."""
        return LoopStatus(
            phase=self._phase,
            iteration=self._iteration,
            max_iterations=self.max_iterations,
            circuit_breaker_state=self.circuit_breaker.state,
            last_response=self._last_response,
        )

    def request_stop(self):
        """Request the loop to stop."""
        self._stop_requested = True

    def _check_completion_signal(self, response: str) -> bool:
        """Check if response contains completion signals."""
        completion_patterns = [
            "task completed",
            "task is complete",
            "finished successfully",
            "all done",
            "work is complete",
            "nothing more to do",
            "EXIT_SIGNAL: true",
        ]
        response_lower = response.lower()
        return any(pattern in response_lower for pattern in completion_patterns)

    def _detect_progress(self, response: str) -> bool:
        """Detect if progress was made based on response."""
        # Check for tool usage or substantive work
        progress_indicators = [
            "[tool]",
            "created",
            "modified",
            "updated",
            "implemented",
            "fixed",
            "added",
            "wrote",
            "edited",
        ]
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in progress_indicators)

    async def start(
        self,
        client: LoopClient,
        initial_prompt: str,
        continuation_prompt: str = "Continue with the task. What's the next step?",
    ):
        """Start the autonomous loop.

        Args:
            client: LoopClient instance (must be connected)
            initial_prompt: Initial task description
            continuation_prompt: Prompt for subsequent iterations
        """
        self._phase = LoopPhase.RUNNING
        self._iteration = 0
        self._stop_requested = False
        self.circuit_breaker.reset()

        current_prompt = initial_prompt

        while self._iteration < self.max_iterations:
            self._iteration += 1

            # Check stop conditions
            if self._stop_requested:
                self._phase = LoopPhase.PAUSED
                break

            if self.circuit_breaker.should_halt():
                self._phase = LoopPhase.HALTED
                raise CircuitBreakerOpenError(self.circuit_breaker.get_halt_reason())

            # Execute query
            response_text = ""
            try:
                async for event_type, data in client.query(current_prompt):
                    if event_type == "text":
                        response_text += data
                        # Stream text in real-time
                        if self.on_text:
                            self.on_text(data)
                    elif event_type == "tool_use":
                        # Notify tool usage
                        if self.on_tool_use:
                            self.on_tool_use(data.get("name", "unknown"), data.get("input", {}))
                    elif event_type == "result":
                        if data.get("is_error"):
                            self.circuit_breaker.record_error(
                                data.get("error", "Unknown error")
                            )

            except Exception as e:
                self.circuit_breaker.record_error(str(e))
                if self.circuit_breaker.should_halt():
                    self._phase = LoopPhase.HALTED
                    raise CircuitBreakerOpenError(self.circuit_breaker.get_halt_reason())
                continue

            self._last_response = response_text

            # Check for completion
            if self._check_completion_signal(response_text):
                self._phase = LoopPhase.COMPLETED
                break

            # Check for progress
            if self._detect_progress(response_text):
                self.circuit_breaker.record_progress()
            else:
                self.circuit_breaker.record_no_progress()

            # Notify iteration callback
            if self.on_iteration:
                self.on_iteration(self.get_status())

            # Prepare next iteration
            current_prompt = continuation_prompt

            # Small delay to prevent tight loop
            await asyncio.sleep(0.1)

        # Final status
        if self._iteration >= self.max_iterations:
            self._phase = LoopPhase.HALTED

        if self.on_complete:
            self.on_complete(self.get_status())

    async def stop(self, client: LoopClient):
        """Stop the loop gracefully."""
        self._stop_requested = True
        await client.interrupt()
