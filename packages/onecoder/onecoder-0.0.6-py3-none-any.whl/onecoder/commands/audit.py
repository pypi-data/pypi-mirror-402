import click
from rich.console import Console
from rich.table import Table
from ..tools.security import SecurityScanner
from ..issues import IssueManager
from ..commands.auth import require_feature
import os
import sys

@click.group()
@require_feature("audit_tools")
def audit():
    """Security and compliance auditing."""
    pass

@audit.command(name="scan")
@click.option("--path", default=".", help="Path to scan")
def audit_scan(path):
    """Scan for vulnerabilities and security issues."""
    console = Console()
    scanner = SecurityScanner(os.path.abspath(path))
    
    with console.status("[bold green]Scanning dependencies..."):
        components = scanner.scan_dependencies()
        
    if components:
        table = Table(title="Dependency Inventory")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="magenta")
        table.add_column("Source", style="green")
        
        for c in components:
            table.add_row(c.get("name"), c.get("version"), c.get("source", "SBOM"))
        console.print(table)
    else:
        console.print("[yellow]No dependencies found or scanned.[/yellow]")

    with console.status("[bold red]Running Bandit SAST & Secret Scan..."):
        findings = scanner.run_bandit()
        secret_findings = scanner.scan_secrets()
        findings.extend(secret_findings)
        
    if findings:
        issue_table = Table(title="Security Findings (SAST & Secrets)")
        issue_table.add_column("ID", style="dim")
        issue_table.add_column("Severity", style="red")
        issue_table.add_column("Issue", style="white")
        issue_table.add_column("Location", style="cyan")
        
        for f in findings:
            issue_table.add_row(
                f.get("id"),
                f.get("severity"),
                f.get("issue_text"),
                f"{f.get('file')}:{f.get('line')}"
            )
        console.print(issue_table)
        
        if click.confirm("Do you want to capture these findings into local .issues?"):
            manager = IssueManager()
            for f in findings:
                data = {
                    "message": f.get("issue_text"),
                    "error_type": f.get("id"),
                    "context": {"file": f.get("file"), "line": f.get("line")},
                    "severity": f.get("severity")
                }
                manager.create_from_telemetry(data, title=f"Security: {f.get('issue_text')[:50]}")
            console.print("[bold green]✓ Findings captured.[/bold green]")
    else:
        console.print("[green]No SAST/Secret findings detected.[/green]")

@audit.command(name="public")
@click.option("--org", help="GitHub Organization to scan")
@click.option("--repo", help="Specific repo to scan (format: owner/repo)")
def audit_public(org, repo):
    """Scan public repositories for secrets."""
    console = Console()
    
    if not org and not repo:
        console.print("[red]Error: Must specify --org or --repo[/red]")
        return
        
    target = repo if repo else org
    context_type = "Repository" if repo else "Organization"
    
    # Load & Execute PublicScanner Skill
    try:
        # Resolve platform root
        curr = os.path.abspath(os.path.dirname(__file__))
        # Walk up to find packages usually ../../../../
        platform_root = None
        p = os.path.dirname(curr)
        for _ in range(5):
             if os.path.exists(os.path.join(p, "packages")):
                 platform_root = p
                 break
             p = os.path.dirname(p)
        if not platform_root: # Fallback
             platform_root = os.getcwd()

        skills_pkg_path = os.path.join(platform_root, "packages", "skills")
        
        if os.path.exists(skills_pkg_path):
             if str(skills_pkg_path) not in sys.path:
                  sys.path.append(str(skills_pkg_path))
             try:
                 from skills.public_scanner.scanner import PublicScanner
             except ImportError:
                  skill_dir = os.path.join(skills_pkg_path, "skills", "public_scanner")
                  if os.path.exists(skill_dir):
                       sys.path.append(skill_dir)
                       from scanner import PublicScanner
                  else:
                       console.print(f"[red]PublicScanner skill not found at {skill_dir}[/red]")
                       return
        else:
             console.print(f"[red]Skills package not found at {skills_pkg_path}[/red]")
             return  

        scanner = PublicScanner()
        with console.status(f"[bold blue]Scanning public {context_type}: {target}..."):
             result = scanner.execute(context={}, org=org, repo=repo)
             
        stats = result.get("stats", {})
        findings = result.get("findings", [])
        
        table = Table(title=f"Public Scan Results: {target}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Repos Scanned", str(stats.get("scanned", 0)))
        table.add_row("Secrets Found", str(stats.get("secrets_found", 0)))
        table.add_row("Suspicious Files", str(stats.get("suspicious_files", 0)))
        
        console.print(table)
        
        if findings:
            console.print("[yellow]⚠ Suspicious files detected. Creating audit log...[/yellow]")
            try:
                manager = IssueManager()
                for f in findings:
                    manager.create_from_telemetry({
                        "message": f.get("message"),
                        "severity": f.get("severity"),
                        "context": {"target": target, "file": f.get("file")}
                    }, title=f"Audit: {target}")
                console.print("[green]✓ Audit log created.[/green]")
            except Exception:
                 console.print("[dim]Could not create issue log (local env only)[/dim]")

    except Exception as e:
        console.print(f"[red]Scan failed: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
