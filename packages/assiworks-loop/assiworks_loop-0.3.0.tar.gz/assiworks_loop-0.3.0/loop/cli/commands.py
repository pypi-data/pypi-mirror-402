"""Slash command handlers."""

from typing import Optional, Callable, Awaitable
from dataclasses import dataclass

from loop.cli import ui
from loop.core.session import Session, SessionManager
from loop.core.config import Config


@dataclass
class CommandContext:
    """Context for command execution."""

    config: Config
    session: Session
    session_manager: SessionManager
    ralph_loop: Optional[any] = None  # RalphLoop instance when running


class CommandResult:
    """Result of command execution."""

    def __init__(
        self,
        handled: bool = True,
        should_exit: bool = False,
        message: Optional[str] = None,
    ):
        self.handled = handled
        self.should_exit = should_exit
        self.message = message


async def handle_command(
    command: str,
    context: CommandContext,
    client: Optional[any] = None,
) -> CommandResult:
    """Handle slash command.

    Args:
        command: Command string (e.g., "/help", "/ralph start")
        context: Command context
        client: LoopClient instance (for ralph commands)

    Returns:
        CommandResult indicating how command was handled
    """
    parts = command.strip().split()
    if not parts:
        return CommandResult(handled=False)

    cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    # Help
    if cmd in ["/help", "/?"]:
        ui.print_help()
        return CommandResult()

    # Exit
    if cmd in ["/exit", "/quit", "/q"]:
        # Save session before exit
        context.session_manager.save(context.session)
        ui.print_success("Session saved.")
        return CommandResult(should_exit=True)

    # Clear
    if cmd == "/clear":
        # Note: This creates a new session since SDK doesn't support clearing
        context.session = Session(
            working_directory=context.session.working_directory,
            model=context.config.model,
        )
        ui.print_success("Conversation cleared. New session started.")
        return CommandResult()

    # Save
    if cmd == "/save":
        context.session_manager.save(context.session)
        ui.print_success(f"Session saved: {context.session.id}")
        return CommandResult()

    # Tools
    if cmd == "/tools":
        ui.console.print("[bold]Available Tools:[/bold]")
        for tool in context.config.allowed_tools:
            ui.console.print(f"  [cyan]{tool}[/cyan]")
        return CommandResult()

    # Session info
    if cmd == "/session":
        ui.console.print("[bold]Session Information:[/bold]")
        ui.console.print(f"  ID: {context.session.id}")
        ui.console.print(f"  SDK Session: {context.session.sdk_session_id or 'Not set'}")
        ui.console.print(f"  Created: {context.session.created_at}")
        ui.console.print(f"  Updated: {context.session.updated_at}")
        ui.console.print(f"  Directory: {context.session.working_directory}")
        return CommandResult()

    # Interrupt
    if cmd == "/interrupt":
        if client:
            await client.interrupt()
            ui.print_warning("Interrupted.")
        return CommandResult()

    # Ralph commands
    if cmd == "/ralph":
        if not args:
            ui.print_error("Usage: /ralph <start|stop|status>")
            return CommandResult()

        subcmd = args[0].lower()

        if subcmd == "start":
            # Ralph loop start is handled in main.py
            return CommandResult(handled=False, message="ralph_start")

        elif subcmd == "stop":
            if context.ralph_loop:
                context.ralph_loop.request_stop()
                ui.print_warning("Ralph loop stop requested.")
            else:
                ui.print_warning("No Ralph loop is running.")
            return CommandResult()

        elif subcmd == "status":
            if context.ralph_loop:
                status = context.ralph_loop.get_status()
                ui.console.print("[bold]Ralph Loop Status:[/bold]")
                ui.console.print(f"  Phase: {status.phase.value}")
                ui.console.print(f"  Iteration: {status.iteration}/{status.max_iterations}")
                ui.console.print(f"  Circuit Breaker: {status.circuit_breaker_state.value}")
            else:
                ui.print_info("No Ralph loop is running.")
            return CommandResult()

        else:
            ui.print_error(f"Unknown ralph command: {subcmd}")
            return CommandResult()

    # Unknown command
    if cmd.startswith("/"):
        ui.print_error(f"Unknown command: {cmd}")
        ui.print_info("Type /help for available commands.")
        return CommandResult()

    # Not a command
    return CommandResult(handled=False)
