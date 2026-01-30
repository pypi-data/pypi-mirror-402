"""Claude Agent SDK Client wrapper."""

from typing import AsyncIterator, Optional
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)


class LoopClient:
    """Thin wrapper around ClaudeSDKClient for AssiWorks Loop."""

    def __init__(self, options: ClaudeAgentOptions):
        self.options = options
        self._client: Optional[ClaudeSDKClient] = None
        self._session_id: Optional[str] = None

    async def __aenter__(self) -> "LoopClient":
        self._client = ClaudeSDKClient(options=self.options)
        await self._client.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.disconnect()
            self._client = None

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    async def query(self, prompt: str) -> AsyncIterator[tuple[str, any]]:
        """Send query and yield (event_type, data) tuples."""
        if not self._client:
            raise RuntimeError("Client not connected. Use 'async with' context.")

        await self._client.query(prompt)

        async for message in self._client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield ("text", block.text)
                    elif isinstance(block, ToolUseBlock):
                        yield ("tool_use", {"name": block.name, "input": block.input})
            elif isinstance(message, ResultMessage):
                self._session_id = message.session_id
                yield ("result", {
                    "session_id": message.session_id,
                    "num_turns": message.num_turns,
                    "total_cost_usd": message.total_cost_usd,
                    "is_error": message.is_error,
                    "error": getattr(message, "error", None),
                })

    async def interrupt(self):
        """Interrupt current operation."""
        if self._client:
            await self._client.interrupt()
