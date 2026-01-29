import subprocess
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# ADK Imports
try:
    from google.adk.agents import LlmAgent
    from google.adk.models.lite_llm import LiteLlm
except ImportError:
    # Fallback/Mock if ADK not present
    LlmAgent = None
    LiteLlm = None

from .tools.kit_tools import kit_index_tool, kit_symbols_tool, kit_file_tree_tool
from .tools.coverage_tool import coverage_scanner_tool
from .llm import LLMClient # keep for fallback

try:
    from ai_sprint.state import SprintStateManager
    from ai_sprint.policy import PolicyEngine
    from ai_sprint.trace import trace_specifications
except ImportError as e:
    SprintStateManager = None
    PolicyEngine = None
    trace_specifications = None

console = Console()

class CodeReviewer:
    def __init__(self, project_root: Optional[str] = None):
        if project_root:
            self.project_root = Path(project_root).absolute()
        else:
            # Try to find project root by looking for .git
            current = Path.cwd().absolute()
            while current != current.parent:
                if (current / ".git").exists():
                    self.project_root = current
                    break
                current = current.parent
            else:
                self.project_root = Path.cwd().absolute()
        
        self.console = Console()
        self.use_agent = (LlmAgent is not None)

    def _get_git_diff(self, target: str = "main") -> str:
        """Get the git diff for the review context."""
        try:
            # If local changes (staged or unstaged)
            res = subprocess.run(
                ["git", "diff", target], capture_output=True, text=True
            )
            return res.stdout
        except Exception:
            return ""

    def _get_sprint_context(self) -> Dict[str, Any]:
        """Fetch active sprint context."""
        if not SprintStateManager:
            return {}
        
        # Try to find active sprint
        sprint_dir = self.project_root / ".sprint"
        if not sprint_dir.exists():
            return {}
            
        # Simplified: find first active sprint
        for item in sprint_dir.iterdir():
            if item.is_dir() and item.name.startswith("0"):
                 # Check status
                status_file = item / ".status"
                if not status_file.exists() or status_file.read_text().strip() == "Active":
                    manager = SprintStateManager(item)
                    state = manager.load()
                    return {
                        "goal": state.get("metadata", {}).get("goal", "Unknown Goal"),
                        "active_task": state.get("tasks", [{}])[0] if state.get("tasks") else {},
                    }
        return {}


    def _get_governance_rules(self) -> str:
        """Read governance.yaml."""
        gov_file = self.project_root / "governance.yaml"
        if gov_file.exists():
            return gov_file.read_text()
        return "No governance.yaml found."

    def _get_spec_tracing(self) -> str:
        """Get specification tracing data."""
        if not trace_specifications:
            return "Spec tracing not available."
        
        try:
            trace_map = trace_specifications(self.project_root, limit=50)
            return json.dumps(trace_map, indent=2)
        except Exception as e:
            return f"Error tracing specifications: {e}"

    def _get_coverage_report(self) -> str:
        """Get test coverage report."""
        try:
            return coverage_scanner_tool(str(self.project_root))
        except Exception as e:
            return f"Error scanning coverage: {e}"

    def _get_slop_analysis(self) -> str:
        """Analyze code complexity using tldr."""
        try:
            # Run tldr complexity on changed files
            result = subprocess.run(
                ["onecoder", "tldr", "complexity", "."],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout if result.returncode == 0 else "Complexity analysis unavailable."
        except Exception as e:
            return f"Error analyzing complexity: {e}"

    def review(self, pr_id: Optional[str] = None, local: bool = False, dry_run: bool = False):
        """Perform a policy-grounded review.
        
        Args:
            pr_id: Pull request ID (for GitHub integration)
            local: Review local changes instead of PR
            dry_run: Output raw context data without LLM review
        """
        self.console.print("[cyan]Gathering Context Triad (Code, Intent, Law)...[/cyan]")

        # 1. Code (The Change)
        diff = self._get_git_diff("HEAD" if local else "main")
        if not diff:
            self.console.print("[yellow]No code changes detected.[/yellow]")
            return

        # 2. Intent (Sprint Context)
        sprint_ctx = self._get_sprint_context() or {}
        goal = sprint_ctx.get("goal", "Unknown Goal")
        active_task_obj = sprint_ctx.get("active_task") or {}
        active_task = active_task_obj.get("title", "Unknown Task")

        # 3. Law (Governance)
        rules = self._get_governance_rules()

        # 4. Spec Tracing
        spec_trace = self._get_spec_tracing()

        # 5. Test Coverage
        coverage_report = self._get_coverage_report()

        # 6. Slop Analysis (Complexity)
        slop_analysis = self._get_slop_analysis()

        # 7. The Verdict (Deterministic L1 Status)
        verification_file = self.project_root / ".verification_results.json"
        l1_verdict = "No deterministic L1 verification results found."
        if verification_file.exists():
            try:
                l1_verdict = verification_file.read_text()
            except Exception as e:
                l1_verdict = f"Error reading L1 verification: {e}"

        # Construct System Prompt (Intelligence)
        system_prompt = f"""
You are the Governance Enforcer for OneCoder.

**THE RULES (governance.yaml)**:
{rules}

**THE INTENT (Sprint Context)**:
Goal: {goal}
Active Task: {active_task}

**SPEC TRACING**:
{spec_trace}

**TEST COVERAGE**:
{coverage_report}

**SLOP ANALYSIS (Complexity)**:
{slop_analysis}

**THE VERDICT (Deterministic L1 Status)**:
{l1_verdict}

**YOUR MISSION**:
1. **Spec Tracing**: Verify that the changes implement the specifications referenced in the commit trailers (Spec-Id). If no Spec-Id is found, flag this as a violation.
2. **Test Coverage**: Assess if the overall coverage is adequate (>= 60% is acceptable, >= 80% is excellent). Flag if coverage is below 60% or if critical files have no tests.
3. **Zero Slop Validation**: Identify functions with cyclomatic complexity > 10. Flag any "sloppy" code patterns (overly complex logic, missing error handling, etc.).
4. **L1 Failures**: If there are L1 failures in THE VERDICT, analyze the specific error logs and provide a mitigation plan.
5. **Governance Violations**: Check for banned files, architecture constraints, and other policy violations.
6. **Code Quality**: Assess security and performance concerns.
7. If the diff is ambiguous, USE YOUR TOOLS (kit_index, kit_symbols, coverage_scanner_tool) to investigate.

**OUTPUT FORMAT**:
You must ALWAYS respond with a Strict JSON object:
{{
  "pass": boolean,
  "spec_tracing": {{
    "aligned": boolean,
    "missing_specs": ["list of commits without Spec-Id"],
    "notes": "string"
  }},
  "test_coverage": {{
    "adequate": boolean,
    "overall_percentage": float,
    "notes": "string"
  }},
  "zero_slop": {{
    "clean": boolean,
    "complex_functions": ["list of functions with complexity > 10"],
    "notes": "string"
  }},
  "violations": ["list", "of", "strings"],
  "feedback": "markdown string summarizing the review",
  "mitigation_notes": "Technical notes for a coding agent to fix the violations. Be specific about files and changes needed."
}}
"""
        user_message = f"**THE CODE (Git Diff)**:\n{diff[:10000]} # Truncated"

        # Dry-run mode: output raw context
        if dry_run:
            context = {
                "diff_size": len(diff),
                "sprint_context": sprint_ctx,
                "spec_tracing": json.loads(spec_trace) if spec_trace.startswith("{") else spec_trace,
                "coverage": json.loads(coverage_report) if coverage_report.startswith("{") else coverage_report,
                "slop_analysis": slop_analysis,
            }
            self.console.print(Panel(
                json.dumps(context, indent=2),
                title="[cyan]Governance Review Context (Dry Run)[/cyan]",
                border_style="cyan"
            ))
            return

        self.console.print("[cyan]Consulting Intelligence (Agentic Reviewer)...[/cyan]")

        if self.use_agent:
            try:
                # Use Agentic flow
                asyncio.run(self._run_agent_review(system_prompt, user_message))
                return
            except Exception as e:
                self.console.print(f"[yellow]Agentic review failed ({e}). Falling back to simple LLM.[/yellow]")

        # Fallback to simple LLM
        self._run_simple_review(system_prompt, user_message)

    async def _run_agent_review(self, system_prompt: str, user_message: str):
        """Run the review using LlmAgent with tools."""
        model_name = os.getenv("ONECODER_MODEL", "openrouter/xiaomi/mimo-v2-flash:free")
        model = LiteLlm(model_name)
        
        agent = LlmAgent(
            name="reviewer_agent",
            model=model,
            instruction=system_prompt,
            tools=[kit_index_tool, kit_symbols_tool, kit_file_tree_tool, coverage_scanner_tool],
            output_key="final_response"
        )
        
        # Agent run
        # We append user message to history or as prompt
        # LlmAgent usually takes a user prompt
        response = await agent.run(user_message)
        
        # Parse output - Agent returns a string usually, hopefully JSON if instructed
        try:
            # Clean up markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            
            result = json.loads(clean_response)
            self._render_result(result)
        except json.JSONDecodeError:
             self.console.print(f"[red]Agent output is not valid JSON:[/red] {response}")
             sys.exit(1)

    def _run_simple_review(self, system_prompt: str, user_message: str):
        """Run legacy simple review."""
        llm = LLMClient()
        prompt = system_prompt + "\n\n" + user_message
        result = llm.generate_json(prompt)
        self._render_result(result)

    def _render_result(self, result: Dict[str, Any]):
        passed = result.get("pass", False)
        color = "green" if passed else "red"
        
        self.console.print(Panel(
            Markdown(result.get("feedback", "")),
            title=f"[{color}]Review Result: {'PASSED' if passed else 'FAILED'}[/{color}]",
            border_style=color
        ))
        
        mitigation_notes = result.get("mitigation_notes")
        if mitigation_notes:
             self.console.print("\n[bold yellow]Mitigation Notes for Agent:[/bold yellow]")
             self.console.print(mitigation_notes)
        
        # Persist state for delegation
        try:
            state_dir = self.project_root / ".onecoder"
            state_dir.mkdir(exist_ok=True)
            state_file = state_dir / "review_state.json"
            state_file.write_text(json.dumps(result, indent=2))
        except Exception as e:
            self.console.print(f"[dim]Failed to save review state: {e}[/dim]")

        if not passed:
            self.console.print("\n[bold red]Violations:[/bold red]")
            for v in result.get("violations", []):
                self.console.print(f"  ❌ {v}")
            sys.exit(1)
        else:
             self.console.print("\n[bold green]Policy Checks Passed.[/bold green]")
