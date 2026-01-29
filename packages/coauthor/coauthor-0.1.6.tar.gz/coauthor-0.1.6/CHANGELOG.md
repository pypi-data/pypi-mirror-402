# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Changes are added to the top of each section (newest first) for easier reading.
<!-- start changelog -->

## 0.1.6 ( 2026-01-19 )

### Changed

- Made Jira custom fields configurable via `.coauthor.yml`:
  - Custom field IDs for Epic and Story Points are now configurable under
    `workflows[].watch.jira.custom_fields` section
  - Removed hard-coded custom field IDs from `jira_watcher.py` and
    `jira_utils.py`

## 0.1.5 ( 2026-01-16 )

- Support bearer token authentication with PAT for Jira integration.

## 0.1.4 ( 2026-01-16 )

- Automatic context injection from file frontmatter without explicit
  configuration:
  - Supports `coauthor.context` blocks in any file type (.md, .py, .js, .go,
    etc.)
  - Context types: `file`, `dir`, `url`, `rellink` (Hugo content paths)
  - Eliminates need for complex Jinja templates and `.coauthor.yml`
    configuration for context injection
- Added comprehensive verification test suite for automatic Git staging
  functionality:
  - Created `tests/test_git_staging_verification_c2_1247.py` with 13 additional
    verification tests
  - Tests cover edge cases and integration scenarios not covered in original
    test suite
  - Verification areas include:
    - Immediate visibility of new files via `list_tracked_files`
    - Batch staging operations with `write_files`
    - Git tracking behavior during `move_files` operations
    - Complex `.gitignore` pattern matching
    - Concurrent/consecutive file operations
    - Deep nested directory staging
    - Special characters in filenames
    - Empty file handling
    - Large batch operations (50+ files)
    - Overwriting staged but uncommitted files
    - Mixed new and existing file operations
  - All tests verify that Git staging respects `.gitignore` rules and provides
    graceful degradation
  - Complements existing 17 tests in `tests/test_git_staging_c2_1245.py` for
    total coverage of 30 test cases
- Implemented automatic Git staging for file operations to improve AI feedback
  loop:
  - `write_file` now automatically stages new files in Git after creation
  - `write_files` stages all newly created files
  - `move_files` stages files at their new location after moving
  - Staged files immediately become visible via `list_tracked_files`, enabling
    AI to see and verify changes
  - Git staging respects `.gitignore` rules (ignored files are not staged)
  - Graceful degradation: operations succeed even in non-Git repositories or on
    Git errors (warnings logged only)
  - Added optional `logger` parameter to `write_file`, `write_files`, and
    `move_files` for debugging Git staging issues
  - Implemented `_git_add_file()` helper function for safe Git staging with
    error handling
  - Updated `execute_tool()` in `base.py` to pass logger to file operation tools
  - Comprehensive test coverage with 17 new tests in
    `tests/test_git_staging_c2_1245.py` covering:
    - Basic staging functionality for new and moved files
    - Nested directory handling
    - `.gitignore` respect
    - Non-Git repository graceful handling
    - Multiple file operations
    - JSON string parameter support
    - Backward compatibility (logger parameter is optional)
- Fixed TypeError in write_files tool when OpenAI returns
  JSON-escaped string instead of array. Added robust input validation with type
  checking and JSON parsing in both `generic.write_files()` and
  `base.execute_tool()` to prevent infinite retry loops.
- Fixed tool environment setup for multi-project configurations.
- Improved `insert_projects_status_message` that shows a message that a project
  is read-only when `read-only: true` is present.
- Improved `get_projects` that puts the main project on top of the list.
- Fixed profile-based tools (ansible_lint, ansible_module_doc) now loading
  correctly when project profile matches, even without `include_non_default:
  true`.
- Raise `ValueError` on "unknown tools".
- Fixed workflow selection to support cross-project workflow execution.
- Refactor tool environment setup to create reusable utility for Bash shell
  initialization.
- Refactored tools system to support categorization, Ansible-specific tools,
  default and profile options:

  **New Modular Architecture:**
  - Created `src/coauthor/config/tools/` directory for modular tool
    configurations with category-based organization
  - Created `src/coauthor/modules/tools/` directory for modular tool
    implementations with logical separation
  - Implemented tool category registry system with extensible registration
  - Split tools into categories: `generic.yml` (18 existing tools) and
    `ansible.yml` (2 new tools)

  **New Ansible-Specific Tools:**
  - `ansible_lint`: Run ansible-lint on playbooks, roles, and collections with
    support for custom config files and JSON-formatted results
  - `ansible_module_doc`: Retrieve documentation for Ansible modules with
    support for multiple output formats (JSON, YAML, Markdown)
  - Both tools include graceful degradation when ansible-lint/ansible-doc not
    installed
  - Configured for profiles: `ansible-collection`, `ansible`, `ops`, `ci`

  **Tool Properties and Filtering:**
  - Implemented optional `default` property in tool schema (default: true):
    - Non-default tools only loaded when explicitly configured via
      `include_non_default: true` or when project/workflow profile matches
    - Tools without explicit `default` property are treated as `default: true`
    - All generic tools have `default: true`; Ansible tools have `default: false`
  - Implemented optional `profiles` property (list of profile names):
    - Tools only available when project/workflow matches one of the specified
      profiles
    - Enables profile-specific tool sets without explicit configuration
  - Filtering logic: default filtering applied before profile filtering

  **Core Infrastructure:**
  - Created `src/coauthor/modules/tools/base.py` with:
    - `register_tool_category()`: Register new tool categories dynamically
    - `load_tools_from_category()`: Load tools from specific categories
    - `filter_tools_by_default()`: Filter tools based on default property
    - `filter_tools_by_profile()`: Filter tools based on profile matching
    - Updated `load_tools()`: Load from multiple categories with filtering
    - Updated `load_task_tools()`: Support profile and default filtering
    - Updated `execute_tool()`: Support Ansible tools execution
  - Moved all generic tool implementations to
    `src/coauthor/modules/tools/generic.py` (18 tools: file operations, git
    operations, search, context, utilities, workflow)
  - Created `src/coauthor/modules/tools/ansible.py` with Ansible tool
    implementations
  - Updated `src/coauthor/modules/tools/__init__.py` to export tool functions

  **Documentation:**
  - Updated `COAUTHOR.md` with comprehensive tool development guidelines:
    - Modular tools system architecture
    - How to add new tools with step-by-step instructions
    - Tool properties: category, default, profiles
    - How to register new categories

  **Testing:**
  - Created `tests/modules/test_tools.py` with 29 tests covering:
    - Tool category registration and loading
    - Default property filtering (with/without include_non_default)
    - Profile property filtering and matching
    - Task-specific tool loading with overrides
    - Edge cases and error handling
  - Created `tests/modules/test_tools_ansible.py` with 21 tests covering:
    - ansible_lint tool functionality and error handling
    - ansible_module_doc tool with multiple formats
    - Graceful degradation when tools not installed
    - Integration workflows using both Ansible tools
  - Created `tests/test_tools_integration.py` with 14 tests covering:
    - End-to-end tool loading with profiles and configurations
    - Task override integration
    - Tool execution through main API
    - Real-world scenarios (ansible-collection, Python projects, CI profiles)
  - **All 64 tests pass successfully** with excellent code coverage:
    - `base.py`: 82% coverage
    - `ansible.py`: 96% coverage
    - `__init__.py`: 100% coverage

---

- Added provider override per workflow task.
  - Tasks can now override `api_key_var` and `api_url_var` to use different AI
    providers per task.
  - Enables flexibility in multi-provider workflows where different tasks
    require different models or services.
  - Configuration example:
    ```yaml
    tasks:
      - description: "Task using different provider"
        api_key_var: "ALTERNATIVE_API_KEY"
        api_url_var: "ALTERNATIVE_API_URL"
    ```
  - Implemented in workflow execution logic with proper validation.

---

### Removed

- **[C2-1013]** Removed backward compatibility code for legacy tools system:
  - Deleted `src/coauthor/config/tools.yml` (deprecated monolithic
    configuration file)
  - Deleted `src/coauthor/modules/tools.py` (deprecated facade module)
  - Removed backward compatibility loading logic from
    `src/coauthor/modules/tools/base.py`
  - Updated `src/coauthor/modules/tools/__init__.py` to remove backward
    compatibility notes
  - Removed backward compatibility tests from test suites
  - Updated `COAUTHOR.md` to remove backward compatibility section
  - **Breaking change**: Code importing from `coauthor.modules.tools` must now
    use modular imports from `coauthor.modules.tools.base`,
    `coauthor.modules.tools.generic`, or `coauthor.modules.tools.ansible`
  - All tools must now be defined in category-specific YAML files under
    `src/coauthor/config/tools/`

---

## 0.1.3 ( 2026-01-15 )

### Added

- **[C2-973]** Ansible Collection profile with comprehensive configuration:
  - Profile ID: `ansible-collection`
  - Project type defaults: `Python`, `Ansible Collection`
  - Enhanced instructions for Ansible collection development best practices
  - Template variables: `{namespace}` and `{collection}`
  - Configured with generic tools for file and project management
  - Configured workflow for Ansible collection tasks
  - Documentation in COAUTHOR.md and profiles guide

- **[C2-1001]** Jira integration support:
  - Added `jira` section to configuration schema
  - Support for Jira server URL and authentication (PAT or user/password)
  - Issue tracking integration for workflows
  - Configuration validation for Jira settings
  - Documentation updated with Jira configuration examples

### Changed

- Enhanced configuration schema with optional Jira integration
- Updated documentation to include Jira setup instructions
- Improved profile system documentation with ansible-collection example

---

## 0.1.2 ( 2026-01-10 )

### Added

- Initial release with core functionality
- Support for multiple AI providers (OpenAI, Anthropic, etc.)
- Project management tools
- Workflow system
- Configuration file support (.coauthor.yml)
- Basic documentation

### Fixed

- Various bug fixes and stability improvements

---

## 0.1.1 ( 2026-01-05 )

### Fixed

- Initial bug fixes
- Documentation improvements

---

## 0.1.0 ( 2026-01-01 )

### Added

- Initial project setup
- Basic AI agent functionality
- File and directory operations
- Git integration
