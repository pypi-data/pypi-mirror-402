import os
from coauthor.utils.workflow_utils import (
    get_workflows_that_watch,
    get_workflows_that_scan,
    get_all_directories_from_workflows,
    select_workflow,
)
import logging
import yaml
from coauthor.utils.logger import Logger


def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "data", "coauthor-workflows.yml")
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
        config["current-workflow"] = config["workflows"][0]
        config["current-task"] = config["current-workflow"]["tasks"][0]
    return config


def test_get_workflows_that_watch():
    logger = Logger(__name__, level=logging.DEBUG, log_file=f"{os.getcwd()}/debug.log")
    config = get_config()
    workflow = config["workflows"][0]
    workflows_that_watch = get_workflows_that_watch(config, logger)
    assert workflow == workflows_that_watch[0]
    del config["workflows"][0]["watch"]["filesystem"]
    workflows_that_watch = get_workflows_that_watch(config, logger)
    # After removing filesystem, the watch still has other keys, so workflow is still included
    # But get_workflows_that_watch checks for "filesystem" specifically in watch_filesystem_or parameter
    # So the list should be empty when no "filesystem" key exists
    assert [] == workflows_that_watch
    del config["workflows"][0]["watch"]
    workflows_that_watch = get_workflows_that_watch(config, logger)
    assert [] == workflows_that_watch


def test_get_workflows_that_scan():
    logger = Logger(__name__, level=logging.DEBUG, log_file=f"{os.getcwd()}/debug.log")
    config = get_config()
    workflow = config["workflows"][0]
    workflows_that_scan = get_workflows_that_scan(config, logger)
    assert [] == workflows_that_scan


def test_get_all_directories_from_workflows():
    logger = Logger(__name__, level=logging.DEBUG, log_file=f"{os.getcwd()}/debug.log")
    config = get_config()
    workflow = config["workflows"][0]
    workflows_that_watch = get_workflows_that_watch(config, logger)
    dirs = get_all_directories_from_workflows(config, logger, "watch")
    assert dirs == ["vaults"]
    del config["workflows"][0]["watch"]["filesystem"]
    dirs = get_all_directories_from_workflows(config, logger, "watch")
    assert dirs == []


def test_select_workflow_cross_project():
    """Test select_workflow with project_name parameter for cross-project selection."""

    # Create config with multiple projects
    config = {
        "name": "main",
        "workflows": [{"name": "main-workflow", "tasks": []}],
        "projects": [
            {
                "name": "ansible-tools",
                "path": "/path/to/ansible",
                "workflows": [
                    {"name": "ansible-lint-workflow", "tasks": []},
                    {"name": "ansible-doc-workflow", "tasks": []},
                ],
            },
            {
                "name": "python-project",
                "path": "/path/to/python",
                "workflows": [{"name": "pytest-workflow", "tasks": []}],
            },
        ],
    }

    # Test selecting workflow from specific project
    workflow = select_workflow(config, "ansible-lint-workflow", "ansible-tools")
    assert workflow is not None
    assert workflow["name"] == "ansible-lint-workflow"

    # Test selecting different workflow from same project
    workflow2 = select_workflow(config, "ansible-doc-workflow", "ansible-tools")
    assert workflow2 is not None
    assert workflow2["name"] == "ansible-doc-workflow"

    # Test selecting workflow from different project
    workflow3 = select_workflow(config, "pytest-workflow", "python-project")
    assert workflow3 is not None
    assert workflow3["name"] == "pytest-workflow"

    # Test selecting from main project (root)
    workflow_main = select_workflow(config, "main-workflow", "main")
    assert workflow_main is not None
    assert workflow_main["name"] == "main-workflow"

    # Test backward compatibility - no project_name (searches in provided config)
    workflow_compat = select_workflow(config, "main-workflow")
    assert workflow_compat is not None
    assert workflow_compat["name"] == "main-workflow"

    # Test nonexistent workflow in existing project
    missing_workflow = select_workflow(config, "nonexistent", "ansible-tools")
    assert missing_workflow is None

    # Test workflow in nonexistent project
    missing_project = select_workflow(config, "ansible-lint-workflow", "nonexistent-project")
    assert missing_project is None

    # Test backward compatibility with project config directly
    project_config = config["projects"][0]  # ansible-tools
    workflow_direct = select_workflow(project_config, "ansible-lint-workflow")
    assert workflow_direct is not None
    assert workflow_direct["name"] == "ansible-lint-workflow"
