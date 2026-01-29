import click
import asyncio
from google.adk.runners import Runner
from ..agent import get_root_agent
from ..alignment import auto_detect_sprint_id
from ..sessions import DurableSessionService
from google.genai.types import Content, Part
import sys

@click.group()
def agent():
    """Agentic layer interaction and testing."""
    pass

@agent.command()
@click.argument("message")
@click.option("--sprint-id", help="Explicit sprint ID to use.")
@click.option("--session-id", default="cli-session", help="Session ID for tracking.")
@click.option("--user-id", default="cli-user", help="User ID for tracking.")
@click.option("--impl", default="adk", type=click.Choice(["adk", "rlm"]), help="Implementation to use (ADK or RLM).")
def chat(message, sprint_id, session_id, user_id, impl):
    """Chat with the OneCoder orchestrator agent."""
    effective_sprint_id = sprint_id or auto_detect_sprint_id()

    if impl == "rlm":
        try:
            from onecoder_rlm.rlm_runtime import OneCoderRLM
            from onecoder_rlm.config import RLMConfig
            
            click.echo(f"[*] Talking to RLM Reasoning Agent (Sprint: {effective_sprint_id or 'Detached'})")
            
            # Setup a basic config for CLI testing
            config = RLMConfig(
                max_rlm_iterations=15,
                verbose=True,
                enable_cli_tool=True
            )
            rlm = OneCoderRLM(config=config)
            
            for event in rlm.stream(message):
                etype = event.get("type")
                if etype == "reasoning":
                    click.secho(f"\n💭 Reasoning: {event['content']}", fg="cyan")
                elif etype == "tool_use":
                    click.secho(f"🛠️ Executing: {event['tool']} with {event['args']}", fg="yellow")
                elif etype == "tool_result":
                    res = event['result']
                    if len(res) > 500: res = res[:500] + "... (truncated)"
                    color = "red" if event.get("error") else "green"
                    click.secho(f"✅ Result: {res}", fg=color)
                elif etype == "done":
                    res = event["result"]
                    click.secho(f"\n[+] Task {res['status']}: {res.get('reason', 'Success')}", bold=True, fg="green" if res['status'] == "completed" else "red")
                    usage = res.get("usage", {})
                    click.echo(f"📊 Usage: Input={usage.get('input')} | Output={usage.get('output')}")
            return
        except ImportError:
            click.secho("Error: 'onecoder_rlm' package not found in PYTHONPATH.", fg="red")
            return
        except Exception as e:
            click.secho(f"RLM Error: {e}", fg="red")
            return

    # ADK implementation
    async def _run():
        session_service = DurableSessionService()
        app_name = "onecoder-cli-test"
        
        # Ensure session exists
        session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        if not session:
            await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

        agent_instance = get_root_agent(effective_sprint_id)
        
        runner = Runner(
            session_service=session_service,
            agent=agent_instance,
            app_name=app_name
        )

        click.echo(f"[*] Talking to Orchestrator (Sprint: {effective_sprint_id or 'Detached'}, Implementation: {impl})")
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=Content(parts=[Part(text=message)], role="user"),
        ):
            # Check for text in Content events
            if hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        sys.stdout.write(part.text)
                        sys.stdout.flush()
            
            # Check for tool calls or other events if needed
            if hasattr(event, "type"):
                # You can log events here if verbose
                pass

        click.echo("\n[+] Done.")

    asyncio.run(_run())

@agent.command()
@click.option("--sprint-id", help="Explicit sprint ID to use.")
@click.option("--impl", default="adk", type=click.Choice(["adk", "rlm"]), help="Implementation to use (ADK or RLM).")
def interactive(sprint_id, impl):
    """Start an interactive CLI session with the orchestrator."""
    effective_sprint_id = sprint_id or auto_detect_sprint_id()
    click.echo(f"[*] Starting interactive session (Sprint: {effective_sprint_id or 'Detached'}, Implementation: {impl})")
    click.echo("[*] Type 'exit' or 'quit' to end.")

    session_service = DurableSessionService()
    user_id = "cli-interactive"
    session_id = "cli-interactive-session"
    
    while True:
        try:
            message = click.prompt("User")
            if message.lower() in ["exit", "quit"]:
                break

            if impl == "rlm":
                try:
                    from onecoder_rlm.rlm_runtime import OneCoderRLM
                    from onecoder_rlm.config import RLMConfig
                    
                    config = RLMConfig(max_rlm_iterations=15, verbose=False)
                    rlm = OneCoderRLM(config=config)
                    
                    for event in rlm.stream(message):
                         etype = event.get("type")
                         if etype == "reasoning":
                             click.secho(f"💭 {event['content']}", fg="cyan")
                         elif etype == "tool_use":
                             click.secho(f"🛠️ {event['tool']}({event['args']})", fg="yellow")
                         elif etype == "done":
                             res = event["result"]
                             click.secho(f"Final: {res.get('status')}", bold=True)
                    continue
                except Exception as e:
                    click.secho(f"RLM Error: {e}", fg="red")
                    continue

            async def _run_msg(msg):
                app_name = "onecoder-cli-interactive"
                
                # Ensure session exists
                session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
                if not session:
                    await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

                agent_instance = get_root_agent(effective_sprint_id)
                runner = Runner(
                    session_service=session_service,
                    agent=agent_instance,
                    app_name=app_name
                )
                
                print("Agent: ", end="", flush=True)
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=Content(parts=[Part(text=msg)], role="user"),
                ):
                    if hasattr(event, "content") and event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                sys.stdout.write(part.text)
                                sys.stdout.flush()
                print()

            asyncio.run(_run_msg(message))
            
        except (EOFError, KeyboardInterrupt):
            break

    click.echo("\n[+] Session ended.")
