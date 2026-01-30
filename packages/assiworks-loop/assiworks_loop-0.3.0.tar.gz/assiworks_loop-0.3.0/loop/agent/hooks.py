"""Custom hooks for Claude Agent SDK."""

from typing import Any, List
from claude_agent_sdk import HookMatcher, HookContext


async def block_dangerous_commands(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """Block dangerous bash commands."""
    if input_data.get("tool_name") != "Bash":
        return {}

    command = input_data.get("tool_input", {}).get("command", "")
    dangerous_patterns = [
        "rm -rf /",
        "rm -rf /*",
        "dd if=",
        "mkfs",
        "> /dev/sda",
        "> /dev/null",
        ":(){ :|:& };:",  # Fork bomb
    ]

    for pattern in dangerous_patterns:
        if pattern in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Dangerous command blocked: {pattern}",
                }
            }

    return {}


async def log_tool_use(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """Log tool usage for debugging."""
    # This hook is for logging purposes only
    # In production, you might want to write to a log file
    return {}


def create_safety_hooks(blocked_commands: List[str] = None) -> dict:
    """Create safety hooks configuration.

    Args:
        blocked_commands: Additional command patterns to block

    Returns:
        Hooks configuration dict for ClaudeAgentOptions
    """
    return {
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[block_dangerous_commands]),
            HookMatcher(hooks=[log_tool_use]),
        ]
    }
