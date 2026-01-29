import click
import json
import os
import re
import subprocess
import sys
import shutil
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from ..common import console, PROJECT_ROOT, SPRINT_DIR, SprintStateManager, auto_detect_sprint_id
from ..submodule import get_unpushed_submodules, push_submodule
from ...commit import validate_trailers, create_commit_with_trailers
from ...spec_validator import validate_spec_ids
from ...trace import trace_specifications
from ...preflight import SprintPreflight
from ...policy import PolicyEngine
from onecoder.commands.auth import require_feature
from onecoder.sync import sync_project_context
from onecoder.distillation import capture_engine

def _validate_commit_context(task_id: str, sprint_id: str, spec_id: str):
    """Validate all context requirements before attempting commit."""
    # 1. Git Config Check
    try:
        subprocess.run(["git", "config", "user.name"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        console.print("[bold red]Pre-check Failed:[/bold red] Git user/email not configured.")
        console.print("  Run: git config --global user.name 'Your Name'")
        console.print("  Run: git config --global user.email 'you@example.com'")
        return False
        
    # 2. Sprint Check
    active_sprint = sprint_id or auto_detect_sprint_id()
    if not active_sprint:
        console.print("[bold red]Pre-check Failed:[/bold red] No active sprint detected.")
        console.print("  Run: onecoder sprint init <name>")
        return False
        
    # 3. Spec Check (Syntax Only - full check later)
    if spec_id and not re.match(r"^SPEC-[A-Z]+-\d+(?:\.\d+)*", spec_id):
        console.print(f"[bold red]Pre-check Failed:[/bold red] Invalid Spec ID format: {spec_id}")
        return False

    return True

def _stage_files_helper(files: str):
    """Stage files for commit."""
    # Check for staged changes first
    staged_changes = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True).stdout.strip()
    if not files and not staged_changes:
        console.print("[bold red]Error:[/bold red] No files staged and no --files argument provided.")
        console.print("[dim]Please specify files to commit using -f/--files or stage them manually.[/dim]")
        sys.exit(1)

    if files:
        file_list = [f.strip() for f in files.split(",") if f.strip()]
        if file_list:
            console.print(f"[dim]Staging files: {', '.join(file_list)}[/dim]")
            try:
                subprocess.run(["git", "add"] + file_list, cwd=PROJECT_ROOT, check=True)
            except subprocess.CalledProcessError as e:
                console.print(f"[bold red]Error staging files:[/bold red] {e}")
                sys.exit(1)

def _build_commit_trailers(
    message, reason, sprint_id, component, task_id, status, validation, spec_id
):
    """Construct commit trailers dictionary."""
    trailers = {}
    if reason:
        trailers["Decision-Reason"] = reason
        
    active_sprint_id = sprint_id or auto_detect_sprint_id()
    if active_sprint_id:
        trailers["Sprint-Id"] = active_sprint_id
        if not component:
            try:
                state_manager = SprintStateManager(SPRINT_DIR / active_sprint_id)
                component = state_manager.get_component()
            except Exception: pass
            
    if component: 
        trailers["Component"] = component
    
    if task_id:
        if not re.match(r"^task-\d+$", task_id):
            resolved = None
            if active_sprint_id:
                try:
                    state_manager = SprintStateManager(SPRINT_DIR / active_sprint_id)
                    resolved = state_manager.get_task_id_by_title(task_id)
                except Exception: pass
            if not resolved and task_id.isdigit():
                resolved = f"task-{int(task_id):03d}"
            if resolved:
                console.print(f"[dim]Resolved Task ID: {task_id} -> {resolved}[/dim]")
                task_id = resolved
        trailers["Task-Id"] = task_id

    if status:
        if status == "done":
            try:
                result = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True)
                staged_files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
                # Exclude metadata files
                has_impl_changes = any(not (f.startswith(".sprint/") or f in ["TODO.md", "RETRO.md", "README.md", "sprint.json", "sprint.yaml"]) for f in staged_files)
                is_exception = any(x in message.lower() for x in ["docs", "chore", "governance", "fix", "ci"])
                
                # If no implementation changes and not a standard exception type, flag it
                if not has_impl_changes and not is_exception:
                    console.print("[bold red]Error:[/bold red] Implementation Integrity Violation (SPEC-GOV-008.2)")
                    sys.exit(1)
            except Exception: pass
        trailers["Status"] = status

    if validation: 
        trailers["Validation"] = validation
        
    if spec_id:
        is_valid, errors = validate_spec_ids(spec_id, PROJECT_ROOT)
        if not is_valid:
            for error in errors: console.print(f"  ❌ {error}")
            sys.exit(1)
        trailers["Spec-Id"] = spec_id

    errors = validate_trailers(trailers)
    if errors:
        for error in errors: console.print(f"  ❌ {error}")
        sys.exit(1)
        
    return trailers, active_sprint_id

def _run_guardian_check(reason, trailers):
    """Run Governance Guardian checks on staged files."""
    try:
        from onecoder.governance.guardian import GovernanceGuardian
        guardian = GovernanceGuardian(PROJECT_ROOT / "governance.yaml")
        
        res = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True)
        if res.returncode == 0:
            current_staged = [f.strip() for f in res.stdout.split("\n") if f.strip()]
            is_safe, msg, metadata = guardian.validate_staged_files(current_staged, reason=reason)
            
            if not is_safe:
                console.print(f"[bold red]Governance Block (Guardian):[/bold red] {msg}")
                sys.exit(1)
            elif metadata.get("override"):
                console.print(f"[yellow]Governance Override:[/yellow] {msg}")
                if not click.confirm("Do you want to proceed with this override?"):
                    console.print("[red]Aborted by user.[/red]")
                    sys.exit(1)
                
                if "Decision-Reason" not in trailers:
                    trailers["Decision-Reason"] = reason
                
                # Log decision trace (telemetry)
                try:
                    if not capture_engine.current_session_id:
                         import datetime
                         capture_engine.start_session(f"commit-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}")
                    
                    capture_engine.sync_decision(
                        actor="user:cli",
                        action="commit_override",
                        reasoning={"reason": reason, "violation": metadata.get("violation")},
                        policy_snapshot={"violation_msg": msg}
                    )
                    capture_engine.save_session()
                except Exception as e:
                    console.print(f"[dim]Telemetry warning: {e}[/dim]")
    except ImportError:
        pass
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Governance check failed to run: {e}")

async def _run_check(name: str, cmd: str, cwd: Path) -> Dict[str, Any]:
    """Helper to run a check command asynchronously."""
    proc = await asyncio.create_subprocess_shell(
        cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return {
        "name": name,
        "returncode": proc.returncode,
        "stdout": stdout.decode(),
        "stderr": stderr.decode()
    }

def _ensure_visual_assets(target_dir, name, is_apply, plan, policy_engine):
    """Ensure visual assets exist based on policy."""
    from ...visual_generator import generate_visual_assets
    
    visual_policy = policy_engine.get_visual_policy()
    if visual_policy.get("auto_generate_on_close"):
        media_dir = target_dir / "media"
        if is_apply or media_dir.exists() or plan:
             console.print(f"[cyan]Ensuring visual assets for {name}...[/cyan]")
             try:
                 generate_visual_assets(target_dir, name)
             except Exception as e:
                 if "Google IDE" not in str(e):
                     console.print(f"[yellow]Warning:[/yellow] Visual generation issue: {e}")

def _validate_git_state(target_dir, name, is_apply):
    """Validate git state before closure."""
    unpushed = get_unpushed_submodules(PROJECT_ROOT)
    if unpushed:
        console.print("[bold yellow]Governance Alert:[/bold yellow] Unpushed submodule commits detected.")
        for path, sha in unpushed:
            console.print(f"  • [cyan]{path}[/cyan] ({sha[:7]})")
        
        if is_apply:
            if click.confirm("\nPush these submodules now to satisfy governance?", default=True):
                for path, sha in unpushed:
                    console.print(f"Syncing [cyan]{path}[/cyan]...")
                    if push_submodule(path, PROJECT_ROOT):
                        console.print(f"  [bold green]✓ {path} pushed.[/bold green]")
                    else:
                        console.print(f"  [bold red]❌ Failed to push {path}.[/bold red]")
                        sys.exit(1)
            else:
                console.print("[bold red]Cannot close:[/bold red] Submodule dependency tree not synced.")
                sys.exit(1)
        else:
            console.print("[bold red]Cannot close:[/bold red] Unpushed submodule commits detected.")
            sys.exit(1)

    try:
        # Check for staged changes
        staged = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, cwd=PROJECT_ROOT)
        if staged.returncode == 0 and staged.stdout.strip():
             console.print("[bold red]Cannot close:[/bold red] Found staged changes.")
             sys.exit(1)

        # Check for uncommitted implementation changes
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=PROJECT_ROOT)
        if result.returncode == 0 and result.stdout.strip():
            uncommitted_files = [f for f in result.stdout.strip().split("\n") 
                                if not (f[3:].startswith(".sprint/") or f[3:].endswith(".json") or f[3:].endswith(".yaml") or f[3:] in ["TODO.md", "RETRO.md", "README.md", "sprint.json", "sprint.yaml"])]
            if uncommitted_files:
                console.print(f"[bold red]Cannot close:[/bold red] Found {len(uncommitted_files)} uncommitted implementation changes.")
                sys.exit(1)
    except Exception as e: console.print(f"[yellow]Warning:[/yellow] Git check: {e}")

    # TODO.md check
    todo_file = target_dir / "TODO.md"
    if todo_file.exists():
        with open(todo_file, "r") as f: lines = f.readlines()
        delivery_sections = ["## High Priority", "## Implementation"]
        in_delivery_section = True
        incomplete_tasks = []
        for line in lines:
            if line.startswith("## "):
                section_name = line.strip()
                if section_name in delivery_sections: in_delivery_section = True
                elif section_name in ["## Backlog", "## Future"]: in_delivery_section = False
                else: in_delivery_section = "backlog" not in section_name.lower()
            if in_delivery_section:
                match = re.match(r"-\s*\[\s\]\s*(.+)", line)
                if match and match.group(1).strip(): incomplete_tasks.append(match.group(1).strip())
        if incomplete_tasks:
            console.print(f"[bold red]Cannot close:[/bold red] Found {len(incomplete_tasks)} incomplete tasks.")
            sys.exit(1)

    # Retro check
    retro_file = target_dir / "RETRO.md"
    if not retro_file.exists() or retro_file.stat().st_size < 50:
        if is_apply:
            console.print(f"[cyan]Auto-generating missing RETRO.md for {name}...[/cyan]")
            from onecoder.distillation import SprintDistiller
            distiller = SprintDistiller(PROJECT_ROOT)
            draft = distiller.generate_retro_draft(name)
            retro_file.write_text(draft)
            console.print("[green]✓ RETRO.md draft generated.[/green]")
        else:
            console.print("[bold red]Cannot close:[/bold red] RETRO.md missing or too short.")
            console.print("[dim]Tip: Run with --apply to auto-generate a draft retro.[/dim]")
            sys.exit(1)
            
    # BAKE-IT check
    try:
        trace_map = trace_specifications(PROJECT_ROOT, limit=500)
        sprint_flags = [f for f in trace_map.get("audit", []) if name in str(f.get("message", "")) or name == f.get("id") or (f.get("sprint_id") == name)]
        if sprint_flags:
            console.print("[bold red]Cannot close: BAKE-IT Anti-Patterns Detected![/bold red]")
            sys.exit(1)
    except Exception as e: console.print(f"[yellow]Warning:[/yellow] Audit check skipped: {e}")

def _apply_closure(target_dir, name, pr):
    """Execute the closure phase."""
    from ...pr_creator import create_pull_request
    
    (target_dir / ".status").write_text("Closed")
    try:
        to_add = [a for a in [str(target_dir.relative_to(PROJECT_ROOT)), "TODO.md", "RETRO.md", "README.md", "sprint.json", "sprint.yaml"] if (PROJECT_ROOT / a).exists()]
        if to_add:
            subprocess.run(["git", "add"] + to_add, cwd=PROJECT_ROOT, check=True)
            commit_msg = f"chore(gov): close sprint {name}\n\n[Sprint-Id: {name}]\n[Status: closed]"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=PROJECT_ROOT, check=True)
    except Exception as e: console.print(f"[yellow]Warning:[/yellow] Governance commit failed: {e}")

    console.print(f"[bold green]Success:[/bold green] Sprint {name} closed.")
    if pr:
        try:
            create_pull_request(target_dir, name)
            console.print("[green]✓[/green] Pull request created")
        except Exception as e: console.print(f"[bold red]Error:[/bold red] PR failed: {e}")
