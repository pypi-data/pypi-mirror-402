import click
import os
import subprocess
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..services.delegation_service import DelegationService
from ..services.validation_service import ValidationService, FileExistsRule, CommandSuccessRule
from ..jules_client import JulesAPIClient, JulesAPIError, JulesAuthError

@click.command()
@click.option("--limit", default=10, help="Number of recent sessions to show")
def delegate_list(limit):
    """List active delegation sessions and their status."""
    console = Console()
    service = DelegationService()
    sessions = service.list_sessions()
    
    sessions.sort(key=lambda s: s.created_at, reverse=True)
    
    table = Table(title="Delegation Sessions")
    table.add_column("Session ID", style="cyan", no_wrap=True)
    table.add_column("Task ID (Sprint)", style="magenta")
    table.add_column("Status", style="bold")
    table.add_column("Age", style="white")
    table.add_column("Backend", style="blue")
    
    now = datetime.now()
    
    for s in sessions[:limit]:
        age = now - s.created_at
        age_str = str(age).split('.')[0]
        status_style = "green" if s.status == "running" else "red" if s.status == "failed" else "white"
        
        table.add_row(
            s.id[:8],
            s.task_id,
            f"[{status_style}]{s.status}[/]",
            age_str,
            s.backend
        )
    console.print(table)

@click.command()
@click.argument("session_id")
def delegate_status(session_id):
    """Check the status of a local delegation session."""
    console = Console()
    service = DelegationService()
    session = service.get_session(session_id)
    
    if not session:
        console.print(f"[bold red]Error:[/bold red] Session {session_id} not found.")
        return
        
    status_color = "green" if session.status == "running" else "yellow"
    panel = Panel(
        f"[bold]Status:[/bold] [{status_color}]{session.status}[/]\n"
        f"[bold]Backend:[/bold] {session.backend}\n"
        f"[bold]Worktree:[/bold] {session.worktree_path}\n"
        f"[bold]Tmux Session:[/bold] {session.tmux_session or 'N/A'}\n"
        f"[bold]Task ID:[/bold] {session.task_id}",
        title=f"Session: {session_id}"
    )
    console.print(panel)

@click.command()
@click.argument("session_id")
def delegate_validate(session_id):
    """Manually trigger validation for a local delegation session."""
    console = Console()
    dg_service = DelegationService()
    session = dg_service.get_session(session_id)
    
    if not session:
        console.print(f"[bold red]Error:[/bold red] Session {session_id} not found.")
        return
        
    if not session.worktree_path:
        console.print("[bold red]Error:[/bold red] Session has no associated worktree path.")
        return

    val_service = ValidationService()
    rules = [FileExistsRule("README.md")]
    
    if (Path(session.worktree_path) / "validate.sh").exists():
        rules.append(CommandSuccessRule("bash validate.sh"))

    context = {
        "session_id": session_id,
        "worktree_path": session.worktree_path,
        "task_id": session.task_id
    }
    
    with console.status("[bold green]Running validation rules..."):
        report = val_service.validate_session(context, rules)
    
    table = Table(title=f"Validation Report: {session_id}")
    table.add_column("Rule", style="cyan")
    table.add_column("Passed", style="bold")
    table.add_column("Error", style="red")
    
    for res in report.results:
        passed_str = "[green]YES[/green]" if res["passed"] else "[red]NO[/red]"
        table.add_row(res["rule"], passed_str, res["error"] or "-")
        
    console.print(table)
    
    if report.all_passed:
        console.print("\n[bold green]✓ All validation rules passed![/bold green]")
    else:
        console.print("\n[bold red]✗ Some validation rules failed.[/bold red]")

@click.command()
@click.option("--limit", default=5, help="Number of recent sessions to show")
def jules_sessions_cmd(limit):
    """List recent Jules sessions and their status."""
    console = Console()
    try:
        client = JulesAPIClient()
        if not client._session_cache:
            console.print("[yellow]No cached sessions found.[/yellow]")
            return
        
        table = Table(title="Recent Jules Sessions")
        table.add_column("Session ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("State", style="green")
        table.add_column("PR URL", style="blue")
        
        for session_id, session in list(client._session_cache.items())[:limit]:
            pr_output = client.detect_pr_output(session_id)
            pr_url = pr_output["url"] if pr_output else "-"
            table.add_row(session_id, session.title[:50] if session.title else "N/A", session.state, pr_url)
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
