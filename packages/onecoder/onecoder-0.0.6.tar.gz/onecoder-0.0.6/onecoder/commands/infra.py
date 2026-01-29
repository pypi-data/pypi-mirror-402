import click
import subprocess
import sys
import os
from pathlib import Path
from .auth import require_feature

# Constants
ALCHEMY_BIN = Path("alchemy/alchemy/bin/alchemy.ts").resolve()

def _run_alchemy(args, env=None):
    """Execute the Alchemy CLI via Bun."""
    cmd = ["bun", str(ALCHEMY_BIN)] + args
    
    # Ensure local node_modules etc are mapped if needed, mostly inheriting env
    current_env = os.environ.copy()
    if env:
        current_env.update(env)

    try:
        # We assume 'bun' is in usage path. 
        # In a real setup we might want to resolve 'bun' absolute path or check existence.
        subprocess.run(cmd, check=True, env=current_env)
    except FileNotFoundError:
        click.echo("❌ Error: 'bun' runtime not found. Please install Bun to use OneCoder Infra.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)

@click.group()
@require_feature("infra_tools")
def infra():
    """Manage Infrastructure-as-Code via Typed-Alchemy."""
    pass

@infra.command()
@click.argument("entrypoint", default="alchemy.run.ts")
@click.option("--stage", default="dev", help="Deployment stage (dev, prod)")
def validate(entrypoint, stage):
    """Validate Alchemy configuration (syntax check)."""
    if not Path(entrypoint).exists():
        click.echo(f"❌ Entrypoint '{entrypoint}' not found.")
        sys.exit(1)
        
    # Currently Alchemy doesn't have a pure 'validate', so we dry-run deploy
    click.echo(f"🔍 Validating {entrypoint} for stage {stage}...")
    _run_alchemy(["deploy", entrypoint, "--stage", stage, "--noop", "--quiet"])

@infra.command()
@click.option("--stage", default="dev", help="Deployment stage (dev, prod)")
def sync(stage):
    """Sync infrastructure configuration and secrets."""
    click.echo(f"🔄 Syncing infrastructure for {stage}...")
    
    # 1. Push Secrets (Delegates to onecoder env push)
    click.echo(f"  > Pushing secrets via 'onecoder env push'...")
    try:
        subprocess.run(["onecoder", "env", "push", "--stage", stage], check=True)
    except Exception as e:
        click.secho(f"  ⚠️  Secret sync failed: {e}", fg="yellow")

    click.secho("✓ Infrastructure sync complete.", fg="green")
    click.secho("✓ Infrastructure sync complete.", fg="green")

@infra.command()
@click.argument("entrypoint", default="alchemy.run.ts")
@click.option("--stage", default="dev", help="Deployment stage (dev, prod)")
@click.option("--out-file", help="Output file for the plan (optional)")
def plan(entrypoint, stage, out_file):
    """Generate an infrastructure execution plan."""
    if not Path(entrypoint).exists():
        click.echo(f"❌ Entrypoint '{entrypoint}' not found.")
        sys.exit(1)

    click.echo(f"📝 Generating plan for {stage}...")
    # TODO: Capture output if out_file is specified
    _run_alchemy(["deploy", entrypoint, "--stage", stage, "--noop"])

@infra.command()
@click.argument("entrypoint", default="alchemy.run.ts")
@click.option("--stage", default="dev", help="Deployment stage (dev, prod)")
@click.option("--force", is_flag=True, help="Skip confirmation")
def apply(entrypoint, stage, force):
    """Apply infrastructure changes."""
    if not Path(entrypoint).exists():
        click.echo(f"❌ Entrypoint '{entrypoint}' not found.")
        sys.exit(1)

    if not force:
        click.confirm(f"⚠️  Are you sure you want to deploy to {stage}?", abort=True)

    click.echo(f"🚀 Deploying to {stage}...")
    _run_alchemy(["deploy", entrypoint, "--stage", stage])
