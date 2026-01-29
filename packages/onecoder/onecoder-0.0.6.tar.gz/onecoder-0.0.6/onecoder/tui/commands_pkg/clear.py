from .base import TUICommand
from typing import List

class ClearCommand(TUICommand):
    @property
    def name(self) -> str:
        return "clear"

    @property
    def description(self) -> str:
        return "Clear the chat log"

    async def handle(self, args: List[str]) -> None:
        self.app.chat_log.clear()
        self.app.chat_log.write("[dim]Log cleared.[/dim]")
