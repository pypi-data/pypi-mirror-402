import yaml
import os
import json
import logging
from typing import Dict, Any, Tuple, Optional

class FinOpsGuardian:
    """
    Enforces FinOps policies including budget constraints and model selection.
    """

    # Mock pricing table (USD per 1M input/output tokens blended for simplicity)
    # In a real system, this would be fetched from an API or updated regularly.
    MODEL_PRICING = {
        "gpt-4o": 5.00,
        "claude-3-5-sonnet": 3.00,
        "gemini-1.5-pro": 3.50,
        "gemini-2.0-flash": 0.10,
        "gpt-3.5-turbo": 0.50,
    }

    def __init__(self, governance_path="governance.yaml"):
        self.governance_path = governance_path
        self.policy = self._load_policy()
        self.logger = logging.getLogger("onecoder.governance.finops")

    def _load_policy(self) -> Dict[str, Any]:
        """Loads the FinOps policy from governance.yaml."""
        if not os.path.exists(self.governance_path):
            return {}

        try:
            with open(self.governance_path, "r") as f:
                data = yaml.safe_load(f) or {}
                # Support both root-level and nested under 'policies'
                policy = data.get("finops")
                if not policy and "policies" in data:
                    policy = data["policies"].get("finops")
                return policy or {}
        except Exception as e:
            self.logger.error(f"Failed to load FinOps policy: {e}")
            return {}

    def is_enabled(self) -> bool:
        """Checks if FinOps governance is enabled."""
        return self.policy.get("enabled", False)

    def get_tool_metadata(self, manifest_path: str) -> Dict[str, Any]:
        """
        Reads the cost metadata from a tool's manifest.json.
        """
        if not os.path.exists(manifest_path):
            return {}
        try:
            with open(manifest_path, "r") as f:
                data = json.load(f)
                return data.get("cost_metadata", {})
        except Exception as e:
            self.logger.error(f"Failed to read tool manifest {manifest_path}: {e}")
            return {}

    def predict_tool_cost(self, manifest_path: str) -> float:
        """
        Predicts the cost of executing a tool based on its manifest.
        Returns a simplified estimated cost (e.g. fixed fee + avg compute).
        """
        metadata = self.get_tool_metadata(manifest_path)
        if not metadata:
            return 0.0

        # Simple prediction: base fee + average expected compute
        # In a real system, this would be more complex
        base_fee = metadata.get("base_fee", 0.0)
        avg_compute = metadata.get("average_compute_cost", 0.0)
        return base_fee + avg_compute

    def estimate_cost(self, model: str, tokens: int) -> float:
        """
        Estimates the cost of an operation based on model and token count.
        """
        price_per_million = self.MODEL_PRICING.get(model, 1.0) # Default to $1/1M if unknown
        return (tokens / 1_000_000) * price_per_million

    def validate_model_selection(self, model: str) -> Tuple[bool, str]:
        """
        Validates if the selected model is allowed by policy.
        """
        if not self.is_enabled():
            return True, "FinOps Policy disabled"

        model_policy = self.policy.get("model_policy", {})
        allowed_models = model_policy.get("allowed_models", [])

        if allowed_models and model not in allowed_models:
             return False, f"Model '{model}' is not in the allowed list: {allowed_models}"

        return True, "Model allowed"

    def validate_cost(self, estimated_cost: float, context: str = "task") -> Tuple[bool, str]:
        """
        Validates if the estimated cost is within limits.
        """
        if not self.is_enabled():
            return True, "FinOps Policy disabled"

        budget_policy = self.policy.get("budget_policy", {})
        approval_policy = self.policy.get("approval_policy", {})

        # Check approval threshold
        approval_threshold = approval_policy.get("require_approval_above_cost", 100.0)
        if estimated_cost > approval_threshold:
             return False, f"Estimated cost ${estimated_cost:.4f} exceeds approval threshold ${approval_threshold:.2f}. Human approval required."

        # Check per-task limit
        if context == "task":
            max_task_cost = budget_policy.get("max_cost_per_task", 1.0)
            if estimated_cost > max_task_cost:
                return False, f"Estimated cost ${estimated_cost:.4f} exceeds max cost per task ${max_task_cost:.2f}."

        return True, "Cost within limits"

    def check_sprint_budget(self, current_spend: float) -> Tuple[bool, str]:
        """
        Checks if the current sprint spend is within budget.
        """
        if not self.is_enabled():
            return True, "FinOps Policy disabled"

        budget_policy = self.policy.get("budget_policy", {})
        max_sprint_cost = budget_policy.get("max_cost_per_sprint", 10.0)

        if current_spend >= max_sprint_cost:
            return False, f"Sprint budget exceeded: ${current_spend:.2f} / ${max_sprint_cost:.2f}"

        return True, f"Sprint spend ${current_spend:.2f} is within budget ${max_sprint_cost:.2f}"
