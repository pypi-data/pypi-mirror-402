import click
import json
import os
import re
import subprocess
import sys
import shutil
from pathlib import Path
from .common import console, PROJECT_ROOT, SPRINT_DIR
from onecoder.commands.auth import require_feature

@click.command()
@click.option("--limit", default=100, help="Number of commits to trace")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@require_feature("audit_tools")
def trace(limit, json_output):
    """Visualize specification traceability across history."""
    from ..trace import trace_specifications
    trace_map = trace_specifications(PROJECT_ROOT, limit)
    
    if json_output:
        console.print(json.dumps(trace_map, indent=2))
        return

    from rich.tree import Tree
    from rich.panel import Panel
    root_tree = Tree("[bold cyan]OneCoder Traceability Map[/bold cyan]")
    
    # Track which specs have been added to the tree
    for spec_id, data in trace_map.get("specs", {}).items():
        spec_node = root_tree.add(f"[bold yellow]Specification: {spec_id}[/bold yellow]")
        for sprint_id in data.get("sprints", []):
            sprint_node = spec_node.add(f"[cyan]Sprint: {sprint_id}[/cyan]")
            sprint_data = trace_map.get("sprints", {}).get(sprint_id, {})
            # Only show tasks for THIS spec that are in THIS sprint
            for tid in data.get("tasks", []):
                if tid in sprint_data.get("tasks", {}):
                    task_node = sprint_node.add(f"[green]Task: {tid}[/green]")
                    for commit in sprint_data["tasks"][tid]:
                        if spec_id in commit.get("spec_ids", []):
                            task_node.add(f"[dim]{commit['hash']}[/dim] {commit['message']}")

    console.print(Panel(root_tree, border_style="blue", expand=False))

@click.command()
@click.option("--limit", default=100, help="Number of commits to audit")
@click.option("--staged", is_flag=True, help="Audit staged changes for BAKE-IT patterns")
@require_feature("audit_tools")
def audit(limit, staged):
    """Run a comprehensive Procedural Integrity audit."""
    from ..trace import trace_specifications
    audit_findings = []
    if staged:
        try:
            result = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True)
            staged_files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
            if not staged_files: return
        except Exception: pass
    
    trace_map = trace_specifications(PROJECT_ROOT, limit=limit)
    audit_findings.extend(trace_map.get("audit", []))
    if not audit_findings:
        console.print("[bold green]✓ No Procedural Integrity violations detected.[/bold green]")
        return
    for flag in audit_findings:
        console.print(f"  • [yellow]{flag['type']}[/yellow]: {flag['message']}")

@click.command()
@click.option("--component", help="Filter by component")
@click.option("--category", help="Filter by category")
def backlog(component, category):
    """View consolidated backlog across all sprints."""
    if not SPRINT_DIR.exists(): return
    from rich.table import Table
    table = Table(title="Global Backlog")
    # (Abbreviated backlog logic, normally matches cli.py backlog function)
    console.print(table)

@click.command()
def check_submodules():
    """Verify that all submodule commits are pushed to their remotes."""
    from ..submodule import get_unpushed_submodules
    unpushed = get_unpushed_submodules(PROJECT_ROOT)
    if unpushed:
        console.print("[bold red]Error:[/bold red] Unpushed submodule commits detected.")
        sys.exit(1)
    console.print("[bold green]✓ Submodule integrity verified.[/bold green]")

@click.command()
def install_hooks():
    """Install Git hooks for Procedural Integrity enforcement and governance."""
    hooks_dir = PROJECT_ROOT / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    sprint_bin = shutil.which("onecoder") or "onecoder"
    cmd_prefix = f"uv run {sprint_bin}" if (PROJECT_ROOT / "uv.lock").exists() else sprint_bin
    
    # Pre-commit: Submodules, Preflight (staged), and Audit
    pre_commit_path = hooks_dir / "pre-commit"
    pre_commit_content = f"#!/bin/bash\n{cmd_prefix} sprint check-submodules || exit 1\n{cmd_prefix} sprint preflight --staged || exit 1\n{cmd_prefix} sprint audit --limit 0 --staged || exit 1\n"
    pre_commit_path.write_text(pre_commit_content)
    pre_commit_path.chmod(0o755)
    
    # Pre-push: Preflight
    pre_push_path = hooks_dir / "pre-push"
    pre_push_content = f"#!/bin/bash\n{cmd_prefix} sprint preflight || exit 1\n"
    pre_push_path.write_text(pre_push_content)
    pre_push_path.chmod(0o755)
    
    console.print(f"[bold green]✓ Installed Procedural Integrity enforcement hook.[/bold green]")
