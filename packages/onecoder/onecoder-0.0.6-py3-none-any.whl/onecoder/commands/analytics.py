import click
from pathlib import Path
from datetime import datetime
from ai_sprint.commands.common import console, PROJECT_ROOT, SPRINT_DIR
from onecoder.sprint_collector import SprintCollector
from onecoder.tools.tldr_tool import TLDRTool
from onecoder.commands.auth import require_feature

@click.group()
def analytics():
    """Project and agentic productivity analytics."""
    pass

@analytics.command()
@click.option("--path", default=".", help="Path to analyze for debt")
@require_feature("governance_tools")
def debt(path):
    """View project-wide tech debt score (Enterprise)."""
    # 1. Tech Debt
    tldr = TLDRTool()
    abs_path = Path(path).resolve()
    try:
        debt_data = tldr.calculate_debt_score(str(abs_path))
        
        console.print(f"\n[bold cyan]Project Tech Debt Assessment[/bold cyan]")
        console.print(f"  Total Cyclomatic Complexity: [bold]{debt_data['total_complexity']}[/bold]")
        console.print(f"  Avg. Complexity per File: [bold]{debt_data['average_complexity']:.2f}[/bold]")
        console.print(f"  High-Complexity Entities: [bold yellow]{debt_data['high_complexity_functions_count']}[/bold yellow]")
        console.print(f"  Overall Debt Score: [bold red]{debt_data['debt_score']}[/bold red]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not calculate debt score: {e}[/yellow]")
    
    # 2. Productivity (Sprint History)
    try:
        collector = SprintCollector(SPRINT_DIR)
        history = collector.collect_all_sprints()
        
        total_tasks = 0
        completed_tasks = 0
        
        for s in history:
            for t in s.get("tasks", []):
                total_tasks += 1
                if t.get("status") == "done":
                    completed_tasks += 1
                    
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        console.print(f"\n[bold cyan]Agentic Productivity (Historical)[/bold cyan]")
        console.print(f"  Total Sprints: [bold]{len(history)}[/bold]")
        console.print(f"  Total Tasks Attempted: [bold]{total_tasks}[/bold]")
        console.print(f"  Task Completion Rate: [bold green]{completion_rate:.1f}%[/bold green]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not collect productivity data: {e}[/yellow]")

@analytics.command()
@click.argument("sprint_id", required=False)
def sprint(sprint_id):
    """View metrics for a specific sprint (TTU/TTR)."""
    from ai_sprint.commands.common import auto_detect_sprint_id
    sid = sprint_id or auto_detect_sprint_id()
    if not sid:
        console.print("[bold red]Error:[/bold red] Sprint ID required.")
        return
        
    try:
        collector = SprintCollector(SPRINT_DIR)
        sprint_data = None
        for s in collector.collect_all_sprints():
            if s.get("sprintId") == sid:
                sprint_data = s
                break
                
        if not sprint_data:
            console.print(f"[bold red]Error:[/bold red] Sprint {sid} not found.")
            return
            
        console.print(f"\n[bold cyan]Sprint Analytics: {sid}[/bold cyan]")
        tasks = sprint_data.get("tasks", [])
        
        for t in tasks:
            console.print(f"\n[bold]{t['id']}: {t['title']}[/bold]")
            started = t.get("startedAt")
            first_commit = t.get("firstCommitAt")
            completed = t.get("completedAt")
            
            if started and first_commit:
                try:
                    ttu = datetime.fromisoformat(first_commit) - datetime.fromisoformat(started)
                    console.print(f"  Time To Understand (TTU): [bold blue]{ttu.total_seconds() / 60:.1f} min[/bold blue]")
                except Exception:
                    console.print(f"  Time To Understand (TTU): [dim]Error parsing timestamps[/dim]")
            else:
                console.print(f"  Time To Understand (TTU): [dim]N/A (Incomplete data)[/dim]")
                
            if started and completed:
                try:
                    ttr = datetime.fromisoformat(completed) - datetime.fromisoformat(started)
                    console.print(f"  Time To Resolution (TTR): [bold green]{ttr.total_seconds() / 60:.1f} min[/bold green]")
                except Exception:
                    console.print(f"  Time To Resolution (TTR): [dim]Error parsing timestamps[/dim]")
            else:
                console.print(f"  Time To Resolution (TTR): [dim]In progress[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
