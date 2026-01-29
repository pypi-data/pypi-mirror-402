import click
import os
import json
from pathlib import Path
from ..tools.tldr_tool import TLDRTool
from ..tools.indexer import Indexer

@click.group(hidden=True)
def tldr():
    """TLDR: Token-Efficient Lightweight Deep Retrieval."""
    pass

@tldr.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output format (json/text)", default="text")
def symbols(path, output):
    """List symbols (functions, classes) in a file or directory."""
    tool = TLDRTool()

    if os.path.isfile(path):
        results = [tool.scan_file(path)]
    else:
        results = tool.scan_directory(path)

    if output == "json":
        click.echo(json.dumps(results, indent=2))
    else:
        for res in results:
            if "error" in res:
                click.echo(f"  [Error] {res['file']}: {res['error']}")
                continue

            if not res.get("symbols"):
                continue

            click.echo(f"\n📄 {res['file']} ({res['language']})")
            for sym in res["symbols"]:
                icon = "ƒ" if sym["kind"] == "function" else "C" if sym["kind"] == "class" else "●"
                click.echo(f"  {icon} {sym['name']} (line {sym['line']})")

@tldr.command()
@click.argument("query")
@click.argument("path", default=".", type=click.Path(exists=True))
def search(query, path):
    """Search for symbols matching a query."""
    tool = TLDRTool()
    results = tool.search(path, query)

    if not results:
        click.echo("No matches found.")
        return

    click.echo(f"Found {len(results)} matches for '{query}':")
    for sym in results:
        click.echo(f"{sym['file']}:{sym['line']} - {sym['kind']} {sym['name']}")

@tldr.command()
@click.argument("symbol")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--db-path", default=".onecode/tldr.db", help="Path to SQLite index")
def impact(symbol, path, db_path):
    """Find references (calls) to a symbol (L2 Impact Analysis)."""
    # Try using Indexer first
    if os.path.exists(db_path):
        indexer = Indexer(db_path=db_path)
        # Check if index needs update? For now, assume user runs index command.
        
        results = indexer.get_callers(symbol)
        if results:
             click.echo(f"Found {len(results)} calls to '{symbol}' (cached):")
             for call in results:
                 click.echo(f"  📞 {call['file']}:{call['line']}")
             return

    # Fallback to slow scan
    click.echo("Index miss or empty. Falling back to slow scan...")
    tool = TLDRTool()

    # If path is a file, use its parent dir
    search_path = path
    if os.path.isfile(path):
        search_path = os.path.dirname(path)

    results = tool.find_callers(search_path, symbol)

    if not results:
        click.echo(f"No calls found for '{symbol}' in {search_path}")
        return

    click.echo(f"Found {len(results)} calls to '{symbol}':")
    for call in results:
        click.echo(f"  📞 {call['file']}:{call['line']}")

@tldr.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def complexity(path):
    """Analyze cyclomatic complexity of functions (L3 Analysis)."""
    tool = TLDRTool()

    if os.path.isfile(path):
        results = [tool.scan_complexity(path)]
    else:
        results = tool.analyze_complexity(path)

    for res in results:
        if "error" in res:
            continue

        if not res.get("functions"):
            continue

        click.echo(f"\n📊 {res['file']}")

        # Sort by complexity descending
        funcs = sorted(res["functions"], key=lambda x: x["complexity"], reverse=True)

        for func in funcs:
            score = func["complexity"]
            color = "green"
            if score > 10: color = "yellow"
            if score > 20: color = "red"

            click.secho(f"  {func['name']}: {score}", fg=color)

@tldr.command()
@click.argument("function")
@click.argument("path", default=".", type=click.Path(exists=True))
def cfg(function, path):
    """Generate CFG for a function (L3 Analysis) in Mermaid format."""
    tool = TLDRTool()
    
    # If path is a directory, search recursively?
    # For now, simplistic: if file, scan it. If dir, scan all?
    # Arguments order: function, path
    
    target_file = path
    if os.path.isdir(path):
        # Scan directory for symbol first? 
        # Or just tell user to point to file
        click.echo("Please specify a file path for high precision.")
        return

    res = tool.scan_cfg(target_file, function)
    if "error" in res:
         click.echo(f"Error: {res['error']}")
    else:
         click.echo(f"Mermaid CFG for {function} in {target_file}:")
         click.echo("```mermaid")
         click.echo(res["mermaid"])
         click.echo("```")

@tldr.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--db-path", default=".onecode/tldr.db", help="Path to SQLite index")
def index(path, db_path):
    """Build or update the symbol index."""
    click.echo(f"Indexing {path}...")
    indexer = Indexer(db_path=db_path)
    indexer.index_directory(path)
    click.echo("Indexing complete.")

@tldr.command()
@click.argument("variable")
@click.argument("function")
@click.argument("path", default=".", type=click.Path(exists=True))
def flow(variable, function, path):
    """Analyze data flow for a variable (L4 Analysis)."""
    tool = TLDRTool()
    
    if os.path.isdir(path):
        click.echo("Please specify a file path.")
        return

    res = tool.scan_data_flow(path, function, variable)
    if "error" in res:
         click.echo(f"Error: {res['error']}")
    else:
         click.echo(f"Data Flow for '{variable}' in { function} ({path}):")
         for usage in res["usages"]:
             click.echo(f"  Line {usage['line']}: {usage['content']}")

@tldr.command()
@click.argument("variable")
@click.argument("function")
@click.argument("path", default=".", type=click.Path(exists=True))
def slice(variable, function, path):
    """Extract executable slice for a variable (L5 Analysis)."""
    tool = TLDRTool()
    
    if os.path.isdir(path):
        click.echo("Please specify a file path.")
        return

    res = tool.scan_slice(path, function, variable)
    if "error" in res:
         click.echo(f"Error: {res['error']}")
    else:
         click.echo(f"Slice for '{variable}' in {function} ({path}):")
         for line in res["slice"]:
             click.echo(f"  {line}")

if __name__ == "__main__":
    tldr()
