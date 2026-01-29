import os
import json
import keyring
import base64
import re
from pathlib import Path
from typing import Optional, Dict, List, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EnvManager:
    SERVICE_NAME = "onecoder"
    
    def __init__(self):
        self.config_dir = Path.home() / ".onecoder"
        self.secrets_file = self.config_dir / "secrets.enc"
        self._ensure_config_dir()
        self._fernet: Optional[Fernet] = None
        self._secrets_cache: Dict[str, str] = {}
        self._redaction_patterns: List[re.Pattern] = []

    def _ensure_config_dir(self):
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(self.config_dir, 0o700)

    def _get_encryption_key(self) -> bytes:
        """Get or generate an encryption key for fallback storage."""
        # We use a derived key from a machine-specific secret stored in keyring
        # if available, or a fallback.
        machine_secret = keyring.get_password(self.SERVICE_NAME, "machine_secret")
        if not machine_secret:
            machine_secret = base64.b64encode(os.urandom(32)).decode('utf-8')
            keyring.set_password(self.SERVICE_NAME, "machine_secret", machine_secret)
        
        salt = b'onecoder_salt' # In a real app, this should also be stored/unique
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_secret.encode()))
        return key

    @property
    def fernet(self) -> Fernet:
        if self._fernet is None:
            self._fernet = Fernet(self._get_encryption_key())
        return self._fernet

    def set_env(self, key: str, value: str, project_path: Optional[str] = None):
        """Store an environment variable."""
        store_key = f"{key}@{project_path}" if project_path else key
        
        # 1. Try keyring (best effort security)
        try:
            keyring.set_password(self.SERVICE_NAME, store_key, value)
        except Exception:
            pass

        # 2. ALWAYS save to encrypted file. This serves 2 purposes:
        #    a) Manifest (so we can list keys)
        #    b) Fallback/Backup (if keyring is unavailable later)
        secrets = self._load_encrypted_secrets()
        secrets[store_key] = value
        self._save_encrypted_secrets(secrets)
        
        self._secrets_cache[store_key] = value
        self._update_redaction_patterns()

    def get_env(self, key: str, project_path: Optional[str] = None) -> Optional[str]:
        """Retrieve an environment variable."""
        store_key = f"{key}@{project_path}" if project_path else key
        
        if store_key in self._secrets_cache:
            return self._secrets_cache[store_key]

        # Try keyring
        try:
            value = keyring.get_password(self.SERVICE_NAME, store_key)
            if value:
                self._secrets_cache[store_key] = value
                return value
        except Exception:
            pass

        # Try fallback file
        secrets = self._load_encrypted_secrets()
        value = secrets.get(store_key)
        if value:
            self._secrets_cache[store_key] = value
            return value
            
        return None

    def delete_env(self, key: str, project_path: Optional[str] = None):
        """Delete a stored environment variable."""
        store_key = f"{key}@{project_path}" if project_path else key
        
        try:
            keyring.delete_password(self.SERVICE_NAME, store_key)
        except Exception:
            pass

        secrets = self._load_encrypted_secrets()
        if store_key in secrets:
            del secrets[store_key]
            self._save_encrypted_secrets(secrets)
        
        if store_key in self._secrets_cache:
            del self._secrets_cache[store_key]
        
        self._update_redaction_patterns()

    def list_keys(self, project_path: Optional[str] = None) -> List[str]:
        """List keys available for a given project path (including globals)."""
        all_secrets = self._load_encrypted_secrets()
        keys = []
        for sk in all_secrets.keys():
            if "@" in sk:
                k, p = sk.rsplit("@", 1)
                if p == project_path:
                    keys.append(k)
            elif project_path is None:
                # Global env
                keys.append(sk)
        return list(set(keys))

    def get_all_secrets(self) -> Dict[str, str]:
        """Retrieve all raw stored secrets (including @path keys)."""
        return self._load_encrypted_secrets()

    def _load_encrypted_secrets(self) -> Dict[str, str]:
        if not self.secrets_file.exists():
            return {}
        try:
            encrypted_data = self.secrets_file.read_bytes()
            if not encrypted_data:
                return {}
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception:
            return {}

    def _save_encrypted_secrets(self, secrets: Dict[str, str]):
        data = json.dumps(secrets).encode()
        encrypted_data = self.fernet.encrypt(data)
        self.secrets_file.write_bytes(encrypted_data)
        os.chmod(self.secrets_file, 0o600)

    def _update_redaction_patterns(self):
        """Update regex patterns for redaction based on cached and stored secrets."""
        all_secrets = self._load_encrypted_secrets()
        for k, v in all_secrets.items():
            self._secrets_cache[k] = v
            
        values_to_redact = set(self._secrets_cache.values())
        patterns = []
        for val in values_to_redact:
            if len(val) > 4:
                patterns.append(re.escape(val))
        
        if patterns:
            patterns.sort(key=len, reverse=True)
            self._redaction_patterns = [re.compile(p) for p in patterns]
        else:
            self._redaction_patterns = []

    def redact(self, text: str) -> str:
        """Redact known secrets from the given text."""
        if not self._redaction_patterns:
            self._update_redaction_patterns()
            
        for pattern in self._redaction_patterns:
            text = pattern.sub("[REDACTED]", text)
        return text

    def get_context_env(self, project_path: str) -> Dict[str, str]:
        """Get all environment variables applicable to the given project path."""
        secrets = self._load_encrypted_secrets()
        context_env = {}
        for sk, val in secrets.items():
            if "@" in sk:
                k, p = sk.rsplit("@", 1)
                if p == project_path:
                    context_env[k] = val
            else:
                # Global env
                context_env[sk] = val
        return context_env

env_manager = EnvManager()
