import click
import re
from datetime import datetime
from pathlib import Path
from ..issues import IssueManager
from ..config_manager import config_manager
try:
    from ai_sprint.telemetry import FailureModeCapture
except ImportError:
    FailureModeCapture = None

@click.group()
def issue():
    """Manage platform governance issues."""
    pass

@issue.command(name="create")
@click.option("--from-telemetry", is_flag=True, help="Create issue from latest telemetry failure")
@click.option("--title", help="Manual title for the issue")
def issue_create(from_telemetry, title):
    """Create a new governance issue."""
    from rich.console import Console
    console = Console()
    
    manager = IssueManager()
    
    if from_telemetry:
        if FailureModeCapture is None:
            console.print("[red]Error: Telemetry features not available in this installation.[/red]")
            return

        capture = FailureModeCapture()
        failures = capture.get_failures(limit=1)
        if not failures:
            console.print("[yellow]No recent failures found in telemetry.[/yellow]")
            return
            
        failure = failures[0]
        issue_path = manager.create_from_telemetry(failure, title=title)
        console.print(f"[bold green]✓ Issue created from telemetry:[/bold green] {issue_path.name}")
    else:
        # Future: manual issue creation wizard
        console.print("[yellow]Manual issue creation not yet implemented. Use --from-telemetry.[/yellow]")

@issue.command(name="resolve")
@click.argument("issue_id")
@click.option("--message", "-m", help="Resolution message")
@click.option("--pr", help="Pull Request URL")
def issue_resolve(issue_id, message, pr):
    """Mark an issue as resolved."""
    from rich.console import Console
    import subprocess
    
    console = Console()
    manager = IssueManager()
    
    # 1. Get Resolution Metadata
    resolution_meta = {
        "user": config_manager.get_user(),
        "resolved_at": datetime.now().isoformat(),
        "pr_url": pr
    }
    
    # Get Current Commit
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        resolution_meta["commit_sha"] = commit
    except Exception:
        resolution_meta["commit_sha"] = "unknown"
        
    # 2. Update Status
    success = manager.update_status(issue_id, "resolved", resolution_meta)
    
    if success:
        console.print(f"[bold green]✓ Issue {issue_id} marked as resolved.[/bold green]")
        console.print(msg="Resolution metadata captured.", style="dim")
    else:
        console.print(f"[bold red]Error:[/bold red] Issue {issue_id} not found.")

@issue.command(name="sync")
@click.option("--kb", is_flag=True, help="Populate local Knowledge Base (rank_bm25)")
def issue_sync(kb):
    """Sync local governance issues to the OneCoder API (unresolved only) or local KB."""
    from rich.console import Console
    console = Console()

    if kb:
        manage_kb_sync(console)
        return

    import asyncio
    from ..sync import ProjectConfig
    from ..api_client import get_api_client
    from ..services.github_sync import GitHubIssueSync
    
    # Setup
    token = config_manager.get_token()
    if not token:
        click.secho("Error: Not logged in.", fg="red")
        return

    repo_root = Path.cwd() 
    proj_config = ProjectConfig(repo_root)
    project_id = proj_config.get_project_id()
    
    if not project_id:
        click.secho("Error: Project ID not found.", fg="red")
        return

    client = get_api_client(token)
    sync_service = GitHubIssueSync(client, project_id)
    
    # Run Sync
    with console.status("[bold cyan]Syncing unresolved issues..."):
        result = asyncio.run(sync_service.sync_unresolved())
        
    console.print(f"[bold green]✓ Sync complete.[/bold green]")
    console.print(f"  - Synced: {result['synced']}")
    console.print(f"  - Skipped (Resolved): {result['skipped']}", style="dim")

def manage_kb_sync(console):
    """Scan local issues and traces for KB population."""
    from pathlib import Path
    import sys
    
    # Path hacking to import onecoder_rlm if needed
    try:
        from onecoder_rlm.kb.manager import KBManager
    except ImportError:
        # Try to find it relative to current file
        # issue.py is at packages/core/engines/onecoder-cli/onecoder/commands/issue.py
        try:
            current_path = Path(__file__).resolve()
            # 6 levels up to platform/ then packages/core
            rlm_path = current_path.parents[5]
            if str(rlm_path) not in sys.path:
                sys.path.append(str(rlm_path))
            from onecoder_rlm.kb.manager import KBManager
        except Exception:
            console.print("[red]Error: Could not import onecoder_rlm. KB sync failed.[/red]")
            return

    manager = KBManager()
    
    issue_manager = IssueManager()
    issues = issue_manager.get_all_issues()
    
    docs = []
    
    # 1. Process Issues
    for issue in issues:
        # Reconstruct content or use parsed description? 
        # Better to use full markdown content for BM25
        issue_id = issue['id']
        # Find file again
        for item in issue_manager.issues_dir.glob(f"{issue_id}-*.md"):
            content = item.read_text()
            docs.append({
                "content": content,
                "metadata": {
                    "id": f"issue-{issue_id}",
                    "title": issue['title'],
                    "type": "issue",
                    "source": str(item)
                }
            })
            break

    # 2. Process Traces (timetravel)
    repo_root = issue_manager.repo_root
    traces_dir = repo_root / "timetravel"
    if traces_dir.exists():
        for item in traces_dir.glob("*.md"):
            content = item.read_text()
            docs.append({
                "content": content,
                "metadata": {
                    "id": f"trace-{item.stem}",
                    "title": item.stem,
                    "type": "trace",
                    "source": str(item)
                }
            })

    if docs:
        with console.status("[bold cyan]Updating local Knowledge Base..."):
            manager.update_index(docs)
        console.print(f"[bold green]✓ Local KB Sync complete.[/bold green]")
        console.print(f"  - Indexed: {len(docs)} documents (Issues + Traces)")
    else:
        console.print("[yellow]No local documents found to index.[/yellow]")

@issue.command(name="list")
def issue_list():
    """List all local governance issues."""
    from rich.console import Console
    from rich.table import Table
    console = Console()
    
    manager = IssueManager()
    issues_dir = manager.issues_dir
    if not issues_dir.exists():
        console.print("[yellow]No .issues directory found.[/yellow]")
        return
        
    table = Table(title="Local Governance Issues")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", style="magenta")
    
    for item in sorted(issues_dir.iterdir()):
        if item.is_file() and item.suffix == ".md" and item.name != "README.md":
            match = re.match(r"^(\d{3})-(.+)\.md$", item.name)
            if match:
                issue_id = match.group(1)
                issue_title = match.group(2).replace("-", " ").capitalize()
                
                # Try to parse status from file
                content = item.read_text()
                if any(x in content for x in ["Resolved", "🟢 Resolved", "🟢 **Resolved**"]):
                    status = "[green]Resolved[/green]"
                elif any(x in content for x in ["Open", "🔴 Open", "🔴 **Open**"]):
                    status = "[red]Open[/red]"
                else:
                    status = "[yellow]Unknown[/yellow]"
                    
                table.add_row(issue_id, issue_title, status)
                
    console.print(table)
