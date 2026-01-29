import click
import os
import sys
import subprocess
import asyncio
from ..common import console, PROJECT_ROOT, SPRINT_DIR, SprintStateManager
from .utils import (
    _validate_commit_context, 
    _stage_files_helper, 
    _build_commit_trailers, 
    _run_guardian_check
)
from ...commit import create_commit_with_trailers
from onecoder.sync import sync_project_context

@click.command()
@click.option("--message", "-m", required=True, help="Commit message")
@click.option("--task-id", help="Task identifier")
@click.option("--task", help="Alias for --task-id")
@click.option("--status", help="Task status (planning, in-progress, review, done, completed)")
@click.option("--validation", help="Validation status or URI")
@click.option("--sprint-id", help="Override sprint ID")
@click.option("--spec-id", help="Specification ID(s)")
@click.option("--component", help="Component scope")
@click.option("--files", "-f", multiple=True, help="Files to stage (can be repeated or comma-separated)")
@click.argument("files_args", nargs=-1, type=click.Path())
def commit(message, task_id, task, status, validation, sprint_id, spec_id, component, files, files_args):
    """Create atomic commit with metadata trailers."""
    
    # Merge files from flag and positional args
    all_files = list(files_args)
    for f_opt in files:
        all_files.extend([f.strip() for f in f_opt.split(",") if f.strip()])
    
    # 0. Fast-path bypass for emergencies
    if os.environ.get("ONECODER_SKIP_PREFLIGHT") == "true":
        console.print("[yellow]Bypassing governance checks due to ONECODER_SKIP_PREFLIGHT=true[/yellow]")
        if all_files:
            subprocess.run(["git", "add"] + all_files, cwd=PROJECT_ROOT, check=True)
    
    # 1. Parameter Aliasing & Validation
    if task and not task_id:
        task_id = task
    if status == "completed":
        status = "done"

    if status and status not in ["planning", "in-progress", "review", "done"]:
         console.print(f"[bold red]Error:[/bold red] Invalid status: {status}. Allowed: planning, in-progress, review, done, completed")
         sys.exit(1)

    # 2. Spec ID Enforcement (No Exemptions)
    if not spec_id:
         from .utils import _prompt_for_spec_id
         spec_id = _prompt_for_spec_id(message)
         if not spec_id: # User cancelled or empty
             console.print("[bold red]Governance Violation:[/bold red] --spec-id is mandatory for ALL commits.")
             sys.exit(1)

    # 3. Pre-flight Validation
    if not _validate_commit_context(task_id, sprint_id, spec_id):
        sys.exit(1)

    # 4. Stage Files
    task_id = _stage_files_helper(all_files, task_id=task_id, component=component)

    # 6. Build Trailers
    trailers, active_sprint_id = _build_commit_trailers(
        message, None, sprint_id, component, task_id, status, validation, spec_id
    )

    # 6.5 Pre-Commit State Updates (Record event and stage sprint.yaml BEFORE commit)
    # DISABLED: User requested to look at implementation and disable it.
    # if active_sprint_id and task_id:
    #     try:
    #         state_manager = SprintStateManager(SPRINT_DIR / active_sprint_id)
    #         changed = state_manager.record_task_event(task_id, "first_commit")
    #         if changed:
    #             # Stage it so it's included in the upcoming commit
    #             subprocess.run(["git", "add", str(state_manager.state_file)], cwd=PROJECT_ROOT, check=False)
    #     except Exception: pass

    # 7. Safety Checks (Submodules & Guardian)
    from ...submodule import get_unpushed_submodules, push_submodule
    unpushed = get_unpushed_submodules(PROJECT_ROOT)
    if unpushed:
        console.print("[bold yellow]Governance Alert:[/bold yellow] Unpushed submodule commits detected.")
        for path, sha in unpushed:
            console.print(f"  • [cyan]{path}[/cyan] ({sha[:7]})")
        
        if click.confirm("\nPush these submodules now to satisfy governance?", default=True):
            for path, sha in unpushed:
                console.print(f"Syncing [cyan]{path}[/cyan]...")
                if push_submodule(path, PROJECT_ROOT):
                    console.print(f"  [bold green]✓ {path} pushed.[/bold green]")
                else:
                    console.print(f"  [bold red]❌ Failed to push {path}.[/bold red]")
                    sys.exit(1)
        else:
            console.print("[bold red]Error:[/bold red] Commit blocked by unpushed submodules.")
            sys.exit(1)

    _run_guardian_check(None, trailers)

    # 8. Create Commit (Single Call)
    # 7.5 Sync & Normalize Metadata (Before Commit)
    try:
        # Sync first to normalize timestamps/titles in sprint.yaml
        asyncio.run(sync_project_context())
        
        # If active sprint found, stage its metadata to include normalization in this commit
        if active_sprint_id:
             sprint_dir = SPRINT_DIR / active_sprint_id
             metadata_files = [str(sprint_dir / "sprint.yaml"), str(sprint_dir / "TODO.md")]
             # Only stage if they exist
             valid_files = [f for f in metadata_files if os.path.exists(f)]
             if valid_files:
                 subprocess.run(["git", "add"] + valid_files, cwd=PROJECT_ROOT, check=False)
    except Exception as e:
        console.print(f"[dim]Sync warning: {e}[/dim]")

    # 8. Create Commit (Single Call)
    if create_commit_with_trailers(message, trailers):
        console.print("[bold green]Success:[/bold green] Commit created.")
    else:
        sys.exit(1)
