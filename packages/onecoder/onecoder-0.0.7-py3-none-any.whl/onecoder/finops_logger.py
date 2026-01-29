import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from onecoder.finops.focus_schema import FocusRecord, CostMetrics

class FinOpsLogger:
    """
    Logs usage metrics (tokens, cost, model) to a persistent file in the sprint context.
    Dedicated logger for FinOps compliance to avoid interfering with general CLI usage logs.
    Supports both legacy usage logging and new FOCUS-compliant schema.
    """

    def __init__(self, sprint_dir: str = ".sprint"):
        self.sprint_dir = Path(sprint_dir)
        self.log_file = self.sprint_dir / "finops_usage.jsonl"
        self.focus_log_file = self.sprint_dir / "focus_events.jsonl"
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.sprint_dir.exists():
            try:
                self.sprint_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

    def log_usage(self, model: str, tokens: int, cost: float, tool: str = "unknown"):
        """
        Logs a usage event (Legacy format).
        Also emits a FOCUS event for backward compatibility translation.
        """
        event = {
            "timestamp": time.time(),
            "model": model,
            "tokens": tokens,
            "cost": cost,
            "tool": tool
        }

        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(event) + "\n")

            # Auto-translate to FOCUS
            self._log_focus_shim(model, tokens, cost, tool)

        except Exception as e:
            # Silent fail to not disrupt flow
            print(f"[FinOpsLogger] Failed to log usage: {e}")

    def _log_focus_shim(self, model: str, tokens: int, cost: float, tool: str):
        """Internal helper to log a legacy event as a FOCUS record."""
        try:
            metrics = CostMetrics(compute_cost=cost)
            record = FocusRecord(
                provider="onecoder-legacy",
                resource_id=f"tool:{tool}",
                cost_metrics=metrics,
                tags={"model": model, "tokens": str(tokens)}
            )
            self.log_focus_event(record)
        except Exception:
            pass

    def log_focus_event(self, record: FocusRecord):
        """
        Logs a full FOCUS-compliant event.
        """
        try:
            with open(self.focus_log_file, "a") as f:
                f.write(record.to_json() + "\n")
        except Exception as e:
            print(f"[FinOpsLogger] Failed to log FOCUS event: {e}")

    def get_total_spend(self) -> float:
        """
        Calculates total spend from the log file.
        """
        total = 0.0
        if not self.log_file.exists():
            return total

        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            total += data.get("cost", 0.0)
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass

        return total
