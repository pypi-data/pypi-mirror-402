"""
Comprehensive tests for tool_utils module.

Tests cover:
- Loading tool_environment from project configuration dict
- Loading tool_shell from project configuration dict
- Building tool commands with environment setup
- Executing tool commands with proper shell configuration
- Multi-project configuration support
- Edge cases and error handling
"""

import pytest
import subprocess
from unittest.mock import Mock, patch
from coauthor.modules.tool_utils import (
    _load_tool_environment,
    _get_tool_shell,
    build_tool_command,
    execute_tool_command,
)


class TestLoadToolEnvironment:
    """Tests for _load_tool_environment function."""

    def test_load_environment_with_valid_config(self):
        """Test loading tool_environment from valid project config."""
        project = {
            "name": "my-project",
            "path": "/fake/project",
            "tool_environment": "source ~/.bashrc\nsource ~/.virtualenv/myenv/bin/activate\n",
        }

        result = _load_tool_environment(project)

        expected = "source ~/.bashrc\nsource ~/.virtualenv/myenv/bin/activate\n"
        assert result == expected

    def test_load_environment_without_tool_environment_key(self):
        """Test loading when tool_environment is not configured."""
        project = {"name": "my-project", "path": "/fake/project", "profile": "generic"}

        result = _load_tool_environment(project)

        assert result == ""

    def test_load_environment_with_empty_tool_environment(self):
        """Test loading when tool_environment is empty string."""
        project = {"name": "my-project", "path": "/fake/project", "tool_environment": ""}

        result = _load_tool_environment(project)

        assert result == ""

    def test_load_environment_with_multiline_environment(self):
        """Test loading multiline tool_environment."""
        project = {
            "name": "my-project",
            "path": "/fake/project",
            "tool_environment": (
                "source ~/.bashrc\n" "source ~/venvs/my-project/bin/activate\n" "export ANSIBLE_CONFIG=~/.ansible.cfg"
            ),
        }

        result = _load_tool_environment(project)

        assert "source ~/.bashrc" in result
        assert "source ~/venvs/my-project/bin/activate" in result
        assert "export ANSIBLE_CONFIG=~/.ansible.cfg" in result

    def test_load_environment_with_invalid_project_type(self):
        """Test handling when project is not a dict."""
        result = _load_tool_environment("not-a-dict")
        assert result == ""

        result = _load_tool_environment(None)
        assert result == ""

        result = _load_tool_environment([])
        assert result == ""

    def test_load_environment_with_none_value(self):
        """Test loading when tool_environment is None."""
        project = {"name": "my-project", "path": "/fake/project", "tool_environment": None}

        result = _load_tool_environment(project)

        assert result == ""


class TestGetToolShell:
    """Tests for _get_tool_shell function."""

    def test_get_tool_shell_with_valid_config(self):
        """Test getting tool_shell from valid project config."""
        project = {"name": "my-project", "path": "/fake/project", "tool_shell": "/bin/bash"}

        result = _get_tool_shell(project)

        assert result == "/bin/bash"

    def test_get_tool_shell_not_configured(self):
        """Test getting tool_shell when not configured."""
        project = {"name": "my-project", "path": "/fake/project", "profile": "generic"}

        result = _get_tool_shell(project)

        assert result is None

    def test_get_tool_shell_with_custom_shell(self):
        """Test getting custom shell path."""
        project = {"name": "my-project", "path": "/fake/project", "tool_shell": "/bin/zsh"}

        result = _get_tool_shell(project)

        assert result == "/bin/zsh"

    def test_get_tool_shell_with_invalid_project_type(self):
        """Test handling when project is not a dict."""
        result = _get_tool_shell("not-a-dict")
        assert result is None

        result = _get_tool_shell(None)
        assert result is None

        result = _get_tool_shell([])
        assert result is None

    def test_get_tool_shell_with_empty_value(self):
        """Test getting tool_shell with empty string value."""
        project = {"name": "my-project", "path": "/fake/project", "tool_shell": ""}

        result = _get_tool_shell(project)

        assert result == ""

    def test_get_tool_shell_with_none_value(self):
        """Test getting tool_shell when value is None."""
        project = {"name": "my-project", "path": "/fake/project", "tool_shell": None}

        result = _get_tool_shell(project)

        assert result is None


class TestBuildToolCommand:
    """Tests for build_tool_command function."""

    def test_build_command_with_environment(self):
        """Test building command with environment setup."""
        project = {
            "name": "my-project",
            "path": "/fake/project",
            "tool_environment": "source ~/.bashrc\nsource venv/bin/activate",
        }

        result = build_tool_command("pytest tests/", project)

        expected = "source ~/.bashrc\nsource venv/bin/activate\npytest tests/"
        assert result == expected

    def test_build_command_without_environment(self):
        """Test building command without environment setup."""
        project = {"name": "my-project", "path": "/fake/project"}

        result = build_tool_command("pytest tests/", project)

        assert result == "pytest tests/"

    def test_build_command_with_whitespace_environment(self):
        """Test building command with environment containing whitespace."""
        project = {"name": "my-project", "path": "/fake/project", "tool_environment": "  source ~/.bashrc  \n  "}

        result = build_tool_command("ansible-lint playbook.yml", project)

        # Should strip whitespace properly
        expected = "source ~/.bashrc\nansible-lint playbook.yml"
        assert result == expected

    def test_build_command_with_complex_base_command(self):
        """Test building command with complex base command."""
        project = {"name": "my-project", "path": "/fake/project", "tool_environment": "export PATH=/custom/bin:$PATH"}

        result = build_tool_command("ansible-lint --format json --nocolor playbook.yml", project)

        expected = "export PATH=/custom/bin:$PATH\nansible-lint --format json --nocolor playbook.yml"
        assert result == expected

    def test_build_command_preserves_base_command_format(self):
        """Test that base command format is preserved exactly."""
        project = {"name": "my-project", "path": "/fake/project"}

        base_command = "pytest --verbose --cov=src tests/"
        result = build_tool_command(base_command, project)

        assert result == base_command

    def test_build_command_with_empty_environment(self):
        """Test building command with empty tool_environment string."""
        project = {"name": "my-project", "path": "/fake/project", "tool_environment": ""}

        result = build_tool_command("pytest tests/", project)

        assert result == "pytest tests/"

    def test_build_command_with_none_environment(self):
        """Test building command when tool_environment is None."""
        project = {"name": "my-project", "path": "/fake/project", "tool_environment": None}

        result = build_tool_command("pytest tests/", project)

        assert result == "pytest tests/"

    def test_build_command_multi_project_scenario(self):
        """Test building commands for different projects with different environments."""
        project1 = {
            "name": "project1",
            "path": "/path/to/project1",
            "tool_environment": "source ~/venvs/project1/bin/activate",
        }
        project2 = {
            "name": "project2",
            "path": "/path/to/project2",
            "tool_environment": "source ~/venvs/project2/bin/activate",
        }

        result1 = build_tool_command("pytest tests/", project1)
        result2 = build_tool_command("pytest tests/", project2)

        assert "project1/bin/activate" in result1
        assert "project2/bin/activate" in result2
        assert result1 != result2


class TestExecuteToolCommand:
    """Tests for execute_tool_command function."""

    @patch("subprocess.run")
    def test_execute_command_with_default_bash(self, mock_run):
        """Test executing command with default /bin/bash."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        project = {"name": "my-project", "path": "/fake/project"}

        result = execute_tool_command("pytest tests/", "/fake/project", project=project)

        # Verify subprocess.run was called with correct parameters
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == "pytest tests/"
        assert call_args[1]["shell"] is True
        assert call_args[1]["cwd"] == "/fake/project"
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["text"] is True
        assert call_args[1]["check"] is True
        assert call_args[1]["executable"] == "/bin/bash"

        assert result.returncode == 0
        assert result.stdout == "test output"

    @patch("subprocess.run")
    def test_execute_command_with_configured_shell(self, mock_run):
        """Test executing command with configured shell from project config."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        project = {"name": "my-project", "path": "/fake/project", "tool_shell": "/bin/zsh"}

        result = execute_tool_command("pytest tests/", "/fake/project", project=project)

        # Should use configured shell
        call_args = mock_run.call_args
        assert call_args[1]["executable"] == "/bin/zsh"

    @patch("subprocess.run")
    def test_execute_command_with_explicit_shell_parameter(self, mock_run):
        """Test executing command with explicit shell parameter."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        project = {"name": "my-project", "path": "/fake/project", "tool_shell": "/bin/zsh"}  # Should be overridden

        result = execute_tool_command("pytest tests/", "/fake/project", project=project, shell="/bin/sh")

        # Should use explicitly provided shell
        call_args = mock_run.call_args
        assert call_args[1]["executable"] == "/bin/sh"

    @patch("subprocess.run")
    def test_execute_command_without_project(self, mock_run):
        """Test executing command without project config (uses default bash)."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = execute_tool_command("pytest tests/", "/fake/project")

        # Should use default /bin/bash
        call_args = mock_run.call_args
        assert call_args[1]["executable"] == "/bin/bash"

    @patch("subprocess.run")
    def test_execute_command_with_command_failure(self, mock_run):
        """Test handling of command execution failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="pytest tests/", output="test output", stderr="error output"
        )

        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            execute_tool_command("pytest tests/", "/fake/project")

        assert exc_info.value.returncode == 1

    @patch("subprocess.run")
    def test_execute_command_captures_stdout_and_stderr(self, mock_run):
        """Test that command execution captures both stdout and stderr."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "standard output"
        mock_result.stderr = "error output"
        mock_run.return_value = mock_result

        result = execute_tool_command("pytest tests/", "/fake/project")

        assert result.stdout == "standard output"
        assert result.stderr == "error output"

    @patch("subprocess.run")
    def test_execute_command_with_non_zero_exit(self, mock_run):
        """Test handling of non-zero exit code with check=True."""
        mock_run.side_effect = subprocess.CalledProcessError(returncode=2, cmd="ansible-lint playbook.yml")

        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            execute_tool_command("ansible-lint playbook.yml", "/fake/project")

        assert exc_info.value.returncode == 2

    @patch("subprocess.run")
    def test_execute_command_working_directory(self, mock_run):
        """Test that command is executed in correct working directory."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        execute_tool_command("pytest tests/", "/custom/work/dir")

        call_args = mock_run.call_args
        assert call_args[1]["cwd"] == "/custom/work/dir"


class TestToolUtilsIntegration:
    """Integration tests for tool_utils functions working together."""

    @patch("subprocess.run")
    def test_full_workflow_with_environment(self, mock_run):
        """Test complete workflow: build command with env and execute."""
        project = {
            "name": "my-project",
            "path": "/fake/project",
            "tool_environment": "source ~/.bashrc\nsource venv/bin/activate",
            "tool_shell": "/bin/bash",
        }

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Tests passed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Build command with environment
        cmd = build_tool_command("pytest tests/", project)

        # Execute command
        result = execute_tool_command(cmd, "/fake/project", project=project)

        # Verify command was built with environment
        assert "source ~/.bashrc" in cmd
        assert "source venv/bin/activate" in cmd
        assert "pytest tests/" in cmd

        # Verify execution was successful
        assert result.returncode == 0
        assert result.stdout == "Tests passed"

        # Verify subprocess was called with bash
        call_args = mock_run.call_args
        assert call_args[1]["executable"] == "/bin/bash"

    @patch("subprocess.run")
    def test_full_workflow_without_environment(self, mock_run):
        """Test complete workflow without environment configuration."""
        project = {"name": "my-project", "path": "/fake/project"}

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_run.return_value = mock_result

        # Build command without environment
        cmd = build_tool_command("ansible-lint playbook.yml", project)

        # Execute command
        result = execute_tool_command(cmd, "/fake/project", project=project)

        # Verify command is just the base command
        assert cmd == "ansible-lint playbook.yml"

        # Verify execution still uses /bin/bash by default
        assert result.returncode == 0
        call_args = mock_run.call_args
        assert call_args[1]["executable"] == "/bin/bash"

    @patch("subprocess.run")
    def test_full_workflow_with_custom_shell(self, mock_run):
        """Test complete workflow with custom shell configuration."""
        project = {
            "name": "my-project",
            "path": "/fake/project",
            "tool_environment": "export ANSIBLE_CONFIG=~/.ansible.cfg",
            "tool_shell": "/usr/bin/zsh",
        }

        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Build and execute
        cmd = build_tool_command("ansible-doc ansible.builtin.copy", project)
        result = execute_tool_command(cmd, "/fake/project", project=project)

        # Verify custom shell was used
        call_args = mock_run.call_args
        assert call_args[1]["executable"] == "/usr/bin/zsh"

    @patch("subprocess.run")
    def test_multi_project_workflow(self, mock_run):
        """Test workflow with multiple projects having different configurations."""
        project1 = {
            "name": "project1",
            "path": "/path/to/project1",
            "tool_environment": "source ~/venvs/project1/bin/activate",
            "tool_shell": "/bin/bash",
        }
        project2 = {
            "name": "project2",
            "path": "/path/to/project2",
            "tool_environment": "source ~/venvs/project2/bin/activate",
            "tool_shell": "/bin/zsh",
        }

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_run.return_value = mock_result

        # Execute for project1
        cmd1 = build_tool_command("pytest tests/", project1)
        result1 = execute_tool_command(cmd1, project1["path"], project=project1)

        # Execute for project2
        cmd2 = build_tool_command("pytest tests/", project2)
        result2 = execute_tool_command(cmd2, project2["path"], project=project2)

        # Verify different environments were used
        assert "project1/bin/activate" in cmd1
        assert "project2/bin/activate" in cmd2

        # Verify different shells were used
        assert mock_run.call_count == 2
        calls = mock_run.call_args_list
        assert calls[0][1]["executable"] == "/bin/bash"
        assert calls[1][1]["executable"] == "/bin/zsh"


class TestToolUtilsEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_build_command_with_invalid_project_type(self):
        """Test building command with invalid project type."""
        result = build_tool_command("pytest tests/", "not-a-dict")
        assert result == "pytest tests/"

        result = build_tool_command("pytest tests/", None)
        assert result == "pytest tests/"

        result = build_tool_command("pytest tests/", [])
        assert result == "pytest tests/"

    @patch("subprocess.run")
    def test_execute_command_with_empty_command(self, mock_run):
        """Test executing empty command."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = execute_tool_command("", "/fake/project")

        # Should still execute (subprocess will handle empty command)
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ""

    def test_build_command_with_special_characters(self):
        """Test building command with special characters in environment."""
        project = {
            "name": "my-project",
            "path": "/fake/project",
            "tool_environment": "export VAR='value with spaces'\nexport PATH=$PATH:/new/path",
        }

        result = build_tool_command("pytest tests/", project)

        # Should preserve special characters
        assert "export VAR='value with spaces'" in result
        assert "export PATH=$PATH:/new/path" in result

    @patch("subprocess.run")
    def test_execute_with_multiline_command(self, mock_run):
        """Test executing multiline command with environment setup."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        multiline_cmd = "source ~/.bashrc\nsource venv/bin/activate\npytest tests/"
        result = execute_tool_command(multiline_cmd, "/fake/project")

        # Should execute full multiline command
        call_args = mock_run.call_args
        assert call_args[0][0] == multiline_cmd

    def test_load_environment_with_unicode_content(self):
        """Test loading environment with unicode characters."""
        project = {
            "name": "my-project",
            "path": "/fake/project",
            "tool_environment": "# Configuration avec caractères spéciaux: é, à, ü\nexport LANG=en_US.UTF-8",
        }

        result = _load_tool_environment(project)

        # Should handle unicode properly
        assert "caractères spéciaux" in result
        assert "export LANG=en_US.UTF-8" in result

    def test_build_command_with_trailing_newlines(self):
        """Test building command with trailing newlines in environment."""
        project = {"name": "my-project", "path": "/fake/project", "tool_environment": "source ~/.bashrc\n\n\n"}

        result = build_tool_command("pytest tests/", project)

        # Should strip trailing newlines and add exactly one
        expected = "source ~/.bashrc\npytest tests/"
        assert result == expected

    @patch("subprocess.run")
    def test_execute_command_with_invalid_project_type(self, mock_run):
        """Test executing command with invalid project type (should use default shell)."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Pass invalid project type
        result = execute_tool_command("pytest tests/", "/fake/project", project="not-a-dict")

        # Should still execute with default shell
        call_args = mock_run.call_args
        assert call_args[1]["executable"] == "/bin/bash"

    def test_empty_project_dict(self):
        """Test with completely empty project dict."""
        project = {}

        env = _load_tool_environment(project)
        shell = _get_tool_shell(project)
        cmd = build_tool_command("pytest tests/", project)

        assert env == ""
        assert shell is None
        assert cmd == "pytest tests/"
