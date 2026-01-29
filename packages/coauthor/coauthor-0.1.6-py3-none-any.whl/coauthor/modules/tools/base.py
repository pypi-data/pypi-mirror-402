"""
Base module for tools system with registry and loading logic.
"""

import os
import json
import yaml
import importlib.resources
from typing import Dict, List, Any, Optional


# Global tool category registry
_TOOL_CATEGORIES = {}


def register_tool_category(category: str, config_file: str) -> None:
    """Register a tool category with its configuration file.

    Args:
        category: Category name (e.g., 'generic', 'ansible')
        config_file: Relative path to YAML config file within tools/ directory
    """
    _TOOL_CATEGORIES[category] = config_file


def load_tools_from_category(category: str) -> List[Dict]:
    """Load tools from a specific category.

    Args:
        category: Category name to load

    Returns:
        List of tool configurations in OpenAI format
    """
    if category not in _TOOL_CATEGORIES:
        return []

    config_file = _TOOL_CATEGORIES[category]

    try:
        tools_resource = importlib.resources.files("coauthor.config.tools").joinpath(config_file)
        with importlib.resources.as_file(tools_resource) as tools_path:
            with open(tools_path, "r", encoding="utf-8") as f:
                tools_config = yaml.safe_load(f)
                if not tools_config or "tools" not in tools_config:
                    return []
                return tools_config["tools"]
    except Exception:
        return []


def filter_tools_by_default(tools: List[Dict], include_non_default: bool = False) -> List[Dict]:
    """Filter tools based on their 'default' property.

    Args:
        tools: List of tool configurations
        include_non_default: If False, only include tools with default=true (or no default property)

    Returns:
        Filtered list of tools
    """
    if include_non_default:
        return tools

    filtered = []
    for tool in tools:
        # Tools without 'default' property are considered default: true
        default_value = tool.get("default", True)
        if default_value:
            filtered.append(tool)

    return filtered


def filter_tools_by_profile(tools: List[Dict], profile: Optional[str]) -> List[Dict]:
    """Filter tools based on their 'profiles' property.

    Args:
        tools: List of tool configurations
        profile: Current profile name (or None)

    Returns:
        Filtered list of tools
    """
    if not profile:
        # If no profile, include tools without profile restrictions
        return [t for t in tools if not t.get("profiles")]

    filtered = []
    for tool in tools:
        profiles = tool.get("profiles")
        if profiles is None:
            # No profile restriction, include tool
            filtered.append(tool)
        elif isinstance(profiles, list) and profile in profiles:
            # Profile matches, include tool
            filtered.append(tool)

    return filtered


def load_tools(config: Dict, logger) -> List[Dict]:
    """Load all tools from registered categories.

    Args:
        config: Optional configuration dict with project settings

    Returns:
        List of tools in OpenAI format
    """
    all_tools = []
    workflow = config["current-workflow"]

    # Load tools from registered categories
    for category in _TOOL_CATEGORIES:
        category_tools = load_tools_from_category(category)
        # Add category to each tool if not present
        for tool in category_tools:
            if "category" not in tool:
                tool["category"] = category
        all_tools.extend(category_tools)

    tool_names = [tool.get("name", "unnamed") for tool in all_tools]
    logger.debug(f"Loaded tools: {', '.join(tool_names)}")

    # Check for include_non_default setting
    include_non_default = False
    if "tools" in config and isinstance(config["tools"], dict):
        include_non_default = config["tools"].get("include_non_default", False)

    # Get profile from workflow or config level
    profile = workflow.get("profile") if workflow and isinstance(workflow, dict) else None
    if profile is None:
        profile = config.get("profile")

    filtered_tools = []
    for tool in all_tools:
        is_default = tool.get("default", True)
        tool_profiles = tool.get("profiles")
        profile_matches = False

        if profile and tool_profiles and isinstance(tool_profiles, list):
            profile_matches = profile in tool_profiles

        passes_default_filter = is_default or include_non_default or profile_matches

        if not passes_default_filter:
            continue

        if include_non_default:
            filtered_tools.append(tool)
        elif profile:
            if tool_profiles is None or profile_matches:
                filtered_tools.append(tool)
        else:
            if tool_profiles is None:
                filtered_tools.append(tool)

    all_tools = filtered_tools

    return [{"type": "function", "function": t} for t in all_tools]


def load_task_tools(config, logger):
    """Load tools filtered by task override if present.

    Args:
        config: Configuration dict
        logger: Logger instance

    Returns:
        List of tools in OpenAI format
    """
    all_tools = load_tools(config, logger)
    task = config.get("current-task")
    if task is None:
        return all_tools

    override_tools = task.get("tools")

    # Alternative compatibility: allow a single 'tool' to be specified.
    if override_tools is None and task.get("tool"):
        override_tools = [task.get("tool")]

    if override_tools is None:
        filtered = all_tools
    else:
        if isinstance(override_tools, list):
            seen = set()
            unique_override_tools = []
            duplicates = []
            for tool_name in override_tools:
                if tool_name in seen:
                    duplicates.append(tool_name)
                else:
                    seen.add(tool_name)
                    unique_override_tools.append(tool_name)

            if duplicates:
                logger.warning(f"Duplicate tools found in task configuration and removed: {', '.join(duplicates)}")

            override_tools = unique_override_tools

        all_tools_dict = {t["function"]["name"]: t for t in all_tools}
        available = sorted(all_tools_dict.keys())
        filtered = []
        unknown = []
        for tool_name in override_tools:
            if tool_name in all_tools_dict:
                filtered.append(all_tools_dict[tool_name])
            else:
                unknown.append(tool_name)
        if unknown:
            logger.error(
                f"Unknown tools in task override: {', '.join(unknown)}. Available tools: {', '.join(available)}"
            )
            raise ValueError(f"Unknown tools in task override: {', '.join(unknown)}")

    tools_exclude = task.get("tools_exclude")
    if tools_exclude:
        exclude_set = {t for t in tools_exclude if isinstance(t, str)}
        filtered = [t for t in filtered if t["function"]["name"] not in exclude_set]

    return filtered


def execute_tool(config, tool_name: str, params: Dict, logger) -> Any:
    """Execute a specified tool on a project.

    Args:
        config: Configuration dict
        tool_name (str): The name of the tool to execute.
        params (Dict): Parameters for the tool, including 'project_name'.
        logger: Logger instance.

    Returns:
        Any: Result of the tool execution or error dictionary.
    """
    from coauthor.utils.config import get_projects  # pylint: disable=import-outside-toplevel
    from coauthor.modules.tools import generic  # pylint: disable=import-outside-toplevel

    projects = config.get("all_projects") or get_projects(config)
    logger.info(f"Executing tool: {tool_name}, params: {params}")

    if projects:
        project = next((p for p in projects if p["name"] == params["project_name"]), None)
        if not project:
            raise ValueError(f"Project not found: {params['project_name']}, projects: {projects}")
        project_path = os.path.expanduser(project.get("path", os.getcwd()))
    else:
        project = config
        project_path = os.path.expanduser(config.get("path", os.getcwd()))

    if project_path == "none":
        raise ValueError(f"File operations are not supported for project {params['project_name']}")

    all_tools = load_tools(config, logger)
    project_tools = project.get("tools", all_tools)
    tool_config = next((t for t in project_tools if t["function"]["name"] == tool_name), None)
    if not tool_config:
        raise ValueError(f"Unknown tool: {tool_name}")

    logger.debug(f'Executing tool "{tool_name}" on project "{params["project_name"]}", "{project_path}"')

    # Generic tools
    if tool_name == "list_tracked_files":
        result = generic.list_tracked_files(project_path)
    elif tool_name == "list_tracked_directories":
        result = generic.list_tracked_directories(project_path)
    elif tool_name == "list_recently_modified_files":
        limit = params.get("limit", 5)
        result = generic.list_recently_modified_files(project_path, limit)
    elif tool_name == "write_files":
        # Fix for C2-1243: Parse JSON string if needed
        files_param = params["files"]
        if isinstance(files_param, str):
            try:
                files_param = json.loads(files_param)
            except json.JSONDecodeError as json_error:
                raise ValueError(f"Invalid JSON string for files parameter: {str(json_error)}") from json_error
        
        # C2-1245: Pass logger for Git staging
        generic.write_files(project_path, files_param, logger)
        result = {"status": "success"}
    elif tool_name == "write_file":
        # C2-1245: Pass logger for Git staging
        generic.write_file(project_path, params["path"], params["content"], logger)
        result = {"status": "success"}
    elif tool_name == "get_files":
        result = generic.get_files(project_path, params["paths"])
    elif tool_name == "get_context":
        result = generic.get_context(project_path)
    elif tool_name == "update_context":
        result = generic.update_context(project_path, params["content"])
    elif tool_name == "create_directories":
        generic.create_directories(project_path, params["directories"])
        result = {"status": "success"}
    elif tool_name == "list_modified_files":
        result = generic.list_modified_files(project_path)
    elif tool_name == "get_diffs":
        result = generic.get_diffs(project_path, params.get("paths", []))
    elif tool_name == "delete_files":
        result = generic.delete_files(project_path, params["paths"])
    elif tool_name == "move_files":
        # C2-1245: Pass logger for Git staging
        result = generic.move_files(project_path, params["moves"], logger)
    elif tool_name == "search_files":
        result = generic.search_files(
            project_path, params["query"], params.get("is_regex", False), params.get("context_lines", 0)
        )
    elif tool_name == "run_pytest":
        result = generic.run_pytest(project, params["test_path"])
    elif tool_name == "get_url":
        result = generic.get_url(params["url"])
    elif tool_name == "get_example":
        result = generic.get_example(project_path, params["example_name"])
    elif tool_name == "start_workflow":
        from coauthor.modules.workflow import start_workflow  # pylint: disable=import-outside-toplevel

        result = start_workflow(config, params, logger)
    # Ansible tools
    elif tool_name == "ansible_lint":
        from coauthor.modules.tools import ansible  # pylint: disable=import-outside-toplevel

        result = ansible.ansible_lint(project, params.get("paths", []), logger, params.get("config_file"))
    elif tool_name == "ansible_module_doc":
        from coauthor.modules.tools import ansible  # pylint: disable=import-outside-toplevel

        result = ansible.ansible_module_doc(project, params["module_name"], params.get("format", "json"))
    else:
        raise ValueError(f"Unknown tool: {tool_name}")

    if tool_config.get("returns_response", True):
        logger.debug(f"Tool result: {result}")
        return result

    return None


# Register default categories
register_tool_category("generic", "generic.yml")
register_tool_category("ansible", "ansible.yml")
