from typing import List, Optional
from google.adk.agents import LlmAgent, BaseAgent
from google.adk.models.lite_llm import LiteLlm
from ..tools import registry
from ..knowledge import ProjectKnowledge
from ..alignment import AlignmentEngine

def create_orchestrator_agent(model: LiteLlm, sub_agents: Optional[List[BaseAgent]] = None, sprint_id: Optional[str] = None) -> LlmAgent:
    """Create an orchestrator agent that routes to specialist agents or uses tools."""

    # Get available tools from registry for the prompt
    tool_descriptions = registry.get_tool_descriptions()

    # Load Project Knowledge (Governance & Context)
    pk = ProjectKnowledge()
    durable_context = pk.get_durable_context()
    agents_guidelines = durable_context.get("agents_guidelines", "")
    cli_knowledge = pk.get_cli_knowledge()

    governance_section = ""
    if agents_guidelines:
        # Use quadruple braces and concatenation (not f-strings) for intermediate sections
        # to ensure they survive the final f-string interpolation as double braces.
        safe_guidelines = agents_guidelines.replace("{", "{{{{").replace("}", "}}}}")
        governance_section = "\n\nGOVERNANCE & POLICY (Must Follow):\n" + safe_guidelines + "\n"

    # Alignment & Plan Injection
    alignment_section = ""
    if sprint_id:
        alignment = AlignmentEngine()
        # We use 'orchestrator' context to get a high-level plan
        unified_plan = alignment.generate_unified_plan(sprint_id, context="orchestrator")
        safe_plan = unified_plan.replace("{", "{{{{").replace("}", "}}}}")
        alignment_section = "\n\nCURRENT SPRINT CONTEXT & PLAN:\n" + safe_plan + "\n"
    else:
        alignment_section = "\n\nNO SPRINT CONTEXT DETECTED. You are operating in a detached state.\n"

    # Collect and prepare tools from registry for the agent
    all_registered_tools = registry.list_tools()
    tools = []
    for t in all_registered_tools:
        # Ensure function name matches registry entry for ADK discovery
        f = t.func
        try:
            f.__name__ = t.name
        except (AttributeError, TypeError):
            pass
        tools.append(f)

    return LlmAgent(
        name="orchestrator_agent",
        model=model,
        sub_agents=sub_agents or [],
        tools=tools,
        instruction=(
            f"{governance_section}\n"
            "## CRITICAL CONSTRAINTS\n"
            "1. **OneCoder-First Rule**: For ANY inquiry about sprints, tasks, or alignment, you MUST use the `onecoder_sprint_status` or `onecoder_task_list` tool FIRST. Do NOT delegate to sub-agents for this information.\n"
            "2. **No Phantom Delegation**: Do not transfer to a sub-agent if a direct tool (e.g., `onecoder_sprint_status`, `onecoder`, `shell_executor`, `read_file`) can solve the request locally.\n"
            "3. **Plan Mode**: Before taking action, verify if the request can be solved by running a OneCoder tool.\n\n"
            "## IDENTITY & MISSION\n"
            "You are the OneCoder Orchestrator, a high-level coordination agent. Your mission is to solve tasks efficiently by prioritizing local tools before delegating complexity.\n"
            f"{alignment_section}\n"
            "## DECISION HIERARCHY\n"
            "1. **Query Tools**: Use `onecoder_sprint_status` for sprint metadata and `onecoder_task_list` for tasks.\n"
            "2. **Code Intelligence**: Use `onecoder` with 'code symbols <file>' to map dependencies.\n"
            "3. **I/O Tools**: Use `read_file` or `shell_executor` for direct file/env access.\n"
            "4. **Delegation**: Transfer to specialists ONLY for deep execution (e.g., 'refactor this class', 'write this feature', 'deep research on X').\n\n"
            "SELF-KNOWLEDGE (CLI Capabilities):\n"
            f"{cli_knowledge.replace('{', '{{{{').replace('}', '}}}}')}\n\n"
            "SPECIALIST SUB-AGENTS:\n"
            "- 'refactoring_specialist': Complex code modifications and architectural improvements.\n"
            "- 'documentation_specialist': Generating comprehensive docs and technical writing.\n"
            "- 'file_reader_agent': Bulk or complex file reading.\n"
            "- 'file_writer_agent': Applying multi-line changes and creating new components.\n"
            "- 'research_agent': Semantic search and broad codebase indexing.\n\n"
            "EXTERNAL CAPABILITIES:\n"
            "- 'onecoder_sprint_status': PRIMARY tool for current sprint info.\n"
            "- 'onecoder_task_list': PRIMARY tool for task details.\n"
            "- 'onecoder': Generic OneCoder CLI access.\n"
            "- 'shell_executor': System-level queries.\n\n"
            "AVAILABLE TOOLS:\n"
            f"{tool_descriptions}\n\n"
            "RESPONSE STYLE:\n"
            "Maintain a professional engineer tone. Start your thinking with 'PLAN: ...' to justify your tool/agent selection."
        ),
        output_key="final_response",
    )
