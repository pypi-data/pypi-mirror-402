"""Tools module package.

This package contains modular tool implementations organized by category.
"""

from coauthor.modules.tools.base import (
    load_tools,
    load_task_tools,
    execute_tool,
    register_tool_category,
    load_tools_from_category,
)
from coauthor.modules.tools.generic import (
    list_tracked_files,
    list_tracked_directories,
    list_recently_modified_files,
    write_file,
    write_files,
    get_files,
    get_context,
    update_context,
    create_directories,
    list_modified_files,
    get_diffs,
    delete_files,
    move_files,
    search_files,
    run_pytest,
    get_url,
    get_example,
)

__all__ = [
    # Loading functions
    "load_tools",
    "load_task_tools",
    "execute_tool",
    "register_tool_category",
    "load_tools_from_category",
    # Generic tool functions
    "list_tracked_files",
    "list_tracked_directories",
    "list_recently_modified_files",
    "write_file",
    "write_files",
    "get_files",
    "get_context",
    "update_context",
    "create_directories",
    "list_modified_files",
    "get_diffs",
    "delete_files",
    "move_files",
    "search_files",
    "run_pytest",
    "get_url",
    "get_example",
]
