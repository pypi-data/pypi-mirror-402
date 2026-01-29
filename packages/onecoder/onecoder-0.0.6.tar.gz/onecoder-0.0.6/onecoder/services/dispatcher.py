from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import os

@dataclass
class DispatchResult:
    """Standardized result from a dispatched task."""
    task_id: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskDispatcher(ABC):
    """Abstract base class for dispatching tasks to various isolation backends."""

    @abstractmethod
    async def dispatch(self, task_id: str, command: str, context_path: str, env_vars: Dict[str, str]) -> DispatchResult:
        """
        Dispatch a task to the backend.
        
        Args:
            task_id: Unique identifier for the task.
            command: The command/code to execute.
            context_path: Path to the local context (e.g., repo root).
            env_vars: Environment variables to inject.
            
        Returns:
            DispatchResult containing status and metadata.
        """
        pass

    @abstractmethod
    async def get_status(self, task_id: str) -> DispatchResult:
        """Retrieve the current status of a dispatched task."""
        pass

class DispatcherFactory:
    """Factory to create the appropriate dispatcher based on configuration."""
    
    @staticmethod
    def get_dispatcher(isolation_type: str) -> TaskDispatcher:
        if isolation_type == "local":
            # Lazy import to avoid circular dependencies
            from .dispatchers.local_worktree import LocalWorktreeDispatcher
            return LocalWorktreeDispatcher()
        elif isolation_type == "cloudflare":
            from .dispatchers.cloudflare_rpc import CloudflareRpcDispatcher
            return CloudflareRpcDispatcher()
        elif isolation_type == "container":
            # Placeholder for future Docker implementation
            raise NotImplementedError("Container isolation not yet implemented.")
        else:
            raise ValueError(f"Unknown isolation type: {isolation_type}")
