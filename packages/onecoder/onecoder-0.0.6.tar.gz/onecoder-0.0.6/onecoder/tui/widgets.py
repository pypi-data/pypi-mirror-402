"""Custom widgets for OneCoder TUI."""

from textual.widgets import Static, LoadingIndicator, Input, Button, Label
from textual.containers import Vertical, Horizontal, Grid
from textual.binding import Binding
from textual.message import Message
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Optional


class ChatMessage(Static):
    """Widget for displaying chat messages with markdown support."""

    def __init__(self, message: str, role: str = "user", **kwargs):
        super().__init__(**kwargs)
        self.message = message
        self.role = role

    def render(self):
        if self.role == "user":
            panel = Panel(
                self.message, title="You", border_style="bold blue", padding=(0, 1)
            )
            return panel
        else:
            panel = Panel(
                Markdown(self.message),
                title="OneCoder",
                border_style="bold green",
                padding=(0, 1),
            )
            return panel


class ToolCallStatus(Static):
    """Widget for displaying tool call status."""

    def __init__(self, tool_name: str, status: str = "running", **kwargs):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.status = status

    def render(self):
        if self.status == "running":
            content = f"Running {self.tool_name}..."
            border_style = "bold yellow"
        elif self.status == "success":
            content = f"✓ {self.tool_name} finished"
            border_style = "bold green"
        else:
            content = f"✗ {self.tool_name} failed"
            border_style = "bold red"

        panel = Panel(
            content, title="Tool Call", border_style=border_style, padding=(0, 1)
        )
        return panel


class ErrorMessage(Static):
    """Widget for displaying error messages."""

    def __init__(self, message: str, **kwargs):
        super().__init__(**kwargs)
        self.message = message

    def render(self):
        panel = Panel(
            self.message,
            title="Error",
            border_style="bold red",
            style="red",
            padding=(0, 1),
        )
        return panel


class WelcomeMessage(Static):
    """Widget for displaying welcome message on startup."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def render(self):
        from rich.text import Text
        from rich.console import Group

        title = Text("OneCoder TUI", style="bold blue")
        subtitle = Text(
            "Modern terminal interface for AI-powered coding assistance", style="dim"
        )

        panel = Panel(Group(title, "", subtitle), border_style="blue", padding=(1, 2))
        return panel

class SprintDashboard(Static):
    """Widget for displaying active sprint status and alignment."""
    
    def __init__(self, sprint_id: str = "N/A", status: str = "Unknown", **kwargs):
        super().__init__(**kwargs)
        self.sprint_id = sprint_id
        self.status = status

    def render(self):
        color = "green" if self.status == "ALIGNED" else "yellow" if self.status == "DRIFTING" else "red"
        content = f"[bold]Sprint:[/bold] {self.sprint_id}\n[bold]Status:[/bold] [{color}]{self.status}[/{color}]"
        return Panel(content, title="Sprint Alignment", border_style="blue")

class TaskQueue(Static):
    """Widget for displaying the task queue and current progress."""
    
    def __init__(self, tasks: list = None, **kwargs):
        super().__init__(**kwargs)
        self.tasks = tasks or []

    def render(self):
        lines = []
        for i, task in enumerate(self.tasks):
            marker = "[green]✓[/green]" if task.get("status") == "done" else "[yellow]>[/yellow]" if task.get("status") == "in-progress" else "[dim]·[/dim]"
            lines.append(f"{marker} {task.get('title', 'Untitled Task')}")
        
        content = "\n".join(lines) if lines else "[dim]No tasks in queue[/dim]"
        return Panel(content, title="Task Queue", border_style="cyan")

class TokenBudget(Static):
    """Widget for monitoring token consumption."""
    
    def __init__(self, percent: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.percent = percent

    def render(self):
        bar_len = 20
        filled = int(self.percent / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        color = "green" if self.percent < 70 else "yellow" if self.percent < 90 else "red"
        
        content = f"Budget: [{color}]{bar}[/{color}] {self.percent}%"
        return Panel(content, title="Resource Consumption", border_style="magenta")

class ConnectivityStatus(Static):
    """Widget for displaying connectivity state (API and LLM)."""
    
    def __init__(self, api_connected: bool = False, llm_ready: bool = False, env_loaded: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.api_connected = api_connected
        self.llm_ready = llm_ready
        self.env_loaded = env_loaded

    def render(self):
        api_icon = "[green]●[/green]" if self.api_connected else "[red]○[/red]"
        llm_icon = "[green]●[/green]" if self.llm_ready else "[red]○[/red]"
        env_icon = "[green]✓[/green]" if self.env_loaded else "[red]✗[/red]"
        
        content = (
            f"{api_icon} [bold]OneCoder API:[/bold] {'Connected' if self.api_connected else 'Disconnected'}\n"
            f"{llm_icon} [bold]LLM Backend:[/bold] {'Ready' if self.llm_ready else 'Not Configured'}\n"
            f"{env_icon} [bold].env File:[/bold] {'Loaded' if self.env_loaded else 'Not Found'}"
        )
        return Panel(content, title="Connectivity", border_style="dim")

class SuggestiveInput(Input):
    """Input widget that accepts suggestions with Tab."""
    
    BINDINGS = [
        Binding("tab", "cursor_right", "Accept Suggestion", show=False),
    ]

class HITLConfirmation(Static):
    """
    Human-In-The-Loop dialog for reviewing and approving file changes.
    """
    
    class Confirmed(Message):
        """Emitted when the user makes a choice."""
        def __init__(self, choice: str):
            super().__init__()
            self.choice = choice

    def __init__(self, file_path: str, diff: str, **kwargs):
        super().__init__(**kwargs)
        self.file_path = file_path
        self.diff = diff

    def compose(self):
        from rich.syntax import Syntax
        
        yield Vertical(
            Label(f"[bold white]File:[/bold white] [cyan]{self.file_path}[/cyan]", id="hitl-header"),
            Static(Syntax(self.diff, "diff", theme="monokai", line_numbers=True), id="hitl-diff"),
            Label("Apply this change?", id="hitl-question"),
            Horizontal(
                Button("Yes, allow once", variant="success", id="allow-once"),
                Button("Yes, allow always", variant="primary", id="allow-always"),
                Button("Modify", variant="warning", id="modify-change"),
                Button("No, reject", variant="error", id="reject-change"),
                id="hitl-buttons"
            ),
            id="hitl-container"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        choice = str(event.button.id).replace("-", "_")
        self.post_message(self.Confirmed(choice))
        self.remove()
