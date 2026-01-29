"""
Proof of Concept: OneCoder Orchestrator implemented using DSPy.
This demonstrates how the hardcoded prompt in `orchestrator_agent.py` can be replaced
by a structured Signature and Module.
"""
from typing import Dict, Any, List, Optional
try:
    import dspy
except ImportError:
    # Fallback for when dspy is not installed
    class MockDSPy:
        class Signature: pass
        class Module: pass
        class InputField:
            def __init__(self, **kwargs): pass
        class OutputField:
            def __init__(self, **kwargs): pass
        class ChainOfThought:
            def __init__(self, signature): pass
    dspy = MockDSPy()

class OrchestratorSignature(dspy.Signature):
    """
    You are the OneCoder Orchestrator. Your mission is to analyze user requests and coordinate agents.

    STRATEGY:
    1. Analyze: specific task vs research vs generic question.
    2. Delegate: choose the best specialist agent.
    3. Fallback: if no agent fits, use 'shell_executor' or 'gemini_ask'.

    Maintain a professional engineering tone.
    """

    # Inputs
    user_request = dspy.InputField(desc="The raw request from the user")
    governance_context = dspy.InputField(desc="Policy and guidelines that MUST be followed")
    available_tools = dspy.InputField(desc="List of available tools/agents and their capabilities")

    # Outputs
    thought_process = dspy.OutputField(desc="Reasoning step-by-step about the request and capabilities")
    delegation_decision = dspy.OutputField(desc="The name of the agent/tool to call (e.g., 'refactoring_specialist')")
    arguments = dspy.OutputField(desc="A JSON string of arguments for the tool")
    final_response_text = dspy.OutputField(desc="The message to display to the user explaining the action")


class OrchestratorModule(dspy.Module):
    def __init__(self):
        super().__init__()
        # ChainOfThought adds an implicit "Reasoning" field before the outputs
        self.prog = dspy.ChainOfThought(OrchestratorSignature)

    def forward(self, request: str, governance: str, tools_desc: str) -> Dict[str, Any]:
        """
        Executes the orchestrator logic.
        """
        # Call the LLM
        pred = self.prog(
            user_request=request,
            governance_context=governance,
            available_tools=tools_desc
        )

        # Return a structured dictionary that matches what LlmAgent expects
        return {
            "thought": pred.thought_process,
            "tool": pred.delegation_decision,
            "args": pred.arguments,
            "response": pred.final_response_text
        }

# Factory function to fit into existing registry (optional future step)
def create_dspy_orchestrator():
    from ..dspy_utils import configure_dspy
    configure_dspy()
    return OrchestratorModule()
