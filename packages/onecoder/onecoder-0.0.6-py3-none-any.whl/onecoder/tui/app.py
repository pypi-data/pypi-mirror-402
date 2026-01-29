"""OneCoder Textual TUI Application."""

import asyncio
import json
import httpx
import os
import logging
from typing import Optional, AsyncGenerator

logger = logging.getLogger(__name__)

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Label, LoadingIndicator
from textual.containers import Vertical, Container, Horizontal
from textual import events
from textual.binding import Binding

from rich.panel import Panel
from rich.markdown import Markdown

from .widgets import (
    ChatMessage, ToolCallStatus, ErrorMessage, WelcomeMessage, 
    SuggestiveInput, SprintDashboard, TaskQueue, TokenBudget, ConnectivityStatus
)
from .commands import CommandRegistry, CommandSuggester
from .controller import TUIController
from ..alignment import AlignmentEngine


class OneCoderApp(App):
    """Modern Textual TUI for OneCoder agent system."""

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_log", "Clear Log", show=True),
        Binding("ctrl+s", "toggle_theme", "Toggle Theme", show=True),
        Binding("ctrl+d", "toggle_dark", "Dark Mode"),
        Binding("ctrl+g", "guide", "Workflow Guide", show=True),
    ]

    def __init__(self, api_url: Optional[str] = None):
        super().__init__()
        self.api_url = api_url or os.getenv("ONECODER_API_URL", "http://127.0.0.1:8000")
        self.session_id = "tui-session"
        self.user_id = "local-user"
        self.token = None
        self.is_processing = False
        self.active_sprint = None
        
        self.controller = TUIController(self)
        self.command_registry = CommandRegistry(self)
        self.alignment = AlignmentEngine()
        
        from .rlm_handler import RLMHandler
        self.rlm_handler = RLMHandler(self)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Horizontal(
            Vertical(
                SprintDashboard(id="sprint-dash"),
                ConnectivityStatus(id="connectivity"),
                TaskQueue(id="task-queue"),
                TokenBudget(id="token-budget"),
                id="sidebar",
            ),
            Vertical(
                RichLog(id="chat-log", markup=True, wrap=True, highlight=True),
                LoadingIndicator(id="loading-indicator"), # Initially hidden via CSS
                SuggestiveInput(
                    placeholder="Type your message... (or 'exit' to quit)",
                    id="user-input",
                    suggester=CommandSuggester(self.command_registry)
                ),
                id="chat-area",
            ),
            id="main-container",
        )
        yield Footer()

    async def on_mount(self) -> None:
        self.chat_log = self.query_one("#chat-log", RichLog)
        self.input_widget = self.query_one("#user-input", SuggestiveInput)
        self.loading_indicator = self.query_one("#loading-indicator", LoadingIndicator)
        self.loading_indicator.display = False

        if await self.controller.initialize_session():
            self.chat_log.write(WelcomeMessage().render())
            self.chat_log.write("\n")
            self.input_widget.focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        if self.is_processing: return
        message = event.value.strip()
        if not message: return

        self.input_widget.clear()
        if message.startswith("/"):
            await self.command_registry.execute(message)
            if message.lower() in ["/quit", "/exit"]: self.exit()
            return

        if message.lower() in ["exit", "quit"]: self.exit(); return

        self.show_loading()
        await self.controller.process_message(message)
        self.hide_loading()
        self.input_widget.focus()

    def show_loading(self):
        self.is_processing = True
        self.input_widget.disabled = True
        self.loading_indicator.display = True
    
    def hide_loading(self):
        self.is_processing = False
        self.input_widget.disabled = False
        self.loading_indicator.display = False

    # --- UI Helpers ---

    async def _write_user_message(self, message: str):
        self.chat_log.write(Panel(message, title="You", border_style="bold green", padding=(0, 1)))

    async def _write_agent_message(self, text: str):
        self.chat_log.write(Panel(Markdown(text), title="OneCoder", border_style="bold blue", padding=(0, 1)))

    async def _show_tool_call(self, tool_name: str, tool_args: dict, status: str = "running"):
        styles = {"running": ("Run...", "bold yellow"), "success": ("✓ Done", "bold green"), "failed": ("✗ Fail", "bold red")}
        text, style = styles.get(status, ("Unknown", "dim"))
        self.chat_log.write(Panel(f"{text} [bold]{tool_name}[/bold]", title="Tool", border_style=style, padding=(0, 1)))

    async def _write_error(self, message: str):
        self.chat_log.write(Panel(f"Error: {message}", title="Error", border_style="bold red", style="red", padding=(0, 1)))

    # --- Actions ---

    def action_clear_log(self) -> None: self.chat_log.clear()
    
    def action_toggle_theme(self) -> None:
        self.theme = "textual-light" if "dark" in self.theme else "textual-dark"
        self.chat_log.write(Panel(f"Theme: {self.theme}", title="Theme", border_style="dim"))

    async def action_guide(self) -> None: await self.command_registry.execute("/guide")

def main(): OneCoderApp().run()
if __name__ == "__main__": main()
