import click
import sys
import os
import json
from pathlib import Path

try:
    from onecoder_rlm.rlm_runtime import OneCoderRLM
    from onecoder_rlm.config import RLMConfig
except ImportError:
    # Graceful fallback if the package isn't installed in the environment
    OneCoderRLM = None
    RLMConfig = None

@click.group()
def task():
    """Commands for managing and refining development tasks."""
    pass

@task.command()
@click.argument("query", required=True)
@click.option("--context", "-c", help="Additional context for the task.")
@click.option("--max-iters", "-i", default=5, help="Maximum number of RLM iterations.")
def refine(query, context, max_iters):
    """
    Triggers the RLM decision engine to refine and solve a task.
    
    The agent will Plan -> Execute -> Analysis -> Patch until completion.
    """
    if OneCoderRLM is None or RLMConfig is None:
        click.secho("Error: 'onecoder-rlm' package is not installed.", fg="red", bold=True)
        click.echo("This is an internal feature. To enable it, please install the internal version:")
        click.secho("  pip install onecoder[internal]", fg="cyan")
        return

    click.secho(f"🚀 Starting RLM refinement for: '{query}'", fg="cyan", bold=True)
    
    config = RLMConfig()
    config.max_rlm_iterations = max_iters
    
    rlm = OneCoderRLM(config=config)
    
    # Run the loop
    initial_context = context if context else f"Executing in project root: {os.getcwd()}"
    
    try:
        # We wrap in MLflow if available
        import mlflow
        with mlflow.start_run(run_name=f"CLI Refine: {query[:30]}"):
            mlflow.log_param("query", query)
            mlflow.log_param("max_iters", max_iters)
            
            result = rlm.run_rlm_loop(task=query, initial_context=initial_context)
            
            # Log trajectory as artifact
            trajectory = result.get("trajectory", [])
            with open("refine_trajectory.json", "w") as f:
                json.dump(trajectory, f, indent=2)
            mlflow.log_artifact("refine_trajectory.json")
            os.remove("refine_trajectory.json")

            if result["status"] == "completed":
                click.secho("\n✅ Task completed successfully!", fg="green", bold=True)
                mlflow.log_metric("success", 1)
            else:
                click.secho(f"\n❌ Task failed: {result.get('reason')}", fg="red", bold=True)
                mlflow.log_metric("success", 0)
            
            # Display Token Usage
            usage = result.get("usage", {})
            input_tokens = usage.get("input", 0)
            output_tokens = usage.get("output", 0)
            click.secho(f"\n📊 Token Usage: Input={input_tokens} | Output={output_tokens}", fg="blue")
            mlflow.log_metric("input_tokens", input_tokens)
            mlflow.log_metric("output_tokens", output_tokens)
                
    except Exception as e:
        click.secho(f"Error during RLM execution: {e}", fg="red")
        sys.exit(1)
@task.command(name="fix-loc")
@click.argument("path", default=".", type=click.Path(exists=True))
def fix_loc(path):
    """Identify and suggest fixes for functions exceeding LOC limits."""
    from .code import TLDRTool
    tool = TLDRTool()
    
    click.echo(f"🔍 Scanning {path} for LOC governance violations...")
    
    # 1. Scan for complexity/symbols
    if os.path.isfile(path):
        results = [tool.scan_file(path)]
    else:
        results = tool.scan_directory(path)
        
    violations = []
    for res in results:
        if "error" in res: continue
        for sym in res.get("symbols", []):
            loc = sym.get("loc", 0)
            if loc > 10: # Governance limit
                violations.append({
                    "file": res["file"],
                    "name": sym["name"],
                    "loc": loc,
                    "line": sym["line"]
                })
                
    if not violations:
        click.secho("✅ No LOC violations found. All functions are within governance limits.", fg="green")
        return
        
    click.secho(f"Found {len(violations)} violations:", fg="yellow", bold=True)
    for v in violations:
        click.echo(f"  • {v['file']}:{v['line']} - {v['name']} ({v['loc']} LOC)")
        
    click.echo("\n[Action Plan]")
    click.echo("To automatically refactor these functions, run:")
    for v in violations[:3]: # Suggest first few
        click.secho(f"  onecoder task refine \"Refactor {v['name']} in {v['file']} to reduce LOC below 10\"", fg="cyan")
    
    if len(violations) > 3:
        click.echo(f"  ... and {len(violations)-3} more.")
