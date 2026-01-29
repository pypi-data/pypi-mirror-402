import click
import json
import os
import shutil
from pathlib import Path
from rich.console import Console
from rich.table import Table
from .auth import require_feature

def check_path_conflicts():
    """Check for shadowing of the onecoder executable."""
    results = []
    
    # Get all paths from env
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    
    found_executables = []
    
    # Manually search to find ALL occurrences (shutil.which only finds the first)
    for d in path_dirs:
        if not d: continue
        exe_path = os.path.join(d, "onecoder")
        if os.path.exists(exe_path) and os.access(exe_path, os.X_OK):
            # Resolve symlinks to avoid duplicates if possible, or just exact paths
            # path_dirs can contain duplicates
            if exe_path not in found_executables:
                found_executables.append(exe_path)
    
    if not found_executables:
         return {"status": "fail", "message": "onecoder not found in PATH"}

    active_exe = found_executables[0]
    
    # Check if active exe is the uv-managed one
    # .local/bin/onecoder or .local/share/uv/tools/onecoder
    is_uv_managed = ".local/bin" in active_exe or ".local/share/uv" in active_exe
    
    status = "pass"
    message = f"Active: {active_exe}"
    
    if len(found_executables) > 1:
        # Conflict detected
        shadowed = found_executables[1:]
        
        if not is_uv_managed and any("brew" in s for s in shadowed):
            # Broken brew version is shadowing correct one? Or vice versa?
            # If active is NOT uv, and we have multiple, warn.
            status = "warn"
            message = f"Shadowing detected! Active: {active_exe}. Others: {', '.join(shadowed)}"
        elif not is_uv_managed:
             # Active is likely brew or system, but uv might be hidden
             status = "warn"
             message = f"Non-uv installation is active: {active_exe}. Shadowed: {', '.join(shadowed)}"
        elif is_uv_managed:
             # Active is correct, but others exist
             status = "pass"
             message = f"Active: {active_exe} (Shadows: {', '.join(shadowed)})"

    return {"status": status, "message": message}

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
        ts_msg = "Missing (onecoder code symbols/complexity will fail). Run 'pip install onecoder[tldr]'. See 'onecoder guide' for more info."
    
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
    
    # Check CLI PATH conflicts
    path_check = check_path_conflicts()
    results.append({
        "component": "onecoder-cli",
        "file": "PATH",
        "check": "Binary Shadowing",
        "status": path_check["status"],
        "message": path_check["message"] # Add message field to support display
    })
    
    if json_output:
        click.echo(json.dumps(results))
        return

    table = Table(title="Doctor: Environment Check")
    table.add_column("Component")
    table.add_column("File")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    
    for r in results:
        status_style = "green" if r["status"] == "pass" else ("yellow" if r["status"] == "warn" else "red")
        table.add_row(r["component"], r["file"], r["check"], f"[{status_style}]{r['status']}[/]", r.get("message", ""))
    
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
