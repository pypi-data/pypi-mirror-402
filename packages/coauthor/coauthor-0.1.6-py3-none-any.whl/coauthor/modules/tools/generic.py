"""
Generic tool implementations for file and project management.
"""

import os
import yaml
import subprocess
import shutil
import json
from typing import Dict, List, Any, Optional
import importlib.resources
import re
import urllib.request
from coauthor.utils.git import get_files_by_last_commit
from coauthor.modules.tool_utils import build_tool_command, execute_tool_command


def _git_add_file(project_path: str, file_path: str, logger: Optional[Any] = None) -> None:
    """Stage a file in Git, respecting .gitignore rules.

    Args:
        project_path: Path to the project root
        file_path: Relative path to the file to stage
        logger: Optional logger instance for warnings

    Note:
        This function silently fails if Git is not initialized or if the file
        is ignored by .gitignore. This ensures graceful degradation.
    """
    try:
        # Check if we're in a Git repository
        subprocess.run(["git", "rev-parse", "--git-dir"], cwd=project_path, capture_output=True, check=True)

        # Stage the file (git add respects .gitignore by default)
        subprocess.run(["git", "add", file_path], cwd=project_path, capture_output=True, check=True)
    except subprocess.CalledProcessError:
        # Git command failed - could be:
        # - Not a Git repository
        # - File is ignored by .gitignore
        # - Permission issues
        # Log a warning but don't fail the operation
        if logger:
            logger.debug(f"Could not stage file {file_path} in Git (this is non-critical)")
    except Exception as exception_error:
        # Other unexpected errors
        if logger:
            logger.debug(f"Unexpected error staging {file_path}: {str(exception_error)}")


def list_tracked_files(project_path: str) -> List[str]:
    """List all tracked files in the Git repository at project_path."""
    try:
        result = subprocess.run(["git", "ls-files"], cwd=project_path, capture_output=True, text=True, check=True)
        if result.returncode != 0:
            raise ValueError(f"Error listing files: {result.stderr}")
        return result.stdout.splitlines()
    except Exception as exception_error:
        return [f"Error: {str(exception_error)}"]


def list_tracked_directories(project_path: str) -> List[str]:
    """List all directories that contain tracked files in the Git repository at project_path."""
    files = list_tracked_files(project_path)
    if files and isinstance(files[0], str) and files[0].startswith("Error:"):
        return files
    directories = set()
    for file in files:
        directory = os.path.dirname(file)
        while directory not in directories:
            directories.add(directory)
            if directory == "":
                break
            directory = os.path.dirname(directory)
    directories = {"." if d == "" else d for d in directories}
    return sorted(directories)


def list_recently_modified_files(project_path: str, limit: int = 5) -> List[str]:
    """List the most recently modified Git-tracked files, sorted by last commit date."""
    try:
        file_dates = get_files_by_last_commit(project_path)
        return [file for file, _ in file_dates[:limit]]
    except Exception as exception_error:
        return [f"Error: {str(exception_error)}"]


def write_file(project_path: str, path: str, content: str, logger: Optional[Any] = None) -> None:
    """Write or update a single file in the project.

    Args:
        project_path: Path to the project root
        path: Relative path to the file
        content: File content to write
        logger: Optional logger instance for Git staging warnings

    Note:
        New files and moved files are automatically staged in Git.
    """
    full_path = os.path.join(project_path, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Automatically stage the file in Git
    _git_add_file(project_path, path, logger)


def write_files(project_path: str, files: List[Dict[str, str]], logger: Optional[Any] = None) -> None:
    """Write or update files in the project.

    Args:
        project_path: Path to the project root
        files: List of dicts with 'path' and 'content' keys, or JSON string
        logger: Optional logger instance for Git staging warnings

    Note:
        New files are automatically staged in Git.
    """
    # Fix for C2-1243: Handle JSON-escaped string from OpenAI
    if isinstance(files, str):
        try:
            files = json.loads(files)
        except json.JSONDecodeError as json_error:
            raise ValueError(f"Invalid JSON string for files parameter: {str(json_error)}") from json_error

    # Validate that files is a list
    if not isinstance(files, list):
        raise ValueError(f"files parameter must be a list, got {type(files).__name__}")

    # Validate each file element
    for i, file in enumerate(files):
        if not isinstance(file, dict):
            raise ValueError(f"File element at index {i} must be a dict, got {type(file).__name__}")
        if "path" not in file:
            raise ValueError(f"File element at index {i} missing required key 'path'")
        if "content" not in file:
            raise ValueError(f"File element at index {i} missing required key 'content'")

        write_file(project_path, file["path"], file["content"], logger)


def get_files(project_path: str, paths: List[str]) -> Dict[str, str]:
    """Retrieve content of specified files."""
    contents = {}
    for path in paths:
        full_path = os.path.join(project_path, path)
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                contents[path] = "Path is a directory"
            else:
                with open(full_path, "r", encoding="utf-8") as f:
                    contents[path] = f.read()
        else:
            contents[path] = "File not found"
    return contents


def get_context(project_path: str) -> str:
    result = get_files(project_path, ["COAUTHOR.md"])
    return result.get("COAUTHOR.md", "No context found")


def update_context(project_path: str, content: str) -> Dict[str, str]:
    write_files(project_path, [{"path": "COAUTHOR.md", "content": content}])
    return {"status": "updated"}


def create_directories(project_path: str, directories: List[str]) -> None:
    """Create directories in the project, similar to mkdir -p."""
    for dir_path in directories:
        full_path = os.path.join(project_path, dir_path)
        os.makedirs(full_path, exist_ok=True)


def list_modified_files(project_path: str) -> List[str]:
    """List files with outstanding changes in the specified project path."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.splitlines()
        modified = []
        for line in lines:
            if line:
                status = line[0:2]
                path = line[3:]
                if status in ("R ", "C "):
                    path = path.split(" -> ")[1]
                modified.append(path)
        return modified
    except Exception as exception_error:
        return [f"Error: {str(exception_error)}"]


def get_diffs(project_path: str, paths: List[str] = []) -> Dict[str, str]:
    """Retrieve diffs for specified files in the project path."""
    try:
        if paths:
            file_list = paths
        else:
            file_list = list_modified_files(project_path)
        if file_list and isinstance(file_list[0], str) and file_list[0].startswith("Error:"):
            return {"error": file_list[0]}
        diffs = {}
        for file in file_list:
            stat_res = subprocess.run(
                ["git", "status", "--porcelain", file],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            line = stat_res.stdout.strip()
            if not line:
                diffs[file] = "No changes"
                continue
            status = line[0:2]
            if status == "??":
                full_path = os.path.join(project_path, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        lines = f.read().splitlines()
                    diff = f"diff --git a/{file} b/{file}\n"
                    diff += "new file mode 100644\n"
                    diff += "index 0000000..e69de29\n"
                    diff += "--- /dev/null\n"
                    diff += f"+++ b/{file}\n"
                    diff += f"@@ -0,0 +1,{len(lines)} @@\n"
                    diff += "\n".join([f"+{l}" for l in lines]) + "\n"
                    diffs[file] = diff
                except Exception as exception_error:
                    diffs[file] = f"Error reading file: {str(exception_error)}"
            else:
                diff_res = subprocess.run(
                    ["git", "diff", "HEAD", file],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                diffs[file] = diff_res.stdout or "No changes"
        return diffs
    except Exception as exception_error:
        return {"error": f"Error: {str(exception_error)}"}


def delete_files(project_path: str, paths: List[str]) -> Dict[str, str]:
    """Delete specified files or directories in the project."""
    results = {}
    for path in paths:
        full_path = os.path.join(project_path, path)
        try:
            if os.path.exists(full_path):
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                else:
                    os.remove(full_path)
                results[path] = "Deleted"
            else:
                results[path] = "Not found"
        except Exception as exception_error:
            results[path] = f"Error: {str(exception_error)}"
    return results


def move_files(project_path: str, moves: List[Dict[str, str]], logger: Optional[Any] = None) -> Dict[str, str]:
    """Move files or directories in the project.

    Args:
        project_path: Path to the project root
        moves: List of dicts with 'source' and 'destination' keys
        logger: Optional logger instance for Git staging warnings

    Note:
        Moved files are automatically staged in Git at their new location.
    """
    results = {}
    for move in moves:
        source = os.path.join(project_path, move["source"])
        destination = os.path.join(project_path, move["destination"])
        try:
            if os.path.exists(source):
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                shutil.move(source, destination)
                results[move["source"]] = f'Moved to {move["destination"]}'

                # Automatically stage the moved file at its new location
                _git_add_file(project_path, move["destination"], logger)
            else:
                results[move["source"]] = "Source not found"
        except Exception as exception_error:
            results[move["source"]] = f"Error: {str(exception_error)}"
    return results


def _is_binary_file(file_path: str) -> bool:
    """Check if a file is binary by reading a small chunk and looking for null bytes."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(8192)
            return b"\0" in chunk
    except Exception:
        return True


def search_files(
    project_path: str, query: str, is_regex: bool = False, context_lines: int = 0
) -> Dict[str, List[Dict[str, Any]]]:
    """Search for a query in tracked files of the project, ignoring binary files.

    Returns a dictionary mapping file paths to lists of match dictionaries, where each
    match contains the line_number, match_line, and optionally context lines.
    """
    files = list_tracked_files(project_path)
    if isinstance(files, list) and files and isinstance(files[0], str) and files[0].startswith("Error:"):
        return {"error": [{"message": files[0]}]}
    results: Dict[str, List[Dict[str, Any]]] = {}
    for rel_path in files:
        full_path = os.path.join(project_path, rel_path)
        if _is_binary_file(full_path):
            continue
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            matches = []
            for i, line in enumerate(lines):
                if (not is_regex and query in line) or (is_regex and re.search(query, line)):
                    match = {
                        "line_number": i + 1,
                        "match_line": line.strip(),
                    }
                    if context_lines > 0:
                        start = max(0, i - context_lines)
                        end = min(len(lines), i + context_lines + 1)
                        context_list = []
                        for j in range(start, end):
                            context_list.append(lines[j].strip())
                        match["context"] = "".join(context_list)
                    matches.append(match)
            if matches:
                results[rel_path] = matches
        except UnicodeDecodeError:
            continue
        except Exception as exception_error:
            if "error" not in results:
                results["error"] = []
            results["error"].append({"message": f"{rel_path}: {str(exception_error)}"})
    return results


def run_pytest(project: Dict[str, Any], test_path: str) -> str:
    """Run Pytest on the specified test file in the project.

    Args:
        project: Project configuration dictionary
        test_path: Path to test file or directory to run

    Returns:
        Pytest output (stdout + stderr)
    """
    project_path = os.path.expanduser(project.get("path", os.getcwd()))
    base_command = f"pytest {test_path}"
    cmd = build_tool_command(base_command, project)

    try:
        result = execute_tool_command(cmd, project_path, project=project)
        return result.stdout + result.stderr
    except subprocess.CalledProcessError as exception_error:
        return (
            f"Pytest failed with exit code {exception_error.returncode}:\n"
            f"{exception_error.stdout}{exception_error.stderr}"
        )
    except Exception as exception_error:
        return f"Error executing Pytest: {str(exception_error)}"


def get_url(url: str) -> str:
    """Fetch content from the specified URL."""
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read().decode("utf-8")
            return content
    except Exception as exception_error:
        return f"Error fetching URL: {str(exception_error)}"


def _example_name_candidates(example_name: str) -> List[str]:
    """Return candidate example filenames.

    The preferred form is to use example_name as provided. For backwards
    compatibility, if the name has no .md extension, also try adding it.

    This prevents accidental double extensions like .md.md.
    """
    if not example_name:
        return []
    candidates = [example_name]
    if not example_name.lower().endswith(".md"):
        candidates.append(f"{example_name}.md")
    return candidates


def get_example(project_path: str, example_name: str) -> str:
    """Retrieve a specific example/template from the project or its profile."""
    for candidate_name in _example_name_candidates(example_name):
        project_example_path = os.path.join(project_path, ".coauthor/examples", candidate_name)
        if os.path.exists(project_example_path):
            with open(project_example_path, "r", encoding="utf-8") as f:
                return f.read()

    config_path = os.path.join(project_path, ".coauthor.yml")
    if not os.path.exists(config_path):
        return "No config found, cannot locate profile examples"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    profile_name = config.get("profile")
    if not profile_name:
        return "No profile specified in config"

    try:
        for candidate_name in _example_name_candidates(example_name):
            profile_resource = importlib.resources.files("coauthor.profiles").joinpath(
                profile_name, "examples", candidate_name
            )
            with importlib.resources.as_file(profile_resource) as profile_example_path:
                if os.path.exists(profile_example_path):
                    with open(profile_example_path, "r", encoding="utf-8") as f:
                        return f.read()
        return "No example found in profile"
    except Exception as exception_error:
        return f"Error: {str(exception_error)}"
