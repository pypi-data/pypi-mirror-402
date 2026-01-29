from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Literal
import time
import json

@dataclass
class CostMetrics:
    """Breakdown of costs compliant with FOCUS."""
    compute_cost: float = 0.0
    data_cost: float = 0.0
    network_cost: float = 0.0
    license_cost: float = 0.0

    @property
    def total_cost(self) -> float:
        return self.compute_cost + self.data_cost + self.network_cost + self.license_cost

@dataclass
class AllocationSplit:
    """A single split target in an allocation."""
    entity: str
    share: float  # 0.0 to 1.0 or fixed amount depending on method

@dataclass
class AllocationMethod:
    """Logic for splitting costs."""
    method: Literal["percentage", "fixed", "weighted"] = "percentage"
    splits: List[AllocationSplit] = field(default_factory=list)

@dataclass
class FocusRecord:
    """
    A persistent cost record compliant with FOCUS 1.3 schema concepts.
    """
    provider: str  # e.g., "onecoder-cli", "mcp-server"
    resource_id: str  # e.g., "skill:gtm-scout", "tool:read_file"
    timestamp: float = field(default_factory=time.time)
    cost_metrics: CostMetrics = field(default_factory=CostMetrics)
    allocation: Optional[AllocationMethod] = None
    tags: Dict[str, str] = field(default_factory=dict)

    # Optional context fields
    sprint_id: Optional[str] = None
    task_id: Optional[str] = None
    user_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """Serializes the record to a dictionary."""
        data = asdict(self)
        # Flatten total cost for easier querying if needed, but keeping structured for now
        data['total_cost'] = self.cost_metrics.total_cost
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
