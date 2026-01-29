import asyncio
import json
import logging
import os
import shlex
import sys
from typing import Any, Dict, List, Optional

from mcp.server import Server, NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# Configure logging to stderr to avoid interfering with stdout JSON-RPC
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("onecoder-skill-server")

class OneCoderSkillServer:
    def __init__(self, manifest_path: str):
        self.manifest_path = manifest_path
        self.manifest = self._load_manifest()
        self.name = self.manifest.get("name", "unknown-skill")
        self.server = Server(self.name)

        # Register handlers
        self._register_handlers()

    def _load_manifest(self) -> Dict[str, Any]:
        """Load and validate the mcp.json manifest."""
        try:
            with open(self.manifest_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load manifest: {e}")
            sys.exit(1)

    def _register_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name=self.manifest["name"],
                    description=self.manifest.get("description", ""),
                    inputSchema=self.manifest.get("inputSchema", {})
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict | None) -> List[TextContent | ImageContent | EmbeddedResource]:
            if name != self.manifest["name"]:
                raise ValueError(f"Unknown tool: {name}")

            output = await self._execute_command(arguments or {})
            return [TextContent(type="text", text=output)]

    async def _execute_command(self, args: Dict[str, Any]) -> str:
        """Execute the command defined in the manifest with injected arguments."""
        cmd_config = self.manifest.get("command", {})
        cmd_args_template = cmd_config.get("args", [])
        cwd = cmd_config.get("cwd", ".")
        
        # Inject arguments
        final_args = []
        for arg in cmd_args_template:
            # Simple string replacement for now
            formatted_arg = arg.format(**args)
            final_args.append(formatted_arg)
            
        logger.info(f"Executing: {shlex.join(final_args)}")
        
        # Absolute path for cwd if it's relative to manifest
        manifest_dir = os.path.dirname(os.path.abspath(self.manifest_path))
        working_dir = os.path.join(manifest_dir, cwd)

        try:
            process = await asyncio.create_subprocess_exec(
                *final_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env={**os.environ} # Inherit env explicitly
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode().strip()
            error = stderr.decode().strip()
            
            if process.returncode != 0:
                return f"Error (Exit Code {process.returncode}):\n{error}\n\nOutput:\n{output}"
            
            return output if output else "Command executed successfully (no output)."

        except Exception as e:
            return f"Execution failed: {str(e)}"

    async def run(self):
        """Run the MCP server via stdio."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python server_wrapper.py <path_to_mcp.json>", file=sys.stderr)
        sys.exit(1)
        
    server = OneCoderSkillServer(sys.argv[1])
    asyncio.run(server.run())
