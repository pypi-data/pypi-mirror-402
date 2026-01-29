import yaml
import os
import importlib.resources
import copy


def deep_merge(d1, d2):
    for key, value in d2.items():
        if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
            deep_merge(d1[key], value)
        else:
            d1[key] = value
    return d1


def read_config(file_path, logger=None):
    if logger:
        logger.info(f"Reading configuration from {file_path}")
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_config_path(config_filename=".coauthor.yml", search_dir=os.getcwd()):
    traversed_paths = []
    while True:
        potential_path = os.path.join(search_dir, config_filename)
        if os.path.exists(potential_path):
            return potential_path, traversed_paths
        traversed_paths.append(search_dir)
        parent_dir = os.path.dirname(search_dir)
        if parent_dir == search_dir:
            break
        search_dir = parent_dir

    home_dir = os.path.expanduser("~")
    home_path = os.path.join(home_dir, config_filename)
    if os.path.exists(home_path):
        traversed_paths.append(home_dir)
        return home_path, traversed_paths

    return None, traversed_paths


def get_default_config():
    config = {
        "jinja": {"search_path": ".coauthor/templates"},
        "agent": {
            "api_key_var": "OPENAI_API_KEY",
            "api_url_var": "OPENAI_API_URL",
            "model": "anthropic/claude-sonnet-4.5",
        },
        "file-watcher": {"ignore-folders": ["__pycache__", ".obsidian", ".git"]},
    }
    return config


def _ensure_root_project_name(config, projects):
    """Ensure the root config has a deterministic name if it needs to act like a project.

    This is mainly for configs that define workflows at the root level but do not
    define a 'name'. Tools and workflow initialization expect projects to have a name.
    """

    existing_names = {p.get("name") for p in projects if isinstance(p, dict)}
    config_name = config.get("name")

    if config_name:
        return config_name

    base = "main"
    candidate = base
    idx = 1
    while candidate in existing_names:
        idx += 1
        candidate = f"{base}-{idx}"

    config["name"] = candidate
    return candidate


def get_projects(config):
    projects = config.get("projects", [])

    config_name = _ensure_root_project_name(config, projects)

    if not any(isinstance(p, dict) and p.get("name") == config_name for p in projects):
        projects.insert(0, config)

    return projects


def get_project(config: dict, project_name: str):
    """Get a specific project by name from the configuration.

    Args:
        config (dict): The configuration dictionary.
        project_name (str): Name of the project to retrieve.

    Returns:
        dict: The project configuration dictionary.

    Raises:
        ValueError: If the project is not found in the configuration.
    """
    projects = get_projects(config)
    for project in projects:
        if isinstance(project, dict) and project.get("name") == project_name:
            return project
    raise ValueError(f"Project '{project_name}' not found in configuration")


def expand_paths(config):
    if "path" in config:
        config["path"] = os.path.expanduser(config["path"])
    if "projects" in config:
        for proj in config["projects"]:
            expand_paths(proj)


def save_config_dump(config, logger=None):
    dump_path = os.path.join(os.getcwd(), ".coauthor_dump.yml")
    with open(dump_path, "w", encoding="utf-8") as dump_file:
        yaml.safe_dump(config, dump_file, default_flow_style=False)
        if logger:
            logger.info(f"Dumped configuration to {dump_path}")


def _load_profile_config(profile_name: str, logger=None) -> dict:
    """Load a profile config.yml from package resources."""

    profile_path = importlib.resources.files("coauthor.profiles").joinpath(profile_name).joinpath("config.yml")
    profile_config = read_config(profile_path, logger) or {}
    if not isinstance(profile_config, dict):
        return {}
    return profile_config


def _select_profile_workflow(profile_config: dict, workflow: dict, logger=None) -> dict:
    """Select a workflow from a profile config.

    Selection rules:
    - If the profile defines exactly one workflow: use it.
    - Else, if workflow.name matches a workflow in the profile: use that.

    Returns an empty dict if no workflow can be selected.
    """

    workflows = profile_config.get("workflows") or []
    if not isinstance(workflows, list) or not workflows:
        if logger:
            logger.error("Profile config has no workflows")
        return {}

    if len(workflows) == 1 and isinstance(workflows[0], dict):
        return workflows[0]

    workflow_name = workflow.get("name") if isinstance(workflow, dict) else None
    if workflow_name:
        for wf in workflows:
            if isinstance(wf, dict) and wf.get("name") == workflow_name:
                return wf

    if logger:
        available = [wf.get("name") for wf in workflows if isinstance(wf, dict)]
        logger.error(
            "Unable to select workflow from profile config. "
            f"Provided workflow.name={workflow_name}, available={available}"
        )

    return {}


def _apply_profile_to_single_workflow(workflow: dict, logger=None) -> dict:
    """Resolve workflows[].profile (+ workflows[].profile_args) into an effective workflow."""

    if not isinstance(workflow, dict):
        return workflow

    profile_name = workflow.get("profile")
    if not profile_name:
        return workflow

    profile_args = workflow.get("profile_args")
    if profile_args and not isinstance(profile_args, dict):
        profile_args = None

    profile_config = _load_profile_config(profile_name, logger)
    profile_workflow = _select_profile_workflow(profile_config, workflow, logger)
    if not profile_workflow:
        return workflow

    merged = copy.deepcopy(profile_workflow)

    merged["profile"] = profile_name

    if profile_args:
        deep_merge(merged, profile_args)

    local_overrides = copy.deepcopy(workflow)
    local_overrides.pop("profile", None)
    local_overrides.pop("profile_args", None)
    deep_merge(merged, local_overrides)

    return merged


def _apply_profiles_to_workflows(container: dict, logger=None) -> None:
    """Apply workflows[].profile recursively to a container (root config or project)."""

    if not isinstance(container, dict):
        return

    workflows = container.get("workflows")
    if not isinstance(workflows, list) or not workflows:
        return

    new_workflows = []
    for workflow in workflows:
        new_workflows.append(_apply_profile_to_single_workflow(workflow, logger))
    container["workflows"] = new_workflows


def _apply_profile_args_to_single_workflow(profile_config, profile_args):
    """Apply project-level profile_args into the single workflow when a profile defines exactly one workflow.

    Profiles often define a single workflow (e.g. the Jira profile). In that case we flatten the workflow
    into top-level keys, but the runtime still iterates over profile_config['workflows'][0].

    Without this, overrides like profile_args.watch.jira.query would only affect the flattened keys and
    not the workflow itself.
    """

    workflows = profile_config.get("workflows") or []
    if len(workflows) != 1:
        return

    workflow = workflows[0]

    workflow_level_keys = {
        "watch",
        "scan",
        "tasks",
        "content_patterns",
        "path_patterns",
        "path",
        "name",
        "description",
        "agent",
    }
    filtered_profile_args = {k: v for k, v in profile_args.items() if k in workflow_level_keys}
    if filtered_profile_args:
        deep_merge(workflow, filtered_profile_args)


def get_config(path=None, logger=None, config_filename=".coauthor.yml", search_dir=os.getcwd(), args=None):
    config = {}
    config_path = None
    if args and hasattr(args, "config_path") and args.config_path:
        config_path = args.config_path
    elif args and hasattr(args, "profile") and args.profile:
        profile = args.profile
        profile_path = importlib.resources.files("coauthor.profiles").joinpath(profile).joinpath("config.yml")
        config = get_default_config()
        deep_merge(config, read_config(profile_path, logger))
        expand_paths(config)
        _apply_profiles_to_workflows(config, logger)
        return config
    if not config_path:
        if path:
            config_path = path
        else:
            config_path, searched_paths = get_config_path(config_filename, search_dir)
            if not config_path:
                if logger:
                    logger.warning(f"Configuration file not found. Searched directories: {', '.join(searched_paths)}")
                config_path = os.path.join(os.getcwd(), config_filename)
                config = get_default_config()
                with open(config_path, "w", encoding="utf-8") as file:
                    if logger:
                        logger.debug(f"Dump config to YAML file {config_path}")
                    yaml.safe_dump(config, file)

                if logger:
                    logger.info(f"Created default configuration file at {config_path}")
    config = get_default_config()
    deep_merge(config, read_config(config_path, logger))
    expand_paths(config)

    _apply_profiles_to_workflows(config, logger)

    if "projects" in config:
        for proj in config["projects"]:
            if "profile" in proj:
                logger.info(f"Applying profile {proj['profile']} config to project {proj['name']}")
                profile = proj["profile"]
                profile_path = importlib.resources.files("coauthor.profiles").joinpath(profile).joinpath("config.yml")
                profile_config = read_config(profile_path, logger)
                workflows = profile_config.get("workflows", [])
                if len(workflows) == 1:
                    workflow = workflows[0]
                    deep_merge(profile_config, workflow)
                if "profile_args" in proj:
                    profile_args = proj["profile_args"]
                    deep_merge(profile_config, profile_args)
                    _apply_profile_args_to_single_workflow(profile_config, profile_args)
                    del proj["profile_args"]
                local = copy.deepcopy(proj)
                proj.clear()
                default = get_default_config()
                deep_merge(proj, default)
                deep_merge(proj, profile_config)
                deep_merge(proj, local)

            _apply_profiles_to_workflows(proj, logger)

        expand_paths(config)
        all_projects = get_projects(config)
        for proj in config["projects"]:
            proj["all_projects"] = all_projects
    return config


def get_jinja_config(config):
    if "jinja" in config:
        return config["jinja"]
    config_jinja = {"search_path": ".coauthor/templates"}
    return config_jinja
