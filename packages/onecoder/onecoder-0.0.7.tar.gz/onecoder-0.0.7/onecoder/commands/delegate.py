import click
import os
import asyncio
import subprocess
from pathlib import Path
from rich.console import Console

from ..services.delegation_service import DelegationService
from ..jules_client import JulesAPIClient, JulesAPIError, JulesAuthError
from ..config_manager import config_manager
from .delegate_mgmt import delegate_list as list_sessions, delegate_status as status_session, delegate_validate as validate_session, jules_sessions_cmd as jules_sessions
from .delegate_finisher import finish_remote_jules, finish_local_session

@click.group()
@click.pass_context
def delegate(ctx):
    """Delegate a coding task and manage delegation sessions."""
    pass

@delegate.command("start")
@click.argument("prompt")
@click.option("--local", "--tui", is_flag=True, help="Run as a local isolated delegation session (TUI)")
@click.option("--jules", is_flag=True, help="Run as a remote Jules delegation session")
@click.option("--source", help="GitHub source")
@click.option("--branch", default="main", help="Starting branch")
@click.option("--watch", is_flag=True, help="Monitor progress in real-time")
@click.option("--timeout", default=120, help="Timeout in seconds")
@click.option("--poll-interval", default=10, help="Polling interval in seconds")
@click.option("--type", type=click.Choice(['code', 'gtm']), default='code', help="Type of task")
def delegate_start(prompt, local, jules, source, branch, watch, timeout, poll_interval, type):
    """Start a new delegation task."""
    console = Console()
    
    # If jules flag is set, it's a remote session
    if jules:
        isolation = "remote_jules" # We can map this in factory later or keep legacy path
    elif local:
        isolation = "local"
    else:
        isolation = "local" # Default

    from ..services.dispatcher import DispatcherFactory
    
    try:
        dispatcher = DispatcherFactory.get_dispatcher(isolation)
        # Note: Task registration in sprint/db might technically belong in the Service 
        # but for now we dispatch.
        
        # We need to construct a context path and env vars
        context_path = str(Path.cwd())
        env_vars = os.environ.copy()

        # Generate a task ID (or let dispatcher handle it, but dispatcher takes task_id)
        # For local, we usually want it registered in the sprint.
        # This part of existing logic (DelegationService.register_task_in_sprint) 
        # is valuable. We might want to keep using DelegationService for metadata 
        # and then use Dispatcher for execution. 
        
        # Refactored flow:
        service = DelegationService()
        sprint_id, registered_task_id = service.register_task_in_sprint(prompt, Path.cwd())
        task_id = registered_task_id or f"adhoc-{int(asyncio.get_event_loop().time())}"

        if isolation == "local":
             # The LocalWorktreeDispatcher internally uses DelegationService logic for now
             # to maintain compatibility with existing session storage.
             pass

        console.print(f"[cyan]Dispatching task {task_id} via {isolation}...[/cyan]")
        
        async def run_dispatch():
            result = await dispatcher.dispatch(task_id, prompt, context_path, env_vars)
            if result.status == "failed":
                console.print(f"[bold red]Dispatch Failed:[/bold red] {result.error}")
            else:
                console.print(f"[bold green]✓[/bold green] Dispatched. Status: {result.status}")
                if result.output:
                    console.print(result.output)

            # Watch logic could be genericized here using dispatcher.get_status
            if watch and result.status not in ["failed", "completed"]:
                 # ... generic watch loop ...
                 pass

        asyncio.run(run_dispatch())
        return

    except Exception as e:
        console.print(f"[bold red]Error during dispatch:[/bold red] {str(e)}")
        return

    # Remote Jules Logic (Default or explicit --jules)
    service = DelegationService()
    sprint_id, registered_task_id = service.register_task_in_sprint(prompt, Path.cwd())
    task_id = registered_task_id or "jules-task"
    
    governance_context = f"\n\n[GOVERNANCE META]\nTask-Id: {task_id}\n"
    if sprint_id: governance_context += f"Sprint-Id: {sprint_id}\n"
    
    if type == "gtm":
        if "gtm_ops" not in config_manager.get_entitlements():
            console.print("[bold red]Error:[/bold red] Feature 'gtm_ops' not enabled.")
            return
        governance_context += "Task-Type: GTM\nPolicy: SPEC-GOV-013\n"

    try:
        client = JulesAPIClient()
        jules_session = client.create_session(prompt + governance_context, source=source, branch=branch)
        console.print(f"[bold green]✓[/bold green] Jules Session created: [cyan]{jules_session.id}[/cyan]")
        
        local_session = service.create_session(task_id=task_id, backend="jules", command=prompt)
        local_session.external_id = jules_session.id
        local_session.sprint_id = sprint_id
        service._save_session(local_session)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")

@delegate.command("review")
@click.argument("session_id")
def delegate_review(session_id):
    """Review a delegation session in an isolated worktree."""
    console = Console()
    service = DelegationService()
    session = service.get_session(session_id)
    
    if not session:
        # Check if it's a prefix
        sessions = service.list_sessions()
        matches = [s for s in sessions if s.id.startswith(session_id)]
        if len(matches) == 1:
            session = matches[0]
        else:
            console.print(f"[bold red]Error:[/bold red] Session {session_id} not found.")
            return

    console.print(f"[cyan]Preparing review for session {session.id}...[/cyan]")
    
    if session.backend == "jules":
        if not session.external_id:
            console.print("[red]Error: Remote session missing external Jules ID.[/red]")
            return
        
        client = JulesAPIClient()
        pr_info = client.detect_pr_output(session.external_id)
        if not pr_info:
            console.print("[yellow]No PR detected yet for this session. Is it complete?[/yellow]")
            return
            
        pr_url = pr_info["url"]
        pr_number = pr_url.split("/")[-1]
        console.print(f"Found PR: {pr_url}")
        
        wt_path = service.worktree_mgr.create_worktree_from_remote(session.id, pr_number)
        console.print(f"[bold green]✓[/bold green] Jules PR checked out to worktree: [cyan]{wt_path}[/cyan]")
    else:
        # Local session
        wt_path = service.worktree_mgr.get_worktree_path(session.id)
        if not wt_path:
             wt_path = service.worktree_mgr.create_worktree(session.id, base_ref=f"task/{session.id}")
        
        console.print(f"[bold green]✓[/bold green] Local task available at worktree: [cyan]{wt_path}[/cyan]")

@delegate.command("merge")
@click.argument("session_id")
@click.option("--message", "-m", help="Merge commit message")
@click.option("--force", is_flag=True, help="Force merge despite validation failures")
@click.option("--cleanup/--no-cleanup", default=True, help="Cleanup worktree after merge")
def delegate_merge(session_id, message, force, cleanup):
    """Merge a reviewed delegation session back into the sprint branch."""
    console = Console()
    service = DelegationService()
    session = service.get_session(session_id)
    
    if not session:
        sessions = service.list_sessions()
        matches = [s for s in sessions if s.id.startswith(session_id)]
        if len(matches) == 1:
            session = matches[0]
        else:
            console.print(f"[bold red]Error:[/bold red] Session {session_id} not found.")
            return

    msg = message or f"feat: merge delegated task {session.task_id}"
    
    if session.backend == "jules":
        success = finish_remote_jules(session, force, cleanup)
    else:
        success = finish_local_session(session, service, msg, force, cleanup)
    
    if success:
        console.print(f"[bold green]✓[/bold green] Session {session.id} merged successfully.")
    else:
        console.print(f"[bold red]✗[/bold red] Failed to merge session {session.id}.")

@delegate.command("finish")
@click.argument("session_id")
@click.option("--message", "-m", help="Commit message", default="feat: complete delegated task")
@click.option("--force", is_flag=True, help="Force finish despite validation failures")
@click.option("--cleanup/--no-cleanup", default=None, help="Cleanup worktree after finish")
def delegate_finish_cmd(session_id, message, force, cleanup):
    """Finishes a delegation session: validates, commits tracking metadata, and cleans up."""
    delegate_finish_logic(session_id, message, force, cleanup)

def delegate_finish_logic(session_id, message, force, cleanup):
    console = Console()
    dg_service = DelegationService()
    session = dg_service.get_session(session_id)
    
    if not session:
        console.print(f"[bold red]Error:[/bold red] Session {session_id} not found.")
        return

    if session.backend == "jules":
        finish_remote_jules(session, force, cleanup)
    else:
        finish_local_session(session, dg_service, message, force, cleanup)

delegate.add_command(list_sessions, name="list")
delegate.add_command(status_session, name="status")
delegate.add_command(validate_session, name="validate")
delegate.add_command(jules_sessions, name="jules-sessions")
