from .base import TUICommand
from rich.panel import Panel
from typing import List

class DelegateCommand(TUICommand):
    @property
    def name(self) -> str:
        return "delegate"

    @property
    def description(self) -> str:
        return "Delegate a task to a local isolated agent. Usage: /delegate <task description>"

    async def handle(self, args: List[str]) -> None:
        if not args:
            await self.app._write_error("Usage: /delegate <task description> OR /delegate <list|review|merge> [id]")
            return

        subcommand = args[0].lower()
        if subcommand in ["list", "review", "merge", "status", "validate", "jules-sessions"]:
            await self._run_cli_command("delegate", args)
            return

        task_desc = " ".join(args)
        backend_flag = ""
        if "--jules" in task_desc:
            backend_flag = "--jules"
            task_desc = task_desc.replace("--jules", "").strip()
        elif "--tui" in task_desc or "--local" in task_desc:
            backend_flag = "--local"
            task_desc = task_desc.replace("--tui", "").replace("--local", "").strip()
        
        self.app.chat_log.write(Panel(f"Delegating task: [bold]{task_desc}[/bold]", title="Delegation", border_style="yellow"))

        cli_args = [task_desc]
        if backend_flag:
            cli_args.append(backend_flag)
        
        await self._run_cli_command("delegate", cli_args)
