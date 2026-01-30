"""Error definitions - wrapping SDK errors."""

from claude_agent_sdk import (
    ClaudeSDKError,
    CLINotFoundError,
    CLIConnectionError,
    ProcessError,
)


class LoopError(Exception):
    """Base error for AssiWorks Loop."""

    pass


class ConfigError(LoopError):
    """Configuration error."""

    pass


class SessionError(LoopError):
    """Session management error."""

    pass


class AgentError(LoopError):
    """Agent execution error."""

    @classmethod
    def from_sdk_error(cls, e: ClaudeSDKError) -> "AgentError":
        """Create AgentError from SDK error."""
        if isinstance(e, CLINotFoundError):
            return cls(
                "Claude Code CLI not found. "
                "Install: brew install --cask claude-code"
            )
        elif isinstance(e, CLIConnectionError):
            return cls(f"Failed to connect to Claude: {e}")
        elif isinstance(e, ProcessError):
            return cls(f"Process error (exit={e.exit_code}): {e.stderr}")
        return cls(str(e))


class RalphLoopError(LoopError):
    """Ralph Loop execution error."""

    pass


class CircuitBreakerOpenError(RalphLoopError):
    """Circuit breaker is open - stopping execution."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Circuit breaker opened: {reason}")
