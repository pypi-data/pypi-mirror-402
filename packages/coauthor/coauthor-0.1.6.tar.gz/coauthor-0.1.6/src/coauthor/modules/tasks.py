"""
Dictionary mapping task types to their corresponding processing functions.
This is used to dynamically call the appropriate function based on the task type.
"""

from coauthor.modules.ai import run_ai_task
from coauthor.modules.file_processor import regex_replace_in_file, pong, include_file
from coauthor.modules.workflow_tasks import write_file, read_file
from coauthor.modules.plantuml import process_puml_file
from coauthor.modules.markdown import process_frontmatter
from coauthor.modules.web_tasks import replace_redirecting_links
from coauthor.modules.youtube import get_youtube_video_info

task_type_functions = {
    "ai": run_ai_task,
    "regex_replace_in_file": regex_replace_in_file,
    "pong": pong,
    "write_file": write_file,
    "read_file": read_file,
    "plantuml": process_puml_file,
    "include-files": process_frontmatter,
    "include-file": include_file,
    "replace_redirecting_links": replace_redirecting_links,
    "youtube": get_youtube_video_info,
}


def run_task(config: dict, workflow: dict, task: dict, logger):
    """
    Run a task based on the provided configuration, workflow, and task details.

    This function looks up the task type in the task_type_functions dictionary
    and executes the corresponding function with the given config and logger.
    It sets 'current-task' and 'current-workflow' in the config before execution.

    Args:
        config (dict): The configuration dictionary for the task.
        workflow (dict): The workflow dictionary associated with the task.
        task (dict): The task dictionary containing at least a 'type' key.
        logger: The logger object to use for logging.

    Returns:
        The result of the executed task function.

    Raises:
        ValueError: If the task type is not found in task_type_functions.
    """

    if task["type"] in task_type_functions:
        logger.info(f"Running task {task['id']}")
        config["current-task"] = task
        config["current-workflow"] = workflow
        task_type_functions[task["type"]](config, logger)
    else:
        raise ValueError(f'Unsupported task_type: {task["type"]}')


# def get_available_workflows_for_task(config: dict, task: dict, logger):
#     projects = config["all-projects"]
#     allowed = task.get("workflows", {})
#     available = []
#     for project_name, allowed_wfs in allowed.items():
#         project = next((p for p in projects if p["name"] == project_name), None)
#         if project:

#             project_workflows = project.get("workflows", [])
#             for wf_dict in project_workflows:
#                 wf_name = wf_dict.get("name")
#                 if wf_name in allowed_wfs:
#                     desc = wf_dict.get("description", "N.A.")
#                     available.append({"project": project_name, "workflow": wf_name, "description": desc})
#         else:
#             logger.warning(f"Project {project_name} not found")
#     return available
