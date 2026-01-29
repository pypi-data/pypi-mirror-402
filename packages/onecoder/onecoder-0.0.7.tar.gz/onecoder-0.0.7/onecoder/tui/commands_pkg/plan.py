from .base import TUICommand
from rich.panel import Panel
from typing import List

class PlanCommand(TUICommand):
    @property
    def name(self) -> str:
        return "plan"

    @property
    def description(self) -> str:
        return "Generate an implementation plan using Alignment Engine"

    async def handle(self, args: List[str]) -> None:
        if not args:
            await self.app._write_error("Usage: /plan <goal>")
            return
        goal = " ".join(args)
        self.app.chat_log.write(Panel(f"Generating plan for: {goal}", title="Alignment Engine", border_style="cyan"))
        
        # We need to ensure app has alignment engine initialized
        if hasattr(self.app, "alignment"):
            sprint_id = self.app.active_sprint or "unknown"
            plan = self.app.alignment.generate_unified_plan(sprint_id, goal=goal)
            self.app.chat_log.write(Panel(plan, title="Plan Context & Prompt", border_style="green"))
            self.app.chat_log.write(Panel(f"To execute this plan with RLM, run:\n[bold white]/task refine {goal}[/bold white]", title="Next Steps", border_style="blue"))
        else:
            await self.app._write_error("Alignment Engine not available.")
