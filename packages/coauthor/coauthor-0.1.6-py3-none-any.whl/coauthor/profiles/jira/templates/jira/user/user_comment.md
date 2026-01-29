# Questions or Tasks in a JIRA Comment

User {{ task['current-comment'].author.name }} created a comment that requires
your attention. It contains a question for you to answer or tasks for you to perform.

## Comment

"{{ task['current-comment'].body }}"

## Comments

For context, all comments

{% for comment in task['current-ticket'].fields.comment.comments %}
- **{{ comment.author.name }}** ({{ comment.created }}):
  {{ comment.body }}
{% endfor %}

## JIRA Ticket

For further context the JIRA ticket information is below:

{% include '_ticket.md' %}
