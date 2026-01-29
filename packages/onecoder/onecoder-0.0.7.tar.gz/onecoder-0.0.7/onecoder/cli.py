import click
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path.cwd() / ".env"
load_dotenv(env_path)

from .commands.auth import login, logout, whoami
from .config_manager import config_manager
from .commands.server import serve, web, tui
from .commands.issue import issue
from .commands.logs import logs
from .commands.project import (
    init, status, knowledge, distill, sync, alignment, suggest, project_push
)
from .commands.guide import guide
from .commands.feedback import feedback
from .commands.reflect import reflect
from .commands.doctor import doctor, trace
from .commands.delegate import delegate
from .commands.doctor import doctor
from .commands.ci import ci
from .commands.env import env
from .commands.audit import audit
from .commands.content import content
from .commands.task import task
from .commands.release import release
from .commands.tldr import tldr
from .commands.debug import debug
from .commands.skills import skills
from .commands.agent import agent
from .commands.infra import infra
from .review import CodeReviewer

try:
    from .commands.dev import dev
except ImportError:
    dev = None

from .logger import configure_logging
from .usage_logger import usage_logger
from .tracing import setup_tracing
import subprocess

def get_dynamic_version():
    """Determine version dynamically based on git status."""
    base_version = "0.0.7" # Incremented for hardening release
    try:
        # Traverse up to find .git
        path = Path(__file__).resolve()
        folders = [path] + list(path.parents)
        root = None
        for p in folders:
            if (p / ".git").exists():
                root = p
                break
        
        if root:
            # Check for uncommitted changes
            res = subprocess.run(["git", "diff", "--shortstat"], capture_output=True, text=True, cwd=root)
            is_dirty = bool(res.stdout.strip())
            
            # Get short hash
            hash_res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=root)
            short_hash = hash_res.stdout.strip()
            
            if is_dirty:
                return f"{base_version}-dirty"
            elif short_hash:
                return f"{base_version}+{short_hash}"
    except Exception:
        pass
    return base_version


@click.group()
@click.version_option(version=get_dynamic_version(), prog_name="onecoder")
@click.option("--verbose", is_flag=True, help="Enable verbose logging.")
def cli(verbose):
    """OneCoder: Unified Agent Architecture.
    
    [NEW] Run 'onecoder guide' for a quick onboarding walkthrough!
    
    [TIP] Avoid commit friction: onecoder sprint commit -m "..." file1 file2 --spec-id <SPEC>
    """
    configure_logging(verbose=verbose)
    setup_tracing()

def main():
    """Main entry point with telemetry wrapper."""
    try:
        cli()
        # Log successful execution
        if len(sys.argv) > 1:
            usage_logger.log_command(sys.argv[0], sys.argv[1:], exit_code=0)
    except Exception as e:
        # Don't capture Click-internal exit exceptions as failures
        if isinstance(e, (click.exceptions.Exit, click.exceptions.Abort, click.exceptions.ClickException)):
            # Log expected exits/aborts
            usage_logger.log_command(sys.argv[0], sys.argv[1:], exit_code=getattr(e, 'exit_code', 0))
            raise e
            
        try:    
            from ai_sprint.telemetry import FailureModeCapture
            capture = FailureModeCapture()
            capture.capture(e, context={"command_args": sys.argv[1:]})
        except ImportError:
            # Telemetry not available, just re-raise
            pass
        raise e

# Register Commands
def is_internal_features_enabled():
    """Check if internal features should be enabled."""
    return os.getenv("ONECODER_INTERNAL", "false").lower() == "true" or \
           os.getenv("ONE_CODER_DEV", "false").lower() == "true"

# Register Commands
cli.add_command(login)
cli.add_command(logout)
cli.add_command(whoami)

cli.add_command(serve)
cli.add_command(web)

if is_internal_features_enabled():
    cli.add_command(tui)

cli.add_command(issue)
cli.add_command(logs)
cli.add_command(doctor)

cli.add_command(init)
cli.add_command(status)
cli.add_command(knowledge)
cli.add_command(distill)
cli.add_command(sync)
cli.add_command(alignment)
cli.add_command(suggest)
cli.add_command(ci)
cli.add_command(feedback)
cli.add_command(reflect)
cli.add_command(doctor)
cli.add_command(trace)
cli.add_command(env)
cli.add_command(audit)
cli.add_command(content)
cli.add_command(task)
cli.add_command(release)
cli.add_command(tldr)
cli.add_command(debug)
cli.add_command(skills)
cli.add_command(agent)
cli.add_command(infra)
cli.add_command(guide)

@click.group(name="project")
def project_group():
    """Project management commands."""
    pass

project_group.add_command(init)
project_group.add_command(status)
project_group.add_command(project_push)
project_group.add_command(sync)
project_group.add_command(alignment)
project_group.add_command(distill)
project_group.add_command(knowledge)

cli.add_command(project_group)

from .commands.analytics import analytics
cli.add_command(analytics)

from .commands.code import code
cli.add_command(code)

from .commands.mcp import mcp
cli.add_command(mcp)

# Register Dev Commands (Gated for safety)
if dev and is_internal_features_enabled():
    cli.add_command(dev)

if is_internal_features_enabled():
    cli.add_command(delegate)

def load_dynamic_extensions():
    """Discover and load private monorepo extensions."""
    try:
        # Resolve platform root
        curr = Path(__file__).resolve()
        platform_root = None
        for parent in [curr] + list(curr.parents):
            if (parent / "packages").exists() and (parent / "packages" / "content").exists():
                platform_root = parent
                break
        
        if platform_root:
            content_ext = platform_root / "packages" / "content"
            if content_ext.exists():
                import sys
                if str(content_ext) not in sys.path:
                    sys.path.append(str(content_ext))
                
                try:
                    from extension.plugin import content_plus
                    cli.add_command(content_plus)
                except ImportError:
                    pass
    except Exception:
        pass

load_dynamic_extensions()

@cli.command()
@click.argument("pr_id", required=False)
@click.option("--local", is_flag=True, help="Review local changes against main")
def review(pr_id, local):
    """Run a policy-grounded AI review on a PR or local code."""
    reviewer = CodeReviewer()
    reviewer.review(pr_id=pr_id, local=local)

# Sprint Group Integration
# Sprint Group Integration
try:
    from ai_sprint.cli import main as sprint_main
    # Attempt to add the command to the existing group
    if suggest not in sprint_main.commands.values():
         sprint_main.add_command(suggest)
    cli.add_command(sprint_main, name="sprint")
except ImportError:
    @cli.group(name="sprint")
    def sprint_group():
        """Sprint management commands."""
        pass
    sprint_group.add_command(suggest)
    cli.add_command(sprint_group)

# --- Tiered Access Gating ---
def apply_tiered_gating():
    """Hides Pro commands for Free users to provide a focused Sprint experience."""
    if is_internal_features_enabled():
        return  # Developers see everything

    # Define commands that are ALWAYS visible even on Free Tier
    CORE_COMMANDS = {
        "login", "logout", "whoami", "guide", 
        "sprint", "init", "status", "sync", 
        "feedback", "issue", "logs", "web", "serve",
        "doctor", "trace" # Included for support/troubleshooting
    }

    token = config_manager.get_token()
    entitlements = config_manager.get_entitlements() if token else []
    
    # If no token (not logged in) or no pro entitlements, hide the rest
    has_pro = any("_tools" in str(e) for e in entitlements) or "enterprise" in entitlements
    
    if not has_pro:
        for name, command in cli.commands.items():
            if name not in CORE_COMMANDS:
                command.hidden = True

apply_tiered_gating()

if __name__ == "__main__":
    cli()
