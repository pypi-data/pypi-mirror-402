import asyncio
import os
import yaml
from pathlib import Path
from rich.panel import Panel
from onecoder_rlm.rlm_runtime import OneCoderRLM
from onecoder_rlm.config import RLMConfig

class RLMHandler:
    """Handles the RLM refinement logic for the TUI."""
    
    def __init__(self, app):
        self.app = app

    async def run_refine(self, task_query: str):
        """Initializes and runs the RLM refinement stream."""
        config_dict = self._load_config()
        rlm = OneCoderRLM(config=RLMConfig(**config_dict))
        
        self.app.chat_log.write(Panel(f"Refining task: [bold cyan]{task_query}[/bold cyan]", title="RLM Agent", border_style="blue"))
        
        try:
            stream_gen = rlm.stream(task_query)
            for event in stream_gen:
                await asyncio.sleep(0.01)
                await self._handle_event(event)
        except Exception as e:
            await self.app._write_error(f"RLM Engine Crashed: {e}")

    def _load_config(self) -> dict:
        config_path = Path(__file__).parent / "rlm_config.yaml"
        config_dict = {}
        if config_path.exists():
            with open(config_path, "r") as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config and "rlm" in yaml_config:
                    rlm_config = yaml_config["rlm"]
                    config_dict = {
                        "max_rlm_iterations": rlm_config.get("max_iterations", 50),
                        "token_budget": rlm_config.get("token_budget", 200000),
                        "enable_alignment_tools": rlm_config.get("enable_alignment_tools", True),
                        "llm_provider": rlm_config.get("llm", {}).get("provider", "openai"),
                        "llm_model": rlm_config.get("llm", {}).get("model", "gpt-4o-mini"),
                        "sandbox_environment": rlm_config.get("sandbox_environment", "local"),
                        "enable_cli_tool": rlm_config.get("enable_cli_tool", True),
                        "verbose": rlm_config.get("verbose", False),
                    }
        
        if os.getenv("ONECODER_RLM_MAX_ITERS"):
            config_dict["max_rlm_iterations"] = int(os.getenv("ONECODER_RLM_MAX_ITERS"))
        return config_dict

    async def _handle_event(self, event: dict):
        event_type = event["type"]
        if event_type == "status":
            self.app.chat_log.write(f"[dim]{event['content']}[/dim]")
        elif event_type == "reasoning":
            self.app.chat_log.write(Panel(f"[italic]{event['content']}[/italic]", title="💭 Reasoning", border_style="dim white"))
        elif event_type == "tool_use":
            await self._handle_tool_use(event)
        elif event_type == "tool_result":
            self._handle_tool_result(event)
        elif event_type == "error":
            self.app.chat_log.write(Panel(f"Analysis Error: {event['error']}", title="Error", border_style="red"))
        elif event_type == "done":
            self._handle_done(event)

    async def _handle_tool_use(self, event: dict):
        tool = event["tool"]
        args = event["args"]
        if tool == "chat":
            msg = args.get("message", "")
            self.app.chat_log.write(Panel(Markdown(msg), title="OneCoder", border_style="bold blue", padding=(0, 1)))
            return

        if tool == "patch":
            approved = await self._run_hitl_gating(args)
            if not approved: return
        self.app.chat_log.write(Panel(f"Tool: [bold]{tool}[/bold]\nArgs: {args}", title="🛠️ Tool Execution", border_style="yellow"))

    async def _run_hitl_gating(self, args: dict) -> bool:
        file_path = args.get("file_path", "unknown")
        content = args.get("content", "")
        mode = args.get("mode", "append")
        diff_str = f"--- {file_path}\n+++ {file_path}\n@@ (mode: {mode}) @@\n{content}"
        
        from .widgets import HITLConfirmation
        confirmation = HITLConfirmation(file_path, diff_str)
        self.app.chat_log.write(Panel(f"Waiting for approval to modify: [bold]{file_path}[/bold]", border_style="yellow"))
        
        approval_future = asyncio.Future()
        original_on_button = confirmation.on_button_pressed
        def patched_on_button(event):
            original_on_button(event)
            choice = str(event.button.id).replace("-", "_")
            if not approval_future.done():
                approval_future.set_result(choice)
        
        confirmation.on_button_pressed = patched_on_button
        self.app.mount(confirmation)
        choice = await approval_future
        
        if choice == "reject_change":
            self.app.chat_log.write(Panel("Change rejected by user.", border_style="red"))
            return False
        return True

    def _handle_tool_result(self, event: dict):
        res = event["result"]
        if event.get("error"):
            self.app.chat_log.write(Panel(res, title="❌ Tool Error", border_style="red"))
        else:
            if len(res) > 500: res = res[:500] + "... (truncated)"
            self.app.chat_log.write(Panel(res, title="✅ Tool Result", border_style="green"))

    def _handle_done(self, event: dict):
        res = event["result"]
        if res["status"] == "completed":
            self.app.chat_log.write(Panel("Refinement Task Completed Successfully.", title="Success", border_style="bold green"))
        else:
            self.app.chat_log.write(Panel(f"Refinement Failed: {res.get('reason')}", title="Failure", border_style="bold red"))
        usage = res.get("usage", {})
        self.app.chat_log.write(f"📊 Token Usage: Input={usage.get('input', '?')} | Output={usage.get('output', '?')}")
