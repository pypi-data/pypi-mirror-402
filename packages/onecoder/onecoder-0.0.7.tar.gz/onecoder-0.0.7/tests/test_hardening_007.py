import pytest
import os
from click.testing import CliRunner
from onecoder.cli import cli

@pytest.fixture
def runner():
    return CliRunner()

def test_version_007(runner):
    """Verify the version is bumped to 0.0.7."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version 0.0.7" in result.output

def test_tui_hidden_by_default(runner):
    """Verify 'tui' command is hidden for public users."""
    # Ensure environment variables are clean
    env = os.environ.copy()
    env.pop("ONECODER_INTERNAL", None)
    env.pop("ONE_CODER_DEV", None)
    
    with patch.dict(os.environ, env, clear=True):
        result = runner.invoke(cli, ["--help"])
        assert "tui" not in result.output

def test_tui_visible_for_internal(runner):
    """Verify 'tui' command is visible when internal flag is set."""
    with patch.dict(os.environ, {"ONECODER_INTERNAL": "true"}):
        result = runner.invoke(cli, ["--help"])
        assert "tui" in result.output

def test_tiered_gating_for_free_users(runner):
    """Verify non-core commands are hidden for free users."""
    with patch("onecoder.cli.config_manager.get_token", return_value="fake-token"):
        with patch("onecoder.cli.config_manager.get_entitlements", return_value=[]):
            with patch("onecoder.cli.is_internal_features_enabled", return_value=False):
                # We need to re-run the gating logic if it was already run on import
                # For testing purposes, we can manually call apply_tiered_gating or 
                # check if the CLI has the hidden attribute set correctly.
                from onecoder.cli import apply_tiered_gating
                apply_tiered_gating()
                
                result = runner.invoke(cli, ["--help"])
                assert "sprint" in result.output
                assert "login" in result.output
                assert "agent" not in result.output
                assert "infra" not in result.output
                
                # Cleanup: reveal them again so other tests don't fail
                for cmd in cli.commands.values():
                    cmd.hidden = False

from unittest.mock import patch
