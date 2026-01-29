# pylint: disable=broad-exception-caught
"""
Module for constructing AI messages based on configuration and templates.

This module provides functions to build lists of messages for AI interactions,
handling initial system and user messages, as well as additional messages
from various sources like frontmatter, files, or direct content.
"""

import os
import re
import json
import importlib.resources
import yaml
from jinja2 import Template
from coauthor.utils.config import get_projects
from coauthor.utils.jinja import render_template, template_exists, prompt_template_path, render_content
from coauthor.utils.match_utils import file_submit_to_ai
from coauthor.utils.markdown import get_frontmatter_nested_value
from coauthor.modules.tools.base import execute_tool
from coauthor.utils.context_resolvers import resolve_context_item


def ai_messages(config, logger):
    """
    Construct and return a list of AI messages based on the configuration.

    This function initializes a list of messages, adds initial system and user
    messages, and then appends any additional messages specified in the task.

    Args:
        config (dict): Configuration dictionary containing the current task.
        logger (Logger): Logger instance for logging messages.

    Returns:
        list: A list of message dictionaries, each with 'role' and 'content'.
    """
    messages = []
    if not add_initial_messages(messages, config, logger):
        return []
    add_additional_messages(messages, config, logger)
    return messages


def add_initial_messages(messages, config, logger):
    """
    Add initial system and user messages to the messages list.

    This function retrieves and renders templates for system and user roles,
    appending them to the messages list if content is available.

    Args:
        messages (list): List to which messages will be appended.
        config (dict): Configuration dictionary containing the current task.
        logger (Logger): Logger instance for logging messages.

    Returns:
        bool: True if both messages were added successfully, False otherwise.
    """
    task = config["current-task"]
    for role in ["system", "user"]:
        path_template = prompt_template_path(config, f"{role}.md", logger)
        task[f"{role}_template_path"] = path_template
        content = ai_message_content(config, logger, path_template, role)
        if content:
            messages.append({"role": role, "content": content})
        else:
            logger.error("Message content missing!")
            return False
    return True


def extract_frontmatter_context(file_path, logger):
    """
    Extract coauthor.context blocks from any file type using regex.

    Supports:
    - Markdown frontmatter (YAML between --- delimiters)
    - Python docstrings (triple quotes with coauthor: block)
    - JavaScript/Go multi-line comments (/* ... */)
    - Any file with embedded YAML coauthor: blocks

    Args:
        file_path: Path to the file to extract context from
        logger: Logger instance for logging messages

    Returns:
        list: List of context items or None if no context found
    """
    if not os.path.isfile(file_path):
        logger.debug(f"File not found for context extraction: {file_path}")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as exception_error:
        logger.warning(f"Failed to read file for context extraction {file_path}: {exception_error}")
        return None

    # Try to extract from YAML frontmatter first (between --- delimiters)
    frontmatter_pattern = r"^---\s*\n(.*?\ncoauthor:.*?)^---\s*\n"
    frontmatter_match = re.search(frontmatter_pattern, content, re.MULTILINE | re.DOTALL)

    if frontmatter_match:
        yaml_content = frontmatter_match.group(1)
        try:
            parsed = yaml.safe_load(yaml_content)
            if isinstance(parsed, dict) and "coauthor" in parsed:
                coauthor_data = parsed["coauthor"]
                if isinstance(coauthor_data, dict) and "context" in coauthor_data:
                    context_list = coauthor_data["context"]
                    if isinstance(context_list, list):
                        logger.debug(f"Extracted {len(context_list)} context items from frontmatter in {file_path}")
                        return context_list
        except yaml.YAMLError as exception_error:
            logger.warning(f"Failed to parse YAML frontmatter in {file_path}: {exception_error}")

    # Try to extract from embedded coauthor: blocks (in comments or docstrings)
    # Pattern matches coauthor: followed by context: and list items
    embedded_pattern = r"^coauthor:\n(?:  \w+:\n)*  context:\n((?:    - .+\n?)+)"
    embedded_matches = re.finditer(embedded_pattern, content, re.MULTILINE)

    for match in embedded_matches:
        context_block = match.group(1)
        # Parse the context list items
        yaml_content = f"coauthor:\n  context:\n{context_block}"

        try:
            parsed = yaml.safe_load(yaml_content)
            if isinstance(parsed, dict) and "coauthor" in parsed:
                coauthor_data = parsed["coauthor"]
                if isinstance(coauthor_data, dict) and "context" in coauthor_data:
                    context_list = coauthor_data["context"]
                    if isinstance(context_list, list):
                        logger.debug(f"Extracted {len(context_list)} context items from embedded block in {file_path}")
                        return context_list
        except yaml.YAMLError as exception_error:
            logger.debug(f"Failed to parse embedded YAML in {file_path}: {exception_error}")
            continue

    logger.debug(f"No coauthor.context block found in {file_path}")
    return None


def add_additional_messages(messages, config, logger):
    """
    Add additional user messages to the messages list based on task configuration.

    This function processes additional messages specified in the task, rendering
    their content and appending them as user messages. If no explicit messages
    configuration exists, it attempts to automatically extract context from the
    modified file's frontmatter.

    Args:
        messages (list): List to which messages will be appended.
        config (dict): Configuration dictionary containing the current task.
        logger (Logger): Logger instance for logging messages.
    """
    task = config["current-task"]

    # Check if we should try automatic context extraction
    if "messages" not in task and "path-modify-event" in task:
        # Try automatic context extraction
        file_path = task["path-modify-event"]
        logger.debug(f"Attempting automatic context extraction from {file_path}")
        context_items = extract_frontmatter_context(file_path, logger)

        if context_items:
            logger.info(f"Found {len(context_items)} automatic context items in {file_path}")
            # Resolve context items and add as messages
            project_path = os.path.expanduser(config.get("path", os.getcwd()))
            base_path = os.path.dirname(file_path)

            for item in context_items:
                resolved_content = resolve_context_item(item, base_path, project_path, logger)
                if resolved_content:
                    logger.info(f"Adding automatic context message: {item}")
                    messages.append({"role": "user", "content": resolved_content})
            return

    # Original behavior: process explicit messages configuration
    if "messages" not in task:
        return

    for msg in task["messages"]:
        logger.debug(f"message: {msg}")
        items = get_message_items(msg, task, config, logger)
        for item in items:
            if item is not None:
                if "frontmatter" in msg:
                    task["frontmatter-item"] = item
                elif "files" in msg:
                    task["user-message-context-file"] = item
            content = get_additional_message_content(msg, config, logger, task)
            if content:
                logger.info(f"Adding user message: {msg}")
                messages.append({"role": "user", "content": content})
            else:
                logger.error("Missing content for additional user message")


def get_message_items(msg, task, config, logger):
    """
    Retrieve items based on the message configuration.

    If the message specifies a frontmatter key, this function fetches the
    corresponding list from the task's frontmatter. If 'files' is specified,
    it renders the directory path and lists all files in that directory.
    If no key is present, it defaults to 'coauthor/context'.

    This function also supports automatic context extraction when frontmatter
    is not found in the traditional location.

    Args:
        msg (dict): Message dictionary potentially containing 'frontmatter' or 'files' key.
        task (dict): Task dictionary containing frontmatter data.
        config (dict): Configuration dictionary.
        logger (Logger): Logger instance for logging messages.

    Returns:
        list: List of items from frontmatter or files, or [None] if not specified.
    """
    if "frontmatter" in msg:
        frontmatter_key = msg["frontmatter"]
    else:
        frontmatter_key = "coauthor/context"

    # Try to get frontmatter from traditional location
    if "path-modify-event" in task:
        frontmatter_list = get_frontmatter_nested_value(task["path-modify-event"], frontmatter_key)
        if frontmatter_list is not None:
            if not frontmatter_list:
                return []
            return frontmatter_list

        # Fallback: try automatic extraction if traditional frontmatter not found
        logger.debug(f"Traditional frontmatter '{frontmatter_key}' not found, trying automatic extraction")
        context_items = extract_frontmatter_context(task["path-modify-event"], logger)
        if context_items:
            logger.info(f"Using automatically extracted context items from {task['path-modify-event']}")
            return context_items

    if "files" in msg:
        try:
            template_path = msg["files"]
            dir_path = render_content(task, template_path, config, logger)
            logger.debug(f"Looking for files in dir_path: {dir_path}")
        except Exception as exception_error:
            logger.error(f"Failed to render files path: {exception_error}")
            return []
        if not os.path.isdir(dir_path):
            logger.error(f"Directory does not exist: {dir_path}")
            return []
        files = []
        for root, _dirs, filenames in os.walk(dir_path):
            for filename in filenames:
                full = os.path.join(root, filename)
                files.append(full)
        logger.debug(f"Files to include as user message: {', '.join(files)}")
        return files
    return [None]


def get_additional_message_content(msg, config, logger, task):
    """
    Generate content for an additional message.

    This function retrieves content either from a file template or by rendering
    a Jinja2 template string provided in the message. It also supports resolving
    automatic context items.

    Args:
        msg (dict): Message dictionary with 'file' or 'content' for sourcing.
        config (dict): Configuration dictionary.
        logger (Logger): Logger instance for logging messages.
        task (dict): Current task dictionary.

    Returns:
        str or None: The rendered message content, or None if rendering fails.
    """
    content = None
    if "file" in msg:
        path_template = msg["file"]
        content = ai_message_content(config, logger, path_template, "user")
    elif "content" in msg:
        template_string = msg["content"]
        try:
            template = Template(template_string)
            content = template.render(task=task, config=config)
        except Exception as exception_error:
            logger.error(f"Failed to render content: {exception_error}")
            content = None
    else:
        # Check if this is from automatic context extraction
        if "frontmatter-item" in task:
            item = task["frontmatter-item"]
            project_path = os.path.expanduser(config.get("path", os.getcwd()))
            base_path = os.path.dirname(task.get("path-modify-event", "."))
            content = resolve_context_item(item, base_path, project_path, logger)
        else:
            logger.error("Message has neither 'file' nor 'content'")
    return content


def ai_message_content(config, logger, path_template, system_or_user):
    """
    Retrieve or render content for an AI message.

    This function checks for task attributes first, renders them if present,
    falls back to template rendering if attributes are not present, or uses
    file content for user messages in modify events.

    Args:
        config (dict): Configuration dictionary containing the current task.
        logger (Logger): Logger instance for logging messages.
        path_template (str): Path to the template file.
        system_or_user (str): Role of the message ('system' or 'user').

    Returns:
        str or None: The message content, or None if not found.
    """
    task = config["current-task"]
    message_content = None
    attr = f"{system_or_user}_message"
    if attr in task:
        message_content = render_content(task, task[attr], config, logger)
    elif template_exists(task, path_template, config, logger):
        message_content = render_template(task, path_template, config, logger)
    elif "path-modify-event" in task and system_or_user == "user":
        logger.info(f"Using the file {task['path-modify-event']} as the user message")
        message_content = file_submit_to_ai(config, logger)
    return message_content


def _get_profile_examples(profile_name: str, logger):
    """Return examples from a profile's config.yml, normalized to a list of dicts."""
    if not profile_name:
        return []
    try:
        profile_config_resource = importlib.resources.files("coauthor.profiles")
        profile_config_resource = profile_config_resource.joinpath(profile_name).joinpath("config.yml")
        with importlib.resources.as_file(profile_config_resource) as profile_config_path:
            if not os.path.exists(profile_config_path):
                return []
            with open(profile_config_path, "r", encoding="utf-8") as f:
                profile_config = yaml.safe_load(f) or {}

        examples = profile_config.get("examples") or []
        normalized = []
        for example in examples:
            if isinstance(example, str):
                normalized.append({"name": example, "description": ""})
            elif isinstance(example, dict):
                name = example.get("name")
                if not name:
                    continue
                normalized.append({"name": name, "description": example.get("description", "")})
        return normalized
    except Exception as exception_error:
        logger.error(f"Failed to read profile examples for profile {profile_name}: {exception_error}")
        return []


def _get_project_examples(project_path: str):
    """Return examples from a project's .coauthor/examples directory."""
    examples_dir = os.path.join(project_path, ".coauthor", "examples")
    if not os.path.isdir(examples_dir):
        return []

    examples = []
    for filename in sorted(os.listdir(examples_dir)):
        full_path = os.path.join(examples_dir, filename)
        if os.path.isfile(full_path) and filename.lower().endswith(".md"):
            examples.append(
                {
                    "name": filename,
                    "description": "Example stored in the project under .coauthor/examples",
                }
            )
    return examples


def insert_projects_status_message(messages, config, logger):
    """
    Insert a user message with project information including Git status into the messages list.

    This function retrieves project details, fetches modified files for each project using
    the list_modified_files tool, constructs a JSON-formatted string of project infos,
    and inserts it as a user message before the first existing user message.

    Args:
        messages (list): List of message dictionaries to modify.
        config (dict): Configuration dictionary.
        logger (Logger): Logger instance for logging messages.
    """
    projects = config.get("all_projects", get_projects(config))
    project_infos = []
    for project in projects:
        project_name = project.get("name")
        project_path = os.path.expanduser(project.get("path", os.getcwd()))
        profile_name = project.get("profile")

        info = {
            "name": project_name,
            "type": project.get("type"),
            "description": project.get("description"),
            "examples": _get_profile_examples(profile_name, logger),
        }

        if project.get("read-only") is True:
            info["read_only"] = True
            info["note"] = "This project is read-only from the AI perspective. No files should be modified."

        info["examples"].extend(_get_project_examples(project_path))
        logger.debug(f"info: {info}")
        if project_path == "none":
            info["note"] = "This project has no files."
        else:
            try:
                modified_files = execute_tool(config, "list_modified_files", {"project_name": project_name}, logger)
            except Exception as exception_error:
                logger.error(f"Failed to get modified files for {project_name}: {exception_error}")
                modified_files = []
            info["modified_files"] = modified_files

        project_infos.append(info)

    projects_content = f"Information about the projects:\n{json.dumps(project_infos, indent=2)}"
    projects_message = {"role": "user", "content": projects_content}

    insert_index = 0
    for i, msg in enumerate(messages):
        if msg["role"] == "user":
            insert_index = i
            break
    else:
        insert_index = len(messages)
    messages.insert(insert_index, projects_message)


def insert_available_workflows_for_task(messages: list, config: dict, task: dict, logger):
    """
    Insert a user message with available workflows for the task into the messages list.

    This function checks for allowed workflows in the task, retrieves matching workflows
    from projects, constructs a JSON-formatted string of available workflows, and inserts
    it as a user message before the first existing user message or at the end if none exists.

    Args:
        messages (list): List of message dictionaries to modify.
        config (dict): Configuration dictionary.
        task (dict): Task dictionary containing workflow information.
        logger (Logger): Logger instance for logging messages.
    """
    if "workflows" not in task:
        return
    projects = get_projects(config)
    allowed = task.get("workflows", {})
    available = []
    for project_name, allowed_wfs in allowed.items():
        project = next((p for p in projects if p["name"] == project_name), None)
        if project:

            project_workflows = project.get("workflows", [])
            for wf_dict in project_workflows:
                wf_name = wf_dict.get("name")
                if wf_name in allowed_wfs:
                    desc = wf_dict.get("description", "N.A.")
                    available.append({"project": project_name, "workflow": wf_name, "description": desc})
        else:
            logger.warning(f"Project {project_name} not found")
    workflows_content = f"Available workflows for the task:\n{json.dumps(available, indent=2)}"
    workflows_message = {"role": "user", "content": workflows_content}
    insert_index = 0
    for i, msg in enumerate(messages):
        if msg["role"] == "user":
            insert_index = i
            break
    else:
        insert_index = len(messages)
    messages.insert(insert_index, workflows_message)
