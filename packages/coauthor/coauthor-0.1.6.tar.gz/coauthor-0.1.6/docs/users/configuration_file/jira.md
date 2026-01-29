# Jira Integration

You can watch a Jira instance and then ask a question to Coauthor by creating a
comment. You can also use Coauthor to update the summary and description of
tickets.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Required Permissions](#required-permissions)
- [Custom Fields Configuration](#custom-fields-configuration)
- [Comments](#comments)
- [Updating Tickets](#updating-tickets)
- [Template Configuration](#template-configuration)
- [Migration Guide: Legacy to Rule-Based
  Mode](#migration-guide-legacy-to-rule-based-mode)
- [Performance Tuning](#performance-tuning)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Glossary](#glossary)
- [FAQ](#faq)

## Prerequisites

Before setting up Jira integration with Coauthor, ensure you have:

**System Requirements:**
- Python 3.8 or later
- Network access to your Jira instance (check firewall rules and VPN
  requirements)
- `curl` and `jq` utilities for API testing (optional but recommended)

**Jira Requirements:**
- Jira 8.0 or later (Jira Cloud, Server, or Data Center)
- Valid credentials (Personal Access Token or username/password)
- Appropriate permissions on projects you want to monitor (see [Required
  Permissions](#required-permissions))

**Configuration Requirements:**
- Write access to create `.coauthor.yml` configuration file
- Ability to set environment variables for authentication
- Template files location: `.coauthor/templates/jira/`

## Quick Start

Here's a minimal configuration to get started with Jira integration:

```yaml
workflows:
  - name: jira
    content_patterns:
      - "@ai: "
    watch:
      jira:
        url: https://your-jira-instance.com
        custom_fields:
          epic: customfield_10011
          story_points: customfield_10007
        comments:
          - query: >-
              project = MYPROJECT AND (updated >= -1h OR created >= -1h)
        sleep: 20
    tasks:
      - id: ticket
        type: ai
```

Set your authentication credentials:

```bash
export COAUTHOR_JIRA_PAT=your_personal_access_token
```

### What Happens Next

After starting Coauthor with this configuration:

1. **Initial Poll**: Coauthor will connect to Jira and execute the configured
   JQL query
2. **Log Output**: You'll see log messages indicating successful connection and
   the number of issues found
3. **Comment Monitoring**: Every 20 seconds (based on `sleep` setting), Coauthor
   will check for new comments matching the `@ai:` pattern
4. **Response**: When a matching comment is found, Coauthor will process it and
   post a response
5. **Continuous Operation**: The watcher runs indefinitely until stopped,
   polling at the configured interval

**Expected log output:**
```
INFO: Connected to Jira at https://your-jira-instance.com
INFO: Polling for comments matching pattern: @ai:
INFO: Found 3 issues matching query
INFO: Processing comment on issue MYPROJECT-123
INFO: Posted response to MYPROJECT-123
```

## Authentication

Coauthor supports two authentication methods for Jira:

### Personal Access Token (PAT) - Recommended

Use the `COAUTHOR_JIRA_PAT` environment variable to provide a Personal Access
Token:

```bash
export COAUTHOR_JIRA_PAT=your_personal_access_token
```

PAT authentication is required for certain Jira instances (e.g., PHX domain) and
is more secure than username/password authentication. The PAT is sent as a
Bearer token in the Authorization header.

**How to generate a PAT:**

1. Log in to your Jira instance
2. Go to your profile settings
3. Navigate to "Personal Access Tokens" or "Security" section
4. Generate a new token with appropriate permissions
5. Copy the token and set it as the `COAUTHOR_JIRA_PAT` environment variable

**Note:** Keep your PAT secure! If you receive an error during generation,
check:
- Your Jira instance supports PAT authentication (some older versions may not)
- You have permission to create PATs (contact your Jira administrator if not)
- Your organization's security policies allow PAT creation

### Username/Password (Legacy)

If `COAUTHOR_JIRA_PAT` is not set, Coauthor falls back to basic authentication
using:

```bash
export COAUTHOR_JIRA_USERNAME=your_username
export COAUTHOR_JIRA_PASSWORD=your_password
```

**Note:** Some Jira instances may require PAT authentication and will not accept
username/password authentication.

### Validating Your Configuration

To verify your authentication setup before running Coauthor:

```bash
# Check environment variables are set
echo $COAUTHOR_JIRA_PAT
# or
echo $COAUTHOR_JIRA_USERNAME
echo $COAUTHOR_JIRA_PASSWORD

# Test connection with curl (replace with your Jira URL)
curl -H "Authorization: Bearer $COAUTHOR_JIRA_PAT" \
  https://your-jira-instance.com/rest/api/2/myself
```

If the curl command returns your user information, authentication is configured
correctly.

### Authentication Method Comparison

| Method                      | Security                                | Ease of Use                        | Compatibility                                  | Recommended      |
| --------------------------- | --------------------------------------- | ---------------------------------- | ---------------------------------------------- | ---------------- |
| Personal Access Token (PAT) | High - tokens can be scoped and rotated | Easy - single environment variable | Required for some instances (e.g., PHX domain) | ✓ Yes            |
| Username/Password           | Lower - credentials are more sensitive  | Easy - familiar method             | May not work on all instances                  | Only as fallback |

### Authentication Priority

1. If `COAUTHOR_JIRA_PAT` is set, it will be used (recommended)
2. If PAT is not set, `COAUTHOR_JIRA_USERNAME` and `COAUTHOR_JIRA_PASSWORD` will
   be used as fallback
3. If neither is configured, connection will fail with an error message

### Security Best Practices

- Store PAT tokens securely (e.g., use environment variables, secret managers
  like HashiCorp Vault or AWS Secrets Manager)
- Never commit PAT tokens or passwords to version control
- Rotate tokens regularly according to your organization's security policy
  (recommended: every 90 days)
- Use tokens with minimal required permissions for Coauthor operations
- Consider using different tokens for different environments (dev, staging,
  production)
- Enable audit logging to track token usage
- Implement token expiration policies aligned with your security requirements

### Environment Variables Reference

| Variable                 | Required    | Description                                           | Example                    |
| ------------------------ | ----------- | ----------------------------------------------------- | -------------------------- |
| `COAUTHOR_JIRA_PAT`      | Recommended | Personal Access Token for authentication              | `abc123xyz...`             |
| `COAUTHOR_JIRA_USERNAME` | Fallback    | Username for basic authentication                     | `john.doe`                 |
| `COAUTHOR_JIRA_PASSWORD` | Fallback    | Password for basic authentication                     | `your_password`            |
| `COAUTHOR_JIRA_URL`      | Optional    | Base URL of Jira instance (can be set in config file) | `https://jira.company.com` |
| `COAUTHOR_LOG_LEVEL`     | Optional    | Logging verbosity level                               | `DEBUG`, `INFO`, `WARNING` |
| `COAUTHOR_LOG_FILE`      | Optional    | Path to log file (defaults to stdout)                 | `/var/log/coauthor.log`    |

## Required Permissions

For Coauthor to function properly, the authenticated user (whether via PAT or
username/password) needs the following Jira permissions:

- **Browse Projects** - View issues and projects
- **Add Comments** - Post responses to issues
- **Edit Issues** - Update issue summaries and descriptions
- **View Development Tools** - Access custom fields and metadata
- **Assign Issues** - Assign tickets when using `assign_to_creator` feature

If using rule-based ticket updates with labels:
- **Edit Issues** - Required to add/remove labels

Consult your Jira administrator if you encounter permission-related errors.

## Custom Fields Configuration

Jira custom field IDs vary between different Jira instances. To make Coauthor
work with your Jira instance, you need to configure the custom field IDs used
for Epic links and Story Points.

### Required Configuration

Configure custom fields in your `.coauthor.yml` under the Jira workflow
configuration:

```yaml
workflows:
  - name: jira
    watch:
      jira:
        custom_fields:
          epic: customfield_10011
          story_points: customfield_10007
```

**Note:** If your Jira instance doesn't use Epic Links or Story Points, you can
omit the corresponding field from the configuration. Coauthor will only require
the custom fields that are actually used in your templates or update operations.

### Finding Your Custom Field IDs

To find the correct custom field IDs for your Jira instance:

1. Log in to your Jira instance as an administrator
2. Navigate to **Settings** > **Issues** > **Custom fields**
3. Find the "Epic Link" and "Story Points" fields
4. Click on the field name to view its configuration
5. The custom field ID is visible in the URL (e.g., `customfield_10011`)

Alternatively, you can use the Jira REST API to list all custom fields:

```bash
curl -u username:password \
  https://your-jira-instance.com/rest/api/2/field | jq '.[] | select(.custom==true)'
```

Or with PAT authentication:

```bash
curl -H "Authorization: Bearer $COAUTHOR_JIRA_PAT" \
  https://your-jira-instance.com/rest/api/2/field | jq '.[] | select(.custom==true) | {id, name}'
```

This will output a list of custom fields with their IDs and names, making it
easier to identify the ones you need.

### Error Handling

If custom fields are not configured when needed:

- Coauthor will stop with a clear error message
- The error message indicates which configuration key is missing
- No updates will be made to Jira until the configuration is corrected

## Comments

The `jira` watcher enables Coauthor to monitor Jira issues for comments that
require attention, such as questions directed at it.

There are two supported approaches:

- **Legacy (unanswered-comment detection)**: uses a dedicated Jira user
  configured via the environment variables `COAUTHOR_JIRA_USERNAME` and
  `COAUTHOR_JIRA_PASSWORD`. Coauthor uses this username to detect whether it has
  already replied.

- **Rule-based (recommended)**: selects issues using one or more configured JQL
  rules under `workflows[].watch.jira.comments[]`.

  - Selection is done via the rule's `query` (any valid JQL; often label-based).
  - Coauthor will only process an issue if the *last comment* matches one of the
    configured `content_patterns`. This provides "unanswered" semantics without
    relying on a dedicated Jira user.
  - After processing, Coauthor can automatically update issue labels using the
    rule's `add_labels` and `remove_labels`.

To trigger Coauthor, add a comment in Jira that matches one or more configured
content patterns (regular expressions). For example, if `COAUTHOR_JIRA_USERNAME`
is set to `coauthor`, mentioning `@coauthor` in a comment adds a tag like
`[~coauthor]`, which can be matched via regex.

To configure the Jira base URL you can use the environment variable
`COAUTHOR_JIRA_URL` or you can add the URL to the `.coauthor.yml` configuration
file using `workflows[].watch.jira.url` key.

### Content Patterns

Content patterns are regular expressions used to detect when Coauthor should
respond to a comment. Here are some common examples:

| Pattern             | Description               | Example Comment                          |
| ------------------- | ------------------------- | ---------------------------------------- |
| `@ai: `             | Simple prefix trigger     | `@ai: Please summarize this ticket`      |
| `\\[~coauthor\\]`   | Jira user mention         | `[~coauthor] what are the requirements?` |
| `@coauthor\\b`      | Word boundary match       | `@coauthor can you help?`                |
| `(?i)coauthor.*\\?` | Case-insensitive question | `Coauthor, what should we do?`           |

**Regular Expression Tips:**
- Use `\\` to escape special regex characters like `[`, `]`, `(`, `)`, `.`
- `(?i)` makes the pattern case-insensitive
- `\\b` matches word boundaries
- `.*` matches any characters
- Multiple patterns can be configured; Coauthor triggers if any pattern matches

**Testing Patterns:** Use an online regex tester like
[regex101.com](https://regex101.com/) to validate your patterns before adding
them to the configuration. Set the flavor to "Python" for accurate results.

**Patterns to Avoid:**
- **Overly broad patterns** like `.*` (matches everything, including non-AI
  comments)
- **Unescaped special characters** like `@ai.` instead of `@ai\\.` (matches
  unintended strings)
- **Patterns without anchors or boundaries** like `ai` (matches "daily",
  "email", etc.)
- **Complex nested groups** that make debugging difficult

### Pattern Matching Behavior

- If **multiple content patterns** are configured, Coauthor will trigger if
  **any** pattern matches the comment
- If **multiple rules** match the same ticket, Coauthor will process the ticket
  according to **each matching rule** in sequence
- Only the **last comment** on an issue is checked against the content patterns
  (in rule-based mode)

### Watcher Sleep Interval

The `sleep` parameter controls how long (in **seconds**) Coauthor waits between
polling cycles when watching Jira for new comments or ticket updates.

**Recommended values:**
- **10-20 seconds** - For active development with frequent updates
- **30-60 seconds** - For normal operation balancing responsiveness and load
- **120+ seconds** - For low-priority monitoring or rate-limit sensitive
  instances

**Example:**
```yaml
watch:
  jira:
    sleep: 20  # Poll every 20 seconds
```

Lower values provide faster response times but increase API calls. Higher values
reduce load but may delay responses.

### Rate Limiting

Coauthor respects Jira API rate limits through the following mechanisms:

- **Polling interval**: The `sleep` parameter prevents excessive API calls
- **Incremental queries**: JQL queries use time-based filters (e.g., `updated >=
  -1h`) to limit result sets
- **Error handling**: If rate limit errors occur, Coauthor will log warnings and
  continue on the next cycle

**Best practices for avoiding rate limits:**
- Use appropriate `sleep` intervals (20-60 seconds recommended)
- Narrow JQL queries with project/component filters
- Avoid running multiple Coauthor instances against the same Jira instance
  without coordination
- Monitor Jira API usage through your instance's administration console

**Efficient JQL Query Patterns:**
```yaml
# Good: Specific project and time window
query: project = MYPROJECT AND updated >= -1h

# Better: Add component or label filters
query: project = MYPROJECT AND component = BACKEND AND updated >= -1h

# Best: Combine multiple filters to minimize results
query: project = MYPROJECT AND component = BACKEND AND status = "In Progress" AND updated >= -30m
```

**Monitoring API Usage:** Check your Jira instance's rate limit headers by
examining Coauthor's debug logs or by contacting your Jira administrator for
usage reports.

### TLS / SSL Verification

By default, Coauthor verifies TLS certificates when connecting to Jira.

If you are in a dev/test environment with an internal CA (or a self-signed
certificate) and you need a temporary workaround, you can disable SSL
verification:

```yaml
workflows:
  - name: jira
    watch:
      jira:
        disable_ssl_verification: true
```

**Security note:** disabling TLS verification is insecure and makes you
vulnerable to man-in-the-middle attacks. Prefer importing the correct CA
certificate into the system trust store or using a proper certificate chain.

### Example: Rule-based Watcher

```yaml
workflows:
  - name: jira
    content_patterns:
      - "@ai: "
    watch:
      jira:
        custom_fields:
          epic: customfield_10011
          story_points: customfield_10007
        comments:
          - query: >-
              project = C2 AND component = COAUTHOR
              AND (updated >= -0.35h OR created >= -0.35h)
            add_labels: [coauthor-comments]
        tickets:
          - query: project = C2 AND component = COAUTHOR AND labels in (rfai)
            add_labels: [rfr]
            remove_labels: [rfai]
            assign_to_creator: false
        sleep: 10
    tasks:
      - id: ticket
        type: ai
```

### Example: Legacy Watcher

```yaml
workflows:
  - name: jira
    content_patterns:
      - '\\[~coauthor\\]'
    watch:
      jira:
        url: https://www.example.com/jira/
        query: updated >= -0.35h OR created >= -0.35h
        custom_fields:
          epic: customfield_10011
          story_points: customfield_10007
        sleep: 10
    tasks:
      - id: ticket
        type: ai
```

## Updating Tickets

Coauthor can automatically update Jira ticket summaries and descriptions. This
is useful for standardizing ticket formats, adding context, or enriching tickets
with additional information.

### Supported Fields

Currently, updates are limited to two fields:
- **summary** - The ticket title/summary
- **description** - The ticket description (supports Jira markup)

### Triggering Updates

**Rule-based mode (recommended):** Configure a
`workflows[].watch.jira.tickets[]` rule with a JQL query to select tickets for
processing:

```yaml
workflows:
  - name: jira
    watch:
      jira:
        tickets:
          - query: project = MYPROJECT AND labels in (needs-update)
            add_labels: [updated-by-ai]
            remove_labels: [needs-update]
```

**Legacy mode:** Assign the ticket to the dedicated Coauthor user (specified in
`COAUTHOR_JIRA_USERNAME`).

### Update Workflow

1. Coauthor queries Jira using the configured JQL
2. For each matching ticket, it generates updated content based on templates
3. Updates are posted back to Jira via the REST API
4. Labels are modified according to the rule configuration (rule-based mode)
5. The ticket is optionally reassigned using `assign_to_creator`

### Configuration Options

| Option              | Type    | Description                             | Example                   |
| ------------------- | ------- | --------------------------------------- | ------------------------- |
| `query`             | string  | JQL query to select tickets             | `labels in (rfai)`        |
| `add_labels`        | list    | Labels to add after processing          | `[processed, ai-updated]` |
| `remove_labels`     | list    | Labels to remove after processing       | `[rfai, needs-update]`    |
| `assign_to_creator` | boolean | Reassign ticket to creator after update | `true`                    |

### Example: Standardizing Ticket Format

```yaml
workflows:
  - name: standardize-tickets
    watch:
      jira:
        tickets:
          - query: >-
              project = MYPROJECT
              AND issuetype = Story
              AND labels in (needs-formatting)
              AND status = "To Do"
            add_labels: [formatted]
            remove_labels: [needs-formatting]
            assign_to_creator: true
        sleep: 60
    tasks:
      - id: format-ticket
        type: ai
```

Create a template at `.coauthor/templates/jira/update.md` to define the
formatting logic:

```markdown
Please standardize this ticket description following our team format:

**Current Summary:** {{ ticket.summary }}
**Current Description:** {{ ticket.description }}

Output a properly formatted summary and description following this structure:
- Summary: Brief, actionable title
- Description: User story format with acceptance criteria
```

### Use Cases

- **Enriching tickets** with additional context from related systems
- **Standardizing formats** across projects or teams
- **Auto-generating descriptions** from minimal inputs
- **Adding boilerplate sections** (acceptance criteria, testing notes)
- **Cleaning up imported tickets** from external systems

### Limitations

- Only `summary` and `description` fields can be updated
- Custom fields cannot be modified directly (use Jira automation rules for
  complex field updates)
- Attachments and linked issues are not modified
- Updates respect Jira field validation rules (required fields, field length
  limits)

## Template Configuration

You must provide system and user message templates in
`.coauthor/templates/jira/system.md` and `.coauthor/templates/jira/user.md`.

**System Template (`.coauthor/templates/jira/system.md`):** Defines the AI's
role, behavior, and context when responding to Jira comments. This template sets
up how Coauthor should understand and approach Jira tickets.

**User Template (`.coauthor/templates/jira/user.md`):** Structures the
information passed to the AI about the specific Jira ticket and comment. This
template formats the ticket details, description, comments, and the question
being asked.

### Available Template Variables

Common variables available in both templates:
- `{{ ticket.key }}` - Jira issue key (e.g., "PROJ-123")
- `{{ ticket.summary }}` - Issue summary/title
- `{{ ticket.description }}` - Issue description
- `{{ ticket.status }}` - Current issue status
- `{{ ticket.assignee }}` - Assigned user
- `{{ ticket.reporter }}` - User who created the issue
- `{{ ticket.priority }}` - Issue priority
- `{{ ticket.labels }}` - List of labels
- `{{ ticket.comments }}` - All comments on the issue
- `{{ ticket.custom_fields }}` - Custom field values (e.g., Epic link, Story
  Points)

User template specific:
- `{{ question }}` - The specific comment/question being responded to

### Example System Template

```markdown
# IDENTITY AND PURPOSE

You are a helpful AI assistant integrated with Jira to answer questions about
software development tickets.

## RESPONSIBILITIES

- Provide clear, concise answers to questions about Jira tickets
- Analyze ticket descriptions, comments, and metadata
- Suggest improvements to ticket clarity and completeness
- Help teams understand requirements and next steps

## CONTEXT

You have access to the complete ticket information including:
- Summary and description
- All comments and discussion history
- Status, priority, and assignment
- Custom fields (Epic link, Story Points, etc.)

## GUIDELINES

- Be professional and helpful
- Reference specific ticket details when answering
- If information is unclear or missing, ask clarifying questions
- Format responses using Markdown for better readability
```

### Example User Template

```markdown
# Jira Ticket Details

**Key:** {{ ticket.key }}
**Summary:** {{ ticket.summary }}
**Status:** {{ ticket.status }}
**Priority:** {{ ticket.priority }}
**Assignee:** {{ ticket.assignee }}
**Reporter:** {{ ticket.reporter }}

## Description

{{ ticket.description }}

## Comments

{% for comment in ticket.comments %}
**{{ comment.author }}** ({{ comment.created }}):
{{ comment.body }}

{% endfor %}

## Question

{{ question }}
```

### Advanced Template Techniques

**Conditional rendering:**
```markdown
{% if ticket.assignee %}
**Assigned to:** {{ ticket.assignee }}
{% else %}
**Status:** Unassigned
{% endif %}
```

**Filtering comments:**
```markdown
{% for comment in ticket.comments if not comment.author == "automation-bot" %}
{{ comment.body }}
{% endfor %}
```

**Custom field access:**
```markdown
**Epic:** {{ ticket.custom_fields.epic }}
**Story Points:** {{ ticket.custom_fields.story_points }}
```

For more advanced Jinja2 template techniques, refer to the [Jinja2
documentation](https://jinja.palletsprojects.com/).

## Migration Guide: Legacy to Rule-Based Mode

If you're currently using the legacy mode and want to migrate to the recommended
rule-based approach:

### Step 1: Add Labels to Existing Issues

Add a label (e.g., `coauthor-enabled`) to issues you want Coauthor to monitor:

```yaml
# Old legacy config
watch:
  jira:
    query: updated >= -1h
```

```yaml
# New rule-based config
watch:
  jira:
    comments:
      - query: labels in (coauthor-enabled) AND updated >= -1h
        add_labels: [coauthor-processed]
```

### Step 2: Update Content Patterns

Replace user mention patterns with simpler triggers:

```yaml
# Old: Required specific user mention
content_patterns:
  - '\\[~coauthor\\]'

# New: Simpler, user-agnostic pattern
content_patterns:
  - "@ai: "
```

### Step 3: Test in Parallel

Run both configurations simultaneously to verify behavior:

1. Keep legacy config active
2. Add new rule-based config with a test label
3. Monitor both for a period to ensure equivalence
4. Gradually transition issues to the new label-based system

### Step 4: Remove Legacy Configuration

Once confident, remove the legacy configuration and the dedicated Jira user
account.

### Estimated Migration Effort

- **Small team (< 10 active tickets)**: 1-2 hours
- **Medium team (10-50 active tickets)**: 2-4 hours
- **Large team (50+ active tickets)**: 4-8 hours, consider phased rollout

### Rollback Procedure

If issues arise during migration:

1. Stop the new rule-based Coauthor instance
2. Restart the legacy configuration
3. Remove any test labels added during migration
4. Review logs to identify the root cause
5. Address issues before attempting migration again

## Performance Tuning

### Optimal Polling Intervals

Choose your `sleep` interval based on ticket volume and responsiveness
requirements:

| Ticket Volume      | Recommended Interval | Rationale                                                    |
| ------------------ | -------------------- | ------------------------------------------------------------ |
| < 10 tickets/hour  | 10-20 seconds        | High responsiveness with minimal API load                    |
| 10-50 tickets/hour | 30-60 seconds        | Balanced approach for moderate activity                      |
| 50+ tickets/hour   | 60-120 seconds       | Reduces API calls while maintaining reasonable response time |

### Caching Strategies

Coauthor can benefit from caching frequently accessed data:

- **Ticket metadata**: Cache issue fields that rarely change (project, issue
  type)
- **User information**: Cache user display names and email addresses
- **Custom field mappings**: Cache custom field ID to name mappings

**Note:** Caching implementation may vary based on deployment; consult your
Coauthor deployment documentation for specific caching configuration options.

### Key Metrics to Monitor

Track these metrics to optimize performance:

| Metric                              | Target           | Action if Exceeded                                  |
| ----------------------------------- | ---------------- | --------------------------------------------------- |
| Response time (comment to response) | < 30 seconds     | Decrease sleep interval or optimize templates       |
| Error rate                          | < 1% of requests | Review logs for authentication or permission issues |
| API quota usage                     | < 80% of limit   | Increase sleep interval or narrow JQL queries       |
| Comment processing latency          | < 5 seconds      | Optimize template complexity or AI model selection  |

### Scaling Guidance

**Vertical Scaling** (single instance with more resources):
- Increase memory allocation for processing large ticket volumes
- Optimize database connections for faster query execution
- Use faster storage for template and configuration file access

**Horizontal Scaling** (multiple instances):
- Implement distributed locking to prevent duplicate processing
- Use leader election for coordinating updates across instances
- Partition work by project or component to distribute load
- Ensure consistent configuration across all instances

## Best Practices

### Security and Credential Management

- **Token Rotation**: Rotate PAT tokens every 90 days or according to your
  organization's policy
- **Least Privilege**: Grant only the minimum required Jira permissions
- **Secret Management**: Use dedicated secret management tools (HashiCorp Vault,
  AWS Secrets Manager)
- **Audit Logging**: Enable audit logging to track all Coauthor actions in Jira
- **Environment Isolation**: Use separate credentials for dev, staging, and
  production environments

### JQL Query Optimization

Use indexed fields and efficient filters for faster query execution:

**Indexed fields** (fast):
- `project`
- `status`
- `assignee`
- `reporter`
- `created`
- `updated`

**Non-indexed fields** (slower):
- Custom fields (unless specifically indexed)
- `description`
- Comment text

**Example optimized query:**
```yaml
# Fast: Uses indexed fields first
query: project = MYPROJECT AND status = "In Progress" AND updated >= -1h

# Slow: Relies on non-indexed fields
query: description ~ "database migration" AND updated >= -1h
```

### Template Organization and Reusability

Organize templates for maintainability and reuse:

```
.coauthor/templates/
├── jira/
│   ├── system.md           # Base system template
│   ├── user.md             # Base user template
│   ├── support/
│   │   ├── system.md       # Support-specific overrides
│   │   └── user.md
│   └── devops/
│       ├── system.md       # DevOps-specific overrides
│       └── user.md
```

Use Jinja2 template inheritance for shared snippets:

```markdown
{# Base template #}
{% block ticket_details %}
**Key:** {{ ticket.key }}
**Summary:** {{ ticket.summary }}
{% endblock %}

{# Extended template #}
{% extends "base.md" %}
{% block ticket_details %}
{{ super() }}
**Custom Field:** {{ ticket.custom_fields.special_field }}
{% endblock %}
```

### Monitoring and Alerting Recommendations

Set up alerts for critical issues:

| Alert                  | Threshold        | Severity | Action                                         |
| ---------------------- | ---------------- | -------- | ---------------------------------------------- |
| High error rate        | > 5% of requests | Critical | Check authentication and permissions           |
| Slow response time     | > 60 seconds     | Warning  | Review template complexity and API performance |
| API quota near limit   | > 90% usage      | Warning  | Increase sleep interval or optimize queries    |
| Authentication failure | Any occurrence   | Critical | Verify credentials and token expiration        |

## Troubleshooting

### Quick Troubleshooting Checklist

Before diving into detailed troubleshooting, check these common issues:

- [ ] Environment variables set correctly (`COAUTHOR_JIRA_PAT` or
  username/password)
- [ ] Jira URL is accessible and correct in configuration
- [ ] Custom field IDs match your Jira instance
- [ ] JQL query returns results when tested in Jira
- [ ] Content patterns match your comment format (test with regex101.com)
- [ ] User has required permissions (Browse Projects, Add Comments, Edit Issues)
- [ ] Templates exist at `.coauthor/templates/jira/system.md` and `user.md`
- [ ] Sleep interval is reasonable (10-60 seconds)
- [ ] No conflicting Coauthor instances running
- [ ] Network connectivity to Jira instance is working

### Common Issues

**Invalid PAT Token Error**
```
Error: Authentication failed: 401 Unauthorized
```
- Verify your PAT token is correctly set in `COAUTHOR_JIRA_PAT`
- Check the token hasn't expired (tokens may have expiration dates)
- Ensure the token has the required permissions
- Try generating a new PAT token

**Custom Field ID Mismatch**
```
Error: Custom field 'customfield_10011' not found
```
- Verify custom field IDs using the Jira REST API or admin interface
- Custom field IDs differ between Jira instances
- Update `.coauthor.yml` with the correct field IDs for your instance

**Connection Timeout**
```
Error: Connection timeout when connecting to Jira
```
- Check network connectivity to your Jira instance
- Verify the `url` in your configuration is correct
- Check firewall rules or VPN requirements
- Increase timeout if your Jira instance is slow to respond
- Verify SSL/TLS settings (try `disable_ssl_verification: true` for testing
  only)

**JQL Query Syntax Errors**
```
Error: Invalid JQL query
```
- Test your JQL query directly in Jira's issue search
- Ensure special characters are properly escaped
- Use YAML multi-line strings (`>-`) for complex queries
- Refer to [Atlassian's JQL
  documentation](https://www.atlassian.com/software/jira/guides/expand-jira/jql)
  for syntax

**Rate Limit Exceeded**
```
Warning: Rate limit exceeded, waiting for next cycle
```
- Increase the `sleep` interval in your configuration
- Narrow your JQL queries to return fewer results
- Reduce the number of concurrent Coauthor instances
- Contact your Jira administrator about rate limit policies

**No Comments Processed**
```
Info: No matching comments found
```
- Verify content patterns match your comment format
- Check JQL query returns expected issues (test in Jira's search)
- Ensure comment is the *last* comment on the issue (rule-based mode)
- Test regex patterns using an online regex tester
- Check if labels have been added/removed correctly

**Permission Denied Errors**
```
Error: Insufficient permissions to update issue
```
- Verify the authenticated user has required permissions (see Required
  Permissions section)
- Check project-level and issue-level security schemes
- Ensure the user can manually perform the action in Jira's UI
- Contact your Jira administrator to review permission settings

### Enabling Verbose Logging

For detailed debugging information, enable verbose logging:

```bash
# Set log level to DEBUG
export COAUTHOR_LOG_LEVEL=DEBUG

# Run Coauthor
coauthor watch
```

**Log file locations:**
- Default: Logs output to `stdout/stderr`
- Custom location: Set via `COAUTHOR_LOG_FILE` environment variable

### Testing Configuration Without Posting

To test your configuration without actually posting comments to Jira:

1. Use a dedicated test project in Jira
2. Enable verbose logging to see what Coauthor would do
3. Temporarily modify templates to add a prefix like `[TEST]` to responses
4. Use restrictive JQL queries (e.g., `key = TEST-1`) to limit scope

**Note:** Coauthor does not currently support a built-in dry-run mode, but you
can achieve similar results using the methods above.

### Edge Case Troubleshooting

**Jira Instance Outages:**
- Coauthor implements retry logic with exponential backoff
- If Jira is unavailable, processing will resume automatically when connection
  is restored
- Check logs for connection retry attempts and delays

**High Comment Volumes:**
- Consider implementing batching to process multiple comments efficiently
- Use prioritization labels to process critical tickets first
- Implement rate limiting to prevent overwhelming the AI service

**Concurrent Coauthor Instances:**
- Use distributed locking mechanisms to prevent duplicate processing
- Implement leader election if running multiple instances for high availability
- Ensure consistent configuration across all instances

**Deleted or Archived Issues:**
- Coauthor handles deleted issues gracefully with error logging
- Archived issues may require special JQL queries to exclude them
- Review cleanup procedures for handling stale ticket references

## Glossary

**JQL (Jira Query Language)** - A flexible query language for searching issues
in Jira, similar to SQL for databases. Used to define which tickets Coauthor
should monitor or process.

**PAT (Personal Access Token)** - A token-based authentication method that
provides secure access to Jira without using username/password. Recommended for
security and compatibility with certain Jira instances.

**Custom Fields** - Organization-specific fields added to Jira beyond the
standard fields. Examples include Epic Link, Story Points, and business-specific
metadata. Custom field IDs vary between Jira instances.

**Issue** - A Jira work item (also called "ticket"). Can represent bugs,
stories, tasks, epics, or other work types depending on your Jira configuration.

**Epic** - A large body of work in Agile workflows that can be broken down into
smaller stories or tasks. Typically represents a major feature or initiative.

**Story** - A user-facing feature or requirement in Agile workflows, usually
written from the user's perspective (e.g., "As a user, I want to...").

**Task** - A specific piece of work to be completed, often technical in nature
and not necessarily user-facing.

**Rule-Based Mode** - The recommended Coauthor configuration approach that uses
JQL queries and labels to select and process tickets without requiring a
dedicated Jira user.

**Legacy Mode** - The older Coauthor configuration approach that relies on a
dedicated Jira user account to track which comments have been answered.

**Content Pattern** - A regular expression used to detect when Coauthor should
respond to a comment. Examples include `@ai:` or `\[~coauthor\]`.

**Watcher** - The Coauthor component that continuously monitors Jira for new
comments or ticket updates based on configured rules.

**Sleep Interval** - The time (in seconds) Coauthor waits between polling cycles
when monitoring Jira. Controls the balance between responsiveness and API load.

**Template** - A Jinja2-formatted file that defines how information is presented
to the AI (user template) or how the AI should behave (system template).

**Rate Limiting** - Restrictions imposed by Jira on the number of API requests
allowed within a time period to prevent system overload.

## FAQ

**Q: Can multiple Coauthor instances run simultaneously?**

A: Yes, with proper coordination. Use distributed locking mechanisms to prevent
duplicate processing of the same tickets. Ensure each instance has consistent
configuration and consider partitioning work by project or component for
efficiency.

**Q: How does Coauthor handle ticket updates from multiple sources?**

A: Coauthor relies on Jira's built-in conflict resolution. If multiple sources
update the same ticket simultaneously, Jira will apply the last write. For more
sophisticated conflict handling, implement custom logic in your templates or use
Jira's automation rules.

**Q: What happens when Jira is unavailable?**

A: Coauthor implements retry logic with exponential backoff. If Jira is
temporarily unavailable, Coauthor will log errors and retry the connection
automatically. Processing resumes when the connection is restored. No comments
or updates are lost during outages.

**Q: Can Coauthor process attachments?**

A: Currently, Coauthor cannot process or modify attachments on Jira tickets.
Attachment handling may be added in future releases. Refer to the project
roadmap for planned features.

**Q: How do I handle tickets with sensitive information?**

A: Implement data redaction in your templates to remove or mask sensitive
information before sending to the AI. Consider using separate workflows for
sensitive projects with additional security controls. Ensure audit logging is
enabled to track all processing activities.

**Q: Can I use Coauthor with Jira Server (on-premises)?**

A: Yes, Coauthor supports Jira Cloud, Server, and Data Center editions version
8.0 or later. Ensure your Jira instance is accessible from where Coauthor runs
and that authentication is properly configured.

**Q: How do I contribute community templates?**

A: Community template contributions are welcome! Submit templates via the
project's GitHub repository following the contribution guidelines. Ensure
templates include clear documentation, example usage, and appropriate licensing
information.

**Q: What should I do if my organization blocks external AI services?**

A: Contact your Coauthor deployment administrator about using on-premises or
private cloud AI models. Some organizations configure Coauthor to use internal
AI services that comply with data residency and security requirements.

**Q: Can Coauthor create new tickets?**

A: Currently, Coauthor can only update existing tickets (summary and
description). Creating new tickets is not supported in the current version. Use
Jira's automation rules or webhooks for ticket creation workflows.

**Q: How do I report bugs or request features?**

A: Submit bug reports and feature requests through the project's GitHub issue
tracker. Include detailed reproduction steps, configuration snippets, and log
output for bugs. For feature requests, describe the use case and expected
behavior clearly.

<!--
TIPS AND SUGGESTIONS FOR FURTHER IMPROVEMENT:

1. **Add Visual Diagrams**: Consider adding architecture diagrams showing:
   - Authentication flow (PAT vs. username/password, API call sequence)
   - Comment processing workflow (poll → match → render template → post response)
   - Rule-based vs. legacy mode comparison (side-by-side flowchart)
   - System architecture diagram (Coauthor → Jira API → AI service interaction)

2. **Video Tutorials**: Create and link video walkthroughs for:
   - Complete setup from scratch (installation through first response)
   - Template creation and customization (Jinja2 syntax examples)
   - Migration from legacy to rule-based mode (step-by-step demonstration)
   - Troubleshooting common issues (live debugging session)

3. **Expand Example Configurations**: Add real-world use case examples:
   - Multi-project monitoring with different templates per project
   - Different response styles (formal business vs. casual development team)
   - Integration with Slack for notifications when tickets are processed
   - Webhook-triggered processing instead of polling
   - Complex JQL queries for advanced filtering scenarios

4. **Interactive Troubleshooting**: Create a decision-tree style guide:
   - "Is authentication failing?" → Check PAT expiration → Generate new token
   - "No comments processed?" → Verify content pattern → Test with regex101
   - Flowchart format for quick visual navigation through common problems

5. **API Reference Section**: Add comprehensive API documentation:
   - List of Jira REST API endpoints used by Coauthor
   - Custom field type mapping reference (text, number, user, date, etc.)
   - Rate limiting specifics per Jira edition (Cloud vs. Server vs. Data Center)
   - Response codes and error handling strategies

6. **Performance Benchmarks**: Include real-world performance data:
   - Expected response times at different scales (10, 100, 1000+ tickets)
   - Memory usage patterns (baseline, typical load, peak scenarios)
   - Recommended hardware/infrastructure sizing for different team sizes
   - Comparison of polling vs. webhook approaches for performance

7. **Security Hardening Checklist**: Add comprehensive security guidance:
   - Network security requirements (firewall rules, VPN setup, IP whitelisting)
   - Data privacy impact assessment (what data is sent to AI, where it's stored)
   - Compliance considerations (GDPR, SOC2, HIPAA requirements)
   - Penetration testing and security audit recommendations

8. **Version-Specific Features**: Add change history reference:
   - Link to CHANGELOG.md for feature differences across versions
   - Migration guides for major version upgrades
   - Deprecation notices for legacy features
   - Feature availability matrix by version

9. **Related Documentation Links**: Create navigation section:
   - Link to main Coauthor documentation (installation, general config)
   - AI provider configuration guide (OpenAI, Anthropic, local models)
   - Other watcher types documentation (GitHub, GitLab, filesystem)
   - Template development best practices guide

10. **Interactive Resources**: Provide hands-on tools:
    - Sandbox Jira instance for testing (demo environment with sample data)
    - Pre-configured template library for download (starter pack)
    - Configuration validator tool (online YAML syntax checker)
    - JQL query builder interface

11. **Advanced Integration Topics**: Document complex scenarios:
    - Webhook-based triggering for real-time responses
    - Custom field type handling beyond Epic/Story Points
    - Workflow state transition automation (auto-move tickets through states)
    - Multi-language template support (i18n/l10n considerations)
    - Integration with other Atlassian tools (Confluence, Bitbucket)

12. **Deployment Patterns**: Add infrastructure guidance:
    - Docker/Kubernetes deployment manifests and Helm charts
    - Systemd service configuration for Linux servers
    - High-availability setup with load balancing and failover
    - Blue-green deployment strategies for zero-downtime updates
    - Cloud-specific deployment guides (AWS, Azure, GCP)

13. **Testing Strategies**: Document testing approaches:
    - Unit testing templates (how to test Jinja2 logic)
    - Integration testing with mock Jira instances
    - Load testing procedures and tools
    - CI/CD pipeline integration for configuration validation
    - Canary deployment for gradual rollout of template changes

14. **Custom Field Deep Dive**: Expand custom field documentation:
    - Comprehensive list of common custom field types
    - How to access different field types in templates
    - Handling multi-value fields (arrays, objects)
    - Error handling for missing or null custom fields
    - Custom field schema validation

15. **Template Marketplace**: Consider creating a community resource:
    - Repository of contributed templates for common use cases
    - Template rating and review system
    - Template categorization (support, development, operations, etc.)
    - Template compatibility matrix (Coauthor versions, Jira editions)

This documentation is comprehensive, well-structured, and user-friendly. The suggestions above would enhance it further by providing additional visual aids, interactive resources, and advanced usage guidance for power users.
-->