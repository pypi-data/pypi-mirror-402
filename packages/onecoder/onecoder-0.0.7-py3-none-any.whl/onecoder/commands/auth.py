import click
import os
import asyncio
import webbrowser
import sys
from functools import wraps
from ..api_client import get_api_client
from ..config_manager import config_manager

def require_login(f):
    """Decorator to enforce login."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = config_manager.get_token()
        if not token:
            click.echo("Error: You must be logged in to run this command.")
            click.echo("Run 'onecoder login' first.")
            return
        return f(*args, **kwargs)
    return wrapper

def require_feature(feature_name):
    """Decorator to enforce feature entitlements."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = config_manager.get_token()
            if not token:
                 click.secho("Error: You must be logged in to access this feature.", fg="red")
                 return
            
            entitlements = config_manager.get_entitlements()
            
            if feature_name not in entitlements:
                click.secho(f"Error: Feature '{feature_name}' is not enabled for your account.", fg="red")
                click.echo("\nTip: This feature requires a higher tier (e.g., PRO or ENTERPRISE).")
                click.echo("To see what's available in your current tier, run 'onecoder whoami'.")
                click.echo("To learn more about using OneCoder efficiently, run 'onecoder guide'.")
                click.echo(f"Upgrade your plan at: https://onecoder.dev/upgrade")
                sys.exit(1)
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

from ..constants import GITHUB_CLIENT_ID

@click.command()
def login():
    """Authenticates with OneCoder via GitHub."""
    
    async def get_url():
        try:
            client = get_api_client()
            return await client.get_github_auth_url()
        except Exception as e:
            raise e

    # Verbose logging for debug
    api_url = os.getenv("ONECODER_API_URL", "https://api.onecoder.dev")
    is_local = "localhost" in api_url or "127.0.0.1" in api_url
    mode = "LOCAL" if is_local else "REMOTE"
    
    click.secho(f"--- OneCoder Auth Debug ---", fg="blue")
    click.echo(f"API Target: {api_url}")
    click.echo(f"Mode:       {mode}")
    click.echo(f"---------------------------")

    try:
        auth_url = asyncio.run(get_url())
    except Exception as e:
        click.secho(f"Error fetching auth URL from API: {e}", fg="red")
        click.secho("Fallback: Using local configuration if available.", fg="yellow")
        client_id = GITHUB_CLIENT_ID
        client_id_param = f"client_id={client_id}"
        
        # If we are local, we might need a specific redirect_uri to avoid callback mismatch
        # But generally the app is configured to callback to /api/v1/auth/github
        # If local, that is localhost:8787/api/v1/auth/github
        
        auth_url = f"https://github.com/login/oauth/authorize?{client_id_param}&scope=user:email"

    click.echo("To authenticate, please visit the following URL in your browser:")
    click.echo(f"\n  {auth_url}\n")
    click.secho("Note: If you haven't installed the OneCoder GitHub App yet, please do so from the App Profile page.", fg="yellow")
    
    if click.confirm("Open browser automatically?", default=True):
        webbrowser.open(auth_url)
    
    code = click.prompt("Enter the authorization code provided by GitHub")
    
    async def do_login():
        try:
            client = get_api_client()
            # 2. Exchange code and hydrate session
            auth_data = await client.login_with_github(code)
            click.echo(f"Hello, {auth_data['user']['username']}!")
            
            # Use consolidated hydration
            click.echo("Syncing account metadata...")
            me_data = await client.hydrate_session()
            
            tier = me_data.get("subscription", {}).get("plan", {}).get("tier", "free")
            click.secho(f"Subscription: {tier.upper()}", fg="green")
            
            # Save token to file
            config_manager.set_token(auth_data["token"])
            config_manager.set_user(me_data["user"])
            config_manager.set_entitlements(me_data.get("subscription", {}).get("entitlements", []))
            
            click.secho("✓ Successfully logged in!", fg="green")
                 
        except Exception as e:
            import logging
            logging.exception("Login process failed")
            
            # Check if it's a known sync failure (like the 500 on subscriptions)
            if "subscriptions/me" in str(e) or "subscription" in str(e).lower():
                click.secho(f"Auth Success, but Sync Failed: {e}", fg="yellow")
                click.echo("Your account is authenticated, but feature entitlements could not be fetched.")
                click.echo("Please check your network or try again later.")
            else:
                click.secho(f"Error: Login failed: {e}", fg="red")

    asyncio.run(do_login())

@click.command()
def logout():
    """Logs out of OneCoder."""
    config_manager.clear_token()
    config_manager.set_entitlements([])
    click.echo("Successfully logged out.")

@click.command()
def whoami():
    """Shows the currently authenticated user and their entitlements."""
    token = config_manager.get_token()
    if token:
        # Hardening: Always try to refresh from API if possible
        try:
            from ..api_client import get_api_client
            import asyncio
            client = get_api_client(token)
            
            # For simplicity in this CLI hook:
            user_data = asyncio.run(client.get_me())
            if user_data and "user" in user_data:
                config_manager.set_user(user_data.get("user", {}))
                # Update subscription info if present
                sub = user_data.get("subscription", {})
                entitlements = sub.get("entitlements", [])
                config_manager.set_entitlements(entitlements)
                
                # Store plan info in user for whoami access
                user_update = user_data.get("user", {})
                user_update["subscription"] = sub
                config_manager.set_user(user_update)
        except Exception:
            # Fallback to local config if API is unreachable
            pass

    user = config_manager.get_user()
    if user:
        entitlements = config_manager.get_entitlements()
        
        click.secho(f"Logged in as: {user['username']}", fg="green")
        
        # Check for override
        config = config_manager.load_config()
        tier_override = config.get("tier_override")
        
        # Safety Gate check again for the message
        current_api_url = os.getenv("ONECODER_API_URL", "https://api.onecoder.dev")
        is_localhost = "localhost" in current_api_url or "127.0.0.1" in current_api_url
        
        if config_manager.is_bypass_active():
            click.secho(f"Current Plan: {user.get('subscription', {}).get('plan', {}).get('tier', 'enterprise').upper()} [BYPASS ACTIVE]", fg="cyan", bold=True)
        elif tier_override and is_localhost:
            click.secho(f"Current Plan: {tier_override['tier'].upper()} [LOCAL OVERRIDE]", fg="yellow", bold=True)
        elif user.get("subscription", {}).get("plan", {}).get("tier") == "enterprise":
            click.secho("Current Plan: ENTERPRISE", fg="cyan", bold=True)
        elif entitlements:
            # Try to infer tier name from config user data if available, or just say active features
            plan_name = user.get("subscription", {}).get("plan", {}).get("name", "Active Plan")
            click.echo(f"Current Plan: {plan_name}")
        else:
            click.echo("Current Plan: Free Tier")

        if entitlements:
            click.echo(f"Active Features: {', '.join(entitlements)}")
            
        if token:
            click.echo(f"Token: {token[:10]}...{token[-10:]}")
    else:
        click.echo("Not logged in.")
