import os
from google.adk.agents import LlmAgent
from google.adk.models import Gemini, LiteLlm
from dotenv import load_dotenv

from .agents import (
    create_documentation_agent,
    create_orchestrator_agent,
    create_refactoring_agent,
    create_file_reader_agent,
    create_file_writer_agent,
    create_research_agent
)
from .config_manager import config_manager

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from .model_factory import get_model

# --- Agent Instances ---
_root_agent = None

def get_root_agent(sprint_id: str = None):
    # Always create a new agent if sprint_id is provided to ensure fresh context
    # Otherwise return cached global agent if available
    global _root_agent
    
    if sprint_id:
        return _create_agent_stack(sprint_id)
        
    if _root_agent is None:
        _root_agent = _create_agent_stack(None)
    return _root_agent

def _create_agent_stack(sprint_id: str = None):
    model = get_model()
    
    # Create specialist agents
    refactoring_agent = create_refactoring_agent(model)
    documentation_agent = create_documentation_agent(model)
    file_reader_agent = create_file_reader_agent(model)
    file_writer_agent = create_file_writer_agent(model)
    research_agent = create_research_agent(model)

    # Create the orchestrator as root_agent
    return create_orchestrator_agent(
        model,
        sub_agents=[
            refactoring_agent,
            documentation_agent,
            file_reader_agent,
            file_writer_agent,
            research_agent
        ],
        sprint_id=sprint_id
    )
