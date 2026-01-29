"""
Utilities for interacting with Git repositories.

This module provides helper functions to check if a file is tracked by Git,
retrieve the diff of a file, and find the root directory of a Git repository.
"""

import subprocess
import os
import datetime
from typing import List, Tuple


def _find_git_repo_root(file_path):
    """
    Find the root directory of the Git repository containing the given file.

    :param file_path: Full path to a file.
    :return: Absolute path to the repository root directory, or None if not found.
    """
    file_path = os.path.abspath(file_path)
    current_dir = os.path.dirname(file_path)

    while True:
        git_dir = os.path.join(current_dir, ".git")
        if os.path.isdir(git_dir):
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            return None
        current_dir = parent_dir


def is_git_tracked(file_path):
    """
    Check if a file is tracked by Git.

    This method determines if the given file is tracked in the Git repository.
    It finds the .git folder by traversing up from the file's directory,
    then uses Git commands to check if the file is tracked using the
    relative path from the repository root.

    :param file_path: Full path to the file.
    :return: True if the file is tracked by Git, False otherwise.
    """
    repo_root = _find_git_repo_root(file_path)
    if repo_root is None:
        return False

    file_path = os.path.abspath(file_path)
    rel_path = os.path.relpath(file_path, repo_root)

    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel_path],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return result.returncode == 0


def get_git_diff(file_path):
    """
    Given the path of a file, this function checks if the file is part of a Git repository.
    If it is, the function returns the diff of the file showing outstanding changes.
    If the file is not in a Git repository, it returns None.

    :param file_path: The path to the file.
    :return: The diff of the file or None if not in a Git repository.
    """
    repo_root = _find_git_repo_root(file_path)
    if repo_root is None:
        return None

    file_path = os.path.abspath(file_path)
    rel_path = os.path.relpath(file_path, repo_root)

    diff_result = subprocess.run(
        ["git", "diff", rel_path],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if diff_result.returncode != 0:
        return None

    return diff_result.stdout.decode("utf-8")


def get_files_by_last_commit(repo_path: str) -> List[Tuple[str, datetime.datetime]]:
    """
    Get a list of tracked files sorted by their last commit date, descending.

    :param repo_path: Path to the Git repository.
    :return: List of tuples (file_path, last_commit_date)
    """
    # Get all tracked files
    tracked_files = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_path,
        capture_output=True,
        text=True
    ).stdout.splitlines()

    file_dates = []
    for file in tracked_files:
        # Get the last commit date for the file
        commit_date_str = subprocess.run(
            ["git", "log", "-1", "--format=%ci", file],
            cwd=repo_path,
            capture_output=True,
            text=True
        ).stdout.strip()

        if commit_date_str:
            commit_date = datetime.datetime.strptime(commit_date_str, "%Y-%m-%d %H:%M:%S %z")
            file_dates.append((file, commit_date))

    # Sort by date descending
    file_dates.sort(key=lambda x: x[1], reverse=True)
    return file_dates
