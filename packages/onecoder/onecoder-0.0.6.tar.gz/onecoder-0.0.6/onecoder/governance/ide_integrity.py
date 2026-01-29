import os
import re
import fnmatch
from typing import Dict, Any, Tuple

class IdeIntegrityPolicy:
    """
    Enforces policies related to IDE integrity, restricting access to protected
    directories and blocking dangerous content patterns.
    """

    def __init__(self, policy_config: Dict[str, Any]):
        self.config = policy_config
        self.enabled = self.config.get("enabled", False)
        self.protected_dirs = self.config.get("protected_directories", [])
        self.blocked_patterns = self.config.get("blocked_file_patterns", [])
        self.content_scanning = self.config.get("content_scanning", {})

    def is_enabled(self) -> bool:
        return self.enabled

    def check_access(self, filepath: str) -> Tuple[bool, str]:
        """
        Validates basic file access permissions against protected directories and patterns.
        """
        if not self.enabled or not filepath:
            return True, "Safe"

        # Check protected directories
        for pd in self.protected_dirs:
            if pd in filepath or filepath.startswith(pd) or filepath.endswith("/" + pd.strip("/")):
                 return False, f"IDE Integrity Block: Access to protected IDE directory '{filepath}' is forbidden."

        # Check blocked file patterns
        filename = os.path.basename(filepath)
        for pattern in self.blocked_patterns:
            if fnmatch.fnmatch(filename, pattern):
                 return False, f"IDE Integrity Block: Access to protected IDE configuration '{filepath}' is forbidden."

        return True, "Safe"

    def check_content(self, content: str) -> Tuple[bool, str]:
        """
        Scans content for malicious patterns (e.g. Remote Schema Injection).
        """
        if not self.enabled or not content:
             return True, "Safe"

        # Content Scanning (Remote Schema Injection)
        if self.content_scanning.get("block_remote_schemas", False):
            # Regex looks for "$schema" followed by ":" and "http"
            if re.search(r'\"\$schema\"\s*:\s*\"http', content):
                 return False, "IDE Integrity Block: Remote JSON Schema detected (Potential Data Exfiltration)."
        
        return True, "Safe"
