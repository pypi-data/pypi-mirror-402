
import click
import subprocess
import shutil
import os
from datetime import datetime
from pathlib import Path
from ..knowledge import ProjectKnowledge

@click.group()
def debug():
    """Debug tools for OneCoder."""
    pass

@debug.command()
@click.option("--session", default="platform", help="Tmux session name to capture.")
@click.option("--lines", default=2000, help="Number of lines to capture history.")
def capture(session, lines):
    """Capture current TUI state from tmux for debugging."""
    if not shutil.which("tmux"):
        click.secho("Error: tmux is not installed or not in PATH.", fg="red")
        return

    # Check if session exists
    try:
        subprocess.check_call(
            ["tmux", "has-session", "-t", session], 
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        click.secho(f"Error: Tmux session '{session}' not found.", fg="red")
        click.echo("Ensure you started the TUI with: tmux new -s platform 'onecoder tui'")
        return

    # Create capture directory
    pk = ProjectKnowledge()
    repo_root = pk.directory
    capture_dir = repo_root / ".sprint" / "captures"
    capture_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tui_capture_{timestamp}.log"
    file_path = capture_dir / filename

    try:
        # Capture pane content including history
        # -p: print to stdout
        # -S -<lines>: capture history
        output = subprocess.check_output(
            ["tmux", "capture-pane", "-p", "-t", session, "-S", f"-{lines}"],
            text=True
        )
        
        # Save to file
        file_path.write_text(output)
        
        click.secho(f"✅ TUI state captured to: {file_path}", fg="green")
        click.echo(f"Size: {len(output)} bytes")
        
    except subprocess.CalledProcessError as e:
        click.secho(f"Failed to capture pane: {e}", fg="red")
