import json
import httpx
import logging
import asyncio
from typing import Optional
from rich.panel import Panel
from rich.markdown import Markdown
from .widgets import WelcomeMessage, ErrorMessage
from ..ipc_auth import get_token_from_ipc

logger = logging.getLogger(__name__)

class TUIController:
    """Handles business logic and data orchestration for the TUI."""

    def __init__(self, app):
        self.app = app

    async def initialize_session(self) -> bool:
        """Initialize TUI and fetch authentication token."""
        self.app.chat_log.write(
            Panel(
                "[bold blue]OneCoder TUI[/bold blue]",
                title="Initializing secure session...",
                border_style="dim",
            )
        )

        self.app.token = await get_token_from_ipc()

        if not self.app.token:
            self.app.chat_log.write(
                ErrorMessage(
                    "Could not fetch auth token from IPC.\n"
                    "Make sure OneCoder server is running: onecoder serve"
                )
            )
            return False

        self.app.chat_log.write(
            Panel(
                "[bold green]✓[/bold green] Session initialized successfully!",
                title="Success",
                border_style="bold green",
            )
        )

        await self.refresh_dashboard()
        return True

    async def refresh_dashboard(self) -> None:
        """Update the sidebar widgets with current alignment state."""
        from ..alignment import auto_detect_sprint_id, SprintStateManager, SPRINT_DIR
        self.app.active_sprint = auto_detect_sprint_id()
        
        if self.app.active_sprint:
            state = self.app.alignment.check_alignment(self.app.active_sprint)
            
            dash = self.app.query_one("#sprint-dash")
            dash.sprint_id = self.app.active_sprint
            dash.status = state.get("status", "Unknown")
            dash.refresh()

            queue = self.app.query_one("#task-queue")
            sm = SprintStateManager(SPRINT_DIR / self.app.active_sprint)
            sprint_data = sm.load()
            queue.tasks = sprint_data.get("tasks", [])
            queue.refresh()

            budget = self.app.query_one("#token-budget")
            usage = self.app.alignment.get_token_budget_status()
            budget.percent = usage.get("percent", 0)
            budget.refresh()

            # Refresh Connectivity
            conn = self.app.query_one("#connectivity")
            from pathlib import Path
            conn.env_loaded = Path(".env").exists()
            
            # Check API
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(f"{self.app.api_url}/")
                    conn.api_connected = resp.status_code == 200
            except:
                conn.api_connected = False
            
            # Check LLM (if API is connected, we assume LLM ready if keys exist)
            conn.llm_ready = conn.env_loaded and conn.api_connected
            conn.refresh()

    async def process_message(self, message: str):
        """Process user message and stream agent response."""
        await self.app._write_user_message(message)

        # RLM is now the default reasoning engine for TUI
        if hasattr(self.app, "rlm_handler"):
            try:
                await self.app.rlm_handler.run_refine(message)
                return
            except Exception as e:
                logger.error(f"RLM Execution failed, falling back to ADK: {e}")

        current_response = ""
        async with httpx.AsyncClient(timeout=None) as client:
            params = {
                "user_id": self.app.user_id,
                "session_id": self.app.session_id,
                "message": message,
                "token": self.app.token,
            }
            
            if self.app.active_sprint:
                params["sprint_id"] = self.app.active_sprint

            try:
                async with client.stream(
                    "GET", f"{self.app.api_url}/stream", params=params
                ) as response:
                    if response.status_code != 200:
                        await self.app._write_error(f"Error: {response.status_code}")
                        return

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            await self._handle_event(line[6:], current_response)
                            # Update current_response if text event
                            try:
                                data = json.loads(line[6:])
                                if "text" in data:
                                    current_response += data["text"]
                            except: pass

                if current_response:
                    await self.app._write_agent_message(current_response)

            except httpx.ConnectError:
                await self.app._write_error(
                    "Could not connect to OneCoder API.\n"
                    "Is the server running?\n"
                    "Run 'onecoder serve' in another terminal."
                )
            except Exception as e:
                await self.app._write_error(f"Stream Error: {e}")

    async def _handle_event(self, event_json: str, current_response: str):
        """Handle individual stream events."""
        try:
            data = json.loads(event_json)
            if data.get("type") == "Error":
                await self.app._write_error(data.get("message", "Unknown error"))
            elif "tool_call" in data:
                tool_name = data["tool_call"].get("name", "unknown")
                await self.app._show_tool_call(tool_name, {}, status="running")
            elif "tool_result" in data:
                tool_name = data.get("tool_name", "unknown")
                await self.app._show_tool_call(tool_name, {}, status="success")
        except json.JSONDecodeError:
            pass
