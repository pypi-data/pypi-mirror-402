import re
import asyncio
from typing import Dict, Any, List, Optional
from textual.suggester import Suggester
from rich.panel import Panel

class CommandSuggester(Suggester):
    """Provides autocompletion suggestions for slash commands."""

    def __init__(self, registry: 'CommandRegistry'):
        super().__init__(use_cache=True)
        self.registry = registry

    async def get_suggestion(self, value: str) -> Optional[str]:
        if not value.startswith("/"):
            return None
        
        entered = value[1:].lower()
        if not entered:
            return None

        # Find first matching command
        for cmd_name in sorted(self.registry.commands.keys()):
            if cmd_name.startswith(entered):
                return f"/{cmd_name}"
        
        return None

class CommandRegistry:
    """Manages TUI slash commands with a modular architecture."""

    def __init__(self, app):
        self.app = app
        self.commands: Dict[str, Any] = {}
        self._register_default_commands()

    def _register_default_commands(self):
        """Discovers and registers command modules."""
        from .commands_pkg.help import HelpCommand
        from .commands_pkg.clear import ClearCommand
        from .commands_pkg.status import StatusCommand
        from .commands_pkg.delegate import DelegateCommand
        from .commands_pkg.plan import PlanCommand
        from .commands_pkg.env import EnvCommand
        from .commands_pkg.model import ModelCommand
        from .commands_pkg.generic import GenericCLICommand
        
        # Specialized commands
        for cmd_cls in [HelpCommand, ClearCommand, StatusCommand, DelegateCommand, PlanCommand, EnvCommand, ModelCommand]:
            cmd_inst = cmd_cls(self.app)
            self.commands[cmd_inst.name] = cmd_inst

        # Generic CLI wrappers
        generics = [
            ("ttu", "Evaluate Task Technical Understanding (TTU) via sprint audit"),
            ("guide", "Show the OneCoder Best Practices Guide"),
            ("sprint", "Run sprint commands (start, finish, commit, status)"),
            ("task", "Run task commands (start, create, done)"),
            ("refine", "Refine a task using RLM Agent"),
        ]
        for name, cmd_path in [
            ("ttu", "sprint audit"),
            ("guide", "suggest best-practices"),
            ("sprint", "sprint"),
            ("task", "task"),
            ("refine", "task refine"),
        ]:
            desc = dict(generics).get(name, "")
            self.commands[name] = GenericCLICommand(self.app, cmd_path, desc)

    async def execute(self, command_line: str):
        """Parse and execute a slash command."""
        parts = command_line.split()
        if not parts:
            return

        name = parts[0].strip("/").lower()
        args = parts[1:]

        if name in self.commands:
            handler = self.commands[name]
            try:
                if hasattr(handler, "handle"):
                    await handler.handle(args)
                else:
                    await handler(args)
            except Exception as e:
                await self.app._write_error(f"Command '{name}' failed: {str(e)}")
        else:
            await self.app._write_error(f"Unknown command: /{name}. Type /help for available commands.")
