from typing import Optional


def get_all_watch_directories_from_workflows(config, logger):
    return get_all_directories_from_workflows(config, logger, "watch")


def get_all_scan_directories_from_workflows(config, logger):
    return get_all_directories_from_workflows(config, logger, "scan")


def get_all_directories_from_workflows(config, logger, watch_or_scan_key):
    dirs = set()  # Use a set to ensure that directories are unique
    for workflow in config["workflows"]:
        if watch_or_scan_key in workflow:
            if "filesystem" in workflow[watch_or_scan_key]:
                dirs.update(workflow[watch_or_scan_key]["filesystem"]["paths"])
    return list(dirs)  # Convert the set back to a list for the return value


def get_workflows_that_watch(config, logger, watch_filesystem_or="filesystem"):
    wtw = []
    workflows = config.get("workflows", [])  # Default naar een lege lijst
    for workflow in workflows:
        if "watch" in workflow:
            if watch_filesystem_or in workflow["watch"]:
                wtw.append(workflow)
    logger.debug(f"get_workflows_that_watch: workflows_that_watch: {wtw}")
    return wtw


def get_workflows_that_scan(config, logger):
    workflows_that_scan = []
    workflows = config.get("workflows", [])

    for workflow in workflows:
        if "scan" in workflow:
            workflows_that_scan.append(workflow)
    logger.debug(f"get_workflows_that_scan: workflows_that_scan: {workflows_that_scan}")
    return workflows_that_scan


def select_workflow(config: dict, workflow_name: str, project_name: Optional[str] = None) -> Optional[dict]:
    """Select a workflow by name from the configuration.

    Args:
        config (dict): The configuration dictionary (can be root config or project config).
        workflow_name (str): Name of the workflow to select.
        project_name (Optional[str]): Optional project name for cross-project selection.
            If provided, searches in that project's workflows.
            If not provided, searches in the provided config's workflows (backward compatible).

    Returns:
        Optional[dict]: The workflow configuration dictionary or None if not found.
    """
    # If project_name is specified, find that project first
    if project_name:
        from coauthor.utils.config import get_project  # pylint: disable=import-outside-toplevel

        project_config = get_project(config, project_name)
        if not project_config:
            return None
        config = project_config

    workflows = config.get("workflows")
    if not isinstance(workflows, list):
        return None
    for workflow in workflows:
        if isinstance(workflow, dict) and workflow.get("name") == workflow_name:
            return workflow
    return None
