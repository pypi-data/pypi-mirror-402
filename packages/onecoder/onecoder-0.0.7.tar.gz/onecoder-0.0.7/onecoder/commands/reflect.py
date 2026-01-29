import click
import asyncio
from pathlib import Path
from ..api_client import get_api_client
from ..config_manager import config_manager
from ..usage_logger import usage_logger
from .feedback import _submit_feedback
from .auth import require_feature

import subprocess

def _get_git_context():
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        # Get a brief summary of changes
        diff_stats = subprocess.check_output(["git", "diff", "--stat"], stderr=subprocess.DEVNULL).decode().strip()
        return {
            "branch": branch,
            "commit": commit,
            "has_local_changes": bool(diff_stats),
            "diff_summary": diff_stats.split('\n')[-1] if diff_stats else "No changes"
        }
    except Exception:
        return {}

@click.command()
@click.option("--task-id", help="Associated Task ID.")
@click.option("--sprint-id", help="Associated Sprint ID.")
@click.option("--sentiment", type=click.Choice(["positive", "neutral", "negative"]), default="positive", help="Sentiment of the reflection.")
@click.argument("message", required=True)
@require_feature("content_tools")
def reflect(task_id, sprint_id, sentiment, message):
    """Capture a reflection or insight for content generation.
    
    This command helps bridge the gap between technical work and marketing content.
    Reflections are prioritized for blog posts, social media, and video scripts.
    """
    git_ctx = _get_git_context()
    
    asyncio.run(_submit_reflect(sentiment, sprint_id, task_id, message, git_ctx))

async def _submit_reflect(sentiment, sprint_id, task_id, message, git_ctx=None):
    token = config_manager.get_token()
    client = get_api_client(token)
    
    payload = {
        "sentiment": sentiment,
        "category": "content_insight",
        "message": message,
        "context": {
            "sprint_id": sprint_id,
            "task_id": task_id,
            "is_reflection": True,
            "git": git_ctx or {}
        }
    }
    
    try:
        await client.submit_feedback(payload)
        click.secho("✓ Reflection captured and sent to Content Engine.", fg="green")
    except Exception as e:
        click.secho(f"Error submitting reflection: {e}", fg="red")
