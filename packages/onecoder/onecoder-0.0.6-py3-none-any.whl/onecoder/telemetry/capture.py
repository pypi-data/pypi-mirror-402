import os
import json
import datetime
import sqlite3
import asyncio
from typing import Any, List, Dict, Optional
from pathlib import Path
from ..api_client import get_api_client

class SessionCapture:
    """
    Captures session events (text, tool calls) for later distillation.
    """
    def __init__(self, directory: str = "."):
        self.directory = directory
        self.logs_dir = os.path.join(directory, ".sprint", "logs")
        
        self.current_session_id = None
        self.events: List[Dict[str, Any]] = []
        self.db_path = self._get_onedata_db_path()

    def _get_onedata_db_path(self) -> Optional[str]:
        """Locates the OneData SQLite database."""
        try:
            current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            # Traverse up to find repo root
            p = current_dir
            for _ in range(10):
                db_path = p / "packages" / "data" / "data.db"
                if db_path.exists():
                    return str(db_path)
                if (p / ".git").exists():
                    # Even if .git exists, we might be in a submodule or worktree,
                    # but check the path relative to this root anyway
                    if db_path.exists():
                        return str(db_path)
                if p == p.parent:
                    break
                p = p.parent
        except Exception:
            pass
        return None

    def _log_to_onedata(self, level: str, message: str):
        """Logs to the OneData SQLite database if available."""
        if not self.db_path:
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO pipeline_logs (level, message) VALUES (?, ?)",
                (level, message)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            # Fail silently to avoid disrupting the CLI session
            # print(f"Failed to log to OneData: {e}")
            pass

    def _ensure_db_initialized(self):
        """Ensures the pipeline_logs table exists."""
        if not self.db_path:
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_logs (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                  level TEXT NOT NULL,
                  message TEXT NOT NULL
                );
            """)
            conn.commit()
            conn.close()
        except Exception:
            pass

    def start_session(self, session_id: str):
        os.makedirs(self.logs_dir, exist_ok=True)
        self.current_session_id = session_id
        self.events = []
        self._ensure_db_initialized()

    def log_event(self, event_data: Dict[str, Any]):
        """Logs an event within the current session."""
        timestamp = datetime.datetime.now().isoformat()
        event_entry = {
            "timestamp": timestamp,
            "data": event_data
        }
        self.events.append(event_entry)

        # Log to OneData
        # We JSON dump the whole entry so context (timestamp) is preserved in the message
        self._log_to_onedata("INFO", json.dumps(event_entry))

    def log_decision(self, actor: str, action: str, reasoning: Dict[str, Any], policy_snapshot: Dict[str, Any] = None):
        """Logs a structured governance decision event."""
        self.log_event({
            "type": "decision_trace",
            "actor": actor,
            "action": action,
            "reasoning": reasoning,
            "policy_snapshot": policy_snapshot or {}
        })

    def sync_decision(self, actor: str, action: str, reasoning: Dict[str, Any], policy_snapshot: Dict[str, Any] = None):
        """Logs and immediately syncs a decision trace to the API."""
        self.log_decision(actor, action, reasoning, policy_snapshot)
        
        # Fire and forget sync (best effort)
        try:
            async def _sync():
                client = get_api_client()
                # Attempt to get token from current session (optional, might rely on env)
                # For now assume client auto-configuration or anonymous if allowed
                await client.post_trace({
                    "actor": actor,
                    "action": action,
                    "reasoning": reasoning,
                    "policySnapshot": policy_snapshot or {}
                })
            
            # Run in a new event loop if none exists, or just run_until_complete
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_sync())
            loop.close()
            # Note: In a complex async CLI app, this isolated loop might be risky, 
            # but for 'sprint commit' which is largely synchronous, it's fine.
        except Exception as e:
            # Squelch errors to avoid blocking the user flow
            pass

    def save_session(self):
        """Saves the current session logs to the .sprint/logs directory."""
        if not self.current_session_id:
            return
            
        filename = f"session_{self.current_session_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.logs_dir, filename)
        
        with open(filepath, "w") as f:
            json.dump({
                "session_id": self.current_session_id,
                "events": self.events
            }, f, indent=2)
        
        print(f"Session logs saved to {filepath}")
        
    def distill_patterns(self) -> str:
        """
        [v0.1.0 Mechanical] Implementation for pattern capture.
        In the future, this will use an LLM to extract reusable skills.
        """
        patterns = []
        for event in self.events:
            data = event.get("data", {})
            if "tool_call" in data:
                patterns.append(data["tool_call"])
        
        return f"Captured {len(patterns)} tool call patterns."

# Singleton instance for global use
capture_engine = SessionCapture()
