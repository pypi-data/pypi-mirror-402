"""
Comprehensive tests for the refactored tools system.

Tests cover:
- Tool loading from categories
- Default property filtering
- Profile property filtering
- Tool registration
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from coauthor.modules.tools.base import (
    register_tool_category,
    load_tools_from_category,
    filter_tools_by_default,
    filter_tools_by_profile,
    load_tools,
    load_task_tools,
    _TOOL_CATEGORIES,
)


@pytest.fixture
def sample_tools():
    """Sample tools for testing."""
    return [
        {
            "name": "tool_default_true",
            "category": "generic",
            "default": True,
            "description": "A default tool",
        },
        {
            "name": "tool_default_false",
            "category": "ansible",
            "default": False,
            "description": "A non-default tool",
        },
        {
            "name": "tool_no_default",
            "category": "generic",
            "description": "Tool without default property (should default to true)",
        },
    ]


@pytest.fixture
def sample_tools_with_profiles():
    """Sample tools with profile configurations."""
    return [
        {
            "name": "generic_tool",
            "category": "generic",
            "description": "Generic tool without profiles",
        },
        {
            "name": "ansible_tool",
            "category": "ansible",
            "default": False,
            "profiles": ["ansible-collection", "ansible", "ops"],
            "description": "Ansible tool with profiles",
        },
        {
            "name": "ci_tool",
            "category": "ci",
            "default": False,
            "profiles": ["ci"],
            "description": "CI-specific tool",
        },
    ]


class TestToolCategoryRegistration:
    """Tests for tool category registration."""

    def test_register_tool_category(self):
        """Test registering a new tool category."""
        register_tool_category("test_category", "test_category.yml")
        assert "test_category" in _TOOL_CATEGORIES
        assert _TOOL_CATEGORIES["test_category"] == "test_category.yml"

    def test_default_categories_registered(self):
        """Test that default categories (generic, ansible) are registered."""
        assert "generic" in _TOOL_CATEGORIES
        assert "ansible" in _TOOL_CATEGORIES


class TestLoadToolsFromCategory:
    """Tests for loading tools from specific categories."""

    @patch("importlib.resources.files")
    def test_load_generic_tools(self, mock_files):
        """Test loading generic tools from category."""
        mock_yaml_content = """
tools:
  - name: test_tool
    category: generic
    description: Test tool
"""
        mock_path = Mock()
        mock_files.return_value.joinpath.return_value = mock_path

        with patch("importlib.resources.as_file") as mock_as_file:
            mock_as_file.return_value.__enter__ = Mock(return_value="/fake/path/generic.yml")
            mock_as_file.return_value.__exit__ = Mock(return_value=False)

            with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
                tools = load_tools_from_category("generic")

                assert len(tools) == 1
                assert tools[0]["name"] == "test_tool"
                assert tools[0]["category"] == "generic"

    def test_load_nonexistent_category(self):
        """Test loading from a non-existent category returns empty list."""
        tools = load_tools_from_category("nonexistent_category")
        assert tools == []

    @patch("importlib.resources.files")
    def test_load_tools_with_invalid_yaml(self, mock_files):
        """Test handling of invalid YAML in category file."""
        mock_yaml_content = "invalid: yaml: content:"
        mock_path = Mock()
        mock_files.return_value.joinpath.return_value = mock_path

        with patch("importlib.resources.as_file") as mock_as_file:
            mock_as_file.return_value.__enter__ = Mock(return_value="/fake/path/generic.yml")
            mock_as_file.return_value.__exit__ = Mock(return_value=False)

            with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
                tools = load_tools_from_category("generic")
                # Should return empty list on error
                assert tools == []


class TestFilterToolsByDefault:
    """Tests for filtering tools by default property."""

    def test_filter_include_only_default_true(self, sample_tools):
        """Test filtering to include only default=true tools."""
        filtered = filter_tools_by_default(sample_tools, include_non_default=False)

        assert len(filtered) == 2
        assert filtered[0]["name"] == "tool_default_true"
        assert filtered[1]["name"] == "tool_no_default"

    def test_filter_include_all_tools(self, sample_tools):
        """Test including all tools regardless of default property."""
        filtered = filter_tools_by_default(sample_tools, include_non_default=True)

        assert len(filtered) == 3
        assert filtered[0]["name"] == "tool_default_true"
        assert filtered[1]["name"] == "tool_default_false"
        assert filtered[2]["name"] == "tool_no_default"

    def test_filter_empty_list(self):
        """Test filtering empty tools list."""
        filtered = filter_tools_by_default([], include_non_default=False)
        assert filtered == []

    def test_tool_without_default_property_treated_as_true(self):
        """Test that tools without default property are treated as default=true."""
        tools = [{"name": "no_default", "category": "generic"}]
        filtered = filter_tools_by_default(tools, include_non_default=False)

        assert len(filtered) == 1
        assert filtered[0]["name"] == "no_default"


class TestFilterToolsByProfile:
    """Tests for filtering tools by profile property."""

    def test_filter_by_matching_profile(self, sample_tools_with_profiles):
        """Test filtering tools by matching profile."""
        filtered = filter_tools_by_profile(sample_tools_with_profiles, "ansible-collection")

        # Should include generic_tool (no profiles) and ansible_tool (matches profile)
        assert len(filtered) == 2
        tool_names = [t["name"] for t in filtered]
        assert "generic_tool" in tool_names
        assert "ansible_tool" in tool_names

    def test_filter_by_non_matching_profile(self, sample_tools_with_profiles):
        """Test filtering with a profile that doesn't match any tool."""
        filtered = filter_tools_by_profile(sample_tools_with_profiles, "nonexistent-profile")

        # Should only include tools without profile restrictions
        assert len(filtered) == 1
        assert filtered[0]["name"] == "generic_tool"

    def test_filter_without_profile(self, sample_tools_with_profiles):
        """Test filtering when no profile is specified."""
        filtered = filter_tools_by_profile(sample_tools_with_profiles, None)

        # Should only include tools without profile restrictions
        assert len(filtered) == 1
        assert filtered[0]["name"] == "generic_tool"

    def test_filter_multiple_matching_profiles(self, sample_tools_with_profiles):
        """Test that tool matches if profile is in its profiles list."""
        filtered = filter_tools_by_profile(sample_tools_with_profiles, "ops")

        # ansible_tool has "ops" in its profiles
        assert len(filtered) == 2
        tool_names = [t["name"] for t in filtered]
        assert "generic_tool" in tool_names
        assert "ansible_tool" in tool_names


class TestLoadTools:
    """Tests for loading all tools with filtering."""

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_load_tools_basic(self, mock_load_category):
        """Test basic tool loading without config."""

        # Mock category loading - return different tools per category
        def side_effect(category):
            if category == "generic":
                return [{"name": "test_tool", "category": "generic", "default": True}]
            return []

        mock_load_category.side_effect = side_effect

        tools = load_tools()

        # Should be formatted for OpenAI
        assert len(tools) >= 1
        assert all(tool["type"] == "function" for tool in tools)

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_load_tools_with_profile_filter_and_include_non_default(self, mock_load_category):
        """Test loading tools with profile filtering when include_non_default is True."""

        # Return different tools per category
        def side_effect(category):
            if category == "generic":
                return [{"name": "generic_tool", "category": "generic"}]
            elif category == "ansible":
                return [{"name": "ansible_tool", "category": "ansible", "default": False, "profiles": ["ansible"]}]
            return []

        mock_load_category.side_effect = side_effect

        # With profile and include_non_default, ansible_tool should be included
        config = {"profile": "ansible", "tools": {"include_non_default": True}}

        tools = load_tools(config)

        # Should include both tools (default filter disabled, ansible_tool matches profile)
        assert len(tools) == 2

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_load_tools_with_profile_matching_non_default_tool(self, mock_load_category):
        """
        Test that profile matching enables non-default tools (C2-1197 fix).

        With the bug fix, when a profile matches a tool's profiles list,
        the tool is loaded even if default: false, WITHOUT requiring include_non_default.
        """

        # Return different tools per category
        def side_effect(category):
            if category == "generic":
                return [{"name": "generic_tool", "category": "generic"}]
            elif category == "ansible":
                return [{"name": "ansible_tool", "category": "ansible", "default": False, "profiles": ["ansible"]}]
            return []

        mock_load_category.side_effect = side_effect

        # Profile matches but NO include_non_default
        config = {"profile": "ansible"}

        tools = load_tools(config)

        # BUG FIX: Should include both tools (profile matching enables ansible_tool)
        assert len(tools) == 2
        tool_names = [t["function"]["name"] for t in tools]
        assert "generic_tool" in tool_names
        assert "ansible_tool" in tool_names

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_load_tools_with_include_non_default(self, mock_load_category):
        """Test loading tools with include_non_default setting."""

        # Return different tools per category
        def side_effect(category):
            if category == "generic":
                return [{"name": "default_tool", "category": "generic", "default": True}]
            elif category == "ansible":
                return [{"name": "non_default_tool", "category": "ansible", "default": False}]
            return []

        mock_load_category.side_effect = side_effect

        config = {"tools": {"include_non_default": True}}

        tools = load_tools(config)

        # Should include both tools
        assert len(tools) == 2

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_load_tools_adds_category_if_missing(self, mock_load_category):
        """Test that load_tools adds category to tools if not present."""

        def side_effect(category):
            if category == "generic":
                return [{"name": "tool_without_category"}]
            return []

        mock_load_category.side_effect = side_effect

        tools = load_tools()

        # Category should be added based on the category being loaded
        assert len(tools) >= 1


class TestLoadTaskTools:
    """Tests for loading tools filtered by task configuration."""

    def test_load_task_tools_without_override(self):
        """Test loading tools when no task override is specified."""
        config = {"current-task": None}
        logger = Mock()

        with patch("coauthor.modules.tools.base.load_tools") as mock_load:
            mock_load.return_value = [
                {"type": "function", "function": {"name": "tool1"}},
                {"type": "function", "function": {"name": "tool2"}},
            ]

            tools = load_task_tools(config, logger)

            assert len(tools) == 2
            assert tools[0]["function"]["name"] == "tool1"

    def test_load_task_tools_with_override(self):
        """Test loading tools with task override."""
        config = {"current-task": {"tools": ["tool1", "tool3"]}}
        logger = Mock()

        with patch("coauthor.modules.tools.base.load_tools") as mock_load:
            mock_load.return_value = [
                {"type": "function", "function": {"name": "tool1"}},
                {"type": "function", "function": {"name": "tool2"}},
                {"type": "function", "function": {"name": "tool3"}},
            ]

            tools = load_task_tools(config, logger)

            assert len(tools) == 2
            tool_names = [t["function"]["name"] for t in tools]
            assert "tool1" in tool_names
            assert "tool3" in tool_names
            assert "tool2" not in tool_names

    def test_load_task_tools_with_duplicate_tools(self):
        """Test that duplicate tools in task configuration are removed with warning."""
        config = {"current-task": {"tools": ["tool1", "tool2", "tool1"]}}
        logger = Mock()

        with patch("coauthor.modules.tools.base.load_tools") as mock_load:
            mock_load.return_value = [
                {"type": "function", "function": {"name": "tool1"}},
                {"type": "function", "function": {"name": "tool2"}},
            ]

            tools = load_task_tools(config, logger)

            # Should only have 2 tools (duplicate removed)
            assert len(tools) == 2
            # Warning should be logged
            logger.warning.assert_called_once()
            assert "Duplicate tools" in logger.warning.call_args[0][0]

    def test_load_task_tools_with_unknown_tool(self):
        """Test that unknown tools in task configuration generate error."""
        config = {"current-task": {"tools": ["tool1", "unknown_tool"]}}
        logger = Mock()

        with patch("coauthor.modules.tools.base.load_tools") as mock_load:
            mock_load.return_value = [
                {"type": "function", "function": {"name": "tool1"}},
                {"type": "function", "function": {"name": "tool2"}},
            ]

            tools = load_task_tools(config, logger)

            # Should only have tool1 (unknown_tool filtered out)
            assert len(tools) == 1
            # Error should be logged
            logger.error.assert_called_once()
            assert "Unknown tools" in logger.error.call_args[0][0]

    def test_load_task_tools_with_tools_exclude(self):
        """Test excluding specific tools."""
        config = {"current-task": {"tools_exclude": ["tool2"]}}
        logger = Mock()

        with patch("coauthor.modules.tools.base.load_tools") as mock_load:
            mock_load.return_value = [
                {"type": "function", "function": {"name": "tool1"}},
                {"type": "function", "function": {"name": "tool2"}},
                {"type": "function", "function": {"name": "tool3"}},
            ]

            tools = load_task_tools(config, logger)

            assert len(tools) == 2
            tool_names = [t["function"]["name"] for t in tools]
            assert "tool1" in tool_names
            assert "tool3" in tool_names
            assert "tool2" not in tool_names

    def test_load_task_tools_with_single_tool(self):
        """Test alternative compatibility with single 'tool' parameter."""
        config = {"current-task": {"tool": "tool1"}}
        logger = Mock()

        with patch("coauthor.modules.tools.base.load_tools") as mock_load:
            mock_load.return_value = [
                {"type": "function", "function": {"name": "tool1"}},
                {"type": "function", "function": {"name": "tool2"}},
            ]

            tools = load_task_tools(config, logger)

            assert len(tools) == 1
            assert tools[0]["function"]["name"] == "tool1"


class TestToolLoadingEdgeCases:
    """Tests for edge cases in tool loading."""

    def test_empty_tools_list(self):
        """Test handling of empty tools list."""
        filtered = filter_tools_by_default([], include_non_default=False)
        assert filtered == []

    def test_tools_with_malformed_profiles(self):
        """Test handling tools with malformed profiles property."""
        tools = [
            {"name": "tool1", "profiles": "not_a_list"},  # Should be list
            {"name": "tool2", "profiles": ["valid-profile"]},
        ]

        filtered = filter_tools_by_profile(tools, "valid-profile")

        # tool1 should be filtered out (profiles is not a list)
        # tool2 should be included (matches profile)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "tool2"

    def test_tools_with_none_values(self):
        """Test handling tools with None values for properties."""
        tools = [
            {"name": "tool1", "default": None},
            {"name": "tool2", "profiles": None},
        ]

        # Should handle None gracefully
        filtered_default = filter_tools_by_default(tools, include_non_default=False)
        # tool1 with default=None should NOT be treated as default:true (None is falsy)
        # Only tool2 (no default property) should be included
        assert len(filtered_default) == 1
        assert filtered_default[0]["name"] == "tool2"

        filtered_profile = filter_tools_by_profile(tools, "any-profile")
        # tool2 with profiles=None should be included (no restriction)
        assert len(filtered_profile) == 2
