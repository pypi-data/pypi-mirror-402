import os
import re
import time
import yaml
import json
from threading import Thread
from collections import defaultdict
from jira import JIRA, JIRAError
from coauthor.utils.workflow_utils import (
    get_workflows_that_watch,
)
from coauthor.utils.jira_utils import (
    jira_unanswered_comments,
    jira_ticket_last_comment_if_matches,
    execute_jira_query,
    get_jira_connection,
    jira_add_comment,
    get_assigned_tickets,
    jira_update_description_summary,
    jira_assign_to_creator,
)
from coauthor.modules.ai import run_ai_task


def parse_ai_response(response, logger):
    """Parse an AI response that is expected to be JSON.

    The Jira integration expects the model output to be a JSON object, e.g.
    {"comment": "..."} or {"summary": "...", "description": "..."}.

    Some models still wrap JSON in Markdown fences; we attempt to unwrap those.
    """

    log_message = re.sub(r"[\r\n]+", " ", str(response))[:100]
    logger.info(f"AI response → {log_message}")

    if response is None:
        return None
    if isinstance(response, dict):
        return response
    if not isinstance(response, str):
        return None

    candidate = response.strip()
    if not candidate:
        return None

    # 1) Direct JSON
    try:
        return json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        pass

    # 2) Markdown fenced code blocks
    fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", candidate, re.DOTALL)
    if fenced_match:
        try:
            return json.loads(fenced_match.group(1))
        except (json.JSONDecodeError, TypeError):
            pass

    # 3) Best-effort: take substring between first '{' and last '}'
    first_brace = candidate.find("{")
    last_brace = candidate.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(candidate[first_brace : last_brace + 1])
        except (json.JSONDecodeError, TypeError):
            pass

    logger.error("Error parsing JSON response: invalid JSON")
    return None


def _normalize_watch_rules(value):
    """Normalize watch rules configuration.

    Supports:
    - list of rule dicts
    - single rule dict
    - None
    """

    if not value:
        return []
    if isinstance(value, list):
        return [rule for rule in value if isinstance(rule, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _merge_labels(*label_lists):
    merged = []
    for labels in label_lists:
        if not labels:
            continue
        for label in labels:
            if label not in merged:
                merged.append(label)
    return merged or None


def _add_invalid_json_comment(config, logger, ticket, mode: str):
    """Add a Jira comment to mark the item as processed and prevent loops.

    This comment intentionally does NOT contain the trigger patterns (e.g.
    [~coauthor]), so rule-based comment selection will not re-trigger.
    """

    text = (
        "Coauthor could not parse the AI output as valid JSON.\n\n"
        "Please ensure the selected model/endpoint supports JSON mode / response_format, "
        "or adjust the prompt.\n\n"
        f"Expected keys for this operation: {mode}."
    )
    jira_add_comment(config, logger, ticket, text, labels=["coauthor-error"], labels_remove=None)


task_type_functions = {
    "ai": run_ai_task,
}


def watch(config, logger):
    logger.info("Watching Jira workflows")
    new_thread = Thread(target=watch_jira, args=(config, logger))
    new_thread.start()


def watch_jira(config, logger):
    workflows_that_watch_jira = get_workflows_that_watch(config, logger, "jira")
    while True:
        for workflow in workflows_that_watch_jira:
            config["current-workflow"] = workflow
            jira_config = workflow["watch"]["jira"]
            sleep_time = jira_config.get("sleep", 15)
            logger.debug(f"Starting thread for workflow {workflow['name']}, sleep {sleep_time} seconds")
            process_jira_comments(config, logger)
            process_jira_tickets(config, logger)
            time.sleep(sleep_time)


def process_jira_comments(config, logger):
    workflow = config["current-workflow"]
    jira_config = workflow["watch"]["jira"]
    jira_url = jira_config.get("url") or os.environ.get("COAUTHOR_JIRA_URL")
    disable_ssl_verification = jira_config.get("disable_ssl_verification", False)

    logger.debug(f"Checking Jira in workflow {workflow['name']}")

    comment_rules = _normalize_watch_rules(jira_config.get("comments"))

    if not jira_url:
        logger.error(f"JIRA URL missing. Skipping. jira_config: {jira_config}")
        return

    jira_instance = get_jira_connection(jira_url, logger, disable_ssl_verification=disable_ssl_verification)
    config["current-jira-instance"] = jira_instance
    if not jira_instance:
        return

    # Rule-based mode: drive selection via configured rules/queries.
    # "Unanswered" semantics are determined by checking whether the *last* comment matches content_patterns.
    if comment_rules:
        content_patterns = workflow.get("content_patterns")
        for rule in comment_rules:
            jira_query = rule.get("query")
            if not jira_query:
                logger.error(f"Jira comments rule missing query. rule: {rule}")
                continue
            logger.debug(f"jira_query (comments rule): {jira_query}")

            all_tickets = execute_jira_query(jira_instance, jira_query, logger)
            if not all_tickets:
                logger.debug("No Jira tickets found")
                continue

            tickets_to_process = []
            for ticket in all_tickets:
                matching_comment = jira_ticket_last_comment_if_matches(ticket, content_patterns, logger)
                if matching_comment is None:
                    continue
                tickets_to_process.append({"ticket": ticket, "comment": matching_comment})

            if not tickets_to_process:
                logger.debug("No Jira tickets with unanswered trigger comment found")
                continue

            ticket_list = [
                f"{ticket['ticket'].key} - {ticket['ticket'].fields.summary}" for ticket in tickets_to_process
            ]
            logger.info(f"Found tickets for comment processing: {', '.join(ticket_list)}")
            for ticket in tickets_to_process:
                config["current-ticket"] = ticket["ticket"]
                config["current-comment"] = ticket["comment"]
                config["current-jira-rule"] = {"mode": "comments", **rule}
                get_related_tickets(config, logger, ticket["ticket"])
                handle_jira_comments(config, logger)
        return

    # Legacy mode: time-based query + unanswered-comment detection using COAUTHOR_JIRA_USERNAME.
    jira_query = jira_config.get("query", "updated >= -0.3h OR created >= -0.3h")
    logger.debug(f"jira_query: {jira_query}")
    if not jira_query:
        logger.error(f"JIRA query missing. Skipping. jira_config: {jira_config}")
        return

    all_tickets = execute_jira_query(jira_instance, jira_query, logger)
    if not all_tickets:
        logger.debug("No Jira tickets found")
        return

    tickets = jira_unanswered_comments(config, logger, all_tickets)
    if not tickets:
        logger.debug("No Jira tickets with a content match found")
        return

    ticket_list = [f"{ticket['ticket'].key} - {ticket['ticket'].fields.summary}" for ticket in tickets]
    logger.info(f"Found tickets with unanswered comments: {', '.join(ticket_list)}")
    for ticket in tickets:
        config["current-ticket"] = ticket["ticket"]
        config["current-comment"] = ticket["comment"]
        if "current-jira-rule" in config:
            del config["current-jira-rule"]
        get_related_tickets(config, logger, ticket["ticket"])
        handle_jira_comments(config, logger)


def handle_jira_comments(config, logger):
    comment = config["current-comment"]
    ticket = config["current-ticket"]
    workflow = config["current-workflow"]

    current_rule = config.get("current-jira-rule") if isinstance(config.get("current-jira-rule"), dict) else {}
    rule_add_labels = current_rule.get("add_labels")
    rule_remove_labels = current_rule.get("remove_labels")

    logger.info(f"Processing ticket {ticket.key}")
    for task in workflow["tasks"]:
        task["current-ticket"] = ticket
        task["related-tickets"] = config["related-tickets"]
        task["current-comment"] = comment
        logger.debug(f"task: {task}")
        if task["type"] in task_type_functions:
            config["current-task"] = task
            task["json"] = True
            logger.debug(f"Workflow: {workflow['name']}, Task: {task['id']} → {ticket.key}")
            task_type_functions[task["type"]](config, logger)
            response = task["response"]
            response_json = parse_ai_response(response, logger)
            if response_json and isinstance(response_json, dict):
                if "comment" in response_json:
                    comment_text = response_json["comment"]
                    response_labels = response_json.get("labels", None)
                    response_labels_remove = response_json.get("labels_remove", None)

                    labels = _merge_labels(response_labels, rule_add_labels)
                    labels_remove = _merge_labels(response_labels_remove, rule_remove_labels)

                    jira_add_comment(config, logger, ticket, comment_text, labels, labels_remove)
                else:
                    logger.error("Response JSON missing 'comment' key")
                    _add_invalid_json_comment(config, logger, ticket, mode="comment")
            else:
                logger.error("Invalid response for comment processing")
                _add_invalid_json_comment(config, logger, ticket, mode="comment")
        else:
            raise ValueError(f'Unsupported task_type: {task["type"]}')


def get_related_tickets(config, logger, ticket):
    jira_instance = config["current-jira-instance"]
    workflow = config["current-workflow"]
    jira_config = workflow["watch"]["jira"]
    related = {}

    if hasattr(ticket.fields, "parent") and ticket.fields.parent:
        try:
            related["parent"] = jira_instance.issue(ticket.fields.parent.key, fields="summary,description")
        except JIRAError as jira_error:
            logger.error(f"Failed to fetch parent for {ticket.key}: {jira_error}")

    # Get configured epic field or use default
    epic_field = jira_config.get("custom_fields", {}).get("epic")
    if not epic_field:
        logger.error(
            "Epic field access requested but jira.custom_fields.epic is not configured. "
            "Add configuration: workflows[].watch.jira.custom_fields.epic"
        )
        raise ValueError(
            "Missing required configuration: jira.custom_fields.epic. "
            "Configure this field in .coauthor.yml under workflows[].watch.jira.custom_fields.epic"
        )

    epic_key = getattr(ticket.fields, epic_field, None)
    if epic_key:
        try:
            related["epic"] = jira_instance.issue(epic_key, fields="summary,description")
        except JIRAError as jira_error:
            logger.error(f"Failed to fetch epic {epic_key} for {ticket.key}: {jira_error}")

    # Fetch linked issues
    linked_issues = []
    if hasattr(ticket.fields, "issuelinks") and ticket.fields.issuelinks:
        for link in ticket.fields.issuelinks:
            if hasattr(link, "outwardIssue") and link.outwardIssue:
                try:
                    linked_ticket = jira_instance.issue(link.outwardIssue.key, fields="summary,description")
                    linked_issues.append({"type": link.type.outward.lower(), "ticket": linked_ticket})
                except JIRAError as jira_error:
                    logger.error(f"Failed to fetch outward link {link.outwardIssue.key} for {ticket.key}: {jira_error}")
            elif hasattr(link, "inwardIssue") and link.inwardIssue:
                try:
                    linked_ticket = jira_instance.issue(link.inwardIssue.key, fields="summary,description")
                    linked_issues.append({"type": link.type.inward.lower(), "ticket": linked_ticket})
                except JIRAError as jira_error:
                    logger.error(f"Failed to fetch inward link {link.inwardIssue.key} for {ticket.key}: {jira_error}")
    related["linked"] = linked_issues

    # Now group dynamically
    grouped = defaultdict(list)
    for link in related["linked"]:
        grouped[link["type"]].append({"ticket": link["ticket"]})
    related["grouped_linked"] = dict(grouped)

    config["related-tickets"] = related


def process_jira_tickets(config, logger):
    workflow = config["current-workflow"]
    jira_config = workflow["watch"]["jira"]
    jira_url = jira_config.get("url") or os.environ.get("COAUTHOR_JIRA_URL")
    disable_ssl_verification = jira_config.get("disable_ssl_verification", False)

    logger.debug(f"Checking Jira tickets in workflow {workflow['name']}")

    ticket_rules = _normalize_watch_rules(jira_config.get("tickets"))

    if not jira_url:
        logger.error(f"JIRA URL missing. Skipping. jira_config: {jira_config}")
        return

    if "current-jira-instance" in config:
        jira_instance = config["current-jira-instance"]
    else:
        jira_instance = get_jira_connection(jira_url, logger, disable_ssl_verification=disable_ssl_verification)
        config["current-jira-instance"] = jira_instance

    if not jira_instance:
        return

    # Rule-based mode: drive selection by explicit rule queries.
    if ticket_rules:
        for rule in ticket_rules:
            jira_query = rule.get("query")
            if not jira_query:
                logger.error(f"Jira tickets rule missing query. rule: {rule}")
                continue

            logger.debug(f"jira_query (tickets rule): {jira_query}")
            tickets = get_assigned_tickets(jira_instance, logger, query=jira_query)
            if not tickets:
                logger.debug("No Jira tickets found")
                continue

            ticket_list = [f"{ticket.key} - {ticket.fields.summary}" for ticket in tickets]
            logger.info(f"Found tickets for ticket processing: {', '.join(ticket_list)}")
            for ticket in tickets:
                config["current-ticket"] = ticket
                config["current-jira-rule"] = {"mode": "tickets", **rule}
                get_related_tickets(config, logger, ticket)
                handle_jira_tickets(config, logger)
        return

    # Legacy mode: process assigned tickets.
    tickets = get_assigned_tickets(jira_instance, logger)
    if not tickets:
        logger.debug("No assigned Jira tickets found")
        return

    ticket_list = [f"{ticket.key} - {ticket.fields.summary}" for ticket in tickets]
    logger.info(f"Found assigned tickets: {', '.join(ticket_list)}")
    for ticket in tickets:
        config["current-ticket"] = ticket
        if "current-jira-rule" in config:
            del config["current-jira-rule"]
        get_related_tickets(config, logger, ticket)
        handle_jira_tickets(config, logger)


def handle_jira_tickets(config, logger):
    ticket = config["current-ticket"]
    workflow = config["current-workflow"]

    current_rule = config.get("current-jira-rule") if isinstance(config.get("current-jira-rule"), dict) else {}
    rule_add_labels = current_rule.get("add_labels")
    rule_remove_labels = current_rule.get("remove_labels")

    assign_to_creator = current_rule.get("assign_to_creator", True)

    logger.info(f"Processing ticket {ticket.key}")
    for task in workflow["tasks"]:
        task["current-ticket"] = ticket
        task["related-tickets"] = config["related-tickets"]
        if "current-comment" in task:
            del task["current-comment"]
        logger.debug(f"task: {task}")
        if task["type"] in task_type_functions:
            logger.debug(f"Workflow: {workflow['name']}, Task: {task['id']} → {ticket.key}")
            config["current-task"] = task
            task["json"] = True
            task_type_functions[task["type"]](config, logger)
            response = task["response"]
            response_json = parse_ai_response(response, logger)
            if response_json and isinstance(response_json, dict):
                if "summary" in response_json and "description" in response_json:
                    summary = response_json["summary"]
                    description = response_json["description"]
                    response_labels = response_json.get("labels", None)
                    response_labels_remove = response_json.get("labels_remove", None)
                    story_points = response_json.get("story_points", None)

                    labels = _merge_labels(response_labels, rule_add_labels)
                    labels_remove = _merge_labels(response_labels_remove, rule_remove_labels)

                    updated = jira_update_description_summary(
                        config, logger, ticket, summary, description, story_points, labels, labels_remove
                    )

                    if updated and assign_to_creator:
                        try:
                            jira_assign_to_creator(logger, ticket)
                        except Exception as exception_error:
                            logger.error(f"Failed to assign ticket {ticket.key} to creator: {exception_error}")
                            raise ValueError(
                                f"Assignment failed for {ticket.key}: {exception_error}"
                            ) from exception_error
                else:
                    logger.error("Response JSON missing 'summary' or 'description' key")
                    _add_invalid_json_comment(config, logger, ticket, mode="summary/description")
            else:
                logger.error("Invalid response for ticket update")
                _add_invalid_json_comment(config, logger, ticket, mode="summary/description")
        else:
            raise ValueError(f'Unsupported task_type: {task["type"]}')
