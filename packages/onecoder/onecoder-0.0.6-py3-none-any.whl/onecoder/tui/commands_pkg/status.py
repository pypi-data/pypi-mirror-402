from .base import TUICommand
from pathlib import Path
import json
from rich.panel import Panel
from typing import List

class StatusCommand(TUICommand):
    @property
    def name(self) -> str:
        return "status"

    @property
    def description(self) -> str:
        return "Show platform-wide sprint status"

    async def handle(self, args: List[str]) -> None:
        root_path = Path(".").resolve() 
        sprint_dirs = []
        for p in root_path.rglob(".sprint"):
             if "node_modules" in p.parts or ".git" in p.parts:
                continue
             sprint_dirs.append(p)

        if not sprint_dirs:
            self.app.chat_log.write(Panel("No active sprints found.", title="Status", border_style="yellow"))
            return

        status_lines = []
        for sd in sprint_dirs:
            component = sd.parent.name
            subdirs = sorted([d for d in sd.iterdir() if d.is_dir()])
            if subdirs:
                active = subdirs[-1]
                # Check for yaml or json
                state_str = "Unknown"
                state_file = active / "sprint.yaml"
                if not state_file.exists():
                    state_file = active / "sprint.json"
                
                if state_file.exists():
                    try:
                        if state_file.suffix == ".yaml":
                            import yaml
                            with open(state_file) as f:
                                data = yaml.safe_load(f)
                        else:
                            with open(state_file) as f:
                                data = json.load(f)
                        state_str = data.get("status", {}).get("state", "unknown")
                    except:
                        pass
                status_lines.append(f"• [bold]{component}[/bold] -> {active.name}: [green]{state_str}[/green]")

        self.app.chat_log.write(Panel("\n".join(status_lines), title="Platform Status", border_style="blue"))
