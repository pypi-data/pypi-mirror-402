from abc import ABC, abstractmethod
from typing import List, Any

class TUICommand(ABC):
    """Base class for TUI slash commands."""
    
    def __init__(self, app):
        self.app = app

    @property
    @abstractmethod
    def name(self) -> str:
        """The command name (e.g., 'help')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A brief description of the command."""
        pass

    @abstractmethod
    async def handle(self, args: List[str]) -> None:
        """Handle the command logic."""
        pass

    async def _run_cli_command(self, main_cmd: str, args: List[str]) -> None:
        """Helper to run onecoder CLI commands via subprocess."""
        import asyncio
        from rich.panel import Panel
        
        cmd = ["onecoder"] + main_cmd.split() + args
        cmd_str = " ".join(cmd)
        
        self.app.chat_log.write(Panel(f"Running: [bold]{cmd_str}[/bold]", title="Exec", border_style="yellow"))
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode().strip()
            error = stderr.decode().strip()
            
            if output:
                self.app.chat_log.write(Panel(output, title=f"Output: {main_cmd}", border_style="green"))
            
            if error:
                 style = "red" if process.returncode != 0 else "yellow"
                 self.app.chat_log.write(Panel(error, title=f"Stderr: {main_cmd}", border_style=style))
                 
            if process.returncode == 0 and not output and not error:
                 self.app.chat_log.write(Panel("Command completed successfully (no output).", title="Success", border_style="green"))

        except Exception as e:
            await self.app._write_error(f"Execution failed: {e}")
