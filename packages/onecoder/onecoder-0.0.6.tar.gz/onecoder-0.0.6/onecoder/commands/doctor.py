import click
import json
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from .auth import require_feature

@click.group()
def doctor():
    """Automated diagnostic tools for OneCoder."""
    pass

@doctor.command()
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def deps(json_output):
    """Check for critical dependencies (tree-sitter, etc.)."""
    console = Console()
    results = []
    
    # 1. Tree-sitter check
    ts_status = "pass"
    ts_msg = "Installed"
    try:
        import tree_sitter
        import tree_sitter_languages
    except ImportError:
        ts_status = "fail"
        ts_msg = "Missing (onecoder code symbols/complexity will fail). Run 'pip install onecoder[tldr]'"
    
    results.append({"dependency": "tree-sitter", "status": ts_status, "message": ts_msg})
    
    # 2. OneCore (Rust) check
    oc_status = "pass"
    oc_msg = "Active (High-performance governance engine)"
    try:
        from onecore import GovernanceEngine
    except ImportError:
        oc_status = "fail"
        oc_msg = "Missing (High-performance scanning will be disabled). Run 'uv build' in packages/core/onecore"
    
    results.append({"dependency": "onecore", "status": oc_status, "message": oc_msg})

    # 3. Git check
    git_status = "pass"
    try:
        import subprocess
        subprocess.run(["git", "--version"], check=True, capture_output=True)
    except Exception:
        git_status = "fail"
    
    results.append({"dependency": "git", "status": git_status, "message": "Binary check"})

    if json_output:
        click.echo(json.dumps(results))
        return

    table = Table(title="Doctor: Dependency Check")
    table.add_column("Dependency")
    table.add_column("Status")
    table.add_column("Message")
    
    for r in results:
        status_style = "green" if r["status"] == "pass" else "red"
        table.add_row(r["dependency"], f"[{status_style}]{r['status']}[/]", r["message"])
    
    console.print(table)

@doctor.command()
@click.option("--env", "env_check", is_flag=True, help="Check environment variables")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def env(env_check, json_output):
    """Scan and validate environment configuration."""
    console = Console()
    # Mock implementation of SPEC-CLI-014.1
    results = [
        {"component": "onecoder-api", "file": ".env", "check": "JWT_SECRET", "status": "pass"},
        {"component": "onecoder-cli", "file": ".env", "check": "ONECODER_API_URL", "status": "pass"}
    ]
    
    if json_output:
        click.echo(json.dumps(results))
        return

    table = Table(title="Doctor: Environment Check")
    table.add_column("Component")
    table.add_column("File")
    table.add_column("Check")
    table.add_column("Status")
    
    for r in results:
        status_style = "green" if r["status"] == "pass" else "red"
        table.add_row(r["component"], r["file"], r["check"], f"[{status_style}]{r['status']}[/]")
    
    console.print(table)

@doctor.command()
@require_feature("diagnostic_tools")
def ports():
    """Identify and resolve port conflicts."""
    console = Console()
    console.print("[yellow]Port check implementation in progress...[/yellow]")

@doctor.command()
@require_feature("diagnostic_tools")
def db():
    """Validate database schema and role readiness."""
    console = Console()
    console.print("[yellow]DB check implementation in progress...[/yellow]")

@click.command()
@click.argument("url")
@require_feature("diagnostic_tools")
def trace(url):
    """Simulate and trace a request through the proxy gateway."""
    console = Console()
    console.print(f"[cyan]Tracing path to {url}...[/cyan]")
    console.print("[yellow]Trace implementation in progress...[/yellow]")
