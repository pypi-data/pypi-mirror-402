"""
Utility functions for tool environment setup and command execution.

This module provides reusable utilities for tools that require shell environment
initialization, such as virtualenv activation or bashrc sourcing.
"""

import subprocess
from typing import Optional, Dict, Any


def _load_tool_environment(project: Dict[str, Any]) -> str:
    """Load tool_environment configuration from project config.

    Args:
        project: Project configuration dictionary

    Returns:
        Tool environment setup commands as a string, or empty string if not configured
    """
    if not isinstance(project, dict):
        return ""

    tool_env = project.get("tool_environment", "")
    # Handle None or empty values
    return tool_env if tool_env else ""


def _get_tool_shell(project: Dict[str, Any]) -> Optional[str]:
    """Get tool_shell configuration from project config.

    Args:
        project: Project configuration dictionary

    Returns:
        Path to shell executable, or None if not configured
    """
    if not isinstance(project, dict):
        return None

    return project.get("tool_shell", None)


def build_tool_command(base_command: str, project: Dict[str, Any]) -> str:
    """Build a tool command with environment setup prepended.

    Args:
        base_command: The base command to execute (e.g., "pytest tests/")
        project: Project configuration dictionary

    Returns:
        Complete command string with environment setup prepended
    """
    tool_env = _load_tool_environment(project)
    if tool_env:
        cmd = tool_env.strip() + "\n"
        cmd += base_command
        return cmd
    return base_command


def execute_tool_command(
    cmd: str, cwd: str, project: Optional[Dict[str, Any]] = None, shell: Optional[str] = None
) -> subprocess.CompletedProcess:
    """Execute a tool command with proper shell configuration.

    Args:
        cmd: Command string to execute
        cwd: Working directory for command execution
        project: Optional project configuration dictionary
        shell: Optional path to shell executable. If None, uses configured
               tool_shell from project or defaults to /bin/bash

    Returns:
        CompletedProcess instance with execution results

    Raises:
        subprocess.CalledProcessError: If command fails and check=True
        Exception: Other execution errors
    """
    # Determine which shell to use
    if shell is None and project is not None:
        shell = _get_tool_shell(project)

    # Build subprocess arguments
    run_kwargs = {
        "shell": True,
        "cwd": cwd,
        "capture_output": True,
        "text": True,
        "check": True,
    }

    # Use specified shell or default to /bin/bash for source command support
    if shell:
        run_kwargs["executable"] = shell
    else:
        # Default to /bin/bash to support source command
        run_kwargs["executable"] = "/bin/bash"

    return subprocess.run(cmd, **run_kwargs)
