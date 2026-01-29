import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import mlflow
from mlflow.entities import ViewType

class EvalsEngine:
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root:
            self.repo_root = repo_root
        else:
            self.repo_root = self._find_repo_root()
        
        self.finops_file = self.repo_root / ".sprint" / "finops_usage.jsonl"
        self.mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", f"file:{self.repo_root}/mlruns")
        mlflow.set_tracking_uri(self.mlflow_uri)

    def _find_repo_root(self) -> Path:
        current = Path.cwd().absolute()
        while current != current.parent:
            if (current / ".git").exists() or (current / ".sprint").exists():
                return current
            current = current.parent
        return Path.cwd().absolute()

    def get_summary_metrics(self, sprint_id: Optional[str] = None) -> Dict[str, Any]:
        """Aggregates cost, tool usage, and timing for a sprint."""
        if not sprint_id:
            sprint_id = os.getenv("ACTIVE_SPRINT_ID", "unknown")

        costs = self._get_finops_summary(sprint_id)
        traces = self._get_trace_summaries(sprint_id)
        metrics = self._get_sprint_metrics(sprint_id)
        quality = self._get_quality_indicators(sprint_id)

        return {
            "sprint_id": sprint_id,
            "total_cost": costs.get("total_cost", 0.0),
            "total_tokens": costs.get("total_tokens", 0),
            "tool_usage": traces.get("tool_counts", {}),
            "avg_ttu": metrics.get("avg_ttu", 0),
            "avg_ttr": metrics.get("avg_ttr", 0),
            "review_pass_rate": quality.get("pass_rate", 0.0),
            "timestamp": time.time()
        }

    def _get_finops_summary(self, sprint_id: str) -> Dict[str, Any]:
        total_cost = 0.0
        total_tokens = 0
        if not self.finops_file.exists():
            return {}

        try:
            with open(self.finops_file, "r") as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    # Note: currently finops doesn't tag sprint_id per line, 
                    # assuming global file for now or filtering by timestamp if needed.
                    total_cost += data.get("cost", 0.0)
                    total_tokens += data.get("tokens", 0)
        except Exception:
            pass
        
        return {"total_cost": total_cost, "total_tokens": total_tokens}

    def _get_trace_summaries(self, sprint_id: str) -> Dict[str, Any]:
        tool_counts = {}
        try:
            experiment = mlflow.get_experiment_by_name("OneCoder-CLI")
            if not experiment:
                return {"tool_counts": {}}

            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"attributes.tag.sprint_id = '{sprint_id}'",
                run_view_type=ViewType.ACTIVE_ONLY
            )

            # This search_runs returns a pandas DataFrame if available, 
            # but we'll handle it generically or via MLflow client for more control.
            client = mlflow.tracking.MlflowClient()
            runs = client.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"tags.sprint_id = '{sprint_id}'"
            )

            for run in runs:
                # Aggregate tool usage from attributes or spans if we logged them
                # For now, let's just count runs as a proxy or extract from tags if we added them
                pass
        except Exception:
            pass
        
        return {"tool_counts": tool_counts}

    def _get_sprint_metrics(self, sprint_id: str) -> Dict[str, Any]:
        sprint_dir = self.repo_root / ".sprint" / sprint_id
        sprint_json = sprint_dir / "sprint.json"
        
        if not sprint_json.exists():
            return {}

        try:
            with open(sprint_json, "r") as f:
                data = json.load(f)
            
            tasks = data.get("tasks", [])
            ttus = [t.get("ttuSeconds") for t in tasks if t.get("ttuSeconds") is not None]
            # TTR calculation (completedAt - startedAt)
            ttrs = []
            for t in tasks:
                start = t.get("startedAt")
                end = t.get("completedAt")
                if start and end:
                    try:
                        # Assuming ISO format
                        from datetime import datetime
                        d_start = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        d_end = datetime.fromisoformat(end.replace('Z', '+00:00'))
                        ttrs.append((d_end - d_start).total_seconds())
                    except Exception:
                        continue

            return {
                "avg_ttu": sum(ttus) / len(ttus) if ttus else 0,
                "avg_ttr": sum(ttrs) / len(ttrs) if ttrs else 0
            }
        except Exception:
            return {}

    def _get_quality_indicators(self, sprint_id: str) -> Dict[str, Any]:
        review_file = self.repo_root / ".onecoder" / "review_state.json"
        if not review_file.exists():
            return {"pass_rate": 0.0}

        try:
            with open(review_file, "r") as f:
                data = json.load(f)
            # This is currently just the LATEST review. 
            # In a real system, we'd want a history of reviews.
            passed = 1.0 if data.get("pass") else 0.0
            return {"pass_rate": passed}
        except Exception:
            return {"pass_rate": 0.0}

    def get_consolidated_trace(self, session_id: str) -> List[Dict[str, Any]]:
        """Returns all events (LLM calls, tool usage) for a specific session."""
        events = []
        try:
            client = mlflow.tracking.MlflowClient()
            experiment = mlflow.get_experiment_by_name("OneCoder-CLI")
            if not experiment:
                return []

            runs = client.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"tags.session_id = '{session_id}'"
            )

            for run in runs:
                # Extract span data if using MLflow Tracing (preview feature)
                # or just use run data / artifacts
                run_data = {
                    "run_id": run.info.run_id,
                    "start_time": run.info.start_time,
                    "params": run.data.params,
                    "metrics": run.data.metrics,
                    "tags": run.data.tags
                }
                events.append(run_data)
            
            # Sort by timestamp
            events.sort(key=lambda x: x["start_time"])
        except Exception:
            pass
        
        return events
