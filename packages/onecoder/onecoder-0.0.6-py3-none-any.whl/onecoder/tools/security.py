import os
import json
import subprocess
import logging
from typing import List, Dict, Any, Optional
try:
    from onecore import GovernanceEngine
except ImportError:
    GovernanceEngine = None

class SecurityScanner:
    """Native security scanner for OneCoder CLI."""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.logger = logging.getLogger("onecoder.security")

    def scan_dependencies(self) -> List[Dict[str, Any]]:
        """Generate SBOM and scan for vulnerabilities using Trivy if available."""
        components = []
        
        # 1. Try Trivy for comprehensive scan
        try:
            result = subprocess.run(
                ["trivy", "repo", "--format", "cyclonedx", "--output", "sbom.json", self.repo_path],
                capture_output=True, text=True, check=False
            )
            if os.path.exists("sbom.json"):
                with open("sbom.json", "r") as f:
                    sbom_data = json.load(f)
                components = self._parse_cyclonedx(sbom_data)
                os.remove("sbom.json")
                return components
        except Exception as e:
            self.logger.warning(f"Trivy scan failed or not available: {e}")

        # 2. Fallback to manual file parsing
        return self._manual_parse()

    def _parse_cyclonedx(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        components = []
        for comp in data.get("components", []):
            components.append({
                "name": comp.get("name"),
                "version": comp.get("version"),
                "type": comp.get("type"),
                "purl": comp.get("purl")
            })
        return components

    def _manual_parse(self) -> List[Dict[str, Any]]:
        """Manually parse common dependency files."""
        components = []
        
        # package.json
        pkg_json = os.path.join(self.repo_path, "package.json")
        if os.path.exists(pkg_json):
            try:
                with open(pkg_json, "r") as f:
                    data = json.load(f)
                    for name, version in data.get("dependencies", {}).items():
                        components.append({"name": name, "version": version, "type": "library", "source": "package.json"})
                    for name, version in data.get("devDependencies", {}).items():
                        components.append({"name": name, "version": version, "type": "library", "source": "package.json"})
            except Exception as e:
                self.logger.error(f"Error parsing package.json: {e}")

        # requirements.txt
        req_txt = os.path.join(self.repo_path, "requirements.txt")
        if os.path.exists(req_txt):
            try:
                with open(req_txt, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if "==" in line:
                                name, version = line.split("==")
                                components.append({"name": name, "version": version, "type": "library", "source": "requirements.txt"})
                            else:
                                components.append({"name": line, "version": "unknown", "type": "library", "source": "requirements.txt"})
            except Exception as e:
                self.logger.error(f"Error parsing requirements.txt: {e}")

        return components

    def run_bandit(self) -> List[Dict[str, Any]]:
        """Run Bandit for Python SAST."""
        findings = []
        try:
            result = subprocess.run(
                ["bandit", "-r", self.repo_path, "-f", "json"],
                capture_output=True, text=True, check=False
            )
            if result.stdout:
                data = json.loads(result.stdout)
                for issue in data.get("results", []):
                    findings.append({
                        "id": issue.get("test_id"),
                        "issue_text": issue.get("issue_text"),
                        "severity": issue.get("issue_severity"),
                        "file": issue.get("filename"),
                        "line": issue.get("line_number")
                    })
        except Exception as e:
            self.logger.warning(f"Bandit scan failed: {e}")
        return findings

    def scan_secrets(self) -> List[Dict[str, Any]]:
        """Fast secret scanning using Rust engine."""
        findings = []
        if GovernanceEngine:
            try:
                engine = GovernanceEngine(self.repo_path)
                scan_data = json.loads(engine.scan_fast())
                for secret in scan_data.get("secrets_found", []):
                    findings.append({
                        "id": "SEC-001",
                        "issue_text": f"Potential Secret: {secret['secret_type']}",
                        "severity": "CRITICAL",
                        "file": secret['file'],
                        "line": secret['line']
                    })
            except Exception as e:
                self.logger.warning(f"OneCore secret scan failed: {e}")
        return findings
