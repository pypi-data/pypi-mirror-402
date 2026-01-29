import click
import os
import subprocess
import sys
from typing import List, Optional
from pathlib import Path
from ..env_manager import env_manager
from .auth import require_feature

@click.group()
# @require_feature("security_tools")
def env():
    """Manage secure environment variables."""
    pass

@env.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--local", is_flag=True, help="Set variable for current directory only.")
def set_cmd(key, value, local):
    """Store an environment variable."""
    project_path = os.getcwd() if local else None
    env_manager.set_env(key, value, project_path)
    scope = "locally" if local else "globally"
    click.secho(f"✓ Environment variable '{key}' set {scope}.", fg="green")

@env.command(name="get")
@click.argument("key")
@click.option("--force", is_flag=True, help="Retrieve the value (masked).")
def get_cmd(key, force):
    """Retrieve an environment variable (masked)."""
    # Note: --force is kept for backward compatibility but behavior is changed to strict masking
    
    # Try local first, then global
    val = env_manager.get_env(key, os.getcwd())
    if val is None:
        val = env_manager.get_env(key)
        
    if val:
        # Strict Masking
        if len(val) > 6:
            masked_val = f"{val[:3]}***{val[-3:]}"
        else:
            masked_val = "***"
        click.echo(masked_val)
    else:
        click.secho(f"Environment variable '{key}' not found.", fg="red")

@env.command(name="list")
def list_cmd():
    """List stored environment variable keys."""
    global_keys = env_manager.list_keys()
    local_keys = env_manager.list_keys(os.getcwd())
    
    if not global_keys and not local_keys:
        click.echo("No stored environment variables.")
        return

    if global_keys:
        click.secho("Global variables:", bold=True)
        for k in sorted(global_keys):
            click.echo(f"  {k}")
            
    if local_keys:
        click.secho(f"\nLocal variables ({os.getcwd()}):", bold=True)
        for k in sorted(local_keys):
            click.echo(f"  {k}")

@env.command(name="delete")
@click.argument("key")
@click.option("--local", is_flag=True, help="Delete from current directory only.")
def delete_cmd(key, local):
    """Delete a stored environment variable."""
    project_path = os.getcwd() if local else None
    env_manager.delete_env(key, project_path)
    click.secho(f"✓ Environment variable '{key}' deleted.", fg="green")

@env.command(name="run", context_settings=dict(ignore_unknown_options=True))
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
def run_cmd(command):
    """Run a command with secure environment variables injected."""
    if not command:
        click.echo("No command provided.")
        return

    # Prepare environment
    env_to_inject = env_manager.get_context_env(os.getcwd())
    current_env = os.environ.copy()
    current_env.update(env_to_inject)

    # Run command and intercept output for redaction
    full_command = " ".join(command)
    try:
        process = subprocess.Popen(
            full_command,
            env=current_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            shell=True
        )

        for line in process.stdout:
            click.echo(env_manager.redact(line), nl=False)
            
        for line in process.stderr:
            click.echo(env_manager.redact(line), nl=False, err=True)

        process.wait()
        sys.exit(process.returncode)
    except Exception as e:
        click.secho(f"Error running command: {e}", fg="red")
        sys.exit(1)

@env.command(name="scan")
def scan_cmd():
    """Scan local directory for environment files and import keys."""
    start_dir = os.getcwd()
    env_files = []
    
    # 1. Find files (max depth 3, exclude node_modules)
    for root, dirs, files in os.walk(start_dir):
        # Depth check
        rel_path = os.path.relpath(root, start_dir)
        depth = 0 if rel_path == '.' else rel_path.count(os.sep) + 1
        if depth > 3:
            del dirs[:] 
            continue
            
        if "node_modules" in dirs:
            dirs.remove("node_modules")

        for f in files:
            if f in [".env", ".env.local", ".dev.vars"]:
                env_files.append(os.path.join(root, f))

    if not env_files:
        click.echo("No environment files found.")
        return

    click.secho(f"Found {len(env_files)} environment files.", fg="blue")
    
    # 2. Process files
    for file_path in env_files:
        click.secho(f"\nProcessing {os.path.relpath(file_path, start_dir)}...", bold=True)
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            click.secho(f"  Error reading file: {e}", fg="red")
            continue

        for line in lines:
            line = line.strip()
            # Basic parsing: ignore comments, empty lines
            if not line or line.startswith('#'):
                continue
            
            # Simple KEY=VALUE parsing logic
            if '=' not in line:
                continue
                
            key, val = line.split('=', 1)
            key = key.replace('export ', '').strip()
            val = val.strip()
            
            # Remove quotes if present
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            
            if not key:
                continue

            # Check if key exists
            existing_val = env_manager.get_env(key, start_dir) or env_manager.get_env(key)
            if existing_val == val:
                click.echo(f"  {key}: [Already imported] - skipping")
                continue

            # Masking
            masked_val = val
            if len(val) > 6:
                masked_val = f"{val[:3]}***{val[-3:]}"
            else:
                masked_val = "***"

            # Interactive Prompt
            if click.confirm(f"  Found {key} ({masked_val}). Import?"):
                scope = click.prompt(
                    "    Scope?", 
                    type=click.Choice(['Global', 'Local'], case_sensitive=False), 
                    default="Local",
                    show_default=True
                )
                
                project_path = start_dir if scope.lower() == 'local' else None
                env_manager.set_env(key, val, project_path)
                click.secho(f"    ✓ Imported {key} ({scope})", fg="green")
            else:
                click.echo(f"    Skipped {key}")

@env.command(name="lock-env")
@click.option("--directory", default=".", help="Directory to scan for env files")
def lock_env(directory):
    """Lock .env files to prevent modification by agents (read-only)."""
    path = Path(directory).resolve()
    env_files = list(path.rglob(".env*")) + list(path.rglob(".dev.vars"))
    
    locked_count = 0
    for f in env_files:
        if "node_modules" in f.parts or ".git" in f.parts:
            continue
        try:
            # Set to read-only (444)
            os.chmod(f, 0o444)
            click.echo(f"Locked: {f.relative_to(path)}")
            locked_count += 1
        except Exception as e:
            click.secho(f"Failed to lock {f.name}: {e}", fg="red")
            
    click.secho(f"\n✓ Locked {locked_count} environment files.", fg="green")

@env.command(name="push")
@click.option("--stage", default="dev", help="Deployment stage (dev, prod)")
def push_cmd(stage):
    """Push local secrets to Cloudflare Wrangler."""
    click.echo(f"🔄 Pushing secrets to Cloudflare ({stage})...")
    
    # Get all global and local keys
    global_keys = env_manager.list_keys()
    local_keys = env_manager.list_keys(os.getcwd())
    all_keys = set(global_keys + local_keys)
    
    if not all_keys:
        click.echo("No secrets found to push.")
        return

    # Assuming we push to the current directory's project context
    # In reality, might need to specify project name or iterate subprojects (BATCH mode)
    # For now, simplistic implementation: push all known secrets to current wrangler project
    
    # Check for wrangler.toml
    if not Path("wrangler.toml").exists() and not Path("wrangler.json").exists():
        click.secho("⚠️  No wrangler configuration found in current directory.", fg="yellow")
        if not click.confirm("Continue anyway (might fail)?"):
            return

    count = 0
    for key in all_keys:
        val = env_manager.get_env(key, os.getcwd()) or env_manager.get_env(key)
        if not val: 
            continue
            
        # Use bun x wrangler secret put
        try:
            # We use echo to pipe input to secret put to avoid interactive prompt
            # cmd: echo "VALUE" | bun x wrangler secret put KEY
            ps = subprocess.Popen(
                ["bun", "x", "wrangler", "secret", "put", key],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = ps.communicate(input=val)
            
            if ps.returncode == 0:
                click.echo(f"  ✓ Pushed {key}")
                count += 1
            else:
                click.secho(f"  ❌ Failed to push {key}: {stderr.strip()}", fg="red")
        except Exception as e:
            click.secho(f"  ❌ Error pushing {key}: {e}", fg="red")

    click.secho(f"\n✓ Successfully pushed {count} secrets.", fg="green")


@env.command(name="freeze")
@click.option("--out", default=".env.production", help="Output file name")
def freeze_cmd(out):
    """Generate a frozen environment file for production builds."""
    click.echo(f"❄️  Freezing environment to {out}...")
    
    global_keys = env_manager.list_keys()
    local_keys = env_manager.list_keys(os.getcwd())
    all_keys = sorted(list(set(global_keys + local_keys)))
    
    with open(out, 'w') as f:
        f.write("# Generated by onecoder env freeze\n")
        f.write(f"# Timestamp: {os.times}\n\n")
        
        for key in all_keys:
            val = env_manager.get_env(key, os.getcwd()) or env_manager.get_env(key)
            if not val: 
                continue
            
            # Escape value for safety (Fixes TT-092)
            # If value contains double quotes, escape them
            safe_val = val.replace('"', '\\"')
            f.write(f'{key}="{safe_val}"\n')
            
    click.secho(f"✓ Generated {out} with {len(all_keys)} variables.", fg="green")
    
    # Lock the file to prevent accidental edits
    try:
        os.chmod(out, 0o444)
        click.echo(f"  Locked {out} (read-only).")
    except Exception:
        pass

@env.command(name="unlock-env")
@click.option("--directory", default=".", help="Directory to scan for env files")
def unlock_env(directory):
    """Unlock .env files for modification (read-write)."""
    path = Path(directory).resolve()
    env_files = list(path.rglob(".env*")) + list(path.rglob(".dev.vars"))
    
    unlocked_count = 0
    for f in env_files:
        if "node_modules" in f.parts or ".git" in f.parts:
            continue
        try:
            # Set to read-write (644)
            os.chmod(f, 0o644)
            click.echo(f"Unlocked: {f.relative_to(path)}")
            unlocked_count += 1
        except Exception as e:
            click.secho(f"Failed to unlock {f.name}: {e}", fg="red")
            
    click.secho(f"\n✓ Unlocked {unlocked_count} environment files.", fg="green")
