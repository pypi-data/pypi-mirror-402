"""
Tests for bug C2-1243: TypeError in write_files tool fix.

Tests the robust input validation and JSON parsing for write_files tool
when OpenAI returns JSON-escaped strings instead of arrays.
"""

import json
import os
import tempfile
import shutil

from coauthor.modules.tools import generic


class TestWriteFilesC21243:
    """Test write_files with JSON-escaped string parameters (Bug C2-1243)."""

    def setup_method(self):
        """Create a temporary project directory."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_write_files_with_valid_list(self):
        """Test write_files with properly formatted list of dicts (existing behavior)."""
        files = [{"path": "test1.txt", "content": "Content 1"}, {"path": "test2.txt", "content": "Content 2"}]

        generic.write_files(self.temp_dir, files)

        # Verify files were created
        assert os.path.exists(os.path.join(self.temp_dir, "test1.txt"))
        assert os.path.exists(os.path.join(self.temp_dir, "test2.txt"))

        # Verify content
        with open(os.path.join(self.temp_dir, "test1.txt"), "r", encoding="utf-8") as f:
            assert f.read() == "Content 1"
        with open(os.path.join(self.temp_dir, "test2.txt"), "r", encoding="utf-8") as f:
            assert f.read() == "Content 2"

    def test_write_files_with_json_string(self):
        """Test write_files with JSON-escaped string (new behavior for C2-1243)."""
        files_json = json.dumps(
            [{"path": "test1.txt", "content": "Content 1"}, {"path": "test2.txt", "content": "Content 2"}]
        )

        generic.write_files(self.temp_dir, files_json)

        # Verify files were created
        assert os.path.exists(os.path.join(self.temp_dir, "test1.txt"))
        assert os.path.exists(os.path.join(self.temp_dir, "test2.txt"))

        # Verify content
        with open(os.path.join(self.temp_dir, "test1.txt"), "r", encoding="utf-8") as f:
            assert f.read() == "Content 1"
        with open(os.path.join(self.temp_dir, "test2.txt"), "r", encoding="utf-8") as f:
            assert f.read() == "Content 2"

    def test_write_files_with_invalid_json_string(self):
        """Test write_files with invalid JSON string raises ValueError."""
        invalid_json = '{"path": "test.txt", "content": "Invalid'  # Missing closing braces

        try:
            generic.write_files(self.temp_dir, invalid_json)
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "Invalid JSON string for files parameter" in str(exc)
            # Verify exception chaining
            assert exc.__cause__ is not None
            assert isinstance(exc.__cause__, json.JSONDecodeError)

    def test_write_files_with_non_list_non_string(self):
        """Test write_files with non-list, non-string input raises ValueError."""
        try:
            generic.write_files(self.temp_dir, {"path": "test.txt"})
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "files parameter must be a list" in str(exc)
            assert "got dict" in str(exc)

    def test_write_files_with_list_containing_non_dict(self):
        """Test write_files with list containing non-dict elements raises ValueError."""
        files = [
            {"path": "test1.txt", "content": "Content 1"},
            "not a dict",
            {"path": "test3.txt", "content": "Content 3"},
        ]

        try:
            generic.write_files(self.temp_dir, files)
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "File element at index 1 must be a dict" in str(exc)
            assert "got str" in str(exc)

    def test_write_files_with_dict_missing_path_key(self):
        """Test write_files with dict missing 'path' key raises ValueError."""
        files = [{"path": "test1.txt", "content": "Content 1"}, {"content": "Content 2"}]  # Missing 'path'

        try:
            generic.write_files(self.temp_dir, files)
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "File element at index 1 missing required key 'path'" in str(exc)

    def test_write_files_with_dict_missing_content_key(self):
        """Test write_files with dict missing 'content' key raises ValueError."""
        files = [{"path": "test1.txt", "content": "Content 1"}, {"path": "test2.txt"}]  # Missing 'content'

        try:
            generic.write_files(self.temp_dir, files)
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "File element at index 1 missing required key 'content'" in str(exc)

    def test_write_files_with_nested_path(self):
        """Test write_files creates nested directories as needed."""
        files_json = json.dumps([{"path": "subdir/nested/test.txt", "content": "Nested content"}])

        generic.write_files(self.temp_dir, files_json)

        # Verify nested directories and file were created
        nested_path = os.path.join(self.temp_dir, "subdir", "nested", "test.txt")
        assert os.path.exists(nested_path)

        with open(nested_path, "r", encoding="utf-8") as f:
            assert f.read() == "Nested content"

    def test_write_files_with_empty_list(self):
        """Test write_files with empty list (should succeed without creating files)."""
        generic.write_files(self.temp_dir, [])

        # Verify no files were created (directory should be empty)
        assert len(os.listdir(self.temp_dir)) == 0

    def test_write_files_with_json_string_empty_list(self):
        """Test write_files with JSON string representing empty list."""
        generic.write_files(self.temp_dir, "[]")

        # Verify no files were created
        assert len(os.listdir(self.temp_dir)) == 0

    def test_backward_compatibility_existing_code(self):
        """Test that existing code using properly formatted lists still works."""
        # This is how write_files was called before the fix
        files = [
            {"path": "existing.txt", "content": "Existing workflow"},
            {"path": "subdir/file.txt", "content": "Nested file"},
        ]

        # Should work exactly as before
        generic.write_files(self.temp_dir, files)

        # Verify
        assert os.path.exists(os.path.join(self.temp_dir, "existing.txt"))
        assert os.path.exists(os.path.join(self.temp_dir, "subdir/file.txt"))

        with open(os.path.join(self.temp_dir, "existing.txt"), "r", encoding="utf-8") as f:
            assert f.read() == "Existing workflow"

    def test_special_characters_in_content(self):
        """Test write_files handles special characters in content."""
        files = [
            {"path": "test.py", "content": "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"},
            {"path": "test.json", "content": '{"key": "value with \\"quotes\\""}'},
        ]

        generic.write_files(self.temp_dir, files)

        # Verify files and content
        with open(os.path.join(self.temp_dir, "test.py"), "r", encoding="utf-8") as f:
            assert "#!/usr/bin/env python3" in f.read()

        with open(os.path.join(self.temp_dir, "test.json"), "r", encoding="utf-8") as f:
            content = f.read()
            assert "key" in content
            assert "value with" in content

    def test_write_files_complex_json_string(self):
        """Test write_files with complex JSON string containing special characters."""
        complex_content = """def example():
    '''Docstring with "quotes" and 'apostrophes'.'''
    return {"key": "value"}
"""
        files_json = json.dumps([{"path": "complex.py", "content": complex_content}])

        generic.write_files(self.temp_dir, files_json)

        # Verify file was created with correct content
        file_path = os.path.join(self.temp_dir, "complex.py")
        assert os.path.exists(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            actual_content = f.read()
            assert actual_content == complex_content
