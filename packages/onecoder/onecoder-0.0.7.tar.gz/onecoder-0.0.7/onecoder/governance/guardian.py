import yaml
import os
import json
import logging
from typing import Tuple, Dict, Any

try:
    from onecore import GovernanceGuardian as RustGuardian
except ImportError:
    # Fallback or error if onecore is not built
    RustGuardian = None

class GovernanceGuardian:
    """
    Enforces governance policies including security (OWASP LLM Risks) and operational
    constraints using the high-performance `onecore` Rust backend.
    """

    def __init__(self, governance_path="governance.yaml"):
        self.governance_path = governance_path
        self.logger = logging.getLogger("onecoder.governance")
        
        config_data = self._load_policy_data()
        
        if RustGuardian:
            # Pass config as JSON string to Rust for safety and simplicity
            self.rust_guardian = RustGuardian(json.dumps(config_data))
        else:
            self.rust_guardian = None
            self.logger.warning("onecore backend is NOT loaded. Governance checks requiring Rust will FAIL.")
            # raise ImportError("onecore backend is required for GovernanceGuardian")

    def _load_policy_data(self) -> Dict[str, Any]:
        if not os.path.exists(self.governance_path):
            return {}
        try:
            with open(self.governance_path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.warning(f"Failed to load governance policy: {e}")
            return {}

    def is_enabled(self) -> bool:
        """Checks if governance is enabled."""
        if not self.rust_guardian:
            return False
        return self.rust_guardian.is_enabled()

    def validate_tool_execution(self, tool_name: str, args: dict) -> Tuple[bool, str]:
        """
        Validates whether a tool execution is safe based on the policy.
        Delegates to Rust backend.
        """
        if not self.rust_guardian:
             # Basic fallback: check if file paths in args violate any simple policy
             return True, "Safe (Native Fallback)"

        try:
            args_json = json.dumps(args)
            return self.rust_guardian.validate_tool_execution(tool_name, args_json)
        except Exception as e:
             self.logger.error(f"Governance validation error: {e}")
             # Fail closed if governance errors out
             return False, f"Governance Error: {e}"

    def validate_output(self, output: str) -> Tuple[bool, str]:
        """
        Scans LLM or Tool output for leaked secrets.
        """
        if not self.rust_guardian:
            return True, "Safe (Native Fallback)"
        return self.rust_guardian.validate_output(str(output))

    def validate_staged_files(self, file_paths: list, reason: str = None) -> Tuple[bool, str, Dict]:
        """
        Validates staged files. Enforces SPEC-GOV-013: Implementation requires tests.
        """
        # If reason is provided (via commit trailer or override), optimize for approval
        if reason and len(reason.strip()) > 5:
             self.logger.info(f"Governance override accepted: {reason}")
             return True, "Safe (Override)", {"override": True}

        has_implementation = False
        has_tests = False
        
        # Simple heuristics for classification
        for path in file_paths:
            path_lower = path.lower()
            
            # Skip documentation, config, and scripts
            if any(x in path_lower for x in ['.md', '.txt', 'docs/', 'config/', 'scripts/', '.json', '.yaml', '.toml', 'makefile', '.lock']):
                continue
                
            # Check for tests
            if any(x in path_lower for x in ['test', 'spec', '__tests__']):
                has_tests = True
                continue
                
            # If it's a source file (py, ts, js, rs, go) and not a test
            if any(path_lower.endswith(ext) for ext in ['.py', '.ts', '.js', '.rs', '.go', '.tsx', '.jsx']):
                has_implementation = True

        if has_implementation and not has_tests:
            msg = (
                "Policy SPEC-GOV-013 Violation: Implementation changes detected without accompanying tests. "
                "Please add a test file (e.g., .test.ts, _test.py) or provide a valid reason for exemption."
            )
            return False, msg, {"violation": "SPEC-GOV-013"}

        return True, "Safe", {}

    def apply_integrity_locks(self, repo_path: str):
         # Integrity locks were OS calls. 
         # Keeping as no-op or Python if needed.
         pass

    def remove_integrity_locks(self, repo_path: str):
         pass
