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
@click.option("--files", "-f", help="Files to stage (comma-separated or multiple)")
@click.option("--files", "-f", help="Files to stage (comma-separated or multiple)")
def commit(message, task_id, task, status, validation, sprint_id, spec_id, component, files):
    """Create atomic commit with metadata trailers."""
    
    # 0. Fast-path bypass for emergencies
    if os.environ.get("ONECODER_SKIP_PREFLIGHT") == "true":
        console.print("[yellow]Bypassing governance checks due to ONECODER_SKIP_PREFLIGHT=true[/yellow]")
        if files:
            file_list = [f.strip() for f in files.split(",") if f.strip()]
            if file_list:
                subprocess.run(["git", "add"] + file_list, cwd=PROJECT_ROOT, check=True)
    
    # 1. Parameter Aliasing & Validation
    if task and not task_id:
        task_id = task
    if status == "completed":
        status = "done"

    if status and status not in ["planning", "in-progress", "review", "done"]:
         console.print(f"[bold red]Error:[/bold red] Invalid status: {status}. Allowed: planning, in-progress, review, done, completed")
         sys.exit(1)

    # 2. Spec ID Enforcement
    is_exempt = any(p in message.lower() for p in ["docs:", "chore:", "ci:", "test:", "fix:"])
    if not spec_id and not is_exempt:
         console.print("[bold red]Governance Violation:[/bold red] --spec-id is mandatory for implementation commits.")
         console.print("[dim]Tip: Use --spec-id SPEC-XXX or add 'docs:', 'chore:', 'ci:' prefix to message for non-functional changes.[/dim]")
         sys.exit(1)

    # 3. Pre-flight Validation
    if not _validate_commit_context(task_id, sprint_id, spec_id):
        sys.exit(1)

    # 4. Stage Files
    _stage_files_helper(files)

    # 6. Build Trailers
    trailers, active_sprint_id = _build_commit_trailers(
        message, None, sprint_id, component, task_id, status, validation, spec_id
    )

    # 6.5 Pre-Commit State Updates (Record event and stage sprint.yaml BEFORE commit)
    if active_sprint_id and task_id:
        try:
            state_manager = SprintStateManager(SPRINT_DIR / active_sprint_id)
            changed = state_manager.record_task_event(task_id, "first_commit")
            if changed:
                # Stage it so it's included in the upcoming commit
                subprocess.run(["git", "add", str(state_manager.state_file)], cwd=PROJECT_ROOT, check=False)
        except Exception: pass

    # 7. Safety Checks (Submodules & Guardian)
    from ...submodule import get_unpushed_submodules
    if get_unpushed_submodules(PROJECT_ROOT):
        console.print("[bold red]Error:[/bold red] Unpushed submodule commits detected.")
        sys.exit(1)

    _run_guardian_check(None, trailers)

    # 8. Create Commit (Single Call)
    if create_commit_with_trailers(message, trailers):
        console.print("[bold green]Success:[/bold green] Commit created.")

        # Sync Hook
        try:
            asyncio.run(sync_project_context())
        except Exception: pass
    else:
        sys.exit(1)
