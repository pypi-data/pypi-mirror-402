"""CLI entry point."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click

from loop import __version__
from loop.agent.client import LoopClient
from loop.core.config import Config, load_config
from loop.core.session import Session, SessionManager
from loop.core.errors import LoopError, AgentError
from loop.core.ralph_loop import RalphLoop
from loop.cli import ui
from loop.cli.commands import CommandContext, handle_command


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.argument("path", required=False, default=None)
@click.option("--session", "-s", help="Resume session ID")
@click.option("--config", "-c", help="Config file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def main(ctx, path: Optional[str], session: Optional[str], config: Optional[str], verbose: bool):
    """AssiWorks Loop - AI Coding Assistant powered by Claude Agent SDK.

    Run without arguments or with a PATH to start interactive REPL.

    Examples:
        loop          Start REPL in current directory
        loop .        Start REPL in current directory
        loop ~/proj   Start REPL in ~/proj directory
    """
    if ctx.invoked_subcommand is None:
        # Default behavior: start REPL
        working_dir = None
        if path and path not in ("run", "ask", "ralph"):
            working_dir = path
        asyncio.run(_run_repl(session, config, verbose, working_dir))


@main.command()
@click.option("--session", "-s", help="Resume session ID")
@click.option("--config", "-c", help="Config file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(session: Optional[str], config: Optional[str], verbose: bool):
    """Start interactive REPL session."""
    asyncio.run(_run_repl(session, config, verbose))


@main.command()
@click.argument("prompt")
@click.option("--config", "-c", help="Config file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def ask(prompt: str, config: Optional[str], verbose: bool):
    """Ask a single question and exit."""
    asyncio.run(_run_single(prompt, config, verbose))


@main.command()
@click.argument("task")
@click.option("--max-loops", "-m", default=100, help="Maximum iterations")
@click.option("--config", "-c", help="Config file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def ralph(task: str, max_loops: int, config: Optional[str], verbose: bool):
    """Start Ralph autonomous loop."""
    asyncio.run(_run_ralph(task, max_loops, config, verbose))


async def _run_repl(
    session_id: Optional[str],
    config_path: Optional[str],
    verbose: bool,
    working_dir: Optional[str] = None,
):
    """Run interactive REPL."""
    # Load config
    cfg = load_config(config_path)

    # Resolve working directory
    if working_dir:
        work_path = Path(working_dir).expanduser().resolve()
        if not work_path.exists():
            ui.print_error(f"Path not found: {working_dir}")
            return
        if not work_path.is_dir():
            ui.print_error(f"Not a directory: {working_dir}")
            return
        import os
        os.chdir(work_path)

    # Session management
    session_manager = SessionManager(cfg.session_dir)

    # Load or create session
    if session_id:
        session = session_manager.load(session_id)
        if not session:
            ui.print_error(f"Session not found: {session_id}")
            return
        ui.print_info(f"Resuming session: {session_id}")
    else:
        session = Session(
            working_directory=str(Path.cwd()),
            model=cfg.model,
        )

    # Print banner
    ui.print_banner()
    ui.print_session_info(
        session.id,
        cfg.model,
        session.working_directory,
    )

    # Create command context
    context = CommandContext(
        config=cfg,
        session=session,
        session_manager=session_manager,
    )

    # Create SDK options
    sdk_options = cfg.to_sdk_options(resume=session.sdk_session_id)

    try:
        async with LoopClient(sdk_options) as client:
            while True:
                # Get user input
                try:
                    user_input = await ui.get_prompt_async()
                except KeyboardInterrupt:
                    ui.console.print()
                    break

                if not user_input.strip():
                    continue

                # Handle slash commands
                if user_input.startswith("/"):
                    result = await handle_command(user_input, context, client)
                    if result.should_exit:
                        break
                    if result.handled:
                        continue
                    # Special handling for ralph start
                    if result.message == "ralph_start":
                        ui.print_info("Use 'loop ralph <task>' command for autonomous mode.")
                        continue

                # Send to Claude
                try:
                    response_text = ""
                    streaming_text = False  # Track if we're in streaming text mode
                    async for event_type, data in client.query(user_input):
                        if event_type == "text":
                            if not streaming_text:
                                ui.console.print()  # New line before response
                                streaming_text = True
                            # Stream text in real-time
                            ui.print_streaming_text(data)
                            response_text += data
                        elif event_type == "tool_use":
                            # End streaming text mode before showing tool
                            if streaming_text:
                                ui.console.print()  # End current line
                                streaming_text = False
                            # Always show tool usage for visibility
                            ui.print_tool_use(data["name"], data["input"])
                        elif event_type == "result":
                            # End streaming text mode
                            if streaming_text:
                                ui.console.print()  # End current line
                                streaming_text = False
                            # Update session with SDK session ID
                            session.update(data["session_id"])
                            if verbose:
                                ui.print_result(
                                    data["num_turns"],
                                    data.get("total_cost_usd"),
                                )

                    # Final newline after all output
                    ui.console.print()

                except Exception as e:
                    ui.print_error(str(AgentError.from_sdk_error(e)))

    except KeyboardInterrupt:
        ui.console.print("\n")
        ui.print_info("Interrupted.")
    finally:
        # Save session on exit
        session_manager.save(session)
        ui.print_success("Session saved.")


async def _run_single(
    prompt: str,
    config_path: Optional[str],
    verbose: bool,
):
    """Run single query."""
    cfg = load_config(config_path)
    sdk_options = cfg.to_sdk_options()

    try:
        async with LoopClient(sdk_options) as client:
            response_text = ""
            streaming_text = False
            async for event_type, data in client.query(prompt):
                if event_type == "text":
                    if not streaming_text:
                        streaming_text = True
                    ui.print_streaming_text(data)
                    response_text += data
                elif event_type == "tool_use":
                    if streaming_text:
                        ui.console.print()  # End current line
                        streaming_text = False
                    if verbose:
                        ui.print_tool_use(data["name"], data["input"])
                elif event_type == "result":
                    if streaming_text:
                        ui.console.print()  # End current line
                        streaming_text = False
                    if verbose:
                        ui.print_result(
                            data["num_turns"],
                            data.get("total_cost_usd"),
                        )

            ui.console.print()  # Final newline

    except Exception as e:
        ui.print_error(str(AgentError.from_sdk_error(e)))
        sys.exit(1)


async def _run_ralph(
    task: str,
    max_loops: int,
    config_path: Optional[str],
    verbose: bool,
):
    """Run Ralph autonomous loop."""
    cfg = load_config(config_path)
    cfg.ralph_max_iterations = max_loops

    session_manager = SessionManager(cfg.session_dir)
    session = Session(
        working_directory=str(Path.cwd()),
        model=cfg.model,
    )

    sdk_options = cfg.to_sdk_options()

    # Create live status display
    status_display = ui.LiveStatusDisplay()

    def on_iteration(status):
        # Update live status display
        status_display.update(
            phase=status.phase.value,
            iteration=status.iteration,
            max_iterations=status.max_iterations,
            circuit_breaker=status.circuit_breaker_state.value,
        )
        if verbose and status.last_response:
            # Show a snippet of the last response
            snippet = status.last_response[:100].replace("\n", " ")
            if len(status.last_response) > 100:
                snippet += "..."
            status_display.update(last_action=snippet)

    def on_complete(status):
        status_display.stop()
        ui.console.print()
        ui.print_success(f"Ralph loop completed: {status.phase.value}")
        ui.console.print(f"Total iterations: {status.iteration}")

    def on_tool_use(tool_name: str, tool_input: dict):
        """Callback for tool usage."""
        status_display.update(current_tool=tool_name)
        ui.print_tool_use(tool_name, tool_input)

    def on_text(text: str):
        """Callback for streaming text."""
        ui.print_streaming_text(text)

    ralph = RalphLoop(
        max_iterations=max_loops,
        no_progress_threshold=cfg.ralph_no_progress_threshold,
        same_error_threshold=cfg.ralph_same_error_threshold,
        on_iteration=on_iteration,
        on_complete=on_complete,
        on_tool_use=on_tool_use,
        on_text=on_text,
    )

    ui.print_banner()
    ui.print_info(f"Starting Ralph loop: {task}")
    ui.console.print(f"Max iterations: {max_loops}")
    ui.console.print()

    try:
        status_display.start()
        async with LoopClient(sdk_options) as client:
            await ralph.start(client, task)

    except KeyboardInterrupt:
        status_display.stop()
        ui.print_warning("Interrupted by user.")
    except Exception as e:
        status_display.stop()
        ui.print_error(str(e))
        sys.exit(1)
    finally:
        status_display.stop()
        session_manager.save(session)


if __name__ == "__main__":
    main()
