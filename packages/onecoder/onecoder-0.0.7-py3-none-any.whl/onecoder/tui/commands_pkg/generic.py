from .base import TUICommand
from typing import List

class GenericCLICommand(TUICommand):
    def __init__(self, app, name: str, description: str):
        super().__init__(app)
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def handle(self, args: List[str]) -> None:
        await self._run_cli_command(self._name, args)
