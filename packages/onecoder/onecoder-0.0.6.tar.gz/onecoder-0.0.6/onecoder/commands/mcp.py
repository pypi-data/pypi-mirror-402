import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from onecoder.mcp.client import OneCoderMcpClient
from onecoder.mcp.registry import McpRegistry

console = Console()
logger = logging.getLogger("onecoder.commands.mcp")

@click.group()
def mcp():
    """Manage and interact with Model Context Protocol (MCP) servers."""
    pass

@mcp.command()
@click.option("--path", default=".", help="Root path to scan for skills (default: current directory)")
def index(path: str):
    """Scan and index MCP skills/servers in the workspace."""
    registry = McpRegistry()
    abs_path = os.path.abspath(path)
    console.print(f"[bold cyan]Scanning for skills in:[/bold cyan] {abs_path}")
    
    registry.discover_skills(abs_path)
    # The registry saves automatically on modification in our simple implementation
    # But usually we'd want an explicit save.
    # For now, let's just save explicitly to be sure.
    registry._save_config({"servers": {k: v.dict() for k, v in registry.servers.items()}})
    
    count = len(registry.servers)
    console.print(f"[bold green]Successfully indexed {count} skills.[/bold green]")

@mcp.command()
def list():
    """List registered MCP servers/skills."""
    registry = McpRegistry()
    servers = registry.list_servers()
    
    if not servers:
        console.print("No MCP servers registered. Run 'onecoder mcp index' first.")
        return

    table = Table(title="Registered MCP Servers")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Source", style="green")
    
    for server in servers:
        source = server.manifest_path or server.url or "Unknown"
        table.add_row(server.name, server.type, source)
        
    console.print(table)

@mcp.command()
@click.argument("server_name")
def inspect(server_name: str):
    """Inspect tools available on a specific MCP server."""
    async def _inspect():
        registry = McpRegistry()
        server_config = registry.get_server(server_name)
        
        if not server_config:
            console.print(f"[red]Server '{server_name}' not found.[/red]")
            return

        console.print(f"[bold]Connecting to {server_name}...[/bold]")
        
        # Determine command args
        # For 'stdio' type, command is in config
        if server_config.type == "stdio":
            cmd = server_config.command[0]
            args = server_config.command[1:]
            cwd = server_config.env.get("cwd") # Or construct from config if stored
            
            # Temporary fix: In registry.py we stored absolute path but didn't strictly kwarg it
            # Let's trust the command list we built
            
            client = OneCoderMcpClient(cmd, args, cwd=os.getcwd()) # TODO: Use server cwd if needed
            
            try:
                await client.connect()
                tools = await client.list_tools()
                
                table = Table(title=f"Tools in {server_name}")
                table.add_column("Name", style="cyan")
                table.add_column("Description")
                
                for tool in tools.tools:
                    table.add_row(tool.name, tool.description or "")
                    
                console.print(table)
                
            except Exception as e:
                console.print(f"[red]Error inspecting server: {e}[/red]")
            finally:
                await client.close()
        else:
            console.print(f"[yellow]Inspector for type '{server_config.type}' not implemented yet.[/yellow]")

    asyncio.run(_inspect())

@mcp.command()
@click.argument("server_name")
@click.argument("tool_name")
@click.option("--args", "-a", multiple=True, help="Arguments in key=value format")
def call(server_name: str, tool_name: str, args):
    """Call a tool on an MCP server."""
    async def _call():
        registry = McpRegistry()
        server_config = registry.get_server(server_name)
        
        if not server_config:
            console.print(f"[red]Server '{server_name}' not found.[/red]")
            return

        # Parse args
        tool_args = {}
        for arg in args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                tool_args[key] = value
            else:
                console.print(f"[yellow]Skipping invalid arg '{arg}'. Use key=value.[/yellow]")

        if server_config.type == "stdio":
            cmd = server_config.command[0]
            cmd_args = server_config.command[1:]
            
            client = OneCoderMcpClient(cmd, cmd_args, cwd=os.getcwd())
            
            try:
                await client.connect()
                console.print(f"[bold]Calling {tool_name} on {server_name}...[/bold]")
                
                result = await client.call_tool(tool_name, tool_args)
                
                # Result structure depends on MCP SDK version, usually it has `content` list
                console.print("[bold green]Result:[/bold green]")
                for content in result.content:
                    if hasattr(content, "text"):
                        console.print(content.text)
                    else:
                        console.print(str(content))
                        
            except Exception as e:
                console.print(f"[red]Error calling tool: {e}[/red]")
            finally:
                await client.close()
        else:
            console.print(f"[yellow]Call for type '{server_config.type}' not implemented yet.[/yellow]")

    asyncio.run(_call())
