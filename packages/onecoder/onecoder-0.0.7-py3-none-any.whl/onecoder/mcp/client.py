from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
import contextlib

class OneCoderMcpClient:
    def __init__(self, command: str, args: list[str], cwd: str = None, env: dict = None):
        self.server_params = StdioServerParameters(
            command=command,
            args=args,
            cwd=cwd,
            env=env
        )
        self.session: ClientSession | None = None
        self._exit_stack = contextlib.AsyncExitStack()

    async def connect(self):
        """Connect to the MCP server via stdio."""
        # Create stdio transport
        read, write = await self._exit_stack.enter_async_context(
            stdio_client(self.server_params)
        )
        # Create session
        self.session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self.session.initialize()
        return self.session

    async def list_tools(self):
        if not self.session:
            raise RuntimeError("Not connected")
        return await self.session.list_tools()

    async def call_tool(self, name: str, arguments: dict):
        if not self.session:
            raise RuntimeError("Not connected")
        return await self.session.call_tool(name, arguments)

    async def close(self):
        await self._exit_stack.aclose()
