from .base import TUICommand
from rich.panel import Panel
from typing import List

class HelpCommand(TUICommand):
    @property
    def name(self) -> str:
        return "help"

    @property
    def description(self) -> str:
        return "Show available commands"

    async def handle(self, args: List[str]) -> None:
        lines = ["[bold]Available Commands:[/bold]"]
        # We access registry from app
        for name, cmd in self.app.command_registry.commands.items():
            desc = cmd.description if hasattr(cmd, "description") else "No description"
            lines.append(f"• [cyan]/{name}[/cyan]: {desc}")

        panel = Panel("\n".join(lines), title="Help", border_style="blue")
        self.app.chat_log.write(panel)
