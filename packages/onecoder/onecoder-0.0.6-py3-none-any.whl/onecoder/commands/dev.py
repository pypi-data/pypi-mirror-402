import click
from ..config_manager import config_manager

@click.group()
def dev():
    """Developer-only diagnostic and testing commands."""
    pass

@dev.command(name="set-tier")
@click.argument("tier", type=click.Choice(["free", "pro", "enterprise", "internal"], case_sensitive=False))
def set_tier(tier):
    """Overrides the local account tier and entitlements for testing."""
    tier = tier.lower()
    
    # Define mapping of tiers to entitlements
    TIER_ENTITLEMENTS = {
        "free": [],
        "pro": ["project_analysis", "advanced_drafting", "unlimited_sprints", "governance_tools"],
        "enterprise": ["project_analysis", "advanced_drafting", "unlimited_sprints", "governance_audit", "team_collaboration", "audit_tools", "governance_tools"],
        "internal": [
            "project_analysis", 
            "advanced_drafting", 
            "unlimited_sprints", 
            "governance_audit", 
            "team_collaboration", 
            "audit_tools", 
            "governance_tools",
            "ci_tools",
            "content_tools",
            "diagnostic_tools",
            "roadmap_tools",
            "knowledge_tools",
            "security_tools"
        ]
    }
    
    entitlements = TIER_ENTITLEMENTS.get(tier, [])
    
    # Update local config
    user = config_manager.load_config().get("user", {})
    if not user:
        click.secho("Error: No user found in config. Please login first.", fg="red")
        return

    # Store the override in config
    config = config_manager.load_config()
    config["tier_override"] = {
        "tier": tier,
        "entitlements": entitlements
    }
    config_manager.save_config(config)
    
    click.secho(f"✓ Local tier successfully set to: {tier.upper()}", fg="green")
    click.echo(f"Active Entitlements: {', '.join(entitlements) if entitlements else 'None'}")
    click.secho("\nNote: This override is only respected when ONECODER_API_URL points to localhost.", fg="yellow")

@dev.command(name="clear-tier")
def clear_tier():
    """Clears any local tier overrides."""
    config = config_manager.load_config()
    if "tier_override" in config:
        del config["tier_override"]
        config_manager.save_config(config)
        click.secho("✓ Local tier override cleared.", fg="green")
    else:
        click.echo("No tier override found.")
