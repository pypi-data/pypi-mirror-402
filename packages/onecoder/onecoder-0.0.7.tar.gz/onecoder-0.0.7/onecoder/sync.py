import os
import json
import click
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from .api_client import get_api_client
from .config_manager import config_manager
from .sprint_collector import SprintCollector
from .issues import IssueManager
from .knowledge import ProjectKnowledge

def handle_sync_error(context: str, error: Exception, critical: bool = False):
    """Unifies 'Metrics sync skipped' messaging for non-critical failures."""
    import httpx
    
    msg = f"{error}"
    # Check for common connection/auth errors to provide cleaner messaging
    if isinstance(error, (httpx.ConnectError, httpx.TimeoutException)):
        msg = "Network/API unreachable"
    elif isinstance(error, httpx.HTTPStatusError) and error.response.status_code == 401:
        msg = "Authentication failed (401)"
    elif isinstance(error, httpx.HTTPStatusError) and error.response.status_code == 404:
        msg = "Endpoint not found (404)"

    if critical:
        click.secho(f"❌ Critical failure in {context}: {msg}", fg="red", bold=True)
    else:
        click.secho(f"⚠️  {context} sync skipped ({msg})", fg="yellow")

class ProjectConfig:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.config_file = repo_root / ".onecoder.json"

    def load(self) -> Dict[str, Any]:
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            click.echo(f"Error loading project config: {e}")
            return {}

    def save(self, config: Dict[str, Any]):
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            click.echo(f"Error saving project config: {e}")

    def get_project_id(self) -> Optional[str]:
        # Priority: Env Var > Local Config
        project_id = os.getenv("ONECODER_PROJECT_ID")
        if project_id:
            return project_id
        return self.load().get("project_id")

def find_repo_root() -> Path:
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()

async def sync_sprint(client, project_id: str, sprint: Dict[str, Any], force: bool = False):
    """Syncs a single sprint to the API."""
    try:
        # Check if hash has changed
        import hashlib
        sprint_content = json.dumps(sprint, sort_keys=True).encode()
        current_hash = hashlib.md5(sprint_content).hexdigest()
        
        # Local state file for sync progress
        repo_root = find_repo_root()
        sync_state_file = repo_root / ".onecoder.sync.json"
        sync_state = {}
        if sync_state_file.exists():
            with open(sync_state_file, "r") as f:
                sync_state = json.load(f)
        
        last_hash = sync_state.get("sprints", {}).get(sprint["id"])
        
        if last_hash == current_hash and not force:
            # click.secho(f"  - {sprint['id']}: skipped (no changes)", fg="white", dim=True)
            return {"status": "skipped"}

        payload = {
            "sprint": {
                "id": sprint["id"],
                "title": sprint["title"],
                "status": sprint["status"],
                "goals": sprint["goals"]
            },
            "tasks": sprint["tasks"],
            "projectId": project_id
        }
        
        result = await client.sync_sprint(payload)
        
        # Update sync state
        sync_state.setdefault("sprints", {})[sprint["id"]] = current_hash
        with open(sync_state_file, "w") as f:
            json.dump(sync_state, f, indent=4)
            
        click.secho(f"  ✓ {sprint['id']}: {len(sprint['tasks'])} tasks", fg="green")
        return {"status": "success", "id": sprint["id"]}
    except Exception as e:
        click.secho(f"  ✗ {sprint['id']}: {e}", fg="red")
        return {"status": "error", "id": sprint["id"], "error": str(e)}

async def sync_project_context():
    """Aggregates local context and syncs with the API."""
    repo_root = find_repo_root()
    proj_config = ProjectConfig(repo_root)
    project_id = proj_config.get_project_id()

    if not project_id:
        click.secho("Error: No project ID found. Run 'onecoder login' or set ONECODER_PROJECT_ID.", fg="red")
        return

    token = config_manager.get_token()
    if not token:
        click.secho("Error: Not logged in. Run 'onecoder login'.", fg="red")
        return

    # Aggregate context
    spec_path = repo_root / "SPECIFICATION.md"
    gov_path = repo_root / "governance.yaml"
    learnings_path = repo_root / "ANTIGRAVITY.md"

    sync_data = {
        "metadata": {}
    }

    if spec_path.exists():
        sync_data["specification"] = spec_path.read_text()
    
    if gov_path.exists():
        sync_data["governance"] = gov_path.read_text()

    if learnings_path.exists():
        sync_data["metadata"]["learnings"] = learnings_path.read_text()

    # Get project name from folder if not in config
    if not sync_data.get("name"):
        sync_data["name"] = repo_root.name

    client = get_api_client(token)
    
    # 1. Sync Project Metadata
    try:
        result = await client.sync_project(project_id, sync_data)
        click.secho(f"✅ Project context synced successfully for ID: {project_id}", fg="green")
    except Exception as e:
        handle_sync_error("Project Metadata", e)
        # If we can't even sync project metadata, skip the rest to avoid noise
        return None

    # 2. Sync Sprints
    sprint_errors = 0
    try:
        collector = SprintCollector(repo_root)
        sprints = collector.collect_all_sprints()
        if sprints:
            click.secho(f"\n📦 Syncing {len(sprints)} sprints...", fg="cyan")
            for sprint in sprints:
                res = await sync_sprint(client, project_id, sprint)
                if res and res.get("status") == "error":
                    sprint_errors += 1
            
            if sprint_errors == 0:
                click.secho(f"✅ All sprints synced successfully", fg="green")
            else:
                click.secho(f"⚠️  {sprint_errors} sprints failed to sync", fg="yellow")
        else:
            click.secho("\nℹ️  No sprints found to sync", fg="yellow")
    except Exception as e:
        handle_sync_error("Sprints", e)
        sprint_errors += 1

    # 3. Sync Knowledge Base
    kb_stats = await sync_knowledge(client, project_id)
    kb_errors = kb_stats.get('errors', 0) if kb_stats else 0
    
    # 4. Sync Issues
    issue_stats = await sync_issues(client, project_id)
    issue_errors = issue_stats.get('errors', 0) if issue_stats else 0

    # 5. Sync Specs
    spec_stats = await sync_specs(client, project_id, repo_root)
    spec_errors = spec_stats.get('errors', 0) if spec_stats else 0
    
    total_errors = sprint_errors + kb_errors + issue_errors + spec_errors
    
    if total_errors == 0:
        click.secho("\n✨ Project sync complete: All data in sync.", fg="green", bold=True)
    else:
        click.secho(f"\n⚠️  Project sync complete with {total_errors} errors. Check industrial logs for details.", fg="yellow", bold=True)
    
    return result if 'result' in locals() else None

async def sync_issues(client, project_id: str):
    """Syncs local issues to the API."""
    manager = IssueManager()
    issues = manager.get_all_issues()
    
    if not issues:
        click.secho("ℹ️  No issues found to sync", fg="yellow")
        return

    click.secho(f"📦 Syncing {len(issues)} issues...", fg="cyan")
    
    try:
        payload = {
            "projectId": project_id,
            "issues": issues
        }
        
        result = await client.sync_issues(payload)
        
        stats = result.get("stats", {})
        click.secho(f"✅ Issues synced: {stats.get('upserted', 0)} upserted, {stats.get('errors', 0)} errors", fg="green")
        return stats
    except Exception as e:
        handle_sync_error("Issues", e)
        return {"errors": 1}

async def sync_knowledge(client, project_id: str):
    """Aggregates local KB entries and syncs to API."""
    pk = ProjectKnowledge()
    entries = pk.get_knowledge_base_entries()
    
    if not entries:
        click.secho("ℹ️  No Knowledge Base entries found to sync", fg="yellow")
        return

    click.secho(f"📦 Syncing {len(entries)} Knowledge Base entries...", fg="cyan")
    
    try:
        result = await client.enrich_knowledge(project_id, entries)
        stats = result.get("stats", {})
        click.secho(f"✅ KB enriched: {stats.get('upserted', 0)} upserted, {stats.get('errors', 0)} errors", fg="green")
        return stats
    except Exception as e:
        handle_sync_error("Knowledge Base", e)
        return {"errors": 1}

async def sync_specs(client, project_id: str, repo_root: Path):
    """Parses SPECIFICATION.md and syncs individual specs to API."""
    spec_path = repo_root / "SPECIFICATION.md"
    if not spec_path.exists():
        return

    content = spec_path.read_text()
    click.secho("\n📋 Syncing Specifications...", fg="cyan")
    
    # Simple regex to find blocks starting with **[SPEC-XXX-YYY]**
    # This assumes the convention used in SPECIFICATION.md
    import re
    import re
    # Allow optional list marker
    pattern = r"(?:-\s*)?\*\*\[(SPEC-[A-Z]+-\d+(?:\.\d+)*)\]\*\*\s*(.*?)(?=(?:-\s*)?\*\*\[SPEC-|\Z)"
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    click.secho(f"  Found {len(matches)} specs in SPECIFICATION.md", dim=True)
    
    count = 0
    errors = 0
    for match in matches:
        spec_id = match.group(1)
        full_text = match.group(2).strip()
        lines = full_text.split("\n")
        title = lines[0].strip() if lines else "Untitled"
        # Truncate title to fit DB schema (typically 255)
        if len(title) > 255:
            title = title[:252] + "..."
        
        body = "\n".join(lines[1:]).strip()
        
        payload = {
            "id": spec_id,
            "projectId": project_id,
            "title": title,
            "content": body,
            "status": "active", 
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            await client.sync_spec(payload)
            count += 1
        except Exception as e:
            # Only show first error for specs to avoid flooding
            if errors == 0:
                 handle_sync_error(f"Spec ({spec_id})", e)
            errors += 1

    if count > 0 or errors > 0:
        color = "green" if errors == 0 else "yellow"
        click.secho(f"✅ Synced {count} specs ({errors} failed)", fg=color)
    
    return {"upserted": count, "errors": errors}
