import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

@click.command()
def guide():
    """Getting Started & Best Practices Guide."""
    console = Console()
    
    console.print(Panel(
        "[bold cyan]Welcome to OneCoder![/bold cyan]\n"
        "Your AI-native workspace for shipping fast with zero slop.",
        title="OneCoder Guide",
        border_style="blue"
    ))

    # Core Workflows
    workflow_table = Table(title="Common Workflows", show_header=True, header_style="bold magenta")
    workflow_table.add_column("Goal", style="dim", width=30)
    workflow_table.add_column("Command(s)", style="yellow")
    
    workflow_table.add_row("Start a new sprint", "onecoder sprint init <name>")
    workflow_table.add_row("Work on a task", "onecoder sprint task start <id>")
    workflow_table.add_row("Commit and sync", "onecoder sprint commit -m 'message' --spec-id SPEC-123")
    workflow_table.add_row("Check project health", "onecoder status / onecoder doctor deps")
    workflow_table.add_row("Deep code analysis", "onecoder code symbols / onecoder code complexity")
    
    console.print(workflow_table)

    # Best Practices
    console.print("\n[bold green]✓ Best Practices[/bold green]")
    console.print("  • [cyan]Plan First[/cyan]: Always have an implementation plan before writing code.")
    console.print("  • [cyan]Atomic Commits[/cyan]: One task = One commit. Use `sprint commit` for metadata.")
    console.print("  • [cyan]Frictionless Commits[/cyan]: Pass files directly as arguments to avoid prompts:")
    console.print("      [dim]onecoder sprint commit -m 'feat: ...' file1 file2 --spec-id SPEC-XXX[/dim]")
    console.print("  • [cyan]Touch Grass[/cyan]: Verify critical state (tiers, auth) via direct API calls (`curl`) if local CLI feels stale.")
    console.print("  • [cyan]Telemetry[/cyan]: Failure modes are captured automatically. Check `.issues/` for history.")

    console.print("\n[bold yellow]Tier Information[/bold yellow]")
    console.print("  Run [bold white]onecoder whoami[/bold white] to see your current tier and active features.")
    console.print("  Core sprint management (init, status, preflight) is available for [bold green]FREE[/bold green].")
    console.print("  Advanced governance and audit tools require a [bold cyan]PRO[/bold cyan] or [bold cyan]ENTERPRISE[/bold cyan] plan.")
    
    console.print("\n[dim]For more details, visit: https://docs.onecoder.dev[/dim]")

if __name__ == "__main__":
    guide()
