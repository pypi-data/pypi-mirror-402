import re
import os
from typing import List, Optional

class SecretScanner:
    """
    Scans text content for potential secrets and API keys using heuristic patterns.
    """

    def __init__(self, patterns: Optional[List[str]] = None):
        # Default patterns
        self.patterns = patterns or [
            r"sk-[a-zA-Z0-9\-]{20,}", # OpenAI/Stripe style
            r"gh[pousr]-[a-zA-Z0-9\-]{20,}", # GitHub tokens
            r"xox[baprs]-[a-zA-Z0-9\-]{10,}", # Slack tokens
            r"AIza[0-9A-Za-z\-_]{35}", # Google API Key
            # r"[a-f0-9]{32,}", # REMOVED: Generic MD5/hex token (Too many false positives with hashes)
        ]
        
        # High-risk environment variables to check against
        self.sensitive_env_keys = ["API_KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIALS"]

    def contains_secrets(self, text: str) -> bool:
        """
        Heuristically checks if the text contains secrets.
        """
        # 1. Check regex patterns
        for pattern in self.patterns:
            if re.search(pattern, text):
                return True

        # 2. Check for values of sensitive environment variables
        # (Only check if the value is long enough to avoid false positives)
        for key, value in os.environ.items():
            if any(s in key for s in self.sensitive_env_keys) and len(value) > 8:
                if value in text:
                    return True

        return False
