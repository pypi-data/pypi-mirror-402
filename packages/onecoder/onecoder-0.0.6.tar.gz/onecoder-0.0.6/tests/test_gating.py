import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from ai_sprint.commands.utility import audit as sprint_audit, trace as sprint_trace
from ai_sprint.commands.governance import verify as sprint_verify, preflight as sprint_preflight
from onecoder.commands.project import alignment, knowledge, distill, sprint_suggest
from onecoder.commands.audit import audit as top_audit
from onecoder.commands.ci import ci as top_ci
from onecoder.commands.doctor import doctor as top_doctor, trace as top_trace
from onecoder.commands.env import env as top_env
from onecoder.commands.reflect import reflect as top_reflect
from onecoder.commands.content import content as top_content

@pytest.fixture
def runner():
    return CliRunner()

def test_sprint_audit_gating(runner):
    with patch("onecoder.commands.auth.config_manager.get_token", return_value="fake-token"):
        with patch("onecoder.commands.auth.config_manager.get_entitlements", return_value=[]):
            result = runner.invoke(sprint_audit)
            assert "Error: Feature 'audit_tools' is not enabled for your account." in result.output

def test_alignment_gating(runner):
    with patch("onecoder.commands.auth.config_manager.get_token", return_value="fake-token"):
        with patch("onecoder.commands.auth.config_manager.get_entitlements", return_value=[]):
            result = runner.invoke(alignment)
            assert "Error: Feature 'roadmap_tools' is not enabled for your account." in result.output

def test_top_audit_gating(runner):
    with patch("onecoder.commands.auth.config_manager.get_token", return_value="fake-token"):
        with patch("onecoder.commands.auth.config_manager.get_entitlements", return_value=[]):
            result = runner.invoke(top_audit, ["scan"])
            assert "Error: Feature 'audit_tools' is not enabled for your account." in result.output

def test_ci_gating(runner):
    with patch("onecoder.commands.auth.config_manager.get_token", return_value="fake-token"):
        with patch("onecoder.commands.auth.config_manager.get_entitlements", return_value=[]):
            result = runner.invoke(top_ci)
            assert "Error: Feature 'ci_tools' is not enabled for your account." in result.output

def test_knowledge_gating(runner):
    with patch("onecoder.commands.auth.config_manager.get_token", return_value="fake-token"):
        with patch("onecoder.commands.auth.config_manager.get_entitlements", return_value=[]):
            result = runner.invoke(knowledge)
            assert "Error: Feature 'knowledge_tools' is not enabled for your account." in result.output

def test_doctor_gating(runner):
    with patch("onecoder.commands.auth.config_manager.get_token", return_value="fake-token"):
        with patch("onecoder.commands.auth.config_manager.get_entitlements", return_value=[]):
            result = runner.invoke(top_doctor, ["env"])
            assert "Error: Feature 'diagnostic_tools' is not enabled for your account." in result.output

def test_env_gating(runner):
    with patch("onecoder.commands.auth.config_manager.get_token", return_value="fake-token"):
        with patch("onecoder.commands.auth.config_manager.get_entitlements", return_value=[]):
            result = runner.invoke(top_env, ["list"])
            assert "Error: Feature 'security_tools' is not enabled for your account." in result.output

def test_reflect_gating(runner):
    with patch("onecoder.commands.auth.config_manager.get_token", return_value="fake-token"):
        with patch("onecoder.commands.auth.config_manager.get_entitlements", return_value=[]):
            result = runner.invoke(top_reflect, ["some message"])
            assert "Error: Feature 'content_tools' is not enabled for your account." in result.output

def test_content_gating(runner):
    with patch("onecoder.commands.auth.config_manager.get_token", return_value="fake-token"):
        with patch("onecoder.commands.auth.config_manager.get_entitlements", return_value=[]):
            result = runner.invoke(top_content, ["ops", "list-insights"])
            assert "Error: Feature 'content_tools' is not enabled for your account." in result.output
