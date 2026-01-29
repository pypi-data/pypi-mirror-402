"""
Tests for C2-1197 Bug Fix: Profile-based tools loading without include_non_default.

This test suite specifically validates that tools with default: false are available
when the project profile matches one of the tool's profiles, WITHOUT requiring
include_non_default: true.

Bug scenario:
- Project: core-collection
- Type: ansible-collection
- Profile: ansible-collection
- Tools: ansible_lint, ansible_module_doc (both have default: false, profiles: ["ansible-collection"])
- Expected: Tools should be available based on profile match alone
- Actual (before fix): "Unknown tools in task override" error
"""

import pytest
from unittest.mock import Mock, patch
from coauthor.modules.tools.base import (
    load_tools,
    load_task_tools,
)


class TestProfileBasedToolLoadingBugFix:
    """Tests for C2-1197: Profile-based tools should load without include_non_default."""

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_ansible_collection_profile_loads_ansible_tools_without_include_non_default(self, mock_load_category):
        """
        C2-1197 Bug Fix Test: Ansible tools should load based on profile match alone.

        This is the core test for the bug fix. Before the fix, ansible_lint and
        ansible_module_doc would not be available without include_non_default: true,
        even though the profile matched.
        """
        generic_tools = [
            {"name": "list_tracked_files", "category": "generic", "default": True},
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

        # KEY TEST: Config with ansible-collection profile but NO include_non_default
        config = {"profile": "ansible-collection"}

        tools = load_tools(config)

        # BUG FIX VALIDATION: Should load generic tools + ansible tools (profile matches)
        tool_names = [t["function"]["name"] for t in tools]
        assert "list_tracked_files" in tool_names, "Generic tool should be loaded"
        assert "ansible_lint" in tool_names, "ansible_lint should be loaded based on profile match"
        assert "ansible_module_doc" in tool_names, "ansible_module_doc should be loaded based on profile match"
        assert len(tools) == 3, "Should have exactly 3 tools"

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_task_override_with_ansible_tools_after_profile_loading(self, mock_load_category):
        """
        Test that task override works correctly after profile-based loading.

        This simulates the exact scenario from the bug report where a workflow task
        attempts to use ansible_lint and ansible_module_doc.
        """
        generic_tools = [
            {"name": "list_tracked_files", "category": "generic", "default": True},
            {"name": "write_files", "category": "generic", "default": True},
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

        # Simulate workflow configuration from bug report
        config = {"profile": "ansible-collection", "current-task": {"tools": ["ansible_lint", "ansible_module_doc"]}}
        logger = Mock()

        # Load task tools - this is where the error occurred before the fix
        tools = load_task_tools(config, logger)

        # Validation: Should NOT log "Unknown tools in task override" error
        logger.error.assert_not_called()

        # Should successfully load both ansible tools
        tool_names = [t["function"]["name"] for t in tools]
        assert "ansible_lint" in tool_names
        assert "ansible_module_doc" in tool_names
        assert len(tools) == 2

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_non_matching_profile_excludes_ansible_tools(self, mock_load_category):
        """
        Test that ansible tools are NOT loaded when profile doesn't match.

        This validates the profile restriction still works correctly.
        """
        generic_tools = [
            {"name": "list_tracked_files", "category": "generic", "default": True},
        ]

        ansible_tools = [
            {
                "name": "ansible_lint",
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

        # Config with python profile (doesn't match ansible tools)
        config = {"profile": "python"}

        tools = load_tools(config)

        # Should only have generic tools
        tool_names = [t["function"]["name"] for t in tools]
        assert "list_tracked_files" in tool_names
        assert "ansible_lint" not in tool_names
        assert len(tools) == 1

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_no_profile_excludes_profile_restricted_tools(self, mock_load_category):
        """
        Test that tools with profile restrictions are NOT loaded when no profile is set.

        This ensures backward compatibility - tools with profiles only load when a
        matching profile is active. Tools with default: false AND profiles should
        NOT be loaded when no profile is set.
        """
        generic_tools = [
            {"name": "list_tracked_files", "category": "generic", "default": True},
        ]

        ansible_tools = [
            {
                "name": "ansible_lint",
                "category": "ansible",
                "default": False,
                "profiles": ["ansible-collection"],
            },
        ]

        def category_side_effect(category):
            if category == "generic":
                return generic_tools
            elif category == "ansible":
                return ansible_tools
            return []

        mock_load_category.side_effect = category_side_effect

        # Config with NO profile explicitly set - use None to ensure filtering runs
        config = {"profile": None}

        tools = load_tools(config)

        # Should only have generic tools (no profile restrictions)
        # ansible_lint should NOT be loaded because:
        # 1. default: false (fails default filter)
        # 2. No profile set, so profile_matches is false
        # 3. include_non_default is false
        tool_names = [t["function"]["name"] for t in tools]
        assert "list_tracked_files" in tool_names
        assert "ansible_lint" not in tool_names, "Tool with default: false and profiles should not load without profile"

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_include_non_default_still_works_with_profile(self, mock_load_category):
        """
        Test backward compatibility: include_non_default: true still works.

        Ensures the fix doesn't break existing behavior where include_non_default
        is explicitly set to true.
        """
        generic_tools = [
            {"name": "list_tracked_files", "category": "generic", "default": True},
        ]

        ansible_tools = [
            {
                "name": "ansible_lint",
                "category": "ansible",
                "default": False,
                "profiles": ["ansible-collection"],
            },
        ]

        def category_side_effect(category):
            if category == "generic":
                return generic_tools
            elif category == "ansible":
                return ansible_tools
            return []

        mock_load_category.side_effect = category_side_effect

        # Config with profile AND include_non_default (backward compatibility)
        config = {"profile": "ansible-collection", "tools": {"include_non_default": True}}

        tools = load_tools(config)

        # Should work the same as profile alone (both tools loaded)
        tool_names = [t["function"]["name"] for t in tools]
        assert "list_tracked_files" in tool_names
        assert "ansible_lint" in tool_names

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_include_non_default_without_profile_still_works(self, mock_load_category):
        """
        Test backward compatibility: include_non_default works without profile.

        Ensures that setting include_non_default: true loads all tools regardless
        of profile restrictions (when include_non_default=true, profile restrictions
        are ignored).
        """
        generic_tools = [
            {"name": "list_tracked_files", "category": "generic", "default": True},
        ]

        ansible_tools = [
            {
                "name": "ansible_lint",
                "category": "ansible",
                "default": False,
                "profiles": ["ansible-collection"],
            },
        ]

        def category_side_effect(category):
            if category == "generic":
                return generic_tools
            elif category == "ansible":
                return ansible_tools
            return []

        mock_load_category.side_effect = category_side_effect

        # Config with include_non_default but NO profile
        config = {"tools": {"include_non_default": True}}

        tools = load_tools(config)

        # Should load all tools (include_non_default ignores profile restrictions)
        tool_names = [t["function"]["name"] for t in tools]
        assert "list_tracked_files" in tool_names
        assert "ansible_lint" in tool_names

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_multiple_profiles_any_match_loads_tool(self, mock_load_category):
        """
        Test that a tool is loaded if ANY of its profiles match the active profile.

        Validates the OR logic in profile matching.
        """
        generic_tools = [
            {"name": "list_tracked_files", "category": "generic", "default": True},
        ]

        ansible_tools = [
            {
                "name": "ansible_lint",
                "category": "ansible",
                "default": False,
                "profiles": ["ansible-collection", "ansible", "ops"],
            },
        ]

        def category_side_effect(category):
            if category == "generic":
                return generic_tools
            elif category == "ansible":
                return ansible_tools
            return []

        mock_load_category.side_effect = category_side_effect

        # Test with "ops" profile (one of the tool's profiles)
        config = {"profile": "ops"}

        tools = load_tools(config)

        # Should load ansible_lint (profile matches one of its profiles)
        tool_names = [t["function"]["name"] for t in tools]
        assert "ansible_lint" in tool_names

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_default_true_tool_always_loaded_regardless_of_profile(self, mock_load_category):
        """
        Test that tools with default: true are always loaded.

        Ensures default tools are not affected by profile filtering.
        """
        generic_tools = [
            {"name": "list_tracked_files", "category": "generic", "default": True},
        ]

        ansible_tools = [
            {
                "name": "ansible_lint",
                "category": "ansible",
                "default": False,
                "profiles": ["ansible-collection"],
            },
        ]

        def category_side_effect(category):
            if category == "generic":
                return generic_tools
            elif category == "ansible":
                return ansible_tools
            return []

        mock_load_category.side_effect = category_side_effect

        # Config with non-matching profile
        config = {"profile": "python"}

        tools = load_tools(config)

        # Generic tool (default: true) should still be loaded
        tool_names = [t["function"]["name"] for t in tools]
        assert "list_tracked_files" in tool_names
        assert "ansible_lint" not in tool_names

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_mixed_default_and_profile_tools(self, mock_load_category):
        """
        Test complex scenario with mix of default and profile-based tools.

        Validates correct filtering with multiple tool types.
        """
        tools = [
            {"name": "default_generic", "category": "generic", "default": True},
            {"name": "non_default_no_profile", "category": "generic", "default": False},
            {
                "name": "non_default_with_profile",
                "category": "ansible",
                "default": False,
                "profiles": ["ansible-collection"],
            },
            {
                "name": "default_with_profile",
                "category": "ansible",
                "default": True,
                "profiles": ["ansible-collection"],
            },
        ]

        def category_side_effect(category):
            return [t for t in tools if t["category"] == category]

        mock_load_category.side_effect = category_side_effect

        # Config with ansible-collection profile
        config = {"profile": "ansible-collection"}

        loaded_tools = load_tools(config)

        # Should load:
        # - default_generic (default: true, no profile restriction)
        # - non_default_with_profile (profile matches)
        # - default_with_profile (default: true AND profile matches)
        # Should NOT load:
        # - non_default_no_profile (default: false, no matching profile, no profiles property)
        tool_names = [t["function"]["name"] for t in loaded_tools]
        assert "default_generic" in tool_names
        assert "non_default_with_profile" in tool_names
        assert "default_with_profile" in tool_names
        assert "non_default_no_profile" not in tool_names
        assert len(loaded_tools) == 3


class TestProfileLoadingEdgeCases:
    """Edge case tests for profile-based tool loading."""

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_tool_with_empty_profiles_list(self, mock_load_category):
        """Test tool with empty profiles list is treated as no match."""

        # Only return tools for "generic" category to avoid duplication
        def category_side_effect(category):
            if category == "generic":
                return [{"name": "tool_with_empty_profiles", "category": "generic", "profiles": []}]
            return []

        mock_load_category.side_effect = category_side_effect

        config = {"profile": "any-profile"}

        loaded_tools = load_tools(config)

        # Tool with empty profiles list should not be loaded (no match)
        assert len(loaded_tools) == 0

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_tool_with_none_profiles(self, mock_load_category):
        """Test tool with profiles: null (None) has no profile restriction."""

        # Only return tools for "generic" category to avoid duplication
        def category_side_effect(category):
            if category == "generic":
                return [{"name": "tool_with_none_profiles", "category": "generic", "profiles": None}]
            return []

        mock_load_category.side_effect = category_side_effect

        config = {"profile": "any-profile"}

        loaded_tools = load_tools(config)

        # Tool with profiles: None should be loaded (no restriction)
        assert len(loaded_tools) == 1

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_tool_without_profiles_property(self, mock_load_category):
        """Test tool without profiles property at all has no restriction."""

        # Only return tools for "generic" category to avoid duplication
        def category_side_effect(category):
            if category == "generic":
                return [{"name": "tool_without_profiles", "category": "generic"}]
            return []

        mock_load_category.side_effect = category_side_effect

        config = {"profile": "any-profile"}

        loaded_tools = load_tools(config)

        # Tool without profiles property should be loaded (no restriction)
        assert len(loaded_tools) == 1

    @patch("coauthor.modules.tools.base.load_tools_from_category")
    def test_profile_none_excludes_profile_restricted_tools(self, mock_load_category):
        """Test that profile: null excludes tools with profile restrictions."""
        tools = [
            {"name": "generic_tool", "category": "generic", "default": True},
            {
                "name": "ansible_tool",
                "category": "ansible",
                "default": False,
                "profiles": ["ansible-collection"],
            },
        ]

        def category_side_effect(category):
            return [t for t in tools if t["category"] == category]

        mock_load_category.side_effect = category_side_effect

        config = {"profile": None}

        loaded_tools = load_tools(config)

        # Should only load tools without profile restrictions
        tool_names = [t["function"]["name"] for t in loaded_tools]
        assert "generic_tool" in tool_names
        assert "ansible_tool" not in tool_names
