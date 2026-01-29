# onecoder/tools/external_tools.py

import subprocess
import os
from ..governance.guardian import GovernanceGuardian

def shell_executor_tool(command: str) -> str:
    """
    Executes a shell command and returns its output (stdout and stderr).
    Use this for running general system commands, testing, or querying tools.

    Args:
        command: The full shell command to execute.

    Returns:
        The command output or an error message.
    """
    try:
        # OWASP LLM Risk Check
        # Resolve path to governance.yaml relative to repository root
        # onecoder-cli/onecoder/tools/external_tools.py -> ../../../governance.yaml
        gov_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "governance.yaml"))

        # Instantiate Guardian on demand
        local_guardian = GovernanceGuardian(gov_path)

        is_safe, message = local_guardian.validate_tool_execution("shell_execute", {"command": command})
        if not is_safe:
            return f"GOVERNANCE BLOCK: {message}. Please verify 'governance.yaml' policies."

        # Run the command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        
        raw_response = output or f"Command exited with code {result.returncode}"

        # OWASP LLM Output Validation
        is_safe, message = local_guardian.validate_output(raw_response)
        if not is_safe:
            return f"GOVERNANCE BLOCK: {message}"

        if not output and result.returncode == 0:
            return "Command executed successfully with no output."

        return raw_response

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"An error occurred while executing the command: {e}"


def gemini_ask_tool(query: str) -> str:
    """
    Executes a Gemini CLI command ('gemini ask') for general queries.
    Note: For image generation (nanobanana), inform the user that it must be done 
    interactively within the Gemini TUI.

    Args:
        query: The query or instruction to pass to 'gemini ask'.

    Returns:
        The result from Gemini CLI or an error/guidance message.
    """
    # Check if the query is about image generation
    image_keywords = ["image", "generate", "draw", "picture", "nanobanana"]
    if any(keyword in query.lower() for keyword in image_keywords):
        return (
            "To generate images with 'nanobanana', you must use the Gemini TUI. "
            "Run 'gemini' in your terminal and use the interactive prompt there."
        )

    try:
        # Construct the 'gemini ask' command
        # We escape single quotes in the query to avoid shell injection issues
        escaped_query = query.replace("'", "'\\''")
        command = f"gemini ask '{escaped_query}'"
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60, # Gemini might take longer
        )

        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error running gemini: {result.stderr}"

    except subprocess.TimeoutExpired:
        return "Error: Gemini command timed out."
    except Exception as e:
        return f"An error occurred while running Gemini: {e}"


def onecoder_sprint_status_tool() -> str:
    """
    Returns the current sprint status, active tasks, and alignment information.
    Use this as the FIRST step for any question about 'the sprint', 'current tasks', or 'alignment'.
    """
    return onecoder_tool("sprint status")


def onecoder_task_list_tool() -> str:
    """
    Returns a detailed list of all tasks in the current sprint.
    """
    return onecoder_tool("task list")


def onecoder_tool(command: str) -> str:
    """
    Executes a OneCoder CLI command (e.g., 'onecoder code symbols').
    Note: For 'sprint status' or 'task list', use the dedicated tools instead.

    Args:
        command: The subcommand to run (e.g., 'doctor environment', 'code symbols <file>').
                 Do NOT include the 'onecoder' prefix.

    Returns:
        The command output or an error message.
    """
    try:
        # Construction 'onecoder <command>'
        # We assume 'onecoder' is available in the PATH or we use 'uv run onecoder'
        full_command = f"onecoder {command}"
        
        # Governance check (reusing shell_execute policy for now or specific onecoder policy)
        gov_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "governance.yaml"))
        local_guardian = GovernanceGuardian(gov_path)
        
        is_safe, message = local_guardian.validate_tool_execution("shell_execute", {"command": full_command})
        if not is_safe:
            return f"GOVERNANCE BLOCK: {message}"

        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
            
        return output or "Command executed successfully with no output."

    except Exception as e:
        return f"Error running onecoder command: {e}"
