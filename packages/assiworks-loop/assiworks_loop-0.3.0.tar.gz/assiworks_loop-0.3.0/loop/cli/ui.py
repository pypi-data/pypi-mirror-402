"""Rich UI components for terminal output."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.syntax import Syntax
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from pathlib import Path


console = Console()


def print_banner():
    """Print application banner."""
    # Colors: assi=#0174F7 (blue), works=#702EFF (purple), loop=yellow
    assi_color = "#0174F7"
    works_color = "#702EFF"
    loop_color = "yellow"

    # Line 1: ASSI = ▄▀█ █▀ █▀ █ | WORKS = █ █ █▀█ █▀█ █▄▀ █▀ | LOOP = █   █▀█ █▀█ █▀█
    # Line 2: ASSI = █▀█ ▄█ ▄█ █ | WORKS = ▀▄▀▄▀ █▄█ █▀▄ █ █ ▄█ | LOOP = █▄▄ █▄█ █▄█ █▀
    line1 = Text()
    line1.append("     ")
    line1.append("▄▀█ █▀ █▀ █ ", style=assi_color)
    line1.append("█ █ █ █▀█ █▀█ █▄▀ █▀ ", style=works_color)
    line1.append("█   █▀█ █▀█ █▀█", style=loop_color)

    line2 = Text()
    line2.append("     ")
    line2.append("█▀█ ▄█ ▄█ █ ", style=assi_color)
    line2.append("▀▄▀▄▀ █▄█ █▀▄ █ █ ▄█ ", style=works_color)
    line2.append("█▄▄ █▄█ █▄█ █▀ ", style=loop_color)

    line3 = Text()
    line3.append("              ")
    line3.append("LOOP", style=loop_color)
    line3.append(" v0.3.0")

    line4 = Text("       Powered by Claude Agent SDK")

    banner_text = Text()
    banner_text.append_text(line1)
    banner_text.append("\n")
    banner_text.append_text(line2)
    banner_text.append("\n")
    banner_text.append_text(line3)
    banner_text.append("\n")
    banner_text.append_text(line4)

    console.print(Panel(banner_text, border_style="cyan"))


def print_session_info(session_id: str, model: str, cwd: str):
    """Print session information."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="dim")
    table.add_column()
    table.add_row("Model:", model)
    table.add_row("Session:", session_id)
    table.add_row("Working dir:", cwd)
    console.print(table)
    console.print("[dim]Type /help for commands[/dim]\n")


def print_help():
    """Print help message."""
    help_text = """
[bold]Available Commands:[/bold]

[cyan]/help[/cyan]          Show this help message
[cyan]/exit[/cyan], [cyan]/quit[/cyan], [cyan]/q[/cyan]  Save session and exit
[cyan]/clear[/cyan]         Clear conversation history
[cyan]/save[/cyan]          Save current session
[cyan]/tools[/cyan]         List available tools
[cyan]/session[/cyan]       Show session information
[cyan]/interrupt[/cyan]     Interrupt current operation

[bold]Ralph Loop:[/bold]
[cyan]/ralph start[/cyan]   Start autonomous loop
[cyan]/ralph stop[/cyan]    Stop autonomous loop
[cyan]/ralph status[/cyan]  Show loop status
"""
    console.print(Panel(help_text.strip(), title="Help", border_style="blue"))


def print_tool_use(tool_name: str, tool_input: dict):
    """Print tool usage with clear visual separation."""
    console.print()  # Newline before tool
    console.print(f"[dim]┌─[/dim] [bold yellow]🔧 {tool_name}[/bold yellow]")

    # Special handling for Edit tool
    if tool_name == "Edit":
        file_path = tool_input.get("file_path", "")
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        replace_all = tool_input.get("replace_all", False)

        console.print(f"[dim]│[/dim]  [cyan]file_path=[/cyan]{file_path}")
        if replace_all:
            console.print(f"[dim]│[/dim]  [cyan]replace_all=[/cyan]{replace_all}")

        if old_string:
            console.print(f"[dim]│[/dim]  [red]- old_string:[/red]")
            for line in old_string.split("\n"):
                console.print(f"[dim]│[/dim]    [red]{line}[/red]")

        if new_string:
            console.print(f"[dim]│[/dim]  [green]+ new_string:[/green]")
            for line in new_string.split("\n"):
                console.print(f"[dim]│[/dim]    [green]{line}[/green]")
    else:
        # Default handling for other tools
        def truncate_value(v, max_len=60):
            s = str(v)
            if len(s) > max_len:
                return s[:max_len] + "..."
            return s

        for k, v in tool_input.items():
            console.print(f"[dim]│[/dim]  [cyan]{k}=[/cyan]{truncate_value(v)}")

    console.print(f"[dim]└─[/dim]")


def print_text_response(text: str):
    """Print text response with markdown rendering."""
    console.print(Markdown(text))


def print_error(message: str):
    """Print error message."""
    console.print(Panel(message, title="Error", border_style="red", style="red"))


def print_success(message: str):
    """Print success message."""
    console.print(f"[green]{message}[/green]")


def print_info(message: str):
    """Print info message."""
    console.print(f"[blue]{message}[/blue]")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[yellow]{message}[/yellow]")


def print_result(num_turns: int, cost: float = None):
    """Print result summary."""
    msg = f"[dim]Completed in {num_turns} turn(s)"
    if cost:
        msg += f" | Cost: ${cost:.4f}"
    msg += "[/dim]"
    console.print(msg)


# Global prompt session for history support
_prompt_session = None


def _get_prompt_session() -> PromptSession:
    """Get or create prompt session with history."""
    global _prompt_session
    if _prompt_session is None:
        history_file = Path.home() / ".assiworks_loop_history"
        _prompt_session = PromptSession(history=FileHistory(str(history_file)))
    return _prompt_session


async def get_prompt_async() -> str:
    """Get user input with prompt (async, supports arrow keys and history)."""
    try:
        session = _get_prompt_session()
        return await session.prompt_async("> ")
    except EOFError:
        return "/exit"


def get_prompt() -> str:
    """Get user input with prompt (sync fallback)."""
    try:
        return input("> ")
    except EOFError:
        return "/exit"


class SpinnerContext:
    """Context manager for spinner display."""

    def __init__(self, message: str = "Thinking..."):
        self.message = message
        self.live = None

    def __enter__(self):
        self.live = Live(
            Spinner("dots", text=self.message),
            console=console,
            transient=True,
        )
        self.live.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.live:
            self.live.__exit__(exc_type, exc_val, exc_tb)

    def update(self, message: str):
        """Update spinner message."""
        if self.live:
            self.live.update(Spinner("dots", text=message))


def print_streaming_text(text: str, end: str = ""):
    """Print text in streaming mode (no newline by default)."""
    console.print(text, end=end, highlight=False)


def print_phase(phase: str, iteration: int = None, max_iteration: int = None):
    """Print current execution phase."""
    phase_icons = {
        "planning": "📋",
        "ready": "✅",
        "running": "🔄",
        "paused": "⏸️",
        "halted": "🛑",
        "completed": "✨",
    }
    icon = phase_icons.get(phase.lower(), "•")

    if iteration is not None and max_iteration is not None:
        console.print(f"\n[bold cyan]{icon} Phase: {phase}[/bold cyan] [{iteration}/{max_iteration}]")
    else:
        console.print(f"\n[bold cyan]{icon} Phase: {phase}[/bold cyan]")


def print_status_bar(status: dict):
    """Print a compact status bar."""
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

    phase = status.get("phase", "unknown")
    iteration = status.get("iteration", 0)
    max_iter = status.get("max_iterations", 100)
    cb_state = status.get("circuit_breaker", "closed")

    # Color based on circuit breaker state
    cb_colors = {
        "closed": "green",
        "half_open": "yellow",
        "open": "red",
    }
    cb_color = cb_colors.get(cb_state, "white")

    bar = Text()
    bar.append("│ ", style="dim")
    bar.append(f"Phase: ", style="dim")
    bar.append(f"{phase}", style="bold cyan")
    bar.append(" │ ", style="dim")
    bar.append(f"Iter: ", style="dim")
    bar.append(f"{iteration}/{max_iter}", style="bold")
    bar.append(" │ ", style="dim")
    bar.append(f"Circuit: ", style="dim")
    bar.append(f"{cb_state}", style=f"bold {cb_color}")
    bar.append(" │", style="dim")

    console.print(bar)


class LiveStatusDisplay:
    """Live updating status display for Ralph Loop."""

    def __init__(self):
        self.live = None
        self._status = {
            "phase": "ready",
            "iteration": 0,
            "max_iterations": 100,
            "circuit_breaker": "closed",
            "last_action": "",
            "current_tool": None,
        }

    def _render(self) -> Panel:
        """Render the status panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="dim", width=12)
        table.add_column()

        # Phase with icon
        phase_icons = {
            "planning": "📋",
            "ready": "✅",
            "running": "🔄",
            "paused": "⏸️",
            "halted": "🛑",
            "completed": "✨",
        }
        phase = self._status["phase"]
        icon = phase_icons.get(phase.lower(), "•")
        table.add_row("Phase:", f"{icon} {phase}")

        # Iteration progress
        iter_current = self._status["iteration"]
        iter_max = self._status["max_iterations"]
        progress_pct = (iter_current / iter_max * 100) if iter_max > 0 else 0
        table.add_row("Progress:", f"{iter_current}/{iter_max} ({progress_pct:.0f}%)")

        # Circuit breaker
        cb_state = self._status["circuit_breaker"]
        cb_colors = {"closed": "green", "half_open": "yellow", "open": "red"}
        cb_style = cb_colors.get(cb_state, "white")
        table.add_row("Circuit:", Text(cb_state, style=cb_style))

        # Current tool
        if self._status["current_tool"]:
            table.add_row("Tool:", Text(self._status["current_tool"], style="yellow"))

        # Last action
        if self._status["last_action"]:
            action = self._status["last_action"][:40]
            if len(self._status["last_action"]) > 40:
                action += "..."
            table.add_row("Action:", Text(action, style="dim"))

        return Panel(table, title="[bold]Ralph Loop Status[/bold]", border_style="cyan")

    def start(self):
        """Start the live display."""
        self.live = Live(
            self._render(),
            console=console,
            refresh_per_second=4,
            transient=False,
        )
        self.live.start()

    def stop(self):
        """Stop the live display."""
        if self.live:
            self.live.stop()
            self.live = None

    def update(self, **kwargs):
        """Update status values."""
        self._status.update(kwargs)
        if self.live:
            self.live.update(self._render())

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
