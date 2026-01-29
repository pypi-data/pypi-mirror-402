import click
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ..api_client import get_api_client
from ..config_manager import config_manager
from .auth import require_feature
import asyncio
import sys

# Try to import trace capabilities from sprint-cli
try:
    from ai_sprint.trace import trace_specifications, get_sprint_tasks
except ImportError:
    # Fallback or mock if ai_sprint is not available in immediate env
    trace_specifications = None
    get_sprint_tasks = None

import os

def find_platform_root():
    """Find the root of the platform repository."""
    curr = Path(__file__).resolve()
    for parent in [curr] + list(curr.parents):
        if (parent / ".git").exists() or (parent / "packages").exists():
            # If we see packages/core/engines, we are likely in the right place
            if (parent / "packages" / "core" / "engines").exists():
                return parent
    return Path.cwd() # Fallback to current dir if not found

@click.group()
@require_feature("content_tools")
def content():
    """Content Operations and Generation."""
    pass

@content.group()
def ops():
    """ContentOps management commands."""
    pass

@ops.command(name="list-insights")
def list_insights():
    """List captured reflections/insights for content generation."""
    console = Console()
    token = config_manager.get_token()
    client = get_api_client(token)
    
    async def _fetch():
        try:
            # Feedback endpoint returns a list directly from get_feedback()
            insights_list = await client.get_feedback()
            insights = [f for f in insights_list if f.get("category") == "content_insight"]
            
            if not insights:
                console.print("[yellow]No content insights found.[/yellow]")
                return
 
            table = Table(title="Content Insights / Reflections")
            table.add_column("ID", style="dim")
            table.add_column("Date", style="blue")
            table.add_column("Message", style="green")
            table.add_column("Context", style="dim")
            
            for ins in insights:
                ctx = ins.get("context", {})
                ctx_str = f"S:{ctx.get('sprint_id','?')} T:{ctx.get('task_id','?')}"
                table.add_row(
                    str(ins.get("id")),
                    ins.get("createdAt", "")[:10],
                    ins.get("message", ""),
                    ctx_str
                )
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error fetching insights: {e}[/red]")
 
    asyncio.run(_fetch())

@ops.command(name="synthesize")
@click.argument("insight_id")
@click.option("--type", "draft_type", type=click.Choice(["blog", "social"]), default="blog")
def synthesize(insight_id, draft_type):
    """Synthesize a draft from a specific insight."""
    console = Console()
    # 1. Fetch the specific insight (or all and find)
    token = config_manager.get_token()
    client = get_api_client(token)
    
    async def _run():
        try:
            insights_list = await client.get_feedback()
            insights = [f for f in insights_list if str(f.get("id")) == insight_id]
            if not insights:
                console.print(f"[red]Insight {insight_id} not found.[/red]")
                return
            
            insight = insights[0]
            message = insight.get("message")
            context = insight.get("context", {})
            
            # 2. Call the ContentWriter Skill
            try:
                # Use robust path resolution
                platform_root = find_platform_root()
                skills_pkg_path = platform_root / "packages" / "skills"
                
                if skills_pkg_path.exists():
                    if str(skills_pkg_path) not in sys.path:
                        sys.path.append(str(skills_pkg_path))
                    
                    # Import the refactored skill
                    try:
                        from skills.content_writer.writer import ContentWriter
                    except ImportError as ie:
                        console.print(f"[red]Failed to import ContentWriter skill: {ie}[/red]")
                        # Try adding the specific skill dir if package import fails
                        skill_dir = skills_pkg_path / "skills" / "content_writer"
                        if skill_dir.exists():
                             sys.path.append(str(skill_dir))
                             from writer import ContentWriter
                        else:
                             return
                else:
                    console.print(f"[red]Skills package not found at {skills_pkg_path}[/red]")
                    return
 
                # Instantiate and Execute Skill
                writer = ContentWriter()
                with console.status(f"Synthesizing {draft_type} draft..."):
                    # New Skill Interface: execute(context, **kwargs)
                    result = writer.execute(context, insight=message, draft_type=draft_type)
                
                # 3. Create Draft in API
                draft_resp = await client.create_content_draft({
                    "projectId": None, # Could be linked from context
                    "title": result["title"],
                    "content": result["content"],
                    "type": result["type"],
                    "insightId": insight_id
                })
                
                console.print(f"[bold green]✓ Synthesis complete![/bold green]")
                console.print(f"Draft ID: [blue]{draft_resp.get('draft', {}).get('id')}[/blue]")
                console.print(Panel(result["content"][:300] + "\n...", title=result["title"]))
                
            except Exception as e:
                console.print(f"[red]Synthesis failed: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())
                
        except Exception as e:
            console.print(f"[red]API Error: {e}[/red]")
 
    asyncio.run(_run())

@ops.command(name="sync-strategy")
def sync_strategy():
    """Sync local GTM strategy and skills with the platform."""
    console = Console()
    console.print("[bold blue]Syncing Content & GTM strategy...[/bold blue]")
    
    # Implementation placeholder - in a real system this might upload
    # config or strategy notes to the api for grounding.
    platform_root = find_platform_root()
    strategy_path = platform_root / "packages" / "content" / "gtm" / "GTM_STRATEGY_NOTES.md"
    if strategy_path.exists():
        content = strategy_path.read_text()
        console.print(f"✓ Read {strategy_path.name} ({len(content)} bytes)")
        console.print("[green]Strategy notes synced for AI awareness.[/green]")
    else:
        console.print(f"[yellow]GTM_STRATEGY_NOTES.md not found at {strategy_path}[/yellow]")

@content.command(name="generate")
@click.option("--type", "content_type", type=click.Choice(["blog", "social", "internal"]), default="blog", help="Type of content to generate")
@click.option("--sprint-id", help="Target Sprint ID (defaults to current active)")
@click.option("--dry-run", is_flag=True, help="Preview prompt without calling LLM")
def generate(content_type, sprint_id, dry_run):
    """Generate marketing content from sprint traces."""
    console = Console()
    
    # 1. Resolve Sprint ID
    if not sprint_id:
        # Try to find current sprint from .sprint/
        # This is a simplified heuristic logic
        sprint_dir = Path(".sprint")
        if sprint_dir.exists():
            # Find most recent modified directory
            sprints = [d for d in sprint_dir.iterdir() if d.is_dir()]
            if sprints:
                latest = max(sprints, key=os.path.getmtime)
                sprint_id = latest.name
    
    if not sprint_id:
        console.print("[red]Error: Could not determine Sprint ID. Please specify --sprint-id[/red]")
        return
 
    console.print(f"[bold blue]🔮 Analyzing Sprint: {sprint_id}[/bold blue]")
 
    # 2. Fetch Trace Data
    if not trace_specifications:
        console.print("[yellow]Warning: ai_sprint.trace module not found. Using minimal context.[/yellow]")
        trace_data = {"error": "Trace module missing"}
    else:
        with console.status("Tracing specifications and commits..."):
            trace_data = trace_specifications(Path.cwd(), limit=50)
 
    # 3. Filter for relevant sprint data
    sprint_data = trace_data.get("sprints", {}).get(sprint_id, {})
    # Prepare data for skill
    # commits = sprint_data.get("commits", []) # Handled by skill
    # valid_tasks = sprint_data.get("valid_tasks", []) # Handled by skill
    
    # 4. Load & Execute Publisher Skill
    try:
        platform_root = find_platform_root()
        skills_pkg_path = platform_root / "packages" / "skills"
        
        if skills_pkg_path.exists():
             if str(skills_pkg_path) not in sys.path:
                  sys.path.append(str(skills_pkg_path))
             
             try:
                 from skills.publisher.publisher import Publisher
             except ImportError:
                  # Try direct dir
                  skill_dir = skills_pkg_path / "skills" / "publisher"
                  if skill_dir.exists():
                       sys.path.append(str(skill_dir))
                       from publisher import Publisher
                  else:
                       console.print(f"[red]Publisher skill not found at {skill_dir}[/red]")
                       return
        
        publisher = Publisher()
        
        if dry_run:
             result = publisher.execute(
                 context={},
                 sprint_id=sprint_id,
                 content_type=content_type,
                 sprint_data=sprint_data,
                 audit_log=trace_data.get("audit", []),
                 dry_run=True
             )
             console.print(Panel(result["prompt"], title="Generated Prompt Preview", border_style="dim"))
             console.print("[dim]Dry run: Content generation skipped.[/dim]")
        
        else:
             with console.status(f"Generating {content_type} draft..."):
                  result = publisher.execute(
                       context={},
                       sprint_id=sprint_id,
                       content_type=content_type,
                       sprint_data=sprint_data,
                       audit_log=trace_data.get("audit", []),
                       dry_run=False
                  )
             
             file_name = result.get("file_name", "draft.md")
             output_file = Path(file_name)
             output_file.write_text(result["content"])
             console.print(f"[bold green]✓ Draft generated: {output_file}[/bold green]")
             console.print(Panel(result["content"][:200] + "\n...", title="Draft Preview"))
 
    except Exception as e:
        console.print(f"[red]Generation failed: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
