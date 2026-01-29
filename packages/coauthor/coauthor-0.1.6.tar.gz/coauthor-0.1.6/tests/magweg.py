import re

# Regular expression to match the coauthor context block
coauthor_context_pattern = re.compile(
    r"^coauthor:\n" r"(?:  \w+:\n)*" r"  context:\n" r"(?:    - .+\n?)+", re.MULTILINE
)

# This regular expression pattern matches:
# - A line starting with `coauthor:`
# - Followed by a line with two spaces and `context:`
# - Followed by one or more lines starting with four spaces and a `-` character

# The pattern uses:
# - `^` to match the start of a line
# - `\n` to match newlines
# - `(?:  \w+:\n)*` to optionally match other keys at the same indentation level
# - `(?:    - .+\n?)+` to match one or more context items with four spaces, a dash, and content
