import click
import requests
import os
import json
from rich.console import Console
from rich.table import Table
from typing import Optional

console = Console()

# Default to local API for now, can be overridden
SKILLS_API_URL = os.getenv("SKILLS_API_URL", "http://localhost:8787/api/skills")

@click.group()
def skills():
    """Manage and discover OneCoder skills."""
    pass

@skills.command()
@click.option("--search", help="Search term for skills")
@click.option("--category", help="Filter by category")
def list(search: Optional[str], category: Optional[str]):
    """List available skills from the marketplace."""
    try:
        params = {}
        if search:
            params["search"] = search
        if category:
            params["category"] = category
            
        response = requests.get(SKILLS_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        table = Table(title="Available Skills")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Category", style="green")
        table.add_column("Description")
        
        for item in data.get("skills", []):
            skill = item.get("skill", {})
            table.add_row(
                skill.get("id", "N/A"),
                skill.get("name", "N/A"),
                skill.get("category", "N/A"),
                skill.get("description", "N/A")
            )
            
        console.print(table)
        
    except requests.exceptions.ConnectionError:
        console.print("[red]Error: Could not connect to Skills API. Is it running?[/red]")
        console.print(f"Tried connecting to: {SKILLS_API_URL}")
    except Exception as e:
        console.print(f"[red]Error fetching skills: {str(e)}[/red]")

@skills.command()
@click.argument("term")
def search(term):
    """Search for skills (alias for list --search)."""
    # Reuse list logic
    ctx = click.get_current_context()
    ctx.invoke(list, search=term, category=None)

@skills.command()
@click.argument("skill_id")
def info(skill_id):
    """Get detailed information about a skill."""
    try:
        url = f"{SKILLS_API_URL}/{skill_id}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        skill = data.get("skill", {}).get("skill", {})
        versions = data.get("versions", [])
        
        console.print(f"[bold magenta]Skill: {skill.get('name')}[/bold magenta] ({skill.get('id')})")
        console.print(f"[green]Category: {skill.get('category')}[/green]")
        console.print(f"\n{skill.get('description')}\n")
        
        console.print("[bold]Versions:[/bold]")
        for v in versions:
            console.print(f"- {v.get('version')} (Created: {v.get('created_at')})")
            
    except requests.exceptions.ConnectionError:
        console.print("[red]Error: Could not connect to Skills API.[/red]")
    except requests.exceptions.HTTPError as e:
         if e.response.status_code == 404:
             console.print(f"[yellow]Skill '{skill_id}' not found.[/yellow]")
         else:
             console.print(f"[red]API Error: {str(e)}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
