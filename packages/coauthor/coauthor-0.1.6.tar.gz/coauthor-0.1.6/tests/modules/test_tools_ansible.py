"""
Tests for Ansible-specific tools.

Tests cover:
- ansible_lint tool functionality
- ansible_module_doc tool functionality
- Error handling and graceful degradation
- Tool environment support (Bug C2-1203)
- Special path handling for "." (Bug C2-1205)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import subprocess
import json
from coauthor.modules.tools.ansible import ansible_lint, ansible_module_doc


class TestAnsibleLint:
    """Tests for the ansible_lint tool."""

    @patch("coauthor.modules.tools.ansible.os.path.exists")
    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_success_no_issues(self, mock_build, mock_execute, mock_exists):
        """Test ansible-lint with no linting issues."""
        mock_exists.return_value = True

        # Mock version check
        mock_build.side_effect = ["ansible-lint --version", "ansible-lint --format json --nocolor playbook.yml"]

        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "ansible-lint 6.0.0"

        lint_result = Mock()
        lint_result.returncode = 0
        lint_result.stdout = "[]"
        lint_result.stderr = ""

        mock_execute.side_effect = [version_result, lint_result]

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_lint(project, ["playbook.yml"])

        assert result["status"] == "success"
        assert result["message"] == "No linting issues found"
        assert result["issues"] == []

        # Verify build_tool_command was called correctly
        assert mock_build.call_count == 2
        mock_build.assert_any_call("ansible-lint --version", project)

    @patch("coauthor.modules.tools.ansible.os.path.exists")
    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_with_issues(self, mock_build, mock_execute, mock_exists):
        """Test ansible-lint when issues are found."""
        mock_exists.return_value = True

        mock_build.side_effect = ["version_cmd", "lint_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        # Mock lint execution with issues
        lint_result = Mock()
        lint_result.returncode = 2
        lint_result.stdout = json.dumps(
            [{"type": "warning", "message": "Line too long", "filename": "playbook.yml", "linenumber": 10}]
        )
        lint_result.stderr = ""

        mock_execute.side_effect = [version_result, lint_result]

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_lint(project, ["playbook.yml"])

        assert result["status"] == "completed"
        assert "1 linting issue" in result["message"]
        assert len(result["issues"]) == 1
        assert result["issues"][0]["type"] == "warning"
        assert result["return_code"] == 2

    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_not_installed(self, mock_build, mock_execute):
        """Test ansible-lint when not installed."""
        mock_build.return_value = "ansible-lint --version"

        # Mock version check failure
        mock_execute.side_effect = subprocess.CalledProcessError(1, "ansible-lint --version")

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_lint(project, ["playbook.yml"])

        assert result["status"] == "error"
        assert "not installed" in result["message"]
        assert "pip install ansible-lint" in result["message"]

    @patch("coauthor.modules.tools.ansible.os.path.exists")
    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_with_config_file(self, mock_build, mock_execute, mock_exists):
        """Test ansible-lint with custom config file."""
        mock_exists.return_value = True

        mock_build.side_effect = ["version_cmd", "lint_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        lint_result = Mock()
        lint_result.returncode = 0
        lint_result.stdout = "[]"

        mock_execute.side_effect = [version_result, lint_result]

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_lint(project, ["playbook.yml"], config_file=".ansible-lint")

        # Verify config file was included in command
        call_args = mock_build.call_args_list[1][0][0]
        assert "-c" in call_args
        assert ".ansible-lint" in call_args

        assert result["status"] == "success"

    @patch("coauthor.modules.tools.ansible.os.path.exists")
    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_multiple_paths(self, mock_build, mock_execute, mock_exists):
        """Test ansible-lint with multiple paths."""
        mock_exists.return_value = True

        mock_build.side_effect = ["version_cmd", "lint_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        lint_result = Mock()
        lint_result.returncode = 0
        lint_result.stdout = "[]"

        mock_execute.side_effect = [version_result, lint_result]

        paths = ["playbook1.yml", "playbook2.yml", "roles/myrole"]
        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_lint(project, paths)

        assert result["status"] == "success"

        # Verify all paths were included
        call_args = mock_build.call_args_list[1][0][0]
        for path in paths:
            assert path in call_args

    @patch("coauthor.modules.tools.ansible.os.path.exists")
    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_no_valid_paths(self, mock_build, mock_execute, mock_exists):
        """Test ansible-lint when no valid paths are provided."""
        mock_build.return_value = "version_cmd"

        version_result = Mock()
        version_result.returncode = 0

        mock_execute.return_value = version_result
        mock_exists.return_value = False

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_lint(project, ["nonexistent.yml"])

        assert result["status"] == "error"
        assert "No valid paths" in result["message"]

    @patch("coauthor.modules.tools.ansible.os.path.exists")
    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_json_parse_error(self, mock_build, mock_execute, mock_exists):
        """Test ansible-lint when JSON output cannot be parsed."""
        mock_exists.return_value = True

        mock_build.side_effect = ["version_cmd", "lint_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        # Mock lint execution with invalid JSON
        lint_result = Mock()
        lint_result.returncode = 2
        lint_result.stdout = "Invalid JSON output"
        lint_result.stderr = ""

        mock_execute.side_effect = [version_result, lint_result]

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_lint(project, ["playbook.yml"])

        assert result["status"] == "completed"
        assert result["raw_output"] is True
        assert "Invalid JSON output" in result["message"]

    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_command_not_found(self, mock_build):
        """Test ansible-lint when command is not found."""
        mock_build.side_effect = FileNotFoundError()

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_lint(project, ["playbook.yml"])

        assert result["status"] == "error"
        assert "command not found" in result["message"]

    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_unexpected_exception(self, mock_build):
        """Test ansible-lint with unexpected exception."""
        mock_build.side_effect = Exception("Unexpected error")

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_lint(project, ["playbook.yml"])

        assert result["status"] == "error"
        assert "Error running ansible-lint" in result["message"]
        assert "Unexpected error" in result["message"]

    @patch("coauthor.modules.tools.ansible.os.path.exists")
    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_with_tool_environment(self, mock_build, mock_execute, mock_exists):
        """Test ansible-lint with tool_environment configured (Bug C2-1203)."""
        mock_exists.return_value = True

        # Project with tool_environment
        project = {
            "name": "test-project",
            "path": "/fake/project",
            "tool_environment": "source ~/.bashrc\nsource venv/bin/activate",
        }

        mock_build.side_effect = [
            "bash -c 'source ~/.bashrc && source venv/bin/activate && ansible-lint --version'",
            "bash -c 'source ~/.bashrc && source venv/bin/activate && ansible-lint --format json --nocolor playbook.yml'",
        ]

        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "ansible-lint 6.0.0"

        lint_result = Mock()
        lint_result.returncode = 0
        lint_result.stdout = "[]"

        mock_execute.side_effect = [version_result, lint_result]

        result = ansible_lint(project, ["playbook.yml"])

        assert result["status"] == "success"

        # Verify build_tool_command was called with project dict containing tool_environment
        assert mock_build.call_count == 2
        mock_build.assert_any_call("ansible-lint --version", project)

        # Verify execute_tool_command was called with project parameter
        assert mock_execute.call_count == 2
        for call_item in mock_execute.call_args_list:
            assert call_item[1].get("project") == project

    @patch("coauthor.modules.tools.ansible.os.path.exists")
    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_auto_detect_config(self, mock_build, mock_execute, mock_exists):
        """Test ansible-lint auto-detects .ansible-lint config file."""

        # Mock .ansible-lint exists in project root
        def exists_side_effect(path):
            return path.endswith(".ansible-lint") or path.endswith("playbook.yml")

        mock_exists.side_effect = exists_side_effect

        mock_build.side_effect = ["version_cmd", "lint_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        lint_result = Mock()
        lint_result.returncode = 0
        lint_result.stdout = "[]"

        mock_execute.side_effect = [version_result, lint_result]

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_lint(project, ["playbook.yml"])

        assert result["status"] == "success"

        # Verify config file was auto-detected and included
        call_args = mock_build.call_args_list[1][0][0]
        assert "-c" in call_args

    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_with_dot_path(self, mock_build, mock_execute):
        """Test ansible-lint with dot (.) as path to scan entire directory (Bug C2-1205)."""
        mock_build.side_effect = ["version_cmd", "lint_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        lint_result = Mock()
        lint_result.returncode = 0
        lint_result.stdout = "[]"

        mock_execute.side_effect = [version_result, lint_result]

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_lint(project, ["."])

        assert result["status"] == "success"

        # Verify "." was included in command without os.path.exists check
        call_args = mock_build.call_args_list[1][0][0]
        assert " ." in call_args or call_args.endswith(".")

    @patch("coauthor.modules.tools.ansible.os.path.exists")
    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_with_dot_and_config(self, mock_build, mock_execute, mock_exists):
        """Test ansible-lint with dot path and config file (Bug C2-1205)."""
        # Mock .ansible-lint exists
        def exists_side_effect(path):
            return path.endswith(".ansible-lint")

        mock_exists.side_effect = exists_side_effect

        mock_build.side_effect = ["version_cmd", "lint_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        lint_result = Mock()
        lint_result.returncode = 0
        lint_result.stdout = "[]"

        mock_execute.side_effect = [version_result, lint_result]

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_lint(project, ["."])

        assert result["status"] == "success"

        # Verify both config and dot path are in command
        call_args = mock_build.call_args_list[1][0][0]
        assert "-c" in call_args
        assert ".ansible-lint" in call_args
        assert " ." in call_args or call_args.endswith(".")


class TestAnsibleModuleDoc:
    """Tests for the ansible_module_doc tool."""

    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_module_doc_json_format(self, mock_build, mock_execute):
        """Test ansible-doc with JSON output format."""
        mock_build.side_effect = ["version_cmd", "doc_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        # Mock doc retrieval
        doc_result = Mock()
        doc_result.returncode = 0
        doc_result.stdout = json.dumps(
            {
                "ansible.builtin.copy": {
                    "doc": {
                        "module": "copy",
                        "short_description": "Copy files to remote locations",
                        "description": ["The copy module copies a file..."],
                    }
                }
            }
        )
        doc_result.stderr = ""

        mock_execute.side_effect = [version_result, doc_result]

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_module_doc(project, "ansible.builtin.copy", output_format="json")

        assert result["status"] == "success"
        assert result["module"] == "ansible.builtin.copy"
        assert result["format"] == "json"
        assert "documentation" in result
        assert isinstance(result["documentation"], dict)

    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_module_doc_yaml_format(self, mock_build, mock_execute):
        """Test ansible-doc with YAML output format."""
        mock_build.side_effect = ["version_cmd", "doc_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        # Mock doc retrieval
        doc_result = Mock()
        doc_result.returncode = 0
        doc_result.stdout = "module: copy\nshort_description: Copy files"
        doc_result.stderr = ""

        mock_execute.side_effect = [version_result, doc_result]

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_module_doc(project, "ansible.builtin.copy", output_format="yaml")

        assert result["status"] == "success"
        assert result["format"] == "yaml"
        assert isinstance(result["documentation"], str)
        assert "module: copy" in result["documentation"]

    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_module_doc_markdown_format(self, mock_build, mock_execute):
        """Test ansible-doc with markdown output format."""
        mock_build.side_effect = ["version_cmd", "doc_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        # Mock doc retrieval
        doc_result = Mock()
        doc_result.returncode = 0
        doc_result.stdout = "# ansible.builtin.copy\n\nCopy files to remote locations"
        doc_result.stderr = ""

        mock_execute.side_effect = [version_result, doc_result]

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_module_doc(project, "ansible.builtin.copy", output_format="markdown")

        assert result["status"] == "success"
        assert result["format"] == "markdown"
        assert isinstance(result["documentation"], str)

    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_module_doc_not_found(self, mock_build, mock_execute):
        """Test ansible-doc when module is not found."""
        mock_build.side_effect = ["version_cmd", "doc_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        # Mock doc retrieval failure
        doc_error = subprocess.CalledProcessError(
            returncode=1, cmd="ansible-doc -j nonexistent.module", output="", stderr="ERROR! No module found"
        )
        doc_error.stderr = "ERROR! No module found"

        mock_execute.side_effect = [version_result, doc_error]

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_module_doc(project, "nonexistent.module")

        assert result["status"] == "error"
        assert "not found" in result["message"]
        assert result["stderr"] == "ERROR! No module found"

    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_module_doc_not_installed(self, mock_build, mock_execute):
        """Test ansible-doc when not installed."""
        mock_build.return_value = "version_cmd"

        # Mock version check failure
        mock_execute.side_effect = subprocess.CalledProcessError(1, "ansible-doc --version")

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_module_doc(project, "ansible.builtin.copy")

        assert result["status"] == "error"
        assert "not installed" in result["message"]
        assert "pip install ansible" in result["message"]

    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_module_doc_json_parse_error(self, mock_build, mock_execute):
        """Test ansible-doc when JSON output cannot be parsed."""
        mock_build.side_effect = ["version_cmd", "doc_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        # Mock doc retrieval with invalid JSON
        doc_result = Mock()
        doc_result.returncode = 0
        doc_result.stdout = "Invalid JSON"
        doc_result.stderr = ""

        mock_execute.side_effect = [version_result, doc_result]

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_module_doc(project, "ansible.builtin.copy", output_format="json")

        assert result["status"] == "error"
        assert "Failed to parse JSON" in result["message"]
        assert "raw_output" in result

    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_module_doc_command_not_found(self, mock_build):
        """Test ansible-doc when command is not found."""
        mock_build.side_effect = FileNotFoundError()

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_module_doc(project, "ansible.builtin.copy")

        assert result["status"] == "error"
        assert "command not found" in result["message"]

    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_module_doc_unexpected_exception(self, mock_build):
        """Test ansible-doc with unexpected exception."""
        mock_build.side_effect = Exception("Unexpected error")

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_module_doc(project, "ansible.builtin.copy")

        assert result["status"] == "error"
        assert "Error running ansible-doc" in result["message"]

    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_module_doc_collection_module(self, mock_build, mock_execute):
        """Test ansible-doc with a collection module."""
        mock_build.side_effect = ["version_cmd", "doc_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        # Mock doc retrieval
        doc_result = Mock()
        doc_result.returncode = 0
        doc_result.stdout = json.dumps(
            {
                "community.general.docker_container": {
                    "doc": {"module": "docker_container", "short_description": "Manage docker containers"}
                }
            }
        )

        mock_execute.side_effect = [version_result, doc_result]

        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_module_doc(project, "community.general.docker_container", output_format="json")

        assert result["status"] == "success"
        assert result["module"] == "community.general.docker_container"

    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_module_doc_default_format(self, mock_build, mock_execute):
        """Test ansible-doc with default format (json)."""
        mock_build.side_effect = ["version_cmd", "doc_cmd"]

        version_result = Mock()
        version_result.returncode = 0

        # Mock doc retrieval
        doc_result = Mock()
        doc_result.returncode = 0
        doc_result.stdout = json.dumps({"test": "data"})

        mock_execute.side_effect = [version_result, doc_result]

        # Don't specify format, should default to json
        project = {"name": "test-project", "path": "/fake/project"}
        result = ansible_module_doc(project, "ansible.builtin.copy")

        assert result["status"] == "success"
        # Verify JSON format was used
        call_args = mock_build.call_args_list[1][0][0]
        assert "-j" in call_args

    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_module_doc_with_tool_environment(self, mock_build, mock_execute):
        """Test ansible-doc with tool_environment configured (Bug C2-1203)."""
        # Project with tool_environment
        project = {
            "name": "test-project",
            "path": "/fake/project",
            "tool_environment": "source ~/.bashrc\nsource venv/bin/activate",
        }

        mock_build.side_effect = [
            "bash -c 'source ~/.bashrc && source venv/bin/activate && ansible-doc --version'",
            "bash -c 'source ~/.bashrc && source venv/bin/activate && ansible-doc -j ansible.builtin.copy'",
        ]

        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "ansible-doc 2.10.0"

        doc_result = Mock()
        doc_result.returncode = 0
        doc_result.stdout = json.dumps({"ansible.builtin.copy": {"doc": {}}})

        mock_execute.side_effect = [version_result, doc_result]

        result = ansible_module_doc(project, "ansible.builtin.copy", output_format="json")

        assert result["status"] == "success"

        # Verify build_tool_command was called with project dict containing tool_environment
        assert mock_build.call_count == 2
        mock_build.assert_any_call("ansible-doc --version", project)

        # Verify execute_tool_command was called with project parameter
        assert mock_execute.call_count == 2
        for call_item in mock_execute.call_args_list:
            assert call_item[1].get("project") == project


class TestAnsibleToolsIntegration:
    """Integration tests for Ansible tools."""

    @patch("coauthor.modules.tools.ansible.os.path.exists")
    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_lint_and_doc_workflow(self, mock_build, mock_execute, mock_exists):
        """Test a typical workflow using both Ansible tools."""
        mock_exists.return_value = True

        # Mock all commands
        mock_build.side_effect = ["lint_version", "lint_cmd", "doc_version", "doc_cmd"]

        # Mock ansible-lint
        lint_version = Mock()
        lint_version.returncode = 0

        lint_result = Mock()
        lint_result.returncode = 0
        lint_result.stdout = "[]"

        # Mock ansible-doc
        doc_version = Mock()
        doc_version.returncode = 0

        doc_result = Mock()
        doc_result.returncode = 0
        doc_result.stdout = json.dumps({"test": "data"})

        mock_execute.side_effect = [lint_version, lint_result, doc_version, doc_result]

        project = {"name": "test-project", "path": "/fake/project"}

        # Run lint
        lint_output = ansible_lint(project, ["playbook.yml"])
        assert lint_output["status"] == "success"

        # Run doc
        doc_output = ansible_module_doc(project, "ansible.builtin.copy")
        assert doc_output["status"] == "success"

    def test_ansible_tools_error_format_consistency(self):
        """Test that error formats are consistent across Ansible tools."""
        with patch("coauthor.modules.tools.ansible.build_tool_command", side_effect=FileNotFoundError()):
            project = {"name": "test-project", "path": "/fake/project"}

            lint_result = ansible_lint(project, ["playbook.yml"])
            doc_result = ansible_module_doc(project, "ansible.builtin.copy")

            # Both should have same error structure
            assert "status" in lint_result
            assert "message" in lint_result
            assert lint_result["status"] == "error"

            assert "status" in doc_result
            assert "message" in doc_result
            assert doc_result["status"] == "error"

    @patch("coauthor.modules.tools.ansible.os.path.exists")
    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_multi_project_different_environments(self, mock_build, mock_execute, mock_exists):
        """Test Ansible tools with different projects having different environments (Bug C2-1203)."""
        mock_exists.return_value = True

        # Project 1 with venv1
        project1 = {"name": "project1", "path": "/project1", "tool_environment": "source venv1/bin/activate"}

        # Project 2 with venv2
        project2 = {"name": "project2", "path": "/project2", "tool_environment": "source venv2/bin/activate"}

        mock_build.side_effect = [
            "bash -c 'source venv1/bin/activate && ansible-lint --version'",
            "bash -c 'source venv1/bin/activate && ansible-lint --format json --nocolor playbook.yml'",
            "bash -c 'source venv2/bin/activate && ansible-lint --version'",
            "bash -c 'source venv2/bin/activate && ansible-lint --format json --nocolor playbook.yml'",
        ]

        version_result = Mock()
        version_result.returncode = 0

        lint_result = Mock()
        lint_result.returncode = 0
        lint_result.stdout = "[]"

        mock_execute.side_effect = [version_result, lint_result, version_result, lint_result]

        # Run ansible-lint for project1
        result1 = ansible_lint(project1, ["playbook.yml"])
        assert result1["status"] == "success"

        # Run ansible-lint for project2
        result2 = ansible_lint(project2, ["playbook.yml"])
        assert result2["status"] == "success"

        # Verify correct project was passed to each call
        assert mock_build.call_args_list[0][0][1] == project1
        assert mock_build.call_args_list[2][0][1] == project2

    @patch("coauthor.modules.tools.ansible.execute_tool_command")
    @patch("coauthor.modules.tools.ansible.build_tool_command")
    def test_ansible_tools_without_tool_environment(self, mock_build, mock_execute):
        """Test Ansible tools work without tool_environment configured."""
        # Project without tool_environment
        project = {"name": "test-project", "path": "/fake/project"}

        mock_build.side_effect = ["ansible-doc --version", "ansible-doc -j ansible.builtin.copy"]

        version_result = Mock()
        version_result.returncode = 0

        doc_result = Mock()
        doc_result.returncode = 0
        doc_result.stdout = json.dumps({"ansible.builtin.copy": {"doc": {}}})

        mock_execute.side_effect = [version_result, doc_result]

        result = ansible_module_doc(project, "ansible.builtin.copy")

        assert result["status"] == "success"

        # Verify project was still passed to build_tool_command
        mock_build.assert_any_call("ansible-doc --version", project)
