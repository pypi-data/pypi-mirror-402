"""Utilities for summarizing an interaction's message stack.

This module implements *ephemeral* summarization: - No persistence of summary
state to disk. - Intended to reduce prompt size between tool-call iterations.

The summary model is configured under agent.summary_model (e.g. in
.coauthor.yml). Summarization timing is configured per AI task via task.summary.

Example:

    tasks:
      - id: ticket type: ai summary:
          enabled: true summarize_after: 1 summarize_every: 3

Refactor (2025-12-21): - Only summarize tool calls: user messages are *excluded*
from summarization, except the first 3 user messages (always retained). - A
summary is generated only for tool calls (assistant/tool messages), if there are
at least three tool call requests. The last tool call (and response) is never
summarized away. - Summarization logic and configuration moved into this module.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_SUMMARY_SETTINGS: Dict[str, Any] = {
    "enabled": False,
    "summarize_after": 1,
    "summarize_every": 3,
    # Guardrails
    "max_input_chars": 40000,
    "max_output_chars": 40000,
    "max_tool_results_chars": 12000,
}


def should_summarize(request_count: int, summarize_after: int, summarize_every: int) -> bool:
    """Return True when a summary should be generated after request_count."""
    if request_count <= 0:
        return False
    if summarize_after <= 0:
        return False
    if request_count == summarize_after:
        return True
    if request_count > summarize_after and summarize_every and summarize_every > 0:
        return (request_count - summarize_after) % summarize_every == 0
    return False


def _truncate(text: str, max_chars: int) -> Tuple[str, bool]:
    if max_chars <= 0:
        return "", bool(text)
    if len(text) <= max_chars:
        return text, False
    return text[: max_chars - 12] + "\u2026(truncated)", True


def extract_relevant_messages_for_summary(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract only tool-call related messages for summarization, keeping the
    first 3 user messages and all system messages, but skipping other
    user/assistant messages. Only assistant messages containing tool_calls and
    tool (role) messages are included. The last assistant/tool-call and last
    tool (response) are always excluded from summarization.
    """
    first_3_user_msgs = []
    system_msgs = []
    assistant_tool_calls = []
    tool_msgs = []
    user_msgs_count = 0

    # Step 1: classify
    for msg in messages:
        role = msg.get("role", "unknown")
        if role == "system":
            system_msgs.append(msg)
        elif role == "user":
            user_msgs_count += 1
            if len(first_3_user_msgs) < 3:
                first_3_user_msgs.append(msg)
        elif role == "assistant" and msg.get("tool_calls"):
            assistant_tool_calls.append(msg)
        elif role == "tool":
            tool_msgs.append(msg)

    # If fewer than 3 assistant tool calls, return empty list (no summarization needed)
    if len(assistant_tool_calls) < 3:
        return []

    # Exclude the last tool call and the last tool response (they are needed for the model)
    assistant_tool_calls = assistant_tool_calls[:-1]
    tool_msgs = tool_msgs[:-1] if len(tool_msgs) > 0 else []

    return system_msgs + first_3_user_msgs + assistant_tool_calls + tool_msgs


def serialize_messages_for_summary(messages: List[Dict[str, Any]]) -> str:
    """Serialize OpenAI-style messages into a compact text format."""

    chunks: List[str] = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content")
        if role == "assistant" and msg.get("tool_calls"):
            tool_calls = msg.get("tool_calls")
            chunks.append(f"{role.upper()} (tool_calls): {str(tool_calls)[:2000]}")
            continue
        if content is None:
            chunks.append(f"{role.upper()}: (no content)")
            continue
        chunks.append(f"{role.upper()}: {content}")
    return "\n\n".join(chunks)


def format_tool_results_for_followup(tool_results: List[Dict[str, Any]], max_chars: int) -> Tuple[str, bool]:
    """Format tool results (role=tool messages) as a single user message."""
    parts: List[str] = [
        "Tool results (from the previous step):",
    ]
    for result in tool_results:
        tool_name = result.get("name", "unknown")
        content = result.get("content", "")
        parts.append(f"- {tool_name}:\n{content}")
    text = "\n\n".join(parts)
    return _truncate(text, max_chars)


@dataclass
class SummaryResult:
    summary: str
    input_truncated: bool
    output_truncated: bool


def summarize_with_ai(
    client: Any,
    summary_model: str,
    messages: List[Dict[str, Any]],
    logger: Any,
    settings: Dict[str, Any],
    existing_summary: str = "",
) -> Optional[SummaryResult]:
    """Call the LLM to generate an updated interaction summary.

    Returns None when summarization is not possible.
    """
    if not summary_model:
        return None
    max_input_chars = int(settings.get("max_input_chars", DEFAULT_SUMMARY_SETTINGS["max_input_chars"]))
    max_output_chars = int(settings.get("max_output_chars", DEFAULT_SUMMARY_SETTINGS["max_output_chars"]))
    serialized = serialize_messages_for_summary(messages)
    input_text = "Existing summary (may be empty):\n" f"{existing_summary}\n\n" "New messages/events:\n" f"{serialized}"
    input_text, input_truncated = _truncate(input_text, max_input_chars)
    system_prompt = (
        "You are a summarization component used by an automation agent. "
        "Create an UPDATED summary that can be used as compact context for the next request.\n\n"
        "Rules:\n"
        "- Keep it concise and information-dense.\n"
        "- Prefer short bullet points.\n"
        "- Capture: user goal, constraints/guardrails, decisions, relevant file paths, work done, next steps.\n"
        "- Include outcomes of tool calls at a high level (no raw dumps).\n"
        "- Do not repeat the entire ticket text or full logs.\n"
        f"- Hard limit: {max_output_chars} characters.\n"
    )
    try:
        response = client.chat.completions.create(
            model=summary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text},
            ],
        )
        content = response.choices[0].message.content or ""
        content = content.strip()
        content = "What follows below is a AI summary of tool calls:\n\n" + content
        truncated_text, output_truncated = _truncate(content, max_output_chars)
        if input_truncated:
            logger.warning(
                "Summary prompt input was truncated by guardrails "
                + f"({len(input_text)} > max_output_chars {max_output_chars})."
            )
        if output_truncated:
            logger.warning("Summary output was truncated by guardrails (max_output_chars).")
        return SummaryResult(
            summary=truncated_text,
            input_truncated=input_truncated,
            output_truncated=output_truncated,
        )
    except Exception as exception_error:  # pylint: disable=broad-exception-caught
        logger.error(f"Summary model call failed: {exception_error}")
        return None
