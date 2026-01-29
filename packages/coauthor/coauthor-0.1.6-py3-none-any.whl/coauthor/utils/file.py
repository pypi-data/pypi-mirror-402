"""Utilities for selecting lines from text content and fetching content from URLs.

This module includes functions to parse and select specific line ranges from
multiline strings and to download text content from URLs, optionally applying
line selection.
"""

import os
import requests
from coauthor.utils.git import is_git_tracked


def get_recently_modified_file(file_path_inotify, dir_path, logger):
    """
    Retrieves the most recently modified git-tracked file in a specified directory,
    excluding hidden files. This function is primarily used to address
    an issue with gedit, where the editor uses a temporary hidden file
    that complicates direct file modification detection. Files not tracked by git are ignored.

    Args:
        file_path_inotify (str): The file path detected by inotify or similar mechanism.
        dir_path (str): The directory path to search for modified files.
        logger (Logger): A logger instance for logging debug information.

    Returns:
        str: The path to the most recently modified git-tracked file in the specified directory.
             Returns None if no suitable files are found in the directory.

    Notes:
        - If `file_path_inotify` is found in the directory's non-hidden, git-tracked files,
          it will be returned immediately.
        - For gedit and potentially other applications that use hidden temporary
          files upon saving, this method helps identify the correct file by
          checking the last modified time.
    """
    all_files = list(
        set(
            os.path.join(dir_path, f)
            for f in os.listdir(dir_path)
            if os.path.isfile(os.path.join(dir_path, f)) and is_git_tracked(os.path.join(dir_path, f))
        )
    )
    logger.debug(f"all_files: {', '.join(all_files)}")
    if file_path_inotify in all_files:
        return file_path_inotify
    return max(all_files, key=os.path.getmtime) if all_files else None


def select_lines(content, range_str):
    """
    Select specific lines from content based on a range string.

    Parameters:
    - content (str): Either a multiline string or a file path to read from.
    - range_str (str): A string specifying lines to select, e.g., "1,2,4-10,15-end".
                       Supports single lines (e.g., "1"), ranges (e.g., "4-10"),
                       and "end" keyword for the last line.

    Returns:
    - str: The selected lines joined by newline characters.
    """
    lines = content.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return ""

    selected_indices = set()
    for range_part in range_str.replace(" ", "").split(","):
        if not range_part:
            continue
        try:
            if "-" in range_part:
                start_str, end_str = range_part.split("-")
            else:
                start_str = range_part
                end_str = range_part
            start = int(start_str) - 1
            end = total_lines if end_str.lower() == "end" else int(end_str)
            if start < 0 or end > total_lines:
                raise ValueError(f"Range {range_part} out of bounds (total lines: {total_lines})")
            selected_indices.update(range(start, end))
        except ValueError as value_error:
            raise ValueError(f"Invalid entry {range_part}: {str(value_error)}") from value_error

    selected_lines = [lines[i] for i in sorted(selected_indices)]
    return "\n".join(selected_lines)


def get_url(url, range_str=None):
    """
    Download content from a URL and optionally select specific lines.

    Parameters:
    - url (str): The URL to download the content from.
    - range_str (str, optional): A string specifying lines to select, e.g., "1,2,4-10,15-end".

    Returns:
    - str: The full content or selected lines joined by newline characters.
    """
    response = requests.get(url, timeout=10)  # Set a timeout of 10 seconds
    response.raise_for_status()
    content = response.text
    if range_str:
        return select_lines(content, range_str)
    return content
