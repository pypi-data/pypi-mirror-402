import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional
from ..services.dispatcher import TaskDispatcher, DispatchResult
from ..services.delegation_service import DelegationService, DelegationSession
from rich.console import Console

console = Console()

class LocalWorktreeDispatcher(TaskDispatcher):
    """
    Dispatches tasks to a local isolated Git worktree.
    Wraps the existing DelegationService logic.
    """

    async def dispatch(self, task_id: str, command: str, context_path: str, env_vars: Dict[str, str]) -> DispatchResult:
        try:
            service = DelegationService()
            
            # Register task (this might be redundant if ID is provided, but safe)
            # In the new flow, we assume task_id is already determining the worktree name
            
            session = service.create_session(task_id=task_id, command=command)
            # Inject env vars if needed - primarily implied by the context
            
            # Start session (creates worktree)
            connection_info = await service.start_session(session)
            
            return DispatchResult(
                task_id=task_id,
                status="running",
                output=f"Task delegated to worktree: {session.worktree_path}",
                metadata={
                    "session_id": session.id,
                    "worktree_path": str(session.worktree_path),
                    "backend": "local_worktree"
                }
            )
        except Exception as e:
            return DispatchResult(
                task_id=task_id,
                status="failed",
                error=str(e)
            )

    async def get_status(self, task_id: str) -> DispatchResult:
        service = DelegationService()
        # task_id here corresponds to the session_id in DelegationService
        # or we scan for it. Assuming task_id == session_id for simplicity 
        # or we need a lookup. For now, assuming direct mapping.
        
        session = service.get_session(task_id)
        if not session:
            return DispatchResult(task_id=task_id, status="unknown", error="Session not found")

        return DispatchResult(
            task_id=task_id,
            status=session.status,
            metadata={
                "session_id": session.id,
                "backend": "local_worktree"
            }
        )
