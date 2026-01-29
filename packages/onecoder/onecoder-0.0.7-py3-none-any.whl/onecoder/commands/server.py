import click
import asyncio
import threading
import uvicorn
import webbrowser
import signal
import sys
import socket
import logging
from ..ipc_auth import IPCAuthServer, get_token_from_ipc

# Global flag for graceful shutdown
shutdown_event = asyncio.Event()

def check_port_available(port: int) -> bool:
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", port))
            return True
    except OSError:
        return False

async def check_servers_running() -> bool:
    """Check if OneCoder servers are running."""
    try:
        token = await get_token_from_ipc()
        return token is not None
    except:
        return False

def run_api_server(port: int = 8000):
    """Runs the FastAPI server."""
    from ..api import app
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

async def run_servers_async(port: int = 8000):
    """Run both API and IPC servers concurrently."""
    # Start API server in a thread
    api_thread = threading.Thread(target=run_api_server, args=(port,), daemon=True)
    api_thread.start()

    # Give API server time to start
    await asyncio.sleep(1)

    # Start IPC server in main async loop
    ipc_server = IPCAuthServer()
    try:
        await ipc_server.start()
    except asyncio.CancelledError:
        click.echo("Shutting down gracefully...")

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    click.echo("\nReceived shutdown signal. Cleaning up...")
    sys.exit(0)

@click.command()
@click.option("--port", default=8000, help="API server port")
def serve(port):
    """Starts the Agent API and IPC Auth servers."""
    # Check if port is available
    if not check_port_available(port):
        click.echo(f"Error: Port {port} is already in use.")
        click.echo(f"Check for running processes: lsof -i :{port}")
        return

    click.echo(f"Starting OneCoder servers on port {port}...")
    click.echo("Press Ctrl+C to stop.")

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run servers
    try:
        # Start Skills API (as subprocess)
        import subprocess
        from pathlib import Path
        
        # Resolve path to skills api project
        curr = Path(__file__).resolve()
        platform_root = None
        for parent in [curr] + list(curr.parents):
            if (parent / "packages" / "core" / "engines" / "skills-marketplace-api").exists():
                platform_root = parent
                break
        
        skills_process = None
        if platform_root:
            skills_project = platform_root / "packages" / "core" / "engines" / "skills-marketplace-api"
            # Use bun to run the dev server (which uses wrangler)
            # Use --show-interactive-dev-session=false to prevent it from waiting for input
            cmd = ["bun", "run", "dev", "--", "--show-interactive-dev-session=false"]
            skills_process = subprocess.Popen(cmd, cwd=str(skills_project))
        else:
            click.echo("Warning: Could not locate skills-marketplace-api. Skills API will not be available.")

        asyncio.run(run_servers_async(port))
        
    except KeyboardInterrupt:
        click.echo("\nShutting down...")
    finally:
        if skills_process:
             click.echo("Stopping Skills API...")
             skills_process.terminate()
             skills_process.wait()

@click.command()
@click.option("--auto-start", is_flag=True, help="Auto-start servers if not running")
def web(auto_start):
    """Launches the secure Web UI."""

    async def launch():
        # Check if servers are running
        servers_running = await check_servers_running()

        if not servers_running:
            if auto_start:
                click.echo("Servers not running. Starting in background...")
                # Start servers in background thread
                server_thread = threading.Thread(
                    target=lambda: asyncio.run(run_servers_async()), daemon=True
                )
                server_thread.start()
                # Wait for servers to be ready
                await asyncio.sleep(2)

                # Verify they started
                if not await check_servers_running():
                    click.echo("Error: Failed to start servers automatically.")
                    return
            else:
                click.echo("Error: Servers not running.")
                click.echo(
                    "Run 'onecoder serve' in another terminal or use --auto-start"
                )
                return

        # Fetch token
        token = await get_token_from_ipc()
        if not token:
            click.echo("Error: Could not fetch authentication token.")
            return

        # Launch browser
        url = f"http://127.0.0.1:8000/?token={token}"
        click.echo(f"Launching Web UI: {url}")
        webbrowser.open(url)

        if auto_start:
            click.echo("\nServers running in background. Press Ctrl+C to stop.")
            try:
                # Keep running if we auto-started
                await asyncio.Event().wait()
            except KeyboardInterrupt:
                click.echo("\nShutting down...")

    asyncio.run(launch())

@click.command()
@click.option("--auto-start", is_flag=True, help="Auto-start servers if not running")
@click.option("--api-url", help="Override the API URL")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def tui(auto_start, api_url, debug):
    """Launches the modern Textual TUI."""
    
    if debug:
        logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
        click.echo("Debug mode enabled")

    # Load secrets into environment (to handle background thread access)
    try:
        from ..env_manager import env_manager
        import os
        
        # 1. Load global keys
        global_secrets = env_manager.list_keys()
        for key in global_secrets:
             val = env_manager.get_env(key)
             if val:
                 os.environ[key] = val
                 
        # 2. Load local context overrides
        cwd = os.getcwd()
        local_secrets = env_manager.list_keys(cwd)
        for key in local_secrets:
            val = env_manager.get_env(key, cwd)
            if val:
                os.environ[key] = val
                
        click.echo(f"Loaded {len(global_secrets) + len(local_secrets)} secrets into process environment.")
    except Exception as e:
        click.echo(f"Warning: Failed to load secrets into environment: {e}")

    async def launch():
        # Check if servers are running
        servers_running = await check_servers_running()

        if not servers_running:
            if auto_start:
                click.echo("Servers not running. Starting in background...")
                # Start servers in background thread
                server_thread = threading.Thread(
                    target=lambda: asyncio.run(run_servers_async()), daemon=True
                )
                server_thread.start()
                
                # Wait for servers to be ready with health check polling
                click.echo("Waiting for servers to be ready...")
                max_attempts = 10
                for attempt in range(max_attempts):
                    await asyncio.sleep(0.5)
                    if await check_servers_running():
                        click.echo(f"✓ Servers ready (took {(attempt + 1) * 0.5:.1f}s)")
                        break
                else:
                    # Timeout - servers didn't start in time
                    click.echo("⚠ Timeout waiting for servers to start.")
                    click.echo("Try running 'onecoder serve' manually in another terminal.")
                    return
            else:
                click.echo("Error: Servers not running.")
                click.echo(
                    "Run 'onecoder serve' in another terminal or use --auto-start"
                )
                return

        # Launch Textual TUI
        try:
            from ..tui.app import OneCoderApp
        except ImportError:
            click.secho("Error: 'textual' or TUI components not found.", fg="red", bold=True)
            click.echo("This is an internal feature. To enable it, please install the internal version:")
            click.secho("  pip install onecoder[internal]", fg="cyan")
            return

        app = OneCoderApp(api_url=api_url)
        await app.run_async()

    asyncio.run(launch())
