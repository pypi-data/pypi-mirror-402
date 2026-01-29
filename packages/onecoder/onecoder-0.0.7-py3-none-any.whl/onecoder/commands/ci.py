import click
import subprocess
import sys
from pathlib import Path
from .auth import require_feature

@click.group(invoke_without_command=True)
@click.pass_context
def ci(ctx):
    """Run local CI/CD workflows using OneCoder CI."""
    if ctx.invoked_subcommand is None:
        # Default behavior: run the bash script if no subcommand
        ctx.invoke(run)

@ci.command()
def init():
    """Scaffold CI configuration (GitHub Actions)."""
    workflow_path = Path(".github/workflows/onecoder-ci.yml")
    if workflow_path.exists():
        if not click.confirm(f"'{workflow_path}' already exists. Overwrite?", default=False):
            return

    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    
    template = """name: OneCoder CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  onecoder-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          
      - name: Install OneCoder
        run: |
          pip install onecoder
          
      - name: OneCoder Sprint Preflight
        run: onecoder sprint preflight --staged
        env:
          ONECODER_API_URL: ${{ secrets.ONECODER_API_URL }}
          ONECODER_API_TOKEN: ${{ secrets.ONECODER_API_TOKEN }}
"""
    with open(workflow_path, "w") as f:
        f.write(template)
    
    click.secho(f"✓ Created {workflow_path}", fg="green")
    click.echo("Next steps: Set GITHUB_CLIENT_ID and ONECODER_API_URL in your repo secrets.")

@ci.command()
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@require_feature("ci_tools")
def run(args):
    """Run the local CI script."""
    # Assumption: User runs this from the repo root where `scripts/onecoder-ci.sh` exists.
    # Future improvement: Auto-detect repo root.
    script_path = Path("scripts/onecoder-ci.sh")
    
    if not script_path.exists():
        click.echo("❌ Error: 'scripts/onecoder-ci.sh' not found.")
        click.echo("   Please run this command from the root of the 'platform' repository.")
        sys.exit(1)
        
    # Prepare command: bash scripts/onecoder-ci.sh [args]
    cmd = ["bash", str(script_path)] + list(args)
    
    try:
        # Use subprocess.call or run to stream output directly
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except Exception as e:
        click.echo(f"❌ Error executing OneCoder CI: {str(e)}")
        sys.exit(1)
