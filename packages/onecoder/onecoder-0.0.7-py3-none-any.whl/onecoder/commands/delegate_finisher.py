import click
import os
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from ..services.delegation_service import DelegationService
from ..services.validation_service import ValidationService, FileExistsRule, CommandSuccessRule
from ..jules_client import JulesAPIClient

def finish_remote_jules(session, force, cleanup):
    """Governed finish for remote Jules sessions."""
    console = Console()
    if not session.external_id:
        console.print("[red]Error: Remote session missing external Jules ID.[/red]")
        return False
        
    console.print(f"[cyan]Governing remote Jules session {session.external_id}...[/cyan]")
    client = JulesAPIClient()
    pr_info = client.detect_pr_output(session.external_id)
    if not pr_info:
        console.print("[yellow]No PR detected yet for this session. Is it complete?[/yellow]")
        return False
        
    pr_url = pr_info["url"]
    console.print(f"Found PR: {pr_url}")
    
    try:
         console.print("[cyan]Fetching PR branch...[/cyan]")
         subprocess.run(["gh", "pr", "checkout", pr_url], check=True)
         
         val_service = ValidationService()
         rules = [FileExistsRule("README.md")]
         context = {"session_id": session.id, "worktree_path": os.getcwd()}
         
         with console.status("[bold green]Validating remote work..."):
             report = val_service.validate_session(context, rules)
         
         if not report.all_passed:
             console.print("[bold red]Validation Failed.[/bold red]")
             if not force and not click.confirm("Force proceed?"):
                 return False
         
         parent_branch = session.parent_branch or "main"
         current_pr_branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
         
         subprocess.run(["git", "checkout", parent_branch], check=True)
         subprocess.run(["git", "merge", "--no-ff", "-m", f"chore: merge remote task {session.task_id}", current_pr_branch], check=True)
         console.print("[green]✓ Remote task merged and governed.[/green]")
         
         if cleanup:
             subprocess.run(["git", "branch", "-D", current_pr_branch], check=True)
         return True
    except Exception as e:
        console.print(f"[red]Error during remote finish: {e}[/red]")
        return False

def finish_local_session(session, dg_service, message, force, cleanup):
    """Governed finish for local worktree sessions."""
    console = Console()
    val_service = ValidationService()
    rules = [FileExistsRule("README.md")]
    if session.worktree_path and (Path(session.worktree_path) / "validate.sh").exists():
        rules.append(CommandSuccessRule("bash validate.sh"))

    context = {"session_id": session.id, "worktree_path": session.worktree_path}
    with console.status("[bold green]Validating session..."):
        report = val_service.validate_session(context, rules)
    
    if not report.all_passed and not force:
        if not click.confirm("Do you want to force finish despite validation failures?"):
            return False
            
    if session.worktree_path and os.path.exists(session.worktree_path):
        console.print("[cyan]Finalizing work with atomic commit...[/cyan]")
        try:
             cmd = ["sprint", "commit", "-m", message, "--task-id", session.task_id, "--status", "done", "--validation", "Passed"]
             env = os.environ.copy()
             if "PYTHONPATH" not in env:
                 env["PYTHONPATH"] = str(dg_service.worktree_mgr.project_root / "sprint-cli" / "src")
             subprocess.run(cmd, cwd=session.worktree_path, check=True, capture_output=True, env=env)
             console.print("[bold green]✓ Work committed to task branch.[/bold green]")
        except subprocess.CalledProcessError as e:
            if "No staged changes to audit" in e.stdout.decode() or "nothing to commit" in e.stdout.decode():
                 console.print("[bold green]✓ Work already committed to task branch (clean).[/bold green]")
            else:
                subprocess.run(["git", "add", "."], cwd=session.worktree_path, check=True)
                subprocess.run(["git", "commit", "-m", message], cwd=session.worktree_path, check=True)
                console.print("[bold green]✓ Work saved via git commit.[/bold green]")
    
    parent_branch = session.parent_branch
    if parent_branch:
        dg_service.worktree_mgr.remove_worktree(session.id, delete_branch=False)
        if dg_service.worktree_mgr.rebase_onto(session.id, parent_branch):
            if dg_service.worktree_mgr.merge_task_branch(session.id, parent_branch):
                console.print(f"[bold green]✓ Successfully merged into {parent_branch}[/bold green]")
            else:
                console.print("[bold red]Merge failed![/bold red]")
                dg_service.worktree_mgr.create_worktree(session.id, base_ref=f"task/{session.id}")
                return False
        else:
            console.print("[bold red]Rebase failed![/bold red]")
            dg_service.worktree_mgr.create_worktree(session.id, base_ref=f"task/{session.id}")
            return False

    if cleanup or (cleanup is None and click.confirm(f"Delete task branch 'task/{session.id}'?")):
        dg_service.worktree_mgr.remove_worktree(session.id, delete_branch=True)
        console.print("[bold green]✓ Task branch deleted.[/bold green]")
    return True
