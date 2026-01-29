import mlflow
import os
import functools
import time
import json
from typing import Optional, Dict, Any, List
import litellm
from .finops_logger import FinOpsLogger
from .governance.finops_guardian import FinOpsGuardian

_tracing_enabled = False

def _log_litellm_success(kwargs, response_obj, start_time, end_time):
    """
    LiteLLM success callback for traceability and FinOps.
    """
    if not _tracing_enabled:
        return
        
    try:
        usage = response_obj.get("usage", {})
        model = kwargs.get("model", "unknown")
        
        # 1. FinOps Logging
        guardian = FinOpsGuardian()
        cost = guardian.estimate_cost(model, usage.get("total_tokens", 0))
        
        # Log to local finops file
        finops_logger = FinOpsLogger()
        finops_logger.log_usage(model, usage.get("total_tokens", 0), cost, tool="llm_call")
        
        # 2. MLflow Logging
        with mlflow.start_span(name=f"llm:{model}", span_type="llm") as span:
            # Format inputs/outputs for MLflow
            messages = kwargs.get("messages", [])
            span.set_inputs({"messages": messages})
            
            output = ""
            if hasattr(response_obj, "choices") and response_obj.choices:
                output = response_obj.choices[0].message.content
            elif isinstance(response_obj, dict):
                output = response_obj.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            span.set_outputs({"response": output})
            span.set_attributes({
                "model": model,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "cost": cost,
                "latency_sec": end_time - start_time,
                "session_id": os.getenv("ACTIVE_SESSION_ID", "unknown"),
                "sprint_id": os.getenv("ACTIVE_SPRINT_ID", "unknown")
            })
            
    except Exception as e:
        # Silent fail
        pass

def setup_tracing(tracking_uri: Optional[str] = None):
    """
    Initializes MLflow tracing and LiteLLM callbacks for OneCoder.
    """
    global _tracing_enabled

    # Silence MLflow/SQLAlchemy "UBER" warning for SQLite
    os.environ["MLFLOW_SQLALCHEMY_SILENCE_UBER_WARNING"] = "1"
    
    import warnings
    warnings.filterwarnings("ignore", category=FutureWarning, module="mlflow.*")
    
    if not tracking_uri:
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")

    try:
        # Ensure directory exists if it's a file URI
        if tracking_uri.startswith("file:"):
            log_path = Path(tracking_uri[5:])
            log_path.mkdir(parents=True, exist_ok=True)

        mlflow.set_tracking_uri(tracking_uri)
        experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "OneCoder-CLI")
        mlflow.set_experiment(experiment_name)
        
        # Register LiteLLM callbacks
        litellm.success_callback = [_log_litellm_success]
        
        _tracing_enabled = True
        
    except Exception as e:
        print(f"Warning: Failed to initialize MLflow tracing: {e}")
        _tracing_enabled = False

def trace_span(name: str = None, span_type: str = "chain"):
    """
    Decorator to trace a function as an MLflow span.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not _tracing_enabled:
                return func(*args, **kwargs)

            span_name = name or func.__name__
            with mlflow.start_span(name=span_name, span_type=span_type) as span:
                try:
                    # Capture some inputs (careful with secrets or large objects)
                    inputs = {}
                    if args: inputs["args"] = str(args[:3]) # Truncated
                    if kwargs: inputs["kwargs"] = {k: str(v)[:100] for k, v in kwargs.items()}
                    span.set_inputs(inputs)

                    result = func(*args, **kwargs)

                    # Log outputs
                    span.set_outputs({"result": str(result)[:500]})
                    span.set_attributes({
                        "session_id": os.getenv("ACTIVE_SESSION_ID", "unknown"),
                        "sprint_id": os.getenv("ACTIVE_SPRINT_ID", "unknown")
                    })
                    return result
                except Exception as e:
                    span.set_status("ERROR")
                    span.set_attributes({"error": str(e)})
                    raise e
        return wrapper
    return decorator

from pathlib import Path
