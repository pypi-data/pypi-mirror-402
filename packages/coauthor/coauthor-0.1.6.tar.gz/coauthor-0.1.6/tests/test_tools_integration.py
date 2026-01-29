"""
Integration tests for the tools system.

Tests cover:
- End-to-end tool loading with configuration
- Profile-based tool loading
- Integration with execute_tool function
- Real-world usage scenarios
"""

import pytest
from unittest.mock import Mock, patch
from coauthor.modules.tools.base import (
    load_tools,
    load_task_tools,
    execute_tool,
)


class TestToolLoadingIntegration:
    """Integration tests for tool loading with various configurations."""

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_load_tools_with_ansible_profile_and_include_non_default(self, mock_load_category):
        """Test loading tools with ansible-collection profile and include_non_default."""
        # Mock generic tools
        generic_tools = [
            {"name": "list_tracked_files", "category": "generic", "default": True},
            {"name": "write_files", "category": "generic", "default": True},
        ]

        # Mock ansible tools
        ansible_tools = [
            {
                "name": "ansible_lint",
                "category": "ansible",
                "default": False,
                "profiles": ["ansible-collection", "ansible"],
            },
            {
                "name": "ansible_module_doc",
                "category": "ansible",
                "default": False,
                "profiles": ["ansible-collection", "ansible"],
            },
        ]

        def category_side_effect(category):
            if category == "generic":
                return generic_tools
            elif category == "ansible":
                return ansible_tools
            return []

        mock_load_category.side_effect = category_side_effect

        # Config with ansible-collection profile AND include_non_default
        config = {"profile": "ansible-collection", "tools": {"include_non_default": True}}

        tools = load_tools(config)

        # Should load generic tools + ansible tools (profile matches and non-default included)
        assert len(tools) == 4
        tool_names = [t["function"]["name"] for t in tools]
        assert "list_tracked_files" in tool_names
        assert "write_files" in tool_names
        assert "ansible_lint" in tool_names
        assert "ansible_module_doc" in tool_names

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_load_tools_without_ansible_profile(self, mock_load_category):
        """Test loading tools without ansible profile (ansible tools excluded)."""
        generic_tools = [
            {"name": "list_tracked_files", "category": "generic", "default": True},
        ]

        ansible_tools = [
            {"name": "ansible_lint", "category": "ansible", "default": False, "profiles": ["ansible-collection"]},
        ]

        def category_side_effect(category):
            if category == "generic":
                return generic_tools
            elif category == "ansible":
                return ansible_tools
            return []

        mock_load_category.side_effect = category_side_effect

        # Config without ansible profile
        config = {"profile": "python"}

        tools = load_tools(config)

        # Should only load generic tools (ansible tools don't match profile AND default: false)
        tool_names = [t["function"]["name"] for t in tools]
        assert "list_tracked_files" in tool_names
        assert "ansible_lint" not in tool_names

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_load_tools_with_include_non_default(self, mock_load_category):
        """Test loading all tools including non-default ones."""
        generic_tools = [
            {"name": "default_tool", "category": "generic", "default": True},
        ]

        ansible_tools = [
            {"name": "ansible_lint", "category": "ansible", "default": False},
        ]

        def category_side_effect(category):
            if category == "generic":
                return generic_tools
            elif category == "ansible":
                return ansible_tools
            return []

        mock_load_category.side_effect = category_side_effect

        # Config with include_non_default
        config = {"tools": {"include_non_default": True}}

        tools = load_tools(config)

        # Should load both default and non-default tools
        assert len(tools) == 2
        tool_names = [t["function"]["name"] for t in tools]
        assert "default_tool" in tool_names
        assert "ansible_lint" in tool_names


class TestTaskToolsIntegration:
    """Integration tests for task-specific tool loading."""

    @patch("coauthor.modules.tools.base.load_tools")
    def test_task_with_ansible_tools_override(self, mock_load_tools):
        """Test task configuration overriding to include ansible tools."""
        mock_load_tools.return_value = [
            {"type": "function", "function": {"name": "list_tracked_files"}},
            {"type": "function", "function": {"name": "ansible_lint"}},
            {"type": "function", "function": {"name": "ansible_module_doc"}},
        ]

        config = {"current-task": {"tools": ["ansible_lint", "ansible_module_doc"]}}
        logger = Mock()

        tools = load_task_tools(config, logger)

        # Should only include ansible tools
        assert len(tools) == 2
        tool_names = [t["function"]["name"] for t in tools]
        assert "ansible_lint" in tool_names
        assert "ansible_module_doc" in tool_names
        assert "list_tracked_files" not in tool_names

    @patch("coauthor.modules.tools.base.load_tools")
    def test_task_excluding_ansible_tools(self, mock_load_tools):
        """Test task configuration excluding ansible tools."""
        mock_load_tools.return_value = [
            {"type": "function", "function": {"name": "list_tracked_files"}},
            {"type": "function", "function": {"name": "write_files"}},
            {"type": "function", "function": {"name": "ansible_lint"}},
        ]

        config = {"current-task": {"tools_exclude": ["ansible_lint"]}}
        logger = Mock()

        tools = load_task_tools(config, logger)

        # Should exclude ansible_lint
        assert len(tools) == 2
        tool_names = [t["function"]["name"] for t in tools]
        assert "list_tracked_files" in tool_names
        assert "write_files" in tool_names
        assert "ansible_lint" not in tool_names


class TestExecuteToolIntegration:
    """Integration tests for execute_tool function."""

    @patch("coauthor.modules.tools.generic.list_tracked_files")
    @patch("coauthor.modules.tools.base.load_tools")
    @patch("coauthor.utils.config.get_projects")
    def test_execute_generic_tool(self, mock_get_projects, mock_load_tools, mock_list_files):
        """Test executing a generic tool."""
        mock_get_projects.return_value = [{"name": "test_project", "path": "/test/path"}]

        mock_load_tools.return_value = [
            {"type": "function", "function": {"name": "list_tracked_files", "category": "generic"}}
        ]

        mock_list_files.return_value = ["file1.py", "file2.py"]

        config = {"all_projects": mock_get_projects.return_value}
        logger = Mock()
        params = {"project_name": "test_project"}

        result = execute_tool(config, "list_tracked_files", params, logger)

        assert result == ["file1.py", "file2.py"]
        mock_list_files.assert_called_once_with("/test/path")

    @patch("coauthor.modules.tools.ansible.ansible_lint")
    @patch("coauthor.modules.tools.base.load_tools")
    @patch("coauthor.utils.config.get_projects")
    def test_execute_ansible_lint_tool(self, mock_get_projects, mock_load_tools, mock_ansible_lint):
        """Test executing ansible_lint tool."""
        mock_get_projects.return_value = [{"name": "ansible_project", "path": "/ansible/path"}]

        mock_load_tools.return_value = [
            {"type": "function", "function": {"name": "ansible_lint", "category": "ansible"}}
        ]

        mock_ansible_lint.return_value = {"status": "success", "message": "No issues found"}

        config = {"all_projects": mock_get_projects.return_value}
        logger = Mock()
        params = {"project_name": "ansible_project", "paths": ["playbook.yml"]}

        result = execute_tool(config, "ansible_lint", params, logger)

        assert result["status"] == "success"
        mock_ansible_lint.assert_called_once_with("/ansible/path", ["playbook.yml"], None)

    @patch("coauthor.modules.tools.ansible.ansible_module_doc")
    @patch("coauthor.modules.tools.base.load_tools")
    @patch("coauthor.utils.config.get_projects")
    def test_execute_ansible_module_doc_tool(self, mock_get_projects, mock_load_tools, mock_module_doc):
        """Test executing ansible_module_doc tool."""
        mock_get_projects.return_value = [{"name": "ansible_project", "path": "/ansible/path"}]

        mock_load_tools.return_value = [
            {"type": "function", "function": {"name": "ansible_module_doc", "category": "ansible"}}
        ]

        mock_module_doc.return_value = {"status": "success", "documentation": {"module": "copy"}}

        config = {"all_projects": mock_get_projects.return_value}
        logger = Mock()
        params = {"project_name": "ansible_project", "module_name": "ansible.builtin.copy", "format": "json"}

        result = execute_tool(config, "ansible_module_doc", params, logger)

        assert result["status"] == "success"
        mock_module_doc.assert_called_once_with("/ansible/path", "ansible.builtin.copy", "json")

    @patch("coauthor.utils.config.get_projects")
    def test_execute_tool_project_not_found(self, mock_get_projects):
        """Test execute_tool when project is not found."""
        mock_get_projects.return_value = [{"name": "other_project", "path": "/other/path"}]

        config = {"all_projects": mock_get_projects.return_value}
        logger = Mock()
        params = {"project_name": "nonexistent_project"}

        with pytest.raises(ValueError) as exc_info:
            execute_tool(config, "list_tracked_files", params, logger)

        assert "Project not found" in str(exc_info.value)

    @patch("coauthor.modules.tools.base.load_tools")
    @patch("coauthor.utils.config.get_projects")
    def test_execute_unknown_tool(self, mock_get_projects, mock_load_tools):
        """Test execute_tool with unknown tool name."""
        mock_get_projects.return_value = [{"name": "test_project", "path": "/test/path"}]

        mock_load_tools.return_value = [{"type": "function", "function": {"name": "known_tool"}}]

        config = {"all_projects": mock_get_projects.return_value}
        logger = Mock()
        params = {"project_name": "test_project"}

        with pytest.raises(ValueError) as exc_info:
            execute_tool(config, "unknown_tool", params, logger)

        assert "Unknown tool" in str(exc_info.value)


class TestRealWorldScenarios:
    """Tests for real-world usage scenarios."""

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_ansible_collection_project_workflow(self, mock_load_category):
        """Test complete workflow for ansible-collection project with include_non_default."""
        # Simulate ansible-collection project
        generic_tools = [
            {"name": "list_tracked_files", "category": "generic", "default": True},
            {"name": "write_files", "category": "generic", "default": True},
            {"name": "get_files", "category": "generic", "default": True},
        ]

        ansible_tools = [
            {
                "name": "ansible_lint",
                "category": "ansible",
                "default": False,
                "profiles": ["ansible-collection", "ansible"],
            },
            {
                "name": "ansible_module_doc",
                "category": "ansible",
                "default": False,
                "profiles": ["ansible-collection", "ansible"],
            },
        ]

        def category_side_effect(category):
            if category == "generic":
                return generic_tools
            elif category == "ansible":
                return ansible_tools
            return []

        mock_load_category.side_effect = category_side_effect

        # Project config with include_non_default to load ansible tools
        config = {"profile": "ansible-collection", "tools": {"include_non_default": True}, "current-task": None}
        logger = Mock()

        # Load all available tools
        all_tools = load_tools(config)

        # Should have generic + ansible tools (with include_non_default)
        assert len(all_tools) == 5
        tool_names = [t["function"]["name"] for t in all_tools]
        assert "list_tracked_files" in tool_names
        assert "ansible_lint" in tool_names
        assert "ansible_module_doc" in tool_names

        # Load tools for specific task
        config["current-task"] = {"tools": ["ansible_lint", "write_files"]}
        task_tools = load_task_tools(config, logger)

        # Should only have requested tools
        assert len(task_tools) == 2
        task_tool_names = [t["function"]["name"] for t in task_tools]
        assert "ansible_lint" in task_tool_names
        assert "write_files" in task_tool_names

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_non_ansible_project_workflow(self, mock_load_category):
        """Test workflow for non-Ansible project (Python project)."""
        generic_tools = [
            {"name": "list_tracked_files", "category": "generic", "default": True},
            {"name": "run_pytest", "category": "generic", "default": True},
        ]

        ansible_tools = [
            {"name": "ansible_lint", "category": "ansible", "default": False, "profiles": ["ansible-collection"]},
        ]

        def category_side_effect(category):
            if category == "generic":
                return generic_tools
            elif category == "ansible":
                return ansible_tools
            return []

        mock_load_category.side_effect = category_side_effect

        # Python project config (no Ansible profile, no include_non_default)
        config = {"profile": "python"}

        tools = load_tools(config)

        # Should only have generic tools (ansible tools don't match profile and default: false)
        tool_names = [t["function"]["name"] for t in tools]
        assert "list_tracked_files" in tool_names
        assert "run_pytest" in tool_names
        assert "ansible_lint" not in tool_names

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_ci_profile_with_ansible_tools(self, mock_load_category):
        """Test CI profile that includes ansible-lint with include_non_default."""
        generic_tools = [
            {"name": "list_tracked_files", "category": "generic", "default": True},
        ]

        ansible_tools = [
            {
                "name": "ansible_lint",
                "category": "ansible",
                "default": False,
                "profiles": ["ansible-collection", "ansible", "ci"],
            },
        ]

        def category_side_effect(category):
            if category == "generic":
                return generic_tools
            elif category == "ansible":
                return ansible_tools
            return []

        mock_load_category.side_effect = category_side_effect

        # CI profile config with include_non_default
        config = {"profile": "ci", "tools": {"include_non_default": True}}

        tools = load_tools(config)

        # Should include ansible_lint (CI in profiles and include_non_default)
        tool_names = [t["function"]["name"] for t in tools]
        assert "list_tracked_files" in tool_names
        assert "ansible_lint" in tool_names
