from typing import List
import os
from rich.panel import Panel
from rich.text import Text
from .base import TUICommand
from ...env_manager import env_manager

class EnvCommand(TUICommand):
    """Manage secure environment variables."""

    @property
    def name(self) -> str:
        return "env"

    @property
    def description(self) -> str:
        return "Manage environment variables (list, scan, set)"

    async def handle(self, args: List[str]) -> None:
        if not args:
            await self.show_help()
            return

        subcmd = args[0].lower()
        if subcmd == "list":
            await self.list_keys()
        elif subcmd == "scan":
            await self.scan_env_files()
        elif subcmd == "set":
            if len(args) < 3:
                await self.app._write_error("Usage: /env set <key> <value>")
            else:
                key = args[1]
                value = args[2] # Note: This splits by space, so values with spaces might be an issue if not handled.
                # Basic handling for now, assuming simple values or quoted in future parsing improvements
                await self.set_env(key, value)
        else:
             await self.app._write_error(f"Unknown sub-command: {subcmd}. Use list, scan, or set.")

    async def show_help(self):
        text = """
        [bold]Environment Command Usage:[/bold]
        
        • [cyan]/env list[/cyan] - List stored environment variable keys
        • [cyan]/env scan[/cyan] - Scan current directory for .env files and import keys
        • [cyan]/env set <key> <value>[/cyan] - Set an environment variable
        """
        self.app.chat_log.write(Panel(text, title="Env Help", border_style="blue"))

    async def list_keys(self):
        global_keys = env_manager.list_keys()
        cwd = os.getcwd()
        local_keys = env_manager.list_keys(cwd)
        
        if not global_keys and not local_keys:
             self.app.chat_log.write(Panel("No stored environment variables.", title="Environment Variables", border_style="yellow"))
             return

        content = ""
        if global_keys:
            content += "[bold]Global Variables:[/bold]\n"
            for k in sorted(global_keys):
                content += f"  • {k}\n"
        
        if local_keys:
            content += f"\n[bold]Local Variables ({cwd}):[/bold]\n"
            for k in sorted(local_keys):
                content += f"  • {k}\n"

        self.app.chat_log.write(Panel(content, title="Environment Variables", border_style="green"))

    async def scan_env_files(self):
        start_dir = os.getcwd()
        env_files = []
        for root, dirs, files in os.walk(start_dir):
            if "node_modules" in dirs: 
                dirs.remove("node_modules")
            
            # Depth check approximation
            rel = os.path.relpath(root, start_dir)
            if rel.count(os.sep) > 2:
                continue

            for f in files:
                if f in [".env", ".env.local", ".dev.vars"]:
                    env_files.append(os.path.join(root, f))
        
        if not env_files:
            self.app.chat_log.write(Panel("No .env files found to scan.", title="Scan Result", border_style="yellow"))
            return

        imported_count = 0
        for file_path in env_files:
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    
                    key, val = line.split('=', 1)
                    key = key.replace('export ', '').strip()
                    val = val.strip().strip('"').strip("'")
                    
                    if key:
                        # Auto-import into local scope for TUI context
                        # We use the env_manager to persist it securely
                        env_manager.set_env(key, val, start_dir)
                        imported_count += 1
            except Exception as e:
                self.app.chat_log.write(Panel(f"Error reading {file_path}: {e}", title="Scan Error", border_style="red"))

        msg = f"✓ Scanned and imported {imported_count} keys from {len(env_files)} files into local context."
        self.app.chat_log.write(Panel(msg, title="Scan Complete", border_style="green"))
        
        # Trigger an update to the connectivity status widget if it exists
        if hasattr(self.app, "query_one"):
             try:
                 from ..widgets import ConnectivityStatus
                 conn_widget = self.app.query_one("#connectivity", ConnectivityStatus)
                 if conn_widget:
                     conn_widget.env_loaded = True
                     conn_widget.refresh()
             except Exception:
                 pass

    async def set_env(self, key, value):
        env_manager.set_env(key, value)
        self.app.chat_log.write(Panel(f"✓ Set {key} globally.", title="Environment Set", border_style="green"))
