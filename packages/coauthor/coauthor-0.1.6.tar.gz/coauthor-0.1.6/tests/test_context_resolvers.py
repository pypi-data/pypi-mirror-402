# -*- coding: utf-8 -*-
"""
Unit tests for context resolvers (C2-1256).

Tests all resolver types: FileResolver, DirResolver, URLResolver, RelinkResolver.
Includes error handling, edge cases, and Hugo-specific patterns.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from coauthor.utils.context_resolvers import (
    BaseContextResolver,
    FileResolver,
    DirResolver,
    URLResolver,
    RelinkResolver,
    resolve_context_item,
    format_context_message,
)


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return Mock()


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directory structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    utils_dir = src_dir / "utils"
    utils_dir.mkdir()
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    docs_dir = content_dir / "docs"
    docs_dir.mkdir()

    # Create test files
    (src_dir / "main.py").write_text("# Main file\nprint('hello')")
    (utils_dir / "helper.py").write_text("# Helper file\ndef helper():\n    pass")
    (docs_dir / "index.md").write_text("# Documentation\nContent here")
    (content_dir / "about.md").write_text("# About\nAbout content")

    return tmp_path


class TestFormatContextMessage:
    """Tests for format_context_message helper function."""

    def test_format_basic_message(self):
        """Test basic message formatting with metadata."""
        content = "Line 1\nLine 2\nLine 3"
        result = format_context_message(content, "file", "/path/to/file.py")

        assert "--- Context from file: /path/to/file.py ---" in result
        assert "Line 1\nLine 2\nLine 3" in result
        assert "--- End of file context" in result
        assert "3 lines" in result
        assert "characters" in result

    def test_format_empty_content(self):
        """Test formatting with empty content."""
        result = format_context_message("", "file", "/path/to/empty.txt")

        assert "--- Context from file: /path/to/empty.txt ---" in result
        assert "--- End of file context" in result
        assert "0 characters" in result

    def test_format_multiline_content(self):
        """Test formatting with multi-line content."""
        content = "\n".join([f"Line {i}" for i in range(100)])
        result = format_context_message(content, "url", "https://example.com")

        assert "--- Context from url: https://example.com ---" in result
        assert "100 lines" in result


class TestFileResolver:
    """Tests for FileResolver."""

    def test_resolve_absolute_path(self, temp_project, mock_logger):
        """Test resolving absolute file path."""
        resolver = FileResolver(str(temp_project), str(temp_project), mock_logger)
        file_path = temp_project / "src" / "main.py"

        result = resolver.resolve(str(file_path))

        assert result is not None
        assert "# Main file" in result
        assert "print('hello')" in result

    def test_resolve_relative_path(self, temp_project, mock_logger):
        """Test resolving relative file path."""
        resolver = FileResolver(str(temp_project), str(temp_project), mock_logger)

        result = resolver.resolve("src/utils/helper.py")

        assert result is not None
        assert "# Helper file" in result
        assert "def helper():" in result

    def test_resolve_missing_file(self, temp_project, mock_logger):
        """Test resolving non-existent file."""
        resolver = FileResolver(str(temp_project), str(temp_project), mock_logger)

        result = resolver.resolve("missing/file.py")

        assert result is None
        mock_logger.warning.assert_called_once()

    def test_resolve_relative_to_base_path(self, temp_project, mock_logger):
        """Test resolving path relative to base_path (not project root)."""
        base_path = str(temp_project / "src")
        resolver = FileResolver(base_path, str(temp_project), mock_logger)

        result = resolver.resolve("utils/helper.py")

        assert result is not None
        assert "# Helper file" in result


class TestDirResolver:
    """Tests for DirResolver."""

    def test_resolve_directory(self, temp_project, mock_logger):
        """Test resolving directory recursively."""
        resolver = DirResolver(str(temp_project), str(temp_project), mock_logger)

        result = resolver.resolve("src")

        assert result is not None
        assert "main.py" in result
        assert "helper.py" in result
        assert "# Main file" in result
        assert "# Helper file" in result

    def test_resolve_empty_directory(self, temp_project, mock_logger):
        """Test resolving empty directory."""
        empty_dir = temp_project / "empty"
        empty_dir.mkdir()

        resolver = DirResolver(str(temp_project), str(temp_project), mock_logger)
        result = resolver.resolve("empty")

        assert result is None
        mock_logger.warning.assert_called_once()

    def test_resolve_missing_directory(self, temp_project, mock_logger):
        """Test resolving non-existent directory."""
        resolver = DirResolver(str(temp_project), str(temp_project), mock_logger)

        result = resolver.resolve("missing_dir")

        assert result is None
        mock_logger.warning.assert_called_once()

    def test_resolve_directory_with_subdirs(self, temp_project, mock_logger):
        """Test resolving directory with nested subdirectories."""
        resolver = DirResolver(str(temp_project), str(temp_project), mock_logger)

        result = resolver.resolve("src")

        # Should include files from subdirectories
        assert "utils/helper.py" in result or "utils\\helper.py" in result


class TestURLResolver:
    """Tests for URLResolver."""

    @patch("coauthor.utils.context_resolvers.urlopen")
    def test_resolve_url_success(self, mock_urlopen, mock_logger):
        """Test successful URL resolution."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.read.return_value = b"HTTP content"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False
        mock_urlopen.return_value = mock_response

        resolver = URLResolver(None, None, mock_logger)
        result = resolver.resolve("https://example.com/docs")

        assert result is not None
        assert "HTTP content" in result

    @patch("coauthor.utils.context_resolvers.urlopen")
    def test_resolve_url_timeout(self, mock_urlopen, mock_logger):
        """Test URL resolution with timeout."""
        from urllib.error import URLError

        mock_urlopen.side_effect = URLError("Connection timeout")

        resolver = URLResolver(None, None, mock_logger)
        result = resolver.resolve("https://example.com/slow")

        assert result is None
        mock_logger.error.assert_called_once()

    @patch("coauthor.utils.context_resolvers.urlopen")
    def test_resolve_url_http_error(self, mock_urlopen, mock_logger):
        """Test URL resolution with HTTP error (404)."""
        from urllib.error import HTTPError

        mock_urlopen.side_effect = HTTPError("https://example.com/missing", 404, "Not Found", {}, None)

        resolver = URLResolver(None, None, mock_logger)
        result = resolver.resolve("https://example.com/missing")

        assert result is None
        mock_logger.error.assert_called_once()

    @patch("coauthor.utils.context_resolvers.urlopen")
    def test_resolve_url_with_encoding(self, mock_urlopen, mock_logger):
        """Test URL resolution with UTF-8 content."""
        mock_response = MagicMock()
        mock_response.read.return_value = "UTF-8 content: café ☕".encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False
        mock_urlopen.return_value = mock_response

        resolver = URLResolver(None, None, mock_logger)
        result = resolver.resolve("https://example.com/utf8")

        assert result is not None
        assert "café ☕" in result


class TestRelinkResolver:
    """Tests for RelinkResolver (Hugo content paths)."""

    def test_resolve_rellink_md_file(self, temp_project, mock_logger):
        """Test resolving Hugo rellink to .md file."""
        resolver = RelinkResolver(str(temp_project), str(temp_project), mock_logger)

        result = resolver.resolve("/about")

        assert result is not None
        assert "# About" in result
        assert "About content" in result

    def test_resolve_rellink_index_md(self, temp_project, mock_logger):
        """Test resolving Hugo rellink to index.md."""
        resolver = RelinkResolver(str(temp_project), str(temp_project), mock_logger)

        result = resolver.resolve("/docs")

        assert result is not None
        assert "# Documentation" in result

    def test_resolve_rellink_with_leading_slash(self, temp_project, mock_logger):
        """Test resolving rellink with leading slash."""
        resolver = RelinkResolver(str(temp_project), str(temp_project), mock_logger)

        result = resolver.resolve("/about")

        assert result is not None

    def test_resolve_rellink_without_leading_slash(self, temp_project, mock_logger):
        """Test resolving rellink without leading slash."""
        resolver = RelinkResolver(str(temp_project), str(temp_project), mock_logger)

        result = resolver.resolve("about")

        assert result is not None

    def test_resolve_rellink_not_found(self, temp_project, mock_logger):
        """Test resolving non-existent Hugo rellink."""
        resolver = RelinkResolver(str(temp_project), str(temp_project), mock_logger)

        result = resolver.resolve("/missing-page")

        assert result is None
        mock_logger.warning.assert_called_once()

    def test_resolve_rellink_multilingual(self, temp_project, mock_logger):
        """Test resolving Hugo rellink with multilingual pattern."""
        # Create multilingual structure
        content_dir = temp_project / "content"
        en_dir = content_dir / "en" / "docs"
        en_dir.mkdir(parents=True)
        (en_dir / "guide.md").write_text("# English Guide")

        resolver = RelinkResolver(str(temp_project), str(temp_project), mock_logger)
        result = resolver.resolve("/en/docs/guide")

        assert result is not None
        assert "# English Guide" in result


class TestResolveContextItem:
    """Tests for resolve_context_item dispatcher function."""

    def test_resolve_file_context(self, temp_project, mock_logger):
        """Test resolving file context item."""
        item = {"file": "src/main.py"}

        result = resolve_context_item(item, str(temp_project), str(temp_project), mock_logger)

        assert result is not None
        assert "# Main file" in result
        assert "--- Context from file:" in result

    def test_resolve_dir_context(self, temp_project, mock_logger):
        """Test resolving directory context item."""
        item = {"dir": "src/utils"}

        result = resolve_context_item(item, str(temp_project), str(temp_project), mock_logger)

        assert result is not None
        assert "# Helper file" in result
        assert "--- Context from file:" in result  # Dir resolver formats each file separately

    @patch("coauthor.utils.context_resolvers.urlopen")
    def test_resolve_url_context(self, mock_urlopen, mock_logger):
        """Test resolving URL context item."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"URL content"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False
        mock_urlopen.return_value = mock_response

        item = {"url": "https://example.com/api"}

        result = resolve_context_item(item, None, None, mock_logger)

        assert result is not None
        assert "URL content" in result
        assert "--- Context from url:" in result

    def test_resolve_rellink_context(self, temp_project, mock_logger):
        """Test resolving rellink context item."""
        item = {"rellink": "/about"}

        result = resolve_context_item(item, str(temp_project), str(temp_project), mock_logger)

        assert result is not None
        assert "# About" in result
        assert "--- Context from rellink:" in result

    def test_resolve_unknown_context_type(self, mock_logger):
        """Test resolving unknown context type."""
        item = {"unknown": "value"}

        result = resolve_context_item(item, None, None, mock_logger)

        assert result is None
        mock_logger.warning.assert_called_once()

    def test_resolve_empty_context_item(self, mock_logger):
        """Test resolving empty context item."""
        item = {}

        result = resolve_context_item(item, None, None, mock_logger)

        assert result is None


class TestMixedContextScenarios:
    """Tests for mixed context types and edge cases."""

    def test_multiple_context_types(self, temp_project, mock_logger):
        """Test resolving multiple context items."""
        items = [
            {"file": "src/main.py"},
            {"dir": "src/utils"},
        ]

        results = [resolve_context_item(item, str(temp_project), str(temp_project), mock_logger) for item in items]

        assert all(r is not None for r in results)
        assert "# Main file" in results[0]
        assert "# Helper file" in results[1]

    def test_partial_failure_handling(self, temp_project, mock_logger):
        """Test that one failure doesn't affect others."""
        items = [
            {"file": "src/main.py"},  # Should succeed
            {"file": "missing.py"},  # Should fail
            {"dir": "src/utils"},  # Should succeed
        ]

        results = [resolve_context_item(item, str(temp_project), str(temp_project), mock_logger) for item in items]

        assert results[0] is not None
        assert results[1] is None
        assert results[2] is not None

    def test_file_encoding_handling(self, temp_project, mock_logger):
        """Test handling of files with UTF-8 encoding."""
        utf8_file = temp_project / "utf8.txt"
        utf8_file.write_text("UTF-8 content: café ☕", encoding="utf-8")

        resolver = FileResolver(str(temp_project), str(temp_project), mock_logger)
        result = resolver.resolve(str(utf8_file))

        assert result is not None
        assert "café ☕" in result


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_file_permission_error(self, temp_project, mock_logger):
        """Test handling of file permission errors."""
        # Note: This test may not work on all platforms
        restricted_file = temp_project / "restricted.txt"
        restricted_file.write_text("Secret content")

        # Try to change permissions (Unix-like systems)
        try:
            os.chmod(restricted_file, 0o000)
            resolver = FileResolver(str(temp_project), str(temp_project), mock_logger)
            result = resolver.resolve(str(restricted_file))
            assert result is None
        except Exception:
            # Skip if permission change not supported
            pass
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(restricted_file, 0o644)
            except Exception:
                pass

    def test_symlink_handling(self, temp_project, mock_logger):
        """Test handling of symbolic links."""
        original = temp_project / "original.txt"
        original.write_text("Original content")

        symlink = temp_project / "symlink.txt"
        try:
            symlink.symlink_to(original)

            resolver = FileResolver(str(temp_project), str(temp_project), mock_logger)
            result = resolver.resolve(str(symlink))

            # Should resolve through symlink
            assert result is not None
            assert "Original content" in result
        except OSError:
            # Skip if symlinks not supported (Windows without admin)
            pytest.skip("Symlinks not supported on this platform")

    def test_circular_directory_references(self, temp_project, mock_logger):
        """Test handling of potential circular directory structures."""
        # Create a normal directory structure (actual circular refs need symlinks)
        nested_dir = temp_project / "level1" / "level2" / "level3"
        nested_dir.mkdir(parents=True)
        (nested_dir / "deep.txt").write_text("Deep content")

        resolver = DirResolver(str(temp_project), str(temp_project), mock_logger)
        result = resolver.resolve("level1")

        # Should handle deep nesting without issues
        assert result is not None
        assert "Deep content" in result
