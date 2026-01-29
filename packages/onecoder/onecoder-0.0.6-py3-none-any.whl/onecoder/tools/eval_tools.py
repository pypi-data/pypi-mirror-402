from ..evaluation.evals_engine import EvalsEngine
from typing import Optional
import json

def onecoder_evals_summary_tool(sprint_id: Optional[str] = None) -> str:
    """
    Returns aggregate metrics for the specified sprint (or active sprint).
    Useful for checking performance, cost, and alignment.
    """
    try:
        engine = EvalsEngine()
        summary = engine.get_summary_metrics(sprint_id)
        return json.dumps(summary, indent=2)
    except Exception as e:
        return f"Error fetching evals summary: {e}"

def onecoder_evals_performance_tool(sprint_id: Optional[str] = None) -> str:
    """
    Returns performance trends and recommendations based on TTU/TTR and costs.
    Helpful for identifying system logic bottlenecks and improving prompts.
    """
    try:
        engine = EvalsEngine()
        summary = engine.get_summary_metrics(sprint_id)
        # Basic heuristic-based recommendations
        recommendations = [
            "Maintain a TTU (Time to Understand) below 120s for optimal agility.",
            "Monitor cost per task to ensure efficiency."
        ]
        
        if summary.get("avg_ttu", 0) > 120:
            recommendations.append("HIGH TTU DETECTED: Consider providing more explicit context in initial prompts.")
        
        if summary.get("total_cost", 0) > 5.0: # Arbitrary threshold for demo
            recommendations.append("COST ALERT: Review tool usage patterns for potential optimizations.")

        return json.dumps({
            "metrics": summary,
            "recommendations": recommendations
        }, indent=2)
    except Exception as e:
        return f"Error fetching performance data: {e}"
