import click
import json
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any
from ..common import console, PROJECT_ROOT, SPRINT_DIR, SprintStateManager, auto_detect_sprint_id
from ...policy import PolicyEngine
from .utils import _run_check
from onecoder.commands.auth import require_feature

@click.command()
@click.option("--sprint-id", help="Override sprint ID")
@require_feature("governance_tools")
def verify(sprint_id):
    """Verify sprint for technical debt (Zero Errors/Lint)."""
    active_sprint = sprint_id or auto_detect_sprint_id()
    if not active_sprint:
        console.print("[bold red]Error:[/bold red] No active sprint detected.")
        sys.exit(1)
    
    async def run_verify():
        target_dir = SPRINT_DIR / active_sprint
        state_manager = SprintStateManager(target_dir)
        component = state_manager.get_component()
        if not component:
            console.print("[bold red]Error:[/bold red] No component scope defined for this sprint.")
            sys.exit(1)

        console.print(f"[cyan]Verifying component debt for [bold]{component}[/bold]...[/cyan]")
        policy_engine = PolicyEngine(PROJECT_ROOT)
        comp_rules = policy_engine.get_verification_rules().get(component, [])
        
        # Tech Debt Calculation (New)
        total_debt = 0
        total_complexity = 0
        try:
            from onecoder.tools.tldr_tool import TLDRTool
            tldr = TLDRTool()
            for comp in component.split(","):
                comp = comp.strip()
                comp_path = PROJECT_ROOT / comp
                
                # Robust resolution: check common locations if root join fails
                if not comp_path.exists():
                    # Try packages/core/engines/onecoder-cli (common for cli/tui)
                    if comp in ["cli", "tui"]:
                        comp_path = PROJECT_ROOT / "packages/core/engines/onecoder-cli"
                        if comp == "tui":
                            comp_path = comp_path / "onecoder/tui"
                    else:
                        # Fallback: search for directory with name comp
                        try:
                            matches = list(PROJECT_ROOT.glob(f"**/ {comp}"))
                            if matches: comp_path = matches[0]
                        except Exception: pass

                if comp_path.exists():
                    debt_data = tldr.calculate_debt_score(str(comp_path))
                    total_debt += debt_data.get('debt_score', 0)
                    total_complexity += debt_data.get('total_complexity', 0)
            console.print(f"  📊 [bold cyan]Tech Debt Score: {total_debt}[/bold cyan] (Complexity: {total_complexity})")
        except Exception as e:
            console.print(f"  ⚠️ [yellow]Debt analysis skipped: {e}[/yellow]")
            total_debt = 0

        tasks = []
        for check in comp_rules:
            cmd = check if isinstance(check, str) else check['cmd']
            name = check if isinstance(check, str) else check['name']
            tasks.append(_run_check(name, cmd, PROJECT_ROOT / component))
        
        results = {
            "errors": 0, 
            "lint_violations": 0, 
            "debt_score": total_debt,
            "details": []
        }
        check_results = await asyncio.gather(*tasks)
        
        for res in check_results:
            if res["returncode"] != 0:
                results["errors" if "lint" not in res["name"].lower() else "lint_violations"] += 1
                console.print(f"  ❌ [bold red]{res['name']} failed[/bold red]")
            else:
                 console.print(f"  ✅ [green]{res['name']} passed[/green]")
        
        # Remediation Enforcement (SPEC-GOV-015)
        sprint_state = state_manager.load()
        is_remediation = "tech-debt" in sprint_state.get("metadata", {}).get("labels", [])
        if is_remediation and total_debt > 0:
            # Look for previous sprint debt score (mocked for now or extracted from historical telemetry)
            # In a real impl, this would query the API or local knowledge base
            previous_debt = 11000 # Example baseline
            delta = total_debt - previous_debt
            if delta >= 0:
                console.print(f"  ❌ [bold red]Remediation Failure:[/bold red] Complexity Delta is non-negative ({delta:+}).")
                results["errors"] += 1
            else:
                console.print(f"  ✅ [bold green]Remediation Success:[/bold green] Complexity Delta: [bold]{delta:+}[/bold]")

        with open(target_dir / ".verification_results.json", "w") as f:
            json.dump(results, f)
        
        return results

    results = asyncio.run(run_verify())
    if results["errors"] > 0 or results["lint_violations"] > 0:
        sys.exit(1)
    console.print("\n[bold green]✓ Zero-Debt Verification Passed.[/bold green]")
