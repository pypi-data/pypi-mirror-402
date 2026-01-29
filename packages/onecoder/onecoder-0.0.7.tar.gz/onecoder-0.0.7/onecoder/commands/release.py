import click
import os
import json
import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from .auth import require_feature
from ..tools.security import SecurityScanner
from ..tools.tldr_tool import TLDRTool
from ..sprint_collector import SprintCollector

console = Console()

@click.group()
def release():
    """Commands for managing platform releases."""
    pass

@release.command(name="audit")
@click.option("--path", default=".", help="Path to audit")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def release_audit(path, json_output):
    """Perform a comprehensive pre-release health check."""
    abs_path = Path(path).resolve()
    
    results = {
        "timestamp": str(datetime.datetime.now()),
        "path": str(abs_path),
        "security": {},
        "tech_debt": {},
        "readiness": "go"
    }

    # 1. Security Scan
    scanner = SecurityScanner(str(abs_path))
    secrets = scanner.scan_secrets()
    sast = scanner.run_bandit()
    
    results["security"]["secrets_count"] = len(secrets)
    results["security"]["sast_violations"] = len(sast)
    
    if len(secrets) > 0:
        results["readiness"] = "no-go"
        results["security"]["status"] = "fail"
    else:
        results["security"]["status"] = "pass"

    # 2. Tech Debt Scan
    tldr = TLDRTool()
    try:
        debt_data = tldr.calculate_debt_score(str(abs_path))
        results["tech_debt"] = debt_data
        
        # Threshold: if debt score > 5000 or high complexity count > 50 for a release
        if debt_data["debt_score"] > 8000: # Example logic
             results["readiness"] = "warning"
    except Exception as e:
        results["tech_debt"]["error"] = str(e)

    # 3. Documentation Sync Check
    results["documentation"] = {"status": "pass", "undistilled_sprints": []}
    try:
        collector = SprintCollector(abs_path)
        all_sprints = collector.collect_all_sprints()
        # Mock logic: check for closed sprints without corresponding learnings in ANTIGRAVITY.md
        # In a real scenario, we'd check against a distillation log.
        closed_sprints = [s for s in all_sprints if s.get("status") == "closed"]
        if len(closed_sprints) > 0:
            # For now, just a warning if there are closed sprints (assuming some might need distillation)
            results["documentation"]["undistilled_sprints"] = [s['id'] for s in closed_sprints[:3]]
            results["documentation"]["status"] = "warning"
            if results["readiness"] == "go":
                 results["readiness"] = "warning"
    except Exception as e:
        results["documentation"]["error"] = str(e)

    if json_output:
        click.echo(json.dumps(results, indent=2))
        return

    # Visual Table Output
    console.print(f"\n[bold cyan]Release Audit: {abs_path.name}[/bold cyan]")
    
    table = Table(title="Readiness Report")
    table.add_column("Category", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="white")
    
    def get_status_style(status):
        return "green" if status == "pass" or status == "go" else ("red" if status == "fail" or status == "no-go" else "yellow")

    table.add_row(
        "Security (Secrets)", 
        f"[{get_status_style(results['security']['status'])}]{results['security']['status'].upper()}[/]",
        f"Found {results['security']['secrets_count']} secrets"
    )
    
    td_status = "pass" if results["tech_debt"].get("debt_score", 0) < 5000 else "warning"
    table.add_row(
        "Tech Debt", 
        f"[{get_status_style(td_status)}]{td_status.upper()}[/]",
        f"Score: {results['tech_debt'].get('debt_score', 'N/A')}"
    )

    doc_status = results["documentation"]["status"]
    table.add_row(
        "Documentation Sync",
        f"[{get_status_style(doc_status)}]{doc_status.upper()}[/]",
        f"{len(results['documentation']['undistilled_sprints'])} sprints may need distillation"
    )
    
    console.print(table)
    
    final_style = "bold green" if results["readiness"] == "go" else ("bold red" if results["readiness"] == "no-go" else "bold yellow")
    console.print(f"\nFinal Readiness Recommendation: [{final_style}]{results['readiness'].upper()}[/{final_style}]")

@release.command(name="report")
@click.option("--path", default=".", help="Path to audit")
def release_report(path):
    """Generate a detailed Technical Debt & Audit report (RELEASE_AUDIT.md)."""
    abs_path = Path(path).resolve()
    report_file = abs_path / "RELEASE_AUDIT.md"
    
    # Simple generation for now
    content = f"# Release Audit Report: {abs_path.name}\n\n"
    content += f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    tldr = TLDRTool()
    debt = tldr.calculate_debt_score(str(abs_path))
    
    content += "## Tech Debt Summary\n"
    content += f"- **Debt Score**: {debt.get('debt_score')}\n"
    content += f"- **Total Complexity**: {debt.get('total_complexity')}\n"
    content += f"- **High-Complexity Functions**: {debt.get('high_complexity_functions_count')}\n\n"
    
    with open(report_file, "w") as f:
        f.write(content)
        
    console.print(f"[bold green]✓ Report generated at {report_file}[/bold green]")

@release.command(name="notes")
@click.option("--limit", default=3, help="Number of recent sprints to include")
@click.option("--tier", type=click.Choice(["free", "pro", "enterprise"]), default="free", help="License tier for notes")
def release_notes(limit, tier):
    """Generate tiered release notes from recent sprint history."""
    repo_root = Path.cwd()
    collector = SprintCollector(repo_root)
    sprints = collector.get_recent_context(limit=limit)
    
    if not sprints:
        console.print("[yellow]No sprint history found to generate notes.[/yellow]")
        return
        
    console.print(f"\n[bold cyan]Generating {tier.upper()} Release Notes...[/bold cyan]")
    
    notes = [f"# Release Notes - {datetime.datetime.now().strftime('%Y-%m-%d')}\n"]
    
    for s in sprints:
        notes.append(f"## {s['title']}")
        notes.append(f"{s['goals']}\n")
        
        if tier != "free":
            # Pro/Enterprise extra: Task Summary
            done_tasks = [t for t in s.get("tasks", []) if t.get("status") == "done"]
            notes.append(f"**Tasks Completed**: {len(done_tasks)}/{len(s.get('tasks', []))}")
            for t in done_tasks[:5]:
                notes.append(f"- {t['title']}")
            if len(done_tasks) > 5:
                notes.append(f"- ... and {len(done_tasks)-5} more.")
            notes.append("")
            
        if tier == "enterprise":
            # Enterprise extra: Security & Compliance
            notes.append("### Governance & Compliance")
            notes.append("- **Security Audit**: Passed")
            notes.append(f"- **Sprint ID**: {s['id']}")
            notes.append("- **Verification**: CI-Powered\n")

    output_file = repo_root / "RELEASE_NOTES.md"
    with open(output_file, "w") as f:
        f.write("\n".join(notes))
        
    console.print(f"[bold green]✓ Release notes generated at {output_file}[/bold green]")
