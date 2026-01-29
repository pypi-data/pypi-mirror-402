import os
import aiohttp
from typing import Dict, Any, Optional
from ..dispatcher import TaskDispatcher, DispatchResult

class CloudflareRpcDispatcher(TaskDispatcher):
    """
    Dispatches tasks to the OneCoder Cloudflare Gateway via HTTP/RPC-bridge.
    This simulates an RPC call from the CLI -> Cloudflare Worker -> Service Binding.
    """

    def __init__(self):
        self.api_url = os.getenv("ONECODER_API_URL", "https://api.onecoder.dev")
        self.api_key = os.getenv("ONECODER_API_KEY")

    async def dispatch(self, task_id: str, command: str, context_path: str, env_vars: Dict[str, str]) -> DispatchResult:
        if not self.api_key:
             return DispatchResult(task_id=task_id, status="failed", error="ONECODER_API_KEY not found")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-OneCoder-Dispatch-Mode": "generic-executor" # Signal for generic execution
        }

        payload = {
            "jsonrpc": "2.0",
            "method": "execute_task",
            "params": {
                "task_id": task_id,
                "command": command,
                "env": env_vars
            },
            "id": task_id
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/v1/rpc/dispatch", json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return DispatchResult(task_id=task_id, status="failed", error=f"HTTP {resp.status}: {error_text}")
                    
                    data = await resp.json()
                    # Parse JSON-RPC response
                    if "error" in data:
                        return DispatchResult(task_id=task_id, status="failed", error=data["error"]["message"])
                    
                    result = data.get("result", {})
                    return DispatchResult(
                        task_id=task_id,
                        status="dispatched", # Async execution
                        output=result.get("message", "Task queued"),
                        metadata={
                            "backend": "cloudflare_rpc",
                            "remote_id": result.get("execution_id")
                        }
                    )
        except Exception as e:
            return DispatchResult(task_id=task_id, status="failed", error=str(e))

    async def get_status(self, task_id: str) -> DispatchResult:
         if not self.api_key:
             return DispatchResult(task_id=task_id, status="failed", error="ONECODER_API_KEY not found")

         # Polling logic would go here
         return DispatchResult(task_id=task_id, status="unknown", error="Status polling not implemented yet")
