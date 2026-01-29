import yaml
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


def parse_frontmatter(content: str) -> Dict[str, Any]:
    """
    Parse frontmatter from markdown content without using frontmatter library
    because it depends on older pyyaml==5.3.1.

    Returns a dictionary with:
    - 'frontmatter': parsed frontmatter as dict (empty dict if no frontmatter)
    - 'content': markdown content without frontmatter
    - 'frontmatter_str': raw frontmatter string (empty string if no frontmatter)
    """
    if not content.strip().startswith("---"):
        return {"frontmatter": {}, "content": content, "frontmatter_str": ""}

    # Find the second "---" delimiter
    first_delim_end = 3
    second_delim_start = content.find("---", first_delim_end)

    if second_delim_start == -1:
        # No closing delimiter found
        return {"frontmatter": {}, "content": content, "frontmatter_str": ""}

    frontmatter_str = content[first_delim_end:second_delim_start].strip()

    try:
        frontmatter_data = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError as yaml_error:
        logging.warning("Failed to parse frontmatter YAML: %s", yaml_error)
        frontmatter_data = {}

    content_str = content[second_delim_start + 3 :].lstrip()

    return {"frontmatter": frontmatter_data, "content": content_str, "frontmatter_str": frontmatter_str}


def get_frontmatter(path: Union[str, Path], logger: Optional[logging.Logger] = None) -> Tuple[Dict[str, Any], str, str]:
    """
    Reads a Markdown file and parses its frontmatter.

    :param path: Path to the Markdown file.
    :param logger: Optional logger for error reporting.
    :return: Tuple containing:
             - frontmatter dictionary (empty dict on error)
             - frontmatter string (empty string on error)
             - original content (empty string on error)
    """
    path_obj = Path(path) if isinstance(path, str) else path

    if not path_obj.exists():
        if logger:
            logger.warning(f"File not found: {path}")
        return {}, "", ""

    try:
        with open(path_obj, "r", encoding="utf-8") as file:
            content = file.read()
    except (IOError, OSError, UnicodeDecodeError) as e:
        if logger:
            logger.error(f"Error reading file {path}: {e}")
        return {}, "", ""

    parsed = parse_frontmatter(content)
    return parsed["frontmatter"], parsed["frontmatter_str"], content


def get_frontmatter_attribute(
    path: Union[str, Path], attr_name: str, logger: Optional[logging.Logger] = None
) -> Optional[Any]:
    """
    Retrieves a specific attribute from the frontmatter of a Markdown file.

    :param path: Path to the Markdown file.
    :param attr_name: The name of the attribute to retrieve.
    :param logger: Optional logger for error reporting.
    :return: The value of the specified attribute, or None if not found or on error.
    """
    frontmatter, _, _ = get_frontmatter(path, logger=logger)
    return frontmatter.get(attr_name) if frontmatter else None


def get_frontmatter_nested_value(
    path: Union[str, Path], frontmatter_context_path: str, logger: Optional[logging.Logger] = None
) -> List[Any]:
    """
    Retrieves a nested value from the frontmatter of a Markdown file using a path.

    :param path: Path to the Markdown file.
    :param frontmatter_context_path: The nested path to the attribute (e.g., "key1/key2").
    :param logger: Optional logger for error reporting.
    :return: The value as a list if it is a list, otherwise an empty list.
    """
    frontmatter, _, _ = get_frontmatter(path, logger=logger)

    if not frontmatter:
        return []

    keys = frontmatter_context_path.replace("/", ".").split(".")
    value = frontmatter

    try:
        for key in keys:
            if not isinstance(value, dict):
                return []
            value = value.get(key, {})
    except (AttributeError, KeyError):
        return []

    return value if isinstance(value, list) else []
