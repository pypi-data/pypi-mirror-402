# Provider Override Per Workflow Task

Starting from version 0.1.4, Coauthor supports overriding the AI provider on a
per-task basis within workflows. This allows you to use different AI providers
(e.g., Azure OpenAI, OpenRouter, local models) for different tasks in the same
workflow.

## Overview

By default, all AI tasks use the credentials configured in the `agent` section
of your `.coauthor.yml`:

```yaml
agent:
  model: anthropic/claude-sonnet-4.5
  api_key_var: OPENAI_API_KEY
  api_url_var: OPENAI_API_URL
```

However, you can override `api_key_var` and `api_url_var` on individual tasks
to use a different provider for specific workflow steps.

## Use Cases

- **Cost optimization**: Use cheaper models for simple tasks and premium models
  for complex reasoning
- **Provider-specific features**: Leverage unique capabilities of different AI
  providers
- **Fallback providers**: Switch to alternative providers when one is
  unavailable
- **Testing**: Compare outputs from different models in the same workflow

## Configuration

### Task-level Override

Add `api_key_var` and/or `api_url_var` to any AI task in your workflow:

```yaml
workflows:
  - name: implementation
    description: Implement a user story with multiple AI providers
    tasks:
      - id: impact-analysis
        type: ai
        model: deepseek/deepseek-v3.2
        api_key_var: DEEPSEEK_API_KEY
        api_url_var: DEEPSEEK_API_URL
        tools: [list_tracked_files, get_files]

      - id: implement-changes
        type: ai
        model: gpt-4.1
        api_key_var: AZURE_OPENAI_API_KEY
        api_url_var: AZURE_OPENAI_API_URL
        tools_exclude: [get_context, update_context]

      - id: create-tests
        type: ai
        model: anthropic/claude-sonnet-4.5
        # No override - uses agent defaults
        tools: [write_files, run_pytest]
```

### Environment Variables

Make sure the environment variables referenced in your configuration are set:

```bash
# Default provider (used by agent and tasks without overrides)
export OPENAI_API_KEY="your-default-key"
export OPENAI_API_URL="https://api.openai.com/v1"

# Task-specific providers
export DEEPSEEK_API_KEY="your-deepseek-key"
export DEEPSEEK_API_URL="https://api.deepseek.com"

export AZURE_OPENAI_API_KEY="your-azure-key"
export AZURE_OPENAI_API_URL="https://your-resource.openai.azure.com"
```

## How It Works

When an AI task is executed:

1. Coauthor checks if the task has `api_key_var` or `api_url_var` defined
2. If present, those environment variables are used for that task
3. If not present, the agent defaults from the `agent` section are used
4. Each task uses its own credentials independently

This means you can mix and match providers freely within a single workflow.

## Example: Multi-Provider Workflow

Here's a practical example using three different providers for different tasks:

```yaml
agent:
  model: anthropic/claude-sonnet-4.5
  api_key_var: OPENAI_API_KEY
  api_url_var: OPENAI_API_URL

workflows:
  - name: code-review
    description: Multi-provider code review workflow
    tasks:
      - id: analyze-code
        type: ai
        message: Analyze the code for potential issues
        model: deepseek/deepseek-v3.2
        api_key_var: DEEPSEEK_API_KEY
        api_url_var: DEEPSEEK_API_URL
        tools: [list_tracked_files, get_files, search_files]

      - id: suggest-improvements
        type: ai
        message: Based on the analysis, suggest improvements
        model: gpt-4.1
        api_key_var: AZURE_OPENAI_API_KEY
        api_url_var: AZURE_OPENAI_API_URL
        tools: [get_diffs, write_files]

      - id: write-documentation
        type: ai
        message: Write documentation for the changes
        # Uses default agent credentials (Claude)
        tools: [write_files]
```

## Validation

If a task-level override references an environment variable that doesn't exist,
Coauthor will attempt to use it but the OpenAI client will fail with an
appropriate error message. Make sure all referenced environment variables are
set before running workflows.

## Troubleshooting

### Issue: "Response input messages must contain the word 'json' in some form"

This error occurs when:
- A task uses `response_format: json_object`
- But the prompt doesn't mention JSON

**Solution**: Only use `response_format: json_object` on tasks that actually
need JSON output (like Jira integration). Don't inherit this setting from parent
workflows.

### Issue: Wrong provider is being used

Check the logs to see which `api_url` is being used:

```
INFO - Submit AI request 4514 6 messages to https://api.openai.com/v1 / gpt-4.1
```

If the wrong URL appears, verify:
1. The task has the correct `api_url_var` setting
2. The environment variable is set and exported
3. The environment variable name is correct (case-sensitive)

## Related Features

- **Model override per task**: Use the `model` field to specify different models
  per task
- **Tool override per task**: Use `tools` or `tools_exclude` to control which
  tools are available
- **Workflow composition**: Use `start_workflow` tool to chain workflows with
  different providers

## See Also

- [Configuration File](configuration_file.md)
- [Workflows](workflows.md)
- [AI Task Configuration](ai_tasks.md)
