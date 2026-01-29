import click
import asyncio
from typing import Optional
from pathlib import Path
from ..api_client import get_api_client
from ..config_manager import config_manager
from ..usage_logger import usage_logger
import importlib.metadata

@click.command()
@click.option("--sentiment", type=click.Choice(["positive", "neutral", "negative"]), default="neutral", help="Sentiment of the feedback.")
@click.option("--category", type=click.Choice(["tooling", "process", "task", "other"]), default="other", help="Category of the feedback.")
@click.option("--issue-id", help="Associated Issue ID (e.g., 041).")
@click.option("--task-id", help="Associated Task ID.")
@click.option("--feature-request", is_flag=True, help="Submit as a feature request.")
@click.option("--for-content", is_flag=True, help="Flag this feedback for content synthesis.")
@click.option("--include-usage", is_flag=True, help="Include recent CLI usage context.")
@click.option("--list", "list_feedback", is_flag=True, help="List submitted feedback and their status.")
@click.option("--status", help="Filter by status (pending, planned, implemented, deferred).")
@click.option("--auto", is_flag=True, help="Automatically capture system diagnostics and usage context.")
@click.argument("message", required=False)
def feedback(sentiment, category, issue_id, task_id, feature_request, for_content, include_usage, list_feedback, status, auto, message):
    """Provide feedback on tools, sprints, or tasks."""
    if list_feedback:
        asyncio.run(_list_feedback(status))
        return
        
    if not message and not auto:
        click.secho("Error: Message is required unless using --list or --auto.", fg="red")
        return

    asyncio.run(_submit_feedback(sentiment, category, issue_id, task_id, feature_request, for_content, include_usage, auto, message))

async def _list_feedback(status_filter: Optional[str] = None):
    from rich.console import Console
    from rich.table import Table
    console = Console()
    
    token = config_manager.get_token()
    if not token:
        click.secho("Error: Not logged in.", fg="red")
        return
        
    client = get_api_client(token)
    try:
        entries = await client.get_feedback(status=status_filter)
        if not entries:
            console.print("[yellow]No feedback found.[/yellow]")
            return
            
        table = Table(title="Feedback & Status")
        table.add_column("ID", style="dim")
        table.add_column("Status", style="magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Message", style="white")
        table.add_column("Date", style="dim")
        
        for e in entries:
            status_style = {
                "pending": "yellow",
                "planned": "blue",
                "implemented": "green",
                "deferred": "red"
            }.get(e.get("status", "pending"), "white")
            
            table.add_row(
                e.get("id", "")[:8],
                f"[{status_style}]{e.get('status', 'pending')}[/{status_style}]",
                e.get("category", "other"),
                e.get("message", "")[:100],
                e.get("createdAt", "")[:10]
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error fetching feedback: {e}[/red]")
async def _submit_feedback(sentiment, category, issue_id, task_id, feature_request, for_content, include_usage, auto, message):
    token = config_manager.get_token()
    if not token:
        click.secho("Warning: Submitting as guest (not logged in).", fg="yellow")
    
    client = get_api_client(token)
    
    if auto:
        include_usage = True
        if not message:
            message = "[AUTO-FEEDBACK] System diagnostic report."

    if feature_request:
        category = "tooling"
        message = f"[FEATURE REQUEST] {message}"
        
    context = {
        "issue_id": issue_id,
        "task_id": task_id
    }
    
    if include_usage:
        context["usage_history"] = usage_logger.get_recent_usage()
    
    metadata = {}
    if auto:
        import platform
        import sys
        metadata = {
            "os": platform.system(),
            "os_release": platform.release(),
            "python_version": sys.version,
            "cli_version": importlib.metadata.version("onecoder"), 
        }
        # Check tree-sitter status
        try:
            import tree_sitter
            import tree_sitter_languages
            metadata["tree_sitter"] = "installed"
        except ImportError:
            metadata["tree_sitter"] = "missing"

    payload = {
        "sentiment": sentiment,
        "category": category,
        "message": message,
        "context": context,
        "metadata": metadata,
        "for_content": for_content
    }
    
    try:
        # Submit to API
        await client.submit_feedback(payload)
        click.secho("✓ Feedback submitted successfully.", fg="green")
        
        # Knowledge Base lookup
        query = issue_id or message
        if query:
            await _suggest_knowledge(client, query)
            
    except Exception as e:
        click.secho(f"Error submitting feedback: {e}", fg="red")

async def _suggest_knowledge(client, query: str):
    """Suggest Time Travel logs from API Knowledge Base."""
    try:
        entries = await client.search_knowledge(query)
        if entries:
            click.secho("\n[Knowledge Base Suggestions]", fg="cyan", bold=True)
            for entry in entries:
                click.echo(f"  • {entry['title']}")
                # If it's a resolution category, highlight it
                if entry.get("category") == "resolution":
                    click.secho(f"    Resolution available: {entry.get('metadata', {}).get('tt_log', 'See log')}", fg="yellow")
    except Exception:
        # Silent fallback
        pass
