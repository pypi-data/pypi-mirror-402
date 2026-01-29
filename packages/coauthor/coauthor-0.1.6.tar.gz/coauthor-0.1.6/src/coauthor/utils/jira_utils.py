import os
import re
from jira import JIRA, JIRAError
from coauthor.utils.notify import notification


def get_jira_connection(jira_url, logger, disable_ssl_verification=False):
    """Establish a connection to Jira using PAT or username/password authentication.

    Authentication priority:
    1. Personal Access Token (PAT) via COAUTHOR_JIRA_PAT - recommended
    2. Username/password via COAUTHOR_JIRA_USERNAME and COAUTHOR_JIRA_PASSWORD - fallback

    Args:
        jira_url: The base URL of the Jira instance
        logger: Logger instance for debug/error messages
        disable_ssl_verification: If True, disables SSL certificate verification (insecure)

    Returns:
        JIRA instance if connection successful, None otherwise
    """
    jira_pat = os.getenv("COAUTHOR_JIRA_PAT")
    jira_username = os.getenv("COAUTHOR_JIRA_USERNAME")
    jira_password = os.getenv("COAUTHOR_JIRA_PASSWORD")

    options = {"server": jira_url}
    if disable_ssl_verification:
        # NOTE: This disables TLS certificate verification and is insecure.
        # Only use this as a temporary workaround (e.g. in dev/test environments).
        options["verify"] = False
        logger.warning(
            "Jira SSL verification is disabled (options.verify=False). "
            "This is insecure and should only be used temporarily."
        )

    try:
        if jira_pat:
            # Use PAT authentication with Bearer token
            logger.debug("Using PAT authentication for JIRA")
            jira_instance = JIRA(options=options, token_auth=jira_pat)
        elif jira_username and jira_password:
            # Fallback to basic authentication
            logger.debug("Using basic authentication for JIRA")
            jira_instance = JIRA(options=options, basic_auth=(jira_username, jira_password))
        else:
            logger.error(
                "No JIRA authentication credentials found. "
                "Set COAUTHOR_JIRA_PAT (recommended) or "
                "COAUTHOR_JIRA_USERNAME and COAUTHOR_JIRA_PASSWORD."
            )
            return None

        logger.debug(f"Connected to JIRA at {jira_url}")
        return jira_instance
    except JIRAError as jira_error:
        logger.error(f"Failed to connect to JIRA at {jira_url}: {jira_error}")
        return None


def execute_jira_query(jira_instance, query, logger):
    try:
        issues = jira_instance.search_issues(query)
        logger.debug(f"Found {len(issues)} issues for query: {query}")
        return issues
    except (JIRAError, ValueError) as exception_error:
        logger.error(f"Error executing JIRA query: {exception_error}")
        return


def jira_ticket_unanswered_comment(ticket, content_patterns, jira_username, logger):
    comments = ticket.fields.comment.comments
    if not comments:
        return None

    last_match_index = -1
    for i, comment in enumerate(comments):
        body = comment.body
        log_message = re.sub(r"[\r\n]+", " ", body)[:100]
        logger.debug(f"{comment.author.name} → {log_message}")
        if not comment.author.name == jira_username:  # don't answer coauthor own comments
            for pattern in content_patterns:
                if re.search(pattern, body):
                    log_message = re.sub(r"[\r\n]+", " ", body)[:100]
                    logger.debug(f'{ticket.key} matches pattern "{pattern}": {log_message}')
                    last_match_index = i
                    break

    if last_match_index == -1:
        return None

    # Check if there's any comment after the last matched one by jira_username
    answered = False
    for i in range(last_match_index + 1, len(comments)):
        comment = comments[i]
        if comment.author.name == jira_username:
            answered = True
            break

    if answered:
        return None

    return comments[last_match_index]


def jira_ticket_last_matching_comment(ticket, content_patterns, logger):
    """Return the last comment that matches any of the given content_patterns.

    This is used for rule-based processing (no dedicated Jira user required for
    determining whether the comment was already answered).

    Note: this returns the last *matching* comment, not necessarily the last
    comment on the ticket.
    """

    try:
        comments = ticket.fields.comment.comments
    except AttributeError:
        return None

    if not comments:
        return None

    if not content_patterns:
        return comments[-1]

    last_match = None
    for comment in comments:
        body = comment.body or ""
        for pattern in content_patterns:
            if re.search(pattern, body):
                last_match = comment
                break

    return last_match


def jira_ticket_last_comment_if_matches(ticket, content_patterns, logger):
    """Return the ticket's last comment if it matches any content_patterns.

    This is useful when you want "unanswered" semantics without a dedicated Jira
    user:

    - If the last comment contains a trigger (matches content_patterns), process
      it.
    - If the last comment does *not* contain a trigger, assume it was answered
      (e.g. by Coauthor) and skip.
    """

    try:
        comments = ticket.fields.comment.comments
    except AttributeError:
        return None

    if not comments:
        return None

    last_comment = comments[-1]
    last_body = last_comment.body or ""

    if not content_patterns:
        return last_comment

    for pattern in content_patterns:
        if re.search(pattern, last_body):
            return last_comment

    logger.debug(f"{ticket.key} last comment does not match any content pattern; skipping")
    return None


def jira_unanswered_comments(config, logger, tickets):
    """Check Jira tickets for unanswered content matches against defined patterns in comments."""
    jira_username = os.getenv("COAUTHOR_JIRA_USERNAME")
    if not jira_username:
        logger.debug("COAUTHOR_JIRA_USERNAME is not set; unanswered-comment detection is disabled.")
        return []

    workflow = config.get("current-workflow", {})
    content_patterns = workflow.get("content_patterns")
    if not content_patterns:
        logger.debug("No content patterns defined in workflow.")
        return []

    matching_tickets = []
    for ticket in tickets:
        unanswered_comment = jira_ticket_unanswered_comment(ticket, content_patterns, jira_username, logger)
        if unanswered_comment is not None:
            matching_tickets.append({"ticket": ticket, "comment": unanswered_comment})

    return matching_tickets


def get_updated_labels(current_labels, labels=None, labels_remove=None, logger=None, ticket_key=None):
    current_labels = current_labels[:]  # copy
    changed = False

    if labels_remove:
        removed_labels = [l for l in labels_remove if l in current_labels]
        if removed_labels:
            current_labels = [l for l in current_labels if l not in labels_remove]
            logger.info(f"{ticket_key} removed labels → {', '.join(removed_labels)}")
            changed = True

    if labels:
        added_labels = [l for l in labels if l not in current_labels]
        if added_labels:
            current_labels.extend(added_labels)
            logger.info(f"{ticket_key} labels → {', '.join(added_labels)}")
            changed = True

    return current_labels, changed


def _get_ticket_labels_safe(jira_instance, ticket, logger):
    """Return current labels for a ticket without accidentally overwriting labels.

    Some JIRA API calls may return partial issue objects without all fields.
    If labels are missing, we re-fetch them explicitly.
    """

    labels = getattr(ticket.fields, "labels", None)
    if labels is None:
        try:
            refreshed = jira_instance.issue(ticket.key, fields="labels")
            labels = refreshed.fields.labels
        except Exception as exception_error:
            logger.warning(f"Failed to refresh labels for {ticket.key}: {exception_error}")
            labels = []
    return labels or []


def jira_add_comment(config, logger, ticket, content, labels=None, labels_remove=None):
    jira_instance = config["current-jira-instance"]
    try:
        comment = jira_instance.add_comment(ticket, content)
        logger.debug(f"Added comment to {ticket.key} → {comment.id}")

        updated_fields = []

        current_labels = _get_ticket_labels_safe(jira_instance, ticket, logger)
        new_labels, changed = get_updated_labels(current_labels, labels, labels_remove, logger, ticket.key)
        if changed:
            ticket.update(fields={"labels": new_labels})
            updated_fields.append("labels")

        args = config.get("args", None)
        if args and args.notify:
            notification(f"Coauthor updated {ticket.key}", "Coauthor added a comment to the Jira ticket")
        if updated_fields:
            logger.info(f"Updated {', '.join(updated_fields)} for {ticket.key}")
        return comment
    except JIRAError as error:
        logger.error(f"Failed to add comment to {ticket.key}: {error}")
        return None


def get_assigned_tickets(jira_instance, logger, query=None):
    """Return tickets to process.

    Backwards compatible behavior:
    - If query is provided, it is executed.
    - Otherwise, tickets are selected by assignee = COAUTHOR_JIRA_USERNAME.

    The rule-based Jira watcher uses the explicit query mode.
    """

    if query:
        return execute_jira_query(jira_instance, query, logger) or []

    jira_username = os.getenv("COAUTHOR_JIRA_USERNAME")
    if not jira_username:
        logger.debug("COAUTHOR_JIRA_USERNAME not set; skipping assigned-ticket polling.")
        return []

    assignee_query = f'assignee = "{jira_username}"'
    return execute_jira_query(jira_instance, assignee_query, logger) or []


def _get_jira_custom_field(config, field_name):
    """Get the configured custom field ID for a specific Jira field.

    Args:
        config: The configuration dictionary
        field_name: Name of the field (e.g., 'epic', 'story_points')

    Returns:
        str: The custom field ID or None if not configured
    """
    workflow = config.get("current-workflow", {})
    jira_config = workflow.get("watch", {}).get("jira", {})
    custom_fields = jira_config.get("custom_fields", {})
    return custom_fields.get(field_name)


def jira_update_description_summary(
    config, logger, ticket, summary, description, story_points=None, labels=None, labels_remove=None
):
    jira_instance = config["current-jira-instance"]
    try:
        update_kwargs = {"summary": summary, "description": description}
        custom_fields = {}
        updated_fields = ["summary", "description"]

        if story_points is not None and ticket.fields.issuetype.name == "Story":
            story_point_field = _get_jira_custom_field(config, "story_points")
            if not story_point_field:
                logger.error(
                    "Story points update requested but jira.custom_fields.story_points is not configured. "
                    "Add configuration: workflows[].watch.jira.custom_fields.story_points"
                )
                raise ValueError(
                    "Missing required configuration: jira.custom_fields.story_points. "
                    "Configure this field in .coauthor.yml under workflows[].watch.jira.custom_fields.story_points"
                )

            current_sp = getattr(ticket.fields, story_point_field, None)
            if current_sp != story_points:
                logger.info(f"{ticket.key} story_points → {story_points}")
                custom_fields[story_point_field] = story_points

        current_labels = _get_ticket_labels_safe(jira_instance, ticket, logger)
        new_labels, changed = get_updated_labels(current_labels, labels, labels_remove, logger, ticket.key)
        if changed:
            custom_fields["labels"] = new_labels
            updated_fields.append("labels")

        ticket.update(**update_kwargs, fields=custom_fields)
        args = config.get("args", None)
        if args and args.notify:
            notification(f"Coauthor updated {ticket.key}", "Coauthor updated the Jira ticket")
        logger.info(f"Updated {', '.join(updated_fields)} for {ticket.key}")
        return True
    except JIRAError as error:
        logger.error(f"Failed to update summary and description for {ticket.key}: {error}")
        return False


def jira_assign_to_creator(logger, ticket):
    reporter = ticket.fields.reporter.name
    try:
        ticket.update(assignee={"name": reporter})
        logger.info(f"Assigned {ticket.key} to creator {reporter}")
        return True
    except JIRAError as error:
        logger.error(f"Failed to assign {ticket.key} to creator: {error}")
        return False
