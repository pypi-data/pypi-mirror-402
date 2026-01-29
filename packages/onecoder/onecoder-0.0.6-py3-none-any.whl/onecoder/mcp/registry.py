import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger("onecoder.mcp.registry")

class McpServerConfig(BaseModel):
    name: str
    type: str  # "stdio", "inspector", "remote"
    command: Optional[List[str]] = None
    url: Optional[str] = None
    env: Dict[str, str] = {}
    manifest_path: Optional[str] = None

class McpRegistry:
    def __init__(self):
        self.config_dir = Path.home() / ".onecoder" / "mcp"
        self.config_file = self.config_dir / "config.json"
        self.servers: Dict[str, McpServerConfig] = {}
        self._ensure_config()

    def _ensure_config(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            self._save_config({})
        else:
            self._load_config()

    def _load_config(self):
        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
                for name, config in data.get("servers", {}).items():
                    self.servers[name] = McpServerConfig(**config)
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")

    def _save_config(self, data: dict):
        with open(self.config_file, "w") as f:
            json.dump(data, f, indent=2)

    def discover_skills(self, root_path: str):
        """Scan directory for mcp.json files and register them."""
        root = Path(root_path)
        logger.info(f"Scanning for skills in {root}")
        
        for path in root.rglob("mcp.json"):
            try:
                with open(path, "r") as f:
                    manifest = json.load(f)
                    
                name = manifest.get("name")
                if not name:
                    continue
                    
                # Register as a local wrap-server
                # We use the python script wrapper we just made
                self.servers[name] = McpServerConfig(
                    name=name,
                    type="stdio",
                    command=[
                        "uv", "run", "python", 
                        "-m", "onecoder.mcp.server_wrapper", 
                        str(path.absolute())
                    ],
                    expr_path=str(path.parent), # Just context
                    manifest_path=str(path.absolute())
                )
                logger.info(f"Discovered skill: {name} at {path}")
            except Exception as e:
                logger.warning(f"Failed to parse {path}: {e}")

    def list_servers(self) -> List[McpServerConfig]:
        return list(self.servers.values())

    def get_server(self, name: str) -> Optional[McpServerConfig]:
        return self.servers.get(name)
