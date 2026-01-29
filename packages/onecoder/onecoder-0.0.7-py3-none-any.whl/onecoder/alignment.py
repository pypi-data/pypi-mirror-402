import os
import json
import subprocess
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from .model_factory import get_model

from .tracker import (
    auto_detect_sprint_id, AlignmentTracker, SPRINT_DIR
)

class AlignmentEngine:
    """
    Unified Governance Control Plane.
    Combines AlignmentTracker (roadmap), TLDRTool (structure), and Guidance (intent).
    """
    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or self._find_repo_root()
        self.tracker = AlignmentTracker(self.repo_root)
        self.state_file = self.repo_root / ".onecoder" / "alignment" / "state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Lazy load TLDR tool to avoid dependency issues if not needed
        self._tldr = None

    @property
    def tldr(self):
        if self._tldr is None:
            from .tools.tldr_tool import TLDRTool
            self._tldr = TLDRTool()
        return self._tldr

    def _find_repo_root(self) -> Path:
        current = Path.cwd().resolve()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        return Path.cwd().resolve()

    def check_alignment(self, sprint_id: str) -> Dict[str, Any]:
        """Performs a deep alignment check: Roadmap + Implementation + Intent."""
        roadmap = self.tracker.check_roadmap_alignment_agentic()
        
        # Scan component symbols if possible
        sprint_dir = self.repo_root / ".sprint" / sprint_id
        symbols = []
        if sprint_dir.exists():
             state_manager = SprintStateManager(sprint_dir)
             component = state_manager.get_component()
             if component:
                 comp_path = self.repo_root / component
                 if comp_path.exists():
                     symbols = self.tldr.scan_directory(str(comp_path))

        return {
            "roadmap": roadmap,
            "symbols_count": len(symbols),
            "status": roadmap.get("status", "unknown"),
            "timestamp": datetime.datetime.now().isoformat()
        }

    def generate_unified_plan(self, sprint_id: str, context: str = "task", goal: Optional[str] = None) -> str:
        """Generates a plan grounded in code structure and roadmap alignment."""
        from ai_sprint.guidance import GuidanceEngine
        guidance = GuidanceEngine(self.repo_root)
        base_prompt = guidance.generate_plan_prompt(context)
        
        # Fetch alignment context
        alignment = self.check_alignment(sprint_id)
        
        unified_prompt = [
            "# ONECODER UNIFIED PLAN",
            f"**Alignment Status**: {alignment['status']}",
            f"**Current Scope**: {alignment['roadmap'].get('aligned_items', [])}",
            "",
            f"**Goal**: {goal}" if goal else "",
            "",
            base_prompt,
            "",
            "## Code Context (TLDR)",
            f"Detected {alignment['symbols_count']} symbols in component scope.",
            "Ensure your implementation adheres to existing structural patterns."
        ]
        
        return "\n".join(unified_prompt)

    def get_token_budget_status(self) -> Dict[str, Any]:
        """Mock implementation of token budget tracking."""
        # In a real implementation, this would query a usage DB or API
        return {
            "consumed": 150000,
            "limit": 500000,
            "remaining": 350000,
            "percent": 30
        }

    def save_state(self, updates: Dict[str, Any]) -> None:
        """Persists alignment state to disk."""
        state = self.load_state()
        state.update(updates)
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=4)

    def load_state(self) -> Dict[str, Any]:
        """Loads alignment state from disk."""
        if not self.state_file.exists():
            return {"multi_task_queue": [], "current_run_id": None}
        with open(self.state_file, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"multi_task_queue": [], "current_run_id": None}

    def add_to_queue(self, task_id: str) -> None:
        """Adds a task to the multi-task session queue."""
        state = self.load_state()
        if task_id not in state["multi_task_queue"]:
            state["multi_task_queue"].append(task_id)
            self.save_state(state)

    def pop_next_task(self) -> Optional[str]:
        """Retrieves and removes the next task from the queue."""
        state = self.load_state()
        if state["multi_task_queue"]:
            next_task = state["multi_task_queue"].pop(0)
            self.save_state(state)
            return next_task
        return None

class SprintStateManager:
    # Adding a helper here since it's used by AlignmentEngine but defined elsewhere or planned
    def __init__(self, sprint_dir: Path):
        self.sprint_dir = sprint_dir
        self.state_file = sprint_dir / "sprint.json"

    def load(self) -> Dict[str, Any]:
        if not self.state_file.exists(): return {}
        with open(self.state_file, "r") as f: return json.load(f)

    def get_component(self) -> Optional[str]:
        return self.load().get("component")
