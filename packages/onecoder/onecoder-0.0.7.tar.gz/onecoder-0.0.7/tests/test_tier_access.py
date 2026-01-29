import click
from click.testing import CliRunner
from onecoder.cli import cli
import pytest
from unittest.mock import patch, MagicMock

def test_preflight_is_free():
    """Verify that sprint preflight does not require governance_tools entitlement."""
    runner = CliRunner()
    
    # Mock config_manager to return no entitlements
    with patch('onecoder.commands.auth.config_manager') as mock_config:
        mock_config.get_token.return_value = "fake-token"
        mock_config.get_entitlements.return_value = []
        
        # Mock SprintPreflight and auto_detect_sprint_id to avoid actual disk access
        with patch('ai_sprint.commands.governance.preflight.SprintPreflight') as mock_preflight_engine, \
             patch('ai_sprint.commands.governance.preflight.auto_detect_sprint_id') as mock_detect:
            
            mock_detect.return_value = "001-test"
            engine_instance = mock_preflight_engine.return_value
            engine_instance.run_all.return_value = (100, [{"name": "Mock Check", "status": "passed", "message": "OK"}])
            
            # Run 'sprint preflight'
            # Note: sprint is a group, so we need to call it as 'sprint', 'preflight'
            result = runner.invoke(cli, ['sprint', 'preflight'])
            
            # It should NOT fail with "Feature 'governance_tools' is not enabled"
            assert "Feature 'governance_tools' is not enabled" not in result.output
            assert "✅ Mock Check: OK" in result.output
            assert result.exit_code == 0

def test_require_feature_guidance():
    """Verify that require_feature provides improved guidance when a feature is locked."""
    runner = CliRunner()
    
    # We need a command that STILL has @require_feature
    # 'sprint trace' in utility.py has @require_feature("audit_tools")
    
    with patch('onecoder.commands.auth.config_manager') as mock_config:
        mock_config.get_token.return_value = "fake-token"
        mock_config.get_entitlements.return_value = [] # No entitlements
        
        result = runner.invoke(cli, ['sprint', 'trace'])
        
        assert result.exit_code == 1
        assert "Error: Feature 'audit_tools' is not enabled for your account." in result.output
        assert "Tip: This feature requires a higher tier" in result.output
        assert "run 'onecoder guide'" in result.output
