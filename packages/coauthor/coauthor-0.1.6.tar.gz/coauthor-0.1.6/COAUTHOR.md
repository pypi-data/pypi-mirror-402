# Coauthor Context

## Known Issues

### no attribute 'current-ticket'

If AI processing shows error message below in log, this typically has to do with
a missing `user_message` in the task configuration. So, this typically is not a
bug but a misconfiguration. If the `user_message` is missing, Coauthor tries to
find a suitable file based Jinja template.

> jinja2.exceptions.UndefinedError: 'dict object' has no attribute 'current-ticket'

## Language Guidelines

- The primary language for the coauthor project is English. All code,
  documentation, and project files must be in English.
- Interactions with users may be in Dutch or other languages, but when
  generating or modifying code, content, or documentation via tools, always use
  English.
- Jira comments and ticket descriptions "should" be in the language of the
  interaction.
- Do not use Jira syntax (e.g., {code}, {{monospaced}}) in project files. Use
  Markdown syntax instead. Jira syntax is reserved for Jira comments and
  tickets.
- This file (`COAUTHOR.md`) must be written in English using Markdown syntax.

## Coding Conventions

- Use consistent snake_case for variable names.
- In except blocks: avoid single-letter names like `e`; use descriptive names
  like `exception_error`.
- When opening files with `open()`, always specify the encoding explicitly
  (e.g., `encoding='utf-8'`) to avoid linter issues such as pylint W1514
  (unspecified-encoding).

### Example (good)

```python
except Exception as exception_error:
    results[path] = f"Error: {str(exception_error)}"
```

## Changelog

The `CHANGELOG.md` file maintains a concise record of project changes in the form
of bulleted or numbered lists. It focuses exclusively on high-level summaries,
avoiding any in-depth details or implementation notes. For each change, add a
brief summary consisting of one to three sentences, tailored to the complexity
of the update.

## Tool Development Guidelines

### Modular Tools System

The tools system uses a modular architecture:

- **Configuration files** are organized by category under `src/coauthor/config/tools/`:
  - `generic.yml` - Generic file and project management tools
  - `ansible.yml` - Ansible-specific tools
  - Additional categories can be added as needed

- **Implementation modules** are organized under `src/coauthor/modules/tools/`:
  - `base.py` - Tool loading, registry, and execution logic
  - `generic.py` - Generic tool implementations
  - `ansible.py` - Ansible-specific tool implementations
  - Additional modules can be added as needed

### Adding New Tools

When adding or modifying tools:

1. **Choose or create a category** - Determine if the tool fits into an existing
   category (generic, ansible) or requires a new category.

2. **Add tool configuration** - Add the tool definition to the appropriate YAML
   file in `src/coauthor/config/tools/`:

   ```yaml
   - name: tool_name
     category: category_name
     default: true  # Optional, default: true
     profiles: ["profile1", "profile2"]  # Optional
     description: Tool description
     parameters:
       type: object
       properties:
         # ... parameter definitions
       required: [...]
   ```

3. **Implement the tool function** - Add the implementation to the appropriate
   Python module in `src/coauthor/modules/tools/`:

   ```python
   def tool_name(project_path: str, param1: str, ...) -> Any:
       """Tool implementation."""
       # Implementation code
   ```

4. **Register new categories** - If adding a new category, register it in
   `src/coauthor/modules/tools/base.py`:

   ```python
   register_tool_category("category_name", "category_name.yml")
   ```

5. **Update execute_tool** - Add the tool execution case in
   `src/coauthor/modules/tools/base.py` execute_tool() function.

### Tool Properties

- **category** (string): Logical grouping of the tool (e.g., "generic", "ansible")
- **default** (boolean, default: true): If false, tool is only loaded when
  explicitly configured or when a matching profile is active
- **profiles** (list of strings, optional): Tool is only available when the
  project/workflow uses one of the specified profiles

### Tool Environment Setup

Tools that require shell environment initialization (e.g., virtualenv activation,
sourcing bashrc) should use the utility functions in `tool_utils.py`:

```python
from coauthor.modules.tool_utils import build_tool_command, execute_tool_command

def my_tool(project: Dict[str, Any], ...) -> Any:
    """Tool implementation requiring environment setup."""
    project_path = os.path.expanduser(project.get("path", os.getcwd()))
    base_command = "my-command --args"
    cmd = build_tool_command(base_command, project)

    try:
        result = execute_tool_command(cmd, project_path, project=project)
        return process_result(result)
    except subprocess.CalledProcessError as exception_error:
        return handle_error(exception_error)
```

The utility functions automatically:

- Load `tool_environment` from project configuration
- Prepend environment setup commands to the base command
- Execute with `/bin/bash` (or configured `tool_shell`)
- Support `source` command for bashrc and virtualenv activation

Configuration example in `.coauthor.yml`:

```yaml
# Multi-project configuration with project-level tool environments
projects:
  - name: my-project
    path: ~/git/my-project
    tool_environment: |
      source ~/.bashrc
      source ~/venvs/my-project/bin/activate
    tool_shell: /bin/bash  # Optional, defaults to /bin/bash

  - name: other-project
    path: ~/git/other-project
    tool_environment: |
      source ~/.bashrc
      source ~/venvs/other-project/bin/activate

# Or at root level for single project
tool_environment: |
  source ~/.bashrc
  source ~/.virtualenv/myenv/bin/activate
tool_shell: /bin/bash
```

**Key benefits:**

- Eliminates code duplication across tool implementations
- Provides consistent environment setup behavior
- Enables tools to work with virtual environments
- Supports custom shell configurations
- **Correctly supports multi-project configurations** - Each project can have its own tool environment

**Usage guidelines:**

- Tool functions should accept `project` dict parameter (not just `project_path`)
- Use `build_tool_command(base_command, project)` to construct commands with environment setup
- Use `execute_tool_command(cmd, project_path, project=project)` to run commands
- Handle `subprocess.CalledProcessError` for command failures
- Return tool-specific error messages from your implementation

**Architecture notes:**

- The `project` dict comes from the config object parsed by `expand_paths()` in `src/coauthor/utils/config.py`
- Do not re-read `.coauthor.yml` from disk in tool implementations
- The config object is the single source of truth for all project settings

### Workflow Tools

#### start_workflow Tool

The `start_workflow` tool enables workflow composition and cross-project workflow
execution. It allows one workflow to invoke another workflow, either within the
same project or in a different project.

**Tool Definition:**

```yaml
- name: start_workflow
  category: generic
  default: true
  description: Starts a specified workflow in the project.
  parameters:
    type: object
    properties:
      project_name:
        type: string
        description: Name of the project containing the workflow.
      workflow:
        type: string
        description: Name of the workflow to start.
      user_message:
        type: string
        description: Initial user message or context for the workflow.
    required: [project_name, workflow, user_message]
```

**Usage Examples:**

**Same-project workflow invocation:**
```yaml
workflows:
  - name: main-workflow
    tasks:
      - id: prepare
        type: ai
      - id: run-tests
        type: tool
        tool: start_workflow
        params:
          project_name: "my-project"
          workflow: "test-workflow"
          user_message: "Run validation tests"
```

**Cross-project workflow invocation:**
```yaml
# In coauthor project
workflows:
  - name: test-ansible-tools
    tasks:
      - id: invoke-ansible-lint
        type: tool
        tool: start_workflow
        params:
          project_name: "ansible-tools"
          workflow: "ansible-lint-workflow"
          user_message: "Lint all Ansible playbooks"
```

**Implementation Details:**

The workflow selection logic in `select_workflow()` supports:
- **project_name parameter**: Optional parameter for cross-project selection
- **Backward compatibility**: Existing calls without project_name continue to work
- **Root project support**: Can reference workflows in the root configuration
- **Error handling**: Returns None if project or workflow not found

**Configuration Structure:**

For cross-project workflow execution, configure multiple projects in `.coauthor.yml`:

```yaml
name: main-project
workflows:
  - name: orchestrator
    tasks:
      - type: tool
        tool: start_workflow
        params:
          project_name: "sub-project"
          workflow: "sub-workflow"
          user_message: "Execute sub-workflow"

projects:
  - name: sub-project
    path: /path/to/sub-project
    workflows:
      - name: sub-workflow
        tasks:
          - type: ai
            # ... task configuration
```

**Key Features:**
- **Workflow composition**: Chain multiple workflows together
- **Cross-project execution**: Invoke workflows from different projects
- **Context passing**: Pass user messages to invoked workflows
- **Nested invocation**: Workflows can start other workflows recursively
- **State preservation**: Returns to calling workflow after completion

