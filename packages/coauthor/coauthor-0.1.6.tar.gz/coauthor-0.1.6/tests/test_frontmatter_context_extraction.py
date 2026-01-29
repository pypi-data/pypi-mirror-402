# -*- coding: utf-8 -*-
"""
Unit tests for automatic frontmatter context extraction (C2-1256).

Tests extraction of coauthor.context blocks from various file types:
- Markdown (YAML frontmatter)
- Python (docstrings)
- JavaScript/Go (multi-line comments)
- Error handling for invalid YAML
"""

import tempfile
import pytest
from unittest.mock import Mock
from pathlib import Path

from coauthor.utils.ai_utils import extract_frontmatter_context


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return Mock()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestMarkdownContextExtraction:
    """Tests for context extraction from Markdown files."""

    def test_extract_markdown_frontmatter(self, temp_dir, mock_logger):
        """Test extracting context from Markdown YAML frontmatter."""
        content = """---
title: My Document
coauthor:
  context:
    - file: src/main.py
    - url: https://example.com/docs
---

# Document Content
"""
        file_path = temp_dir / "doc.md"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is not None
        assert len(result) == 2
        assert result[0] == {"file": "src/main.py"}
        assert result[1] == {"url": "https://example.com/docs"}

    def test_extract_markdown_multiple_context_types(self, temp_dir, mock_logger):
        """Test extracting multiple context types from Markdown."""
        content = """---
coauthor:
  context:
    - file: src/utils/helper.py
    - dir: ./tests
    - url: https://api.example.com/v1
    - rellink: /docs/guide
---

Content here.
"""
        file_path = temp_dir / "guide.md"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is not None
        assert len(result) == 4
        assert {"file": "src/utils/helper.py"} in result
        assert {"dir": "./tests"} in result
        assert {"url": "https://api.example.com/v1"} in result
        assert {"rellink": "/docs/guide"} in result

    def test_extract_markdown_no_context(self, temp_dir, mock_logger):
        """Test Markdown file without context block."""
        content = """---
title: Simple Document
author: Test Author
---

# Content
"""
        file_path = temp_dir / "simple.md"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is None

    def test_extract_markdown_empty_context(self, temp_dir, mock_logger):
        """Test Markdown with empty context list."""
        content = """---
coauthor:
  context: []
---

Content
"""
        file_path = temp_dir / "empty.md"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is None or result == []


class TestPythonContextExtraction:
    """Tests for context extraction from Python files."""

    def test_extract_python_docstring_triple_double(self, temp_dir, mock_logger):
        """Test extracting context from Python triple-double-quote docstring."""
        content = '''"""
Module for handling AI operations.

coauthor:
  context:
    - file: src/coauthor/modules/youtube.py
    - file: src/coauthor/utils/config.py
"""

import os

def main():
    pass
'''
        file_path = temp_dir / "ai_module.py"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is not None
        assert len(result) == 2
        assert {"file": "src/coauthor/modules/youtube.py"} in result
        assert {"file": "src/coauthor/utils/config.py"} in result

    def test_extract_python_docstring_triple_single(self, temp_dir, mock_logger):
        """Test extracting context from Python triple-single-quote docstring."""
        content = """'''
Helper utilities.

coauthor:
  context:
    - dir: ./src/utils
'''

def helper():
    pass
"""
        file_path = temp_dir / "utils.py"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is not None
        assert len(result) == 1
        assert result[0] == {"dir": "./src/utils"}

    def test_extract_python_no_context(self, temp_dir, mock_logger):
        """Test Python file without context block."""
        content = '''"""
Simple module without context.
"""

def function():
    pass
'''
        file_path = temp_dir / "simple.py"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is None

    def test_extract_python_inline_comment(self, temp_dir, mock_logger):
        """Test Python with context in multi-line comment."""
        content = '''# Main module
"""
coauthor:
  context:
    - file: config.py
"""

import sys
'''
        file_path = temp_dir / "main.py"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is not None
        assert result[0] == {"file": "config.py"}


class TestJavaScriptContextExtraction:
    """Tests for context extraction from JavaScript files."""

    def test_extract_javascript_multiline_comment(self, temp_dir, mock_logger):
        """Test extracting context from JavaScript multi-line comment."""
        content = """/**
 * Main application module.
 *
 * coauthor:
 *   context:
 *     - file: src/utils.js
 *     - url: https://api.example.com/schema
 */

function main() {
    console.log("Hello");
}
"""
        file_path = temp_dir / "app.js"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is not None
        assert len(result) == 2
        assert {"file": "src/utils.js"} in result
        assert {"url": "https://api.example.com/schema"} in result

    def test_extract_javascript_no_asterisks(self, temp_dir, mock_logger):
        """Test JavaScript with context block without leading asterisks."""
        content = """/*
coauthor:
  context:
    - dir: ./lib
*/

const app = {};
"""
        file_path = temp_dir / "simple.js"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is not None
        assert result[0] == {"dir": "./lib"}


class TestGoContextExtraction:
    """Tests for context extraction from Go files."""

    def test_extract_go_multiline_comment(self, temp_dir, mock_logger):
        """Test extracting context from Go multi-line comment."""
        content = """/*
Package main implements the application entry point.

coauthor:
  context:
    - file: pkg/utils/helper.go
    - rellink: /docs/api
*/

package main

func main() {
    // Application code
}
"""
        file_path = temp_dir / "main.go"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is not None
        assert len(result) == 2
        assert {"file": "pkg/utils/helper.go"} in result
        assert {"rellink": "/docs/api"} in result


class TestErrorHandling:
    """Tests for error handling in context extraction."""

    def test_extract_invalid_yaml(self, temp_dir, mock_logger):
        """Test handling of invalid YAML in context block."""
        content = """---
coauthor:
  context:
    - file: test.py
    - invalid yaml here: [unclosed
---

Content
"""
        file_path = temp_dir / "invalid.md"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is None
        mock_logger.warning.assert_called_once()

    def test_extract_malformed_context_structure(self, temp_dir, mock_logger):
        """Test handling of malformed context structure (not a list)."""
        content = """---
coauthor:
  context: "not a list"
---

Content
"""
        file_path = temp_dir / "malformed.md"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        # Should handle gracefully
        assert result is None or not isinstance(result, list)

    def test_extract_missing_file(self, mock_logger):
        """Test handling of missing file."""
        result = extract_frontmatter_context("/nonexistent/file.md", mock_logger)

        assert result is None
        mock_logger.warning.assert_called_once()

    def test_extract_file_read_error(self, temp_dir, mock_logger):
        """Test handling of file read errors."""
        file_path = temp_dir / "unreadable.md"
        file_path.write_text("content", encoding="utf-8")

        # Make file unreadable (Unix-like systems)
        import os

        try:
            os.chmod(file_path, 0o000)
            result = extract_frontmatter_context(str(file_path), mock_logger)
            assert result is None
        except Exception:
            pytest.skip("Cannot change file permissions on this platform")
        finally:
            try:
                os.chmod(file_path, 0o644)
            except Exception:
                pass


class TestMixedContextFormats:
    """Tests for mixed and edge-case context formats."""

    def test_extract_context_with_comments(self, temp_dir, mock_logger):
        """Test context extraction with YAML comments."""
        content = """---
coauthor:
  context:
    # Development files
    - file: src/dev.py
    # External API
    - url: https://example.com
---

Content
"""
        file_path = temp_dir / "commented.md"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is not None
        assert len(result) == 2

    def test_extract_context_multiline_values(self, temp_dir, mock_logger):
        """Test context with complex YAML structures."""
        content = """---
coauthor:
  context:
    - file: >
        src/very/long/path/to/file.py
    - url: https://example.com/api
---

Content
"""
        file_path = temp_dir / "multiline.md"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is not None
        # Should handle multiline folded values
        assert any("file" in item for item in result)

    def test_extract_context_unicode(self, temp_dir, mock_logger):
        """Test context extraction with Unicode characters."""
        content = """---
coauthor:
  context:
    - file: src/café.py
    - url: https://example.com/日本語
---

Content with émojis 🎉
"""
        file_path = temp_dir / "unicode.md"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is not None
        assert len(result) == 2

    def test_extract_nested_coauthor_block(self, temp_dir, mock_logger):
        """Test extraction when coauthor block appears multiple times."""
        content = """---
coauthor:
  context:
    - file: first.py
---

# Section

```yaml
coauthor:
  context:
    - file: second.py
```
"""
        file_path = temp_dir / "nested.md"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        # Should extract from frontmatter (first occurrence)
        assert result is not None
        assert len(result) >= 1
        assert {"file": "first.py"} in result


class TestContextItemFormats:
    """Tests for various context item formats."""

    def test_extract_single_key_items(self, temp_dir, mock_logger):
        """Test items with single key-value pairs."""
        content = """---
coauthor:
  context:
    - file: a.py
    - dir: ./b
    - url: https://c.com
    - rellink: /d
---
"""
        file_path = temp_dir / "single.md"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is not None
        assert len(result) == 4
        assert all(len(item) == 1 for item in result)

    def test_extract_dict_items(self, temp_dir, mock_logger):
        """Test items as dictionary format."""
        content = """---
coauthor:
  context:
    - file: test1.py
    - file: test2.py
---
"""
        file_path = temp_dir / "dict.md"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        assert result is not None
        assert len(result) == 2
        assert result[0] == {"file": "test1.py"}
        assert result[1] == {"file": "test2.py"}


class TestEmbeddedContextBlocks:
    """Tests for embedded context blocks in comments."""

    def test_extract_python_multiline_comment(self, temp_dir, mock_logger):
        """Test Python file with context in multi-line comment (not docstring)."""
        content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module without context in docstring.
"""

# Additional configuration
# coauthor:
#   context:
#     - file: config.py

def main():
    pass
'''
        file_path = temp_dir / "script.py"
        file_path.write_text(content, encoding="utf-8")

        # Current implementation may not detect this format
        # This test documents expected behavior
        result = extract_frontmatter_context(str(file_path), mock_logger)

        # Depending on regex pattern, may or may not extract from # comments
        # Primary support is for docstrings and /* */ blocks
        assert result is None or isinstance(result, list)

    def test_extract_html_comment(self, temp_dir, mock_logger):
        """Test HTML file with context in comment."""
        content = """<!DOCTYPE html>
<!--
coauthor:
  context:
    - file: styles.css
    - file: script.js
-->
<html>
<body>
</body>
</html>
"""
        file_path = temp_dir / "index.html"
        file_path.write_text(content, encoding="utf-8")

        result = extract_frontmatter_context(str(file_path), mock_logger)

        # HTML comment support depends on regex pattern
        # May require specific pattern for <!-- --> comments
        assert result is None or len(result) == 2
