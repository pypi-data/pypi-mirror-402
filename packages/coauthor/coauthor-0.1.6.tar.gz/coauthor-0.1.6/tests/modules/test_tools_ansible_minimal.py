"""
Minimal tests for Ansible-specific tools to verify Bug C2-1203 fix.
"""

import pytest
from unittest.mock import Mock, patch
import subprocess
import json
from coauthor.modules.tools.ansible import ansible_lint, ansible_module_doc


def test_ansible_lint_accepts_project_dict():
    """Test that ansible_lint accepts project dict parameter."""
    with patch("coauthor.modules.tools.ansible.build_tool_command") as mock_build:
        with patch("coauthor.modules.tools.ansible.execute_tool_command") as mock_execute:
            mock_build.return_value = "version_cmd"
            mock_execute.side_effect = subprocess.CalledProcessError(1, "ansible-lint")

            project = {"name": "test", "path": "/fake/project"}
            result = ansible_lint(project, ["playbook.yml"])

            # Should get error about not installed
            assert result["status"] == "error"
            assert "not installed" in result["message"]


def test_ansible_module_doc_accepts_project_dict():
    """Test that ansible_module_doc accepts project dict parameter."""
    with patch("coauthor.modules.tools.ansible.build_tool_command") as mock_build:
        with patch("coauthor.modules.tools.ansible.execute_tool_command") as mock_execute:
            mock_build.return_value = "version_cmd"
            mock_execute.side_effect = subprocess.CalledProcessError(1, "ansible-doc")

            project = {"name": "test", "path": "/fake/project"}
            result = ansible_module_doc(project, "ansible.builtin.copy")

            # Should get error about not installed
            assert result["status"] == "error"
            assert "not installed" in result["message"]
