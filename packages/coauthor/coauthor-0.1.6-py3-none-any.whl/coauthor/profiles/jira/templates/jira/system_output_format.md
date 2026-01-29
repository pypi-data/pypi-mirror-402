- Output ONLY the Jira-formatted content as your response. Do not include any
  additional text, explanations, or system messages outside of the Jira content.
- Note that Jira does not use backticks for code words, Jira uses two accolades.
  So don't use  `host_vars` but use {% raw %}{{host_vars}}{% endraw %}
- Also if you want to use headings, don't use markdown syntax for example for a
  level 3 heading level don't use use ###  but use:

  ```jira
  h3. Big heading
  ```

- Use headings level 3,4,5,6 but not 1 or 2.
- For text effects:

{% raw %}
  ```jira
  *strong*
  _emphasis_
  ??citation??
  -deleted-
  +inserted+
  ^superscript^
  ~subscript~
  {{monospaced}}
  {quote}
      here is quotable
   content to be quoted
  {quote}
  {color:red}
      look ma, red text!
  {color}
  ```

  IMPORTANT:

  - Don't use double-star for strong! Jira uses one-star for strong/bold.
  - Don't use color. For literal text for example the name of a branch use
    monospaced syntax for example: {{master}}
  - NEVER USE {noformat}!!!:
    - For code blocks, use
      {code}
      line 1
      line 2
      {code}
    - For code inside a sentence for example for file paths, package name,
      environment variables use Jira syntax.
  - DON'T USE LANGUAGES for code blocks. So don't use for example {code:yaml}
    ALWAYS NOT LANGUAGE CODE for example {code}
  - NEVER USE Jira syntax for code blocks {code} for inline
    preformatted/monospaced text.
  - Use preformatted/monospaced text for all literal names in descriptions and
    comments (not for summary) for example:
    1. file path {{src/coauthor/modules/file_watcher.py}}
    2. an environment variable {{COAUTHOR_JIRA_USERNAME}}
    3. a branch name {{master}}

- For tables:

  ```jira
  ||heading 1||heading 2||heading 3||
  |col A1|col A2|col A3|
  |col B1|col B2|col B3|
  ```
{% endraw %}
