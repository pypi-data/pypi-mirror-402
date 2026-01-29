"""
Ansible-specific tool implementations.
"""

import os
import subprocess
import json
from typing import List, Optional, Dict, Any
from coauthor.modules.tool_utils import build_tool_command, execute_tool_command


def ansible_lint(
    project: Dict[str, Any], paths: List[str], logger, config_file: Optional[str] = None
) -> Dict[str, Any]:
    """Run ansible-lint on specified paths.

    Args:
        project: Project configuration dictionary
        paths: List of paths to lint (files or directories)
        config_file: Optional path to ansible-lint configuration file

    Returns:
        Dictionary with lint results or error information
    """
    project_path = os.path.expanduser(project.get("path", os.getcwd()))

    # Check if ansible-lint is available using tool environment
    version_cmd = build_tool_command("ansible-lint --version", project)
    # try:
    result = execute_tool_command(version_cmd, project_path, project=project)
    if result.returncode != 0:
        raise RuntimeError(f"ansible-lint is not available in the environment: {result}")

    # Build command parts
    cmd_parts = ["ansible-lint", "--format", "json", "--nocolor"]

    # Check for .ansible-lint config file in project root if no config_file specified
    if not config_file:
        default_config = os.path.join(project_path, ".ansible-lint")
        if os.path.exists(default_config):
            cmd_parts.extend(["-c", ".ansible-lint"])

    if config_file:
        config_path = os.path.join(project_path, config_file)
        if os.path.exists(config_path):
            cmd_parts.extend(["-c", config_file])

    # Use utility functions for environment setup
    base_command = " ".join(cmd_parts)
    cmd = build_tool_command(base_command, project)

    # Execute with environment setup
    result = execute_tool_command(cmd, project_path, project=project)
    logger.debug(f"ansible-lint executed: project_path: {project_path}, cmd: {cmd}, result: {result}")

    # Parse JSON output
    try:
        if result.stdout:
            lint_results = json.loads(result.stdout)
        else:
            lint_results = []
    except json.JSONDecodeError:
        # If JSON parsing fails, return raw output
        error_msg = {
            "status": "completed",
            "return_code": result.returncode,
            "message": result.stdout or result.stderr,
            "raw_output": True,
        }
        logger.error(f"JSON decode failed: error_msg:{error_msg}")
        return error_msg

    # Process results
    if result.returncode == 0:
        return {"status": "success", "message": "No linting issues found", "issues": []}

    return {
        "status": "completed",
        "message": f"Found {len(lint_results)} linting issue(s)",
        "issues": lint_results,
        "return_code": result.returncode,
    }


def ansible_module_doc(project: Dict[str, Any], module_name: str, output_format: str = "json") -> Dict[str, Any]:
    """Get documentation for an Ansible module.

    Args:
        project: Project configuration dictionary
        module_name: Name of the Ansible module (e.g., 'ansible.builtin.copy')
        output_format: Output format - 'json', 'yaml', or 'markdown'

    Returns:
        Dictionary with module documentation or error information
    """
    project_path = os.path.expanduser(project.get("path", os.getcwd()))

    try:
        # Check if ansible-doc is available using tool environment
        version_cmd = build_tool_command("ansible-doc --version", project)
        try:
            execute_tool_command(version_cmd, project_path, project=project)
        except subprocess.CalledProcessError:
            return {
                "status": "error",
                "message": "ansible-doc is not installed or not available in PATH. "
                "Install it with: pip install ansible",
            }

        # Build command based on format
        if output_format == "json":
            cmd_parts = ["ansible-doc", "-j", module_name]
        elif output_format == "yaml":
            cmd_parts = ["ansible-doc", "-t", "module", module_name]
        else:  # markdown or default
            cmd_parts = ["ansible-doc", module_name]

        # Use utility functions for environment setup
        base_command = " ".join(cmd_parts)
        cmd = build_tool_command(base_command, project)

        # Execute with environment setup
        result = execute_tool_command(cmd, project_path, project=project)

        # Parse output based on format
        if output_format == "json":
            try:
                doc_data = json.loads(result.stdout)
                return {"status": "success", "module": module_name, "format": "json", "documentation": doc_data}
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "message": "Failed to parse JSON output from ansible-doc",
                    "raw_output": result.stdout,
                }
        else:
            # Return as text for yaml/markdown formats
            return {"status": "success", "module": module_name, "format": output_format, "documentation": result.stdout}

    except subprocess.CalledProcessError as exception_error:
        return {
            "status": "error",
            "message": f"Module '{module_name}' not found or error retrieving documentation",
            "stderr": getattr(exception_error, "stderr", ""),
        }
    except FileNotFoundError:
        return {"status": "error", "message": "ansible-doc command not found. Install it with: pip install ansible"}
    except Exception as exception_error:
        return {"status": "error", "message": f"Error running ansible-doc: {str(exception_error)}"}
