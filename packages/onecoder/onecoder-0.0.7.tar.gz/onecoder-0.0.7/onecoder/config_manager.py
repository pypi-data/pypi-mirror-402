import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".onecoder"
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions
            os.chmod(self.config_dir, 0o700)

    def is_bypass_active(self) -> bool:
        """
        Check if the local-only ADMIN bypass is active with hardened safeguards.
        """
        # 1. Environment Variable Opt-in
        if os.getenv("ONECODER_DEV_BYPASS") != "true":
            return False

        # 2. Localhost-only Safety Gate
        api_url = os.getenv("ONECODER_API_URL", "https://api.onecoder.dev")
        if not ("localhost" in api_url or "127.0.0.1" in api_url):
            return False

        # 3. Anti-Installation Check (no site-packages)
        current_file = __file__
        if "site-packages" in current_file or "dist-packages" in current_file:
            return False

        # 4. Source-Tree Check (pyproject.toml 2 levels up)
        try:
            # Current file is in package/core/engines/onecoder-cli/onecoder/config_manager.py
            # pyproject.toml is in package/core/engines/onecoder-cli/pyproject.toml
            pkg_root = Path(current_file).resolve().parent.parent
            if not (pkg_root / "pyproject.toml").exists():
                return False
        except Exception:
            return False

        # 5. Execution check: UV_PROJECT_ENVIRONMENT or VIRTUAL_ENV
        # (This confirms we are running via 'uv run' or in a dev venv)
        if not (os.getenv("UV_PROJECT_ENVIRONMENT") or os.getenv("VIRTUAL_ENV")):
            return False

        return True

    def load_config(self) -> Dict[str, Any]:
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def save_config(self, config: Dict[str, Any]):
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
            # Set restrictive permissions
            os.chmod(self.config_file, 0o600)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_token(self) -> Optional[str]:
        if self.is_bypass_active():
            return "local-dev-bypass-token"
        config = self.load_config()
        return config.get("api_token")

    def set_token(self, token: str):
        if self.is_bypass_active():
            return
        config = self.load_config()
        config["api_token"] = token
        self.save_config(config)

    def clear_token(self):
        config = self.load_config()
        if "api_token" in config:
            del config["api_token"]
            self.save_config(config)

    def get_user(self) -> Optional[Dict[str, Any]]:
        if self.is_bypass_active():
            return {
                "id": "local-admin-uuid",
                "username": "local-admin",
                "email": "admin@localhost",
                "is_superadmin": True,
                "subscription": {
                    "plan": {"tier": "enterprise", "name": "Local Bypass"},
                    "entitlements": [
                        "roadmap_tools", "knowledge_tools", "analytics_tools", 
                        "infra_tools", "content_tools", "ci_tools", 
                        "audit_tools", "env_tools", "admin_tools"
                    ]
                }
            }
        config = self.load_config()
        return config.get("user")

    def set_user(self, user: Dict[str, Any]):
        if self.is_bypass_active():
            return
        config = self.load_config()
        config["user"] = user
        self.save_config(config)

    def get_entitlements(self) -> Any: # Use Any to avoid import complication for now if needed, or fix imports
        if self.is_bypass_active():
            return [
                "roadmap_tools", "knowledge_tools", "analytics_tools", 
                "infra_tools", "content_tools", "ci_tools", 
                "audit_tools", "env_tools", "admin_tools"
            ]
            
        config = self.load_config()
        
        # --- Safety Gated Overrides ---
        # Direct check of env var to avoid circular import with .constants
        current_api_url = os.getenv("ONECODER_API_URL", "https://api.onecoder.dev")
        is_localhost = "localhost" in current_api_url or "127.0.0.1" in current_api_url
        
        # 1. Environment Variable Override (Highest Precedence)
        env_override = os.getenv("ONECODER_OVERRIDE_ENTITLEMENTS")
        if env_override and is_localhost:
            return [e.strip() for e in env_override.split(",") if e.strip()]
            
        # 2. Config Override (from 'onecoder dev set-tier')
        tier_override = config.get("tier_override")
        if tier_override and is_localhost:
            return tier_override.get("entitlements", [])
            
        # 3. Default API-fetched entitlements
        return config.get("entitlements", [])

    def set_entitlements(self, entitlements: Any):
        if self.is_bypass_active():
            return
        config = self.load_config()
        config["entitlements"] = entitlements
        self.save_config(config)

    def get_model_config(self) -> Optional[Dict[str, Any]]:
        config = self.load_config()
        return config.get("model")

    def set_model_config(self, model_config: Dict[str, Any]):
        config = self.load_config()
        config["model"] = model_config
        self.save_config(config)

    def get_github_client_id(self) -> str:
        """Get the GitHub Client ID from config or environment variable."""
        # Environment variable takes highest precedence
        env_id = os.getenv("GITHUB_CLIENT_ID")
        if env_id:
            return env_id
            
        config = self.load_config()
        # Return from config or the production default
        return config.get("github_client_id", "Iv23limfvipYiMLhjhq1")

    def set_github_client_id(self, client_id: str):
        """Set the GitHub Client ID in the config file."""
        config = self.load_config()
        config["github_client_id"] = client_id
        self.save_config(config)

config_manager = ConfigManager()
