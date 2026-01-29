#!/usr/bin/env python3
"""
FinOps Audit Script for OneCoder.
This script scans the current sprint context and logs to estimate costs and check against budget.
It is designed to be run as a pre-commit hook or CI step (Shift Left).
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add onecoder-cli path to sys.path to import modules
# Path is: packages/core/engines/onecoder-cli/onecoder/scripts/finops_audit.py
# We want: packages/core/engines/onecoder-cli
current_dir = Path(__file__).parent.resolve()
onecoder_cli_path = current_dir.parent.parent
sys.path.insert(0, str(onecoder_cli_path))

try:
    from onecoder.governance.finops_guardian import FinOpsGuardian
    from onecoder.finops_logger import FinOpsLogger
except ImportError as e:
    print(f"Error importing OneCoder modules: {e}")
    # Fallback to try finding it if we are in repo root
    try:
         sys.path.insert(0, os.getcwd())
         from packages.core.engines.onecoder_cli.onecoder.governance.finops_guardian import FinOpsGuardian
         from packages.core.engines.onecoder_cli.onecoder.finops_logger import FinOpsLogger
    except ImportError:
         sys.exit(1)

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("finops-audit")

    # Locate governance.yaml
    repo_root = Path.cwd()
    # If running from script dir, move up
    if "packages" in str(repo_root):
         # Try to find root by looking for governance.yaml
         while not (repo_root / "governance.yaml").exists():
             if repo_root.parent == repo_root:
                 break
             repo_root = repo_root.parent

    gov_path = repo_root / "governance.yaml"
    if not gov_path.exists():
         logger.error(f"Could not find governance.yaml at {gov_path}")
         sys.exit(1)

    guardian = FinOpsGuardian(str(gov_path))

    if not guardian.is_enabled():
        logger.info("FinOps governance is disabled.")
        sys.exit(0)

    logger.info("Starting FinOps Audit...")

    # 1. Analyze usage logs
    logger_instance = FinOpsLogger(sprint_dir=repo_root / ".sprint")
    current_spend = logger_instance.get_total_spend()

    logger.info(f"Current Sprint Estimated Spend: ${current_spend:.4f}")

    is_valid, msg = guardian.check_sprint_budget(current_spend)
    if not is_valid:
        logger.error(f"FinOps Violation: {msg}")
        sys.exit(1)

    logger.info(msg)

    # 2. Check for high-cost artifacts (Placeholder)
    # e.g., video files in .sprint/media/
    media_dir = repo_root / ".sprint" / "media"

    logger.info("FinOps Audit Passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
