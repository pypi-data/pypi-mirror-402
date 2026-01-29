import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from onecoder.config_manager import ConfigManager

class TestDevBypass(unittest.TestCase):
    def setUp(self):
        # Create a fresh ConfigManager for each test
        self.config_manager = ConfigManager()

    @patch("os.getenv")
    @patch("onecoder.config_manager.__file__", "/tmp/devbox/coding-platform/platform/packages/core/engines/onecoder-cli/onecoder/config_manager.py")
    def test_bypass_inactive_by_default(self, mock_getenv):
        mock_getenv.return_value = None
        self.assertFalse(self.config_manager.is_bypass_active())

    @patch("os.getenv")
    @patch("onecoder.config_manager.__file__", "/tmp/devbox/coding-platform/platform/packages/core/engines/onecoder-cli/onecoder/config_manager.py")
    @patch("pathlib.Path.exists")
    def test_bypass_active_with_proper_env(self, mock_exists, mock_getenv):
        def getenv_side_effect(key, default=None):
            env = {
                "ONECODER_DEV_BYPASS": "true",
                "ONECODER_API_URL": "http://localhost:8787",
                "UV_PROJECT_ENVIRONMENT": "/path/to/venv"
            }
            return env.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        mock_exists.return_value = True # For pyproject.toml check
        
        self.assertTrue(self.config_manager.is_bypass_active())
        self.assertEqual(self.config_manager.get_token(), "local-dev-bypass-token")
        self.assertEqual(self.config_manager.get_user()["username"], "local-admin")
        self.assertIn("roadmap_tools", self.config_manager.get_entitlements())

    @patch("os.getenv")
    @patch("onecoder.config_manager.__file__", "/tmp/devbox/coding-platform/platform/packages/core/engines/onecoder-cli/onecoder/config_manager.py")
    def test_bypass_fails_if_no_localhost(self, mock_getenv):
        def getenv_side_effect(key, default=None):
            env = {
                "ONECODER_DEV_BYPASS": "true",
                "ONECODER_API_URL": "https://api.onecoder.dev",
                "UV_PROJECT_ENVIRONMENT": "/path/to/venv"
            }
            return env.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        self.assertFalse(self.config_manager.is_bypass_active())

    @patch("os.getenv")
    @patch("onecoder.config_manager.__file__", "/home/user/.local/lib/python3.11/site-packages/onecoder/config_manager.py")
    def test_bypass_fails_if_site_packages(self, mock_getenv):
        def getenv_side_effect(key, default=None):
            env = {
                "ONECODER_DEV_BYPASS": "true",
                "ONECODER_API_URL": "http://localhost:8787",
                "UV_PROJECT_ENVIRONMENT": "/path/to/venv"
            }
            return env.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        self.assertFalse(self.config_manager.is_bypass_active())

    @patch("os.getenv")
    @patch("onecoder.config_manager.__file__", "/tmp/devbox/coding-platform/platform/packages/core/engines/onecoder-cli/onecoder/config_manager.py")
    def test_bypass_fails_if_no_uv_run(self, mock_getenv):
        def getenv_side_effect(key, default=None):
            env = {
                "ONECODER_DEV_BYPASS": "true",
                "ONECODER_API_URL": "http://localhost:8787"
                # UV_PROJECT_ENVIRONMENT and VIRTUAL_ENV are missing
            }
            return env.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        self.assertFalse(self.config_manager.is_bypass_active())

if __name__ == "__main__":
    unittest.main()
