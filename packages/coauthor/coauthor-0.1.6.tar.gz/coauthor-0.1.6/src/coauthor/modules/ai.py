# pylint: disable=broad-exception-caught
import os
import re
import traceback
import json
import datetime
from typing import Optional, Any

from openai import OpenAI
from httpx import Client

from coauthor.utils.ai_utils import ai_messages, insert_projects_status_message, insert_available_workflows_for_task
from coauthor.modules.tools.base import execute_tool, load_task_tools
from coauthor.modules.request_history import save_messages, save_response, next_ai_request_id, next_ai_workflow_id
from coauthor.modules.summary import (
    DEFAULT_SUMMARY_SETTINGS,
    format_tool_results_for_followup,
    should_summarize,
    summarize_with_ai,
)


def get_api_credentials(task, agent):
    """Get API credentials from task (if overridden) or agent defaults.

    This function implements the provider override feature per workflow task (C2-1178).
    If task.api_key_var or task.api_url_var is set, those are used instead of the agent defaults.

    Args:
        task (dict): The current task configuration
        agent (dict): The agent configuration with default API settings

    Returns:
        tuple: (api_url, api_key)
    """
    # Check if task overrides api_key_var
    if "api_key_var" in task:
        api_key_var = task["api_key_var"]
        api_key = os.getenv(api_key_var)
    elif "api_key" in agent:
        api_key = agent["api_key"]
    else:
        api_key = os.getenv(agent["api_key_var"])

    # Check if task overrides api_url_var
    if "api_url_var" in task:
        api_url_var = task["api_url_var"]
        api_url = os.getenv(api_url_var)
    elif "api_url" in agent:
        api_url = agent["api_url"]
    else:
        api_url = os.getenv(agent["api_url_var"])

    return api_url, api_key


def _response_format_for_task(task: dict, json_mode: bool) -> Optional[dict]:
    """Return an OpenAI-style response_format dict for the current task.

    Supported task formats:

    - response_format: {type: json_object}
    - response_format: json_object
    - json: true  # backward-compatible shortcut to json_object

    If json_mode is True and no explicit response_format is configured, json_object is used.
    """

    response_format = task.get("response_format")

    if isinstance(response_format, dict):
        return response_format

    if isinstance(response_format, str):
        # Allow a shorthand string form.
        if response_format in ("json_object", "json"):
            return {"type": "json_object"}
        if response_format in ("text", "none"):
            return None

    # Backward compatible: task.json=true implies json_object.
    if task.get("json", False) or json_mode:
        return {"type": "json_object"}

    return None


def _normalize_tool_choice(tool_choice: Any, tools: Optional[list]) -> Any:
    """Normalize tool_choice to an OpenAI-compatible value.

    Accepted:
    - "auto" | "none" | "required"
    - {"type": "function", "function": {"name": "..."}}
    - "<tool_name>" (shorthand)

    If a shorthand tool name is provided, it is converted to a function tool_choice
    only when the tool is present in the offered tools list.
    """

    if tool_choice is None:
        return "auto"

    if isinstance(tool_choice, dict):
        return tool_choice

    if not isinstance(tool_choice, str):
        return tool_choice

    if tool_choice in ("auto", "none", "required"):
        return tool_choice

    if tools and any(t.get("function", {}).get("name") == tool_choice for t in tools):
        return {"type": "function", "function": {"name": tool_choice}}

    return tool_choice


def create_chat_completion_submit(
    config,
    client,
    messages,
    model,
    tools,
    tool_choice,
    logger,
    workflow_id=None,
    json_mode=False,
):
    task = config["current-task"]
    model = task.get("model", model)

    kwargs = {}
    response_format = _response_format_for_task(task, json_mode=json_mode)
    if response_format:
        kwargs["response_format"] = response_format

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice

    api_url, _api_key = get_api_credentials(task, config["agent"])
    logger.debug(f"kwargs: {kwargs}")
    start_time = datetime.datetime.now()
    request_id = next_ai_request_id()
    logger.info(f"Submit AI request {request_id} {len(messages)} messages to {api_url} / {model}")
    save_messages(messages, model, kwargs, logger, workflow_id)

    max_retries = 3
    response = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(messages=messages, model=model, **kwargs)
            save_response(response, logger, workflow_id)
            end_time = datetime.datetime.now()
            duration = (end_time - start_time).seconds
            logger.info(f"Response for {request_id} received after {duration} seconds")
            message = response.choices[0].message
            tool_calls = message.tool_calls

            # Enhanced content extraction
            content = message.content
            if content is None or not content.strip():
                if hasattr(message, "reasoning") and message.reasoning:
                    content = message.reasoning
                elif (
                    hasattr(message, "reasoning_details")
                    and message.reasoning_details
                    and len(message.reasoning_details) > 0
                ):
                    reasoning_detail = message.reasoning_details[0]
                    if hasattr(reasoning_detail, "text") and reasoning_detail.text:
                        content = reasoning_detail.text
                    # For encrypted or unknown formats, we can log but proceed without error
                    else:
                        logger.warning("Reasoning details present but no extractable text.")
                        content = ""
            content = content.strip() if content else None

            return tool_calls, content, message

        except Exception as exception_error:
            logger.error(f"Attempt {attempt+1} failed: {exception_error}")
            if hasattr(exception_error, "response") and response is not None and hasattr(response, "content"):
                logger.error(f"Raw response: {response.content}")
            if attempt == max_retries - 1:
                raise


def is_duplicate_tool_call(messages, tool_call):
    tool_name = tool_call.function.name
    arguments = tool_call.function.arguments
    # Find the most recent previous assistant message
    for msg in reversed(messages):
        if msg["role"] == "assistant" and "tool_calls" in msg:
            for prev_tool_call in msg["tool_calls"]:
                prev_name = prev_tool_call["function"]["name"]
                prev_args = prev_tool_call["function"]["arguments"]
                if prev_name == tool_name and prev_args == arguments:
                    return True
            return False  # Checked the most recent, no match, not duplicate
    return False  # No previous assistant found


def has_context_message(messages, project=None):
    if project is None:
        for msg in messages:
            if msg["role"] == "user" and "Project context from COAUTHOR.md" in msg["content"]:
                return True
    else:
        for msg in messages:
            if msg["role"] == "user" and f"Project context for {project} from COAUTHOR.md" in msg["content"]:
                return True
    return False


def _get_summary_settings(task: dict) -> dict:
    summary_settings = task.get("summary")
    if not isinstance(summary_settings, dict):
        return DEFAULT_SUMMARY_SETTINGS.copy()

    merged = DEFAULT_SUMMARY_SETTINGS.copy()
    merged.update(summary_settings)
    return merged


def _system_messages(messages):
    return [m for m in messages if m.get("role") == "system"]


def _collect_unique_projects_from_tool_calls(tool_calls):
    unique_projects = set()
    for tc in tool_calls:
        try:
            args = json.loads(tc.function.arguments)
        except Exception:  # pylint: disable=broad-exception-caught
            continue
        project = args.get("project_name")
        if project:
            unique_projects.add(project)
    return unique_projects


def _append_project_contexts(config, messages, logger, tool_calls, tools):
    # Collect unique projects from tool calls
    unique_projects = _collect_unique_projects_from_tool_calls(tool_calls)

    # Add context for each project if not already present
    for project in unique_projects:
        if not has_context_message(messages, project):
            try:
                context = execute_tool(config, "get_context", {"project_name": project}, logger)
                context_message = {
                    "role": "user",
                    "content": f"Project context for {project} from COAUTHOR.md:\n{context}",
                }
                messages.append(context_message)
            except Exception as error:
                logger.error(f"Failed to get context for {project}: {error}")


def _maybe_summarize_after_tool_calls(
    config,
    client,
    logger,
    messages,
    tool_results,
):
    task = config["current-task"]
    agent = config.get("agent", {})

    settings = _get_summary_settings(task)
    if not settings.get("enabled", False):
        return None

    request_count = int(task.get("_coauthor_request_count", 0))
    summarize_after = int(settings.get("summarize_after", DEFAULT_SUMMARY_SETTINGS["summarize_after"]))
    summarize_every = int(settings.get("summarize_every", DEFAULT_SUMMARY_SETTINGS["summarize_every"]))

    if not should_summarize(request_count, summarize_after, summarize_every):
        return None

    summary_model = task.get("summary_model") or agent.get("summary_model")
    if not summary_model:
        logger.warning("summary.enabled is true, but no agent.summary_model configured; skipping summarization.")
        return None

    existing_summary = task.get("_coauthor_summary", "")

    summary_result = summarize_with_ai(
        client=client,
        summary_model=summary_model,
        messages=messages,
        logger=logger,
        settings=settings,
        existing_summary=existing_summary,
    )
    if not summary_result:
        return None

    task["_coauthor_summary"] = summary_result.summary

    max_tool_results_chars = int(
        settings.get("max_tool_results_chars", DEFAULT_SUMMARY_SETTINGS["max_tool_results_chars"])
    )
    tool_results_message, tool_results_truncated = format_tool_results_for_followup(
        tool_results, max_tool_results_chars
    )
    if tool_results_truncated:
        logger.warning("Tool results message was truncated by guardrails (max_tool_results_chars).")

    reduced_messages = []
    reduced_messages.extend(_system_messages(messages))
    reduced_messages.append({"role": "user", "content": summary_result.summary})
    reduced_messages.append({"role": "user", "content": tool_results_message})

    return reduced_messages


def create_chat_completion(config, client, messages, logger, tools=None, workflow_id=None, json_mode=False):
    model = config["agent"]["model"]
    task = config["current-task"]

    configured_tool_choice = task.get("tool_choice")
    if configured_tool_choice is None and task.get("tool"):
        configured_tool_choice = task.get("tool")
    if configured_tool_choice is None:
        configured_tool_choice = "auto"

    tool_choice = _normalize_tool_choice(configured_tool_choice, tools)

    # If the task is configured for JSON output, force it on the first request too.
    json_mode = bool(json_mode or task.get("json", False) or task.get("response_format"))
    logger.debug(f"Task {task['id']} json_mode:{json_mode}")

    try:
        tool_calls, content, _message = create_chat_completion_submit(
            config, client, messages, model, tools, tool_choice, logger, workflow_id, json_mode
        )

        task["_coauthor_request_count"] = int(task.get("_coauthor_request_count", 0)) + 1

        if tool_calls:
            # Append the assistant's message including tool_calls
            assistant_message = {
                "role": "assistant",
                "content": content,
                "tool_calls": [tc.model_dump() for tc in tool_calls],
            }
            messages.append(assistant_message)

            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                if is_duplicate_tool_call(messages[:-1], tool_call):  # Check previous messages
                    logger.error(
                        f"Duplicate tool call detected: {tool_name} with arguments {tool_call.function.arguments}"
                    )
                    tool_results.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_name,
                            "content": "Duplicate tool call skipped. This call was already executed.",
                        }
                    )
                    continue

                tool_def = next((t for t in tools if t["function"]["name"] == tool_name), None)
                if tool_def is None:
                    raise ValueError(f"Tool definition not found for {tool_name}")
                result = execute_tool(
                    config,
                    tool_name,
                    json.loads(tool_call.function.arguments),
                    logger,
                )
                tool_content = json.dumps(result) if result is not None else '{"status": "success"}'
                tool_results.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": tool_content,
                    }
                )
                logger.debug(f"Executed tool: {tool_name} with result: {result}")

            messages.extend(tool_results)

            _append_project_contexts(config, messages, logger, tool_calls, tools)

            reduced_messages = _maybe_summarize_after_tool_calls(
                config=config,
                client=client,
                logger=logger,
                messages=messages,
                tool_results=tool_results,
            )
            if reduced_messages is not None:
                messages = reduced_messages

            return create_chat_completion(
                config, client, messages, logger, tools=tools, workflow_id=workflow_id, json_mode=True
            )  # Recurse for final response

        return content

    except Exception as error:
        logger.error(f"Error: {error}")
        logger.error(traceback.format_exc())
        raise


def run_ai_task(config, logger):
    """Submit content to OpenAI API for processing."""
    task = config["current-task"]
    workflow = config["current-workflow"]
    logger.info(f"Preparing AI processing for workflow {workflow['name']} " + f"task {task['id']}")
    logger.debug(f"Default model (via agent.model) is {config['agent']['model']}")
    agent = config["agent"]
    logger.debug(f"agent: {agent}")

    tools = load_task_tools(config, logger)

    api_url, api_key = get_api_credentials(task, agent)
    logger.debug(f"api_url: {api_url}, api_key: {api_key}")

    disable_ssl = agent.get("disable_ssl_verification", False)
    http_client = Client(verify=not disable_ssl) if disable_ssl else None

    client = OpenAI(api_key=api_key, base_url=api_url, http_client=http_client)

    workflow_id = next_ai_workflow_id()

    messages = ai_messages(config, logger)

    # Insert projects status message
    insert_projects_status_message(messages, config, logger)
    insert_available_workflows_for_task(messages, config, task, logger)

    if not messages:
        logger.error("No messages to submit to AI")
        return
    for message in messages:
        log_message = re.sub(r"[\r\n]+", " ", message["content"])[:100]
        logger.info(f"{message['role']} → {log_message}")

    json_mode = bool(task.get("json", False) or task.get("response_format"))
    content = create_chat_completion(
        config,
        client,
        messages,
        logger,
        tools=tools,
        workflow_id=workflow_id,
        json_mode=json_mode,
    )
    task["response"] = content
