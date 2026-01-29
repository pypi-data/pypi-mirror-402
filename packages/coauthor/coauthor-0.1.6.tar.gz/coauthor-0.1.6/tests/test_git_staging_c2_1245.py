"""
Tests for automatic Git staging functionality (C2-1245).

This module tests that write_file, write_files, and move_files automatically
stage new and moved files in Git so they become visible via list_tracked_files.
"""

import os
import tempfile
import shutil
import subprocess
from unittest.mock import Mock
from coauthor.modules.tools import generic


class TestGitStagingC21245:
    """Test automatic Git staging for file operations."""

    def setup_method(self):
        """Create a temporary Git repository for testing."""
        self.temp_dir = tempfile.mkdtemp()
        # Initialize Git repository
        subprocess.run(["git", "init"], cwd=self.temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.temp_dir, check=True)

        # Create an initial commit (Git requires at least one commit)
        initial_file = os.path.join(self.temp_dir, "README.md")
        with open(initial_file, "w", encoding="utf-8") as f:
            f.write("# Test Repository\n")
        subprocess.run(["git", "add", "README.md"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.temp_dir, check=True)

    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_write_file_stages_new_file(self):
        """Test that write_file automatically stages a new file in Git."""
        logger = Mock()

        # Create a new file
        generic.write_file(self.temp_dir, "newfile.txt", "New content", logger)

        # Verify file exists
        assert os.path.exists(os.path.join(self.temp_dir, "newfile.txt"))

        # Verify file is staged (appears in git ls-files)
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "newfile.txt" in tracked_files

        # Verify file is in staging area (git diff --cached)
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"], cwd=self.temp_dir, capture_output=True, text=True, check=True
        )
        assert "newfile.txt" in result.stdout

    def test_write_file_stages_nested_file(self):
        """Test that write_file stages a file in a nested directory."""
        logger = Mock()

        # Create a nested file
        generic.write_file(self.temp_dir, "subdir/nested/file.txt", "Nested content", logger)

        # Verify file is staged
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "subdir/nested/file.txt" in tracked_files

    def test_write_files_stages_multiple_files(self):
        """Test that write_files stages all new files."""
        logger = Mock()

        files = [
            {"path": "file1.txt", "content": "Content 1"},
            {"path": "file2.txt", "content": "Content 2"},
            {"path": "subdir/file3.txt", "content": "Content 3"},
        ]

        generic.write_files(self.temp_dir, files, logger)

        # Verify all files are staged
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "file1.txt" in tracked_files
        assert "file2.txt" in tracked_files
        assert "subdir/file3.txt" in tracked_files

    def test_move_files_stages_at_new_location(self):
        """Test that move_files stages files at their new location."""
        logger = Mock()

        # Create and commit a file
        generic.write_file(self.temp_dir, "original.txt", "Original content", logger)
        subprocess.run(["git", "commit", "-m", "Add original file"], cwd=self.temp_dir, check=True)

        # Move the file
        moves = [{"source": "original.txt", "destination": "moved.txt"}]
        result = generic.move_files(self.temp_dir, moves, logger)

        # Verify move was successful
        assert "Moved to moved.txt" in result["original.txt"]

        # Verify new file is staged
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "moved.txt" in tracked_files

    def test_write_file_respects_gitignore(self):
        """Test that Git staging respects .gitignore rules."""
        logger = Mock()

        # Create .gitignore
        gitignore_path = os.path.join(self.temp_dir, ".gitignore")
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("*.log\n")
        subprocess.run(["git", "add", ".gitignore"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Add gitignore"], cwd=self.temp_dir, check=True)

        # Try to create an ignored file
        generic.write_file(self.temp_dir, "test.log", "Log content", logger)

        # Verify file exists but is not staged
        assert os.path.exists(os.path.join(self.temp_dir, "test.log"))
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "test.log" not in tracked_files

    def test_write_file_without_git_repo(self):
        """Test that write_file works gracefully when not in a Git repository."""
        # Create a non-Git directory
        non_git_dir = tempfile.mkdtemp()
        try:
            logger = Mock()

            # Should not raise an exception
            generic.write_file(non_git_dir, "test.txt", "Content", logger)

            # Verify file was created
            assert os.path.exists(os.path.join(non_git_dir, "test.txt"))

            # Verify debug message was logged
            logger.debug.assert_called()
            debug_messages = [call[0][0] for call in logger.debug.call_args_list]
            assert any("Could not stage file" in msg for msg in debug_messages)
        finally:
            shutil.rmtree(non_git_dir)

    def test_write_file_updates_existing_file_without_staging(self):
        """Test that updating an existing tracked file doesn't require staging."""
        logger = Mock()

        # Create and commit a file
        generic.write_file(self.temp_dir, "existing.txt", "Original content", logger)
        subprocess.run(["git", "commit", "-m", "Add existing file"], cwd=self.temp_dir, check=True)

        # Update the file
        logger.reset_mock()
        generic.write_file(self.temp_dir, "existing.txt", "Updated content", logger)

        # File should still be tracked
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "existing.txt" in tracked_files

        # Verify content was updated
        with open(os.path.join(self.temp_dir, "existing.txt"), "r", encoding="utf-8") as f:
            assert f.read() == "Updated content"

    def test_move_files_with_multiple_moves(self):
        """Test that move_files stages multiple moved files."""
        logger = Mock()

        # Create and commit multiple files
        for i in range(3):
            generic.write_file(self.temp_dir, f"file{i}.txt", f"Content {i}", logger)
        subprocess.run(["git", "commit", "-m", "Add multiple files"], cwd=self.temp_dir, check=True)

        # Move all files
        moves = [
            {"source": "file0.txt", "destination": "moved/file0.txt"},
            {"source": "file1.txt", "destination": "moved/file1.txt"},
            {"source": "file2.txt", "destination": "moved/file2.txt"},
        ]
        generic.move_files(self.temp_dir, moves, logger)

        # Verify all moved files are staged
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "moved/file0.txt" in tracked_files
        assert "moved/file1.txt" in tracked_files
        assert "moved/file2.txt" in tracked_files

    def test_git_staging_error_handling(self):
        """Test that Git staging errors are handled gracefully."""
        logger = Mock()

        # Create a file with permissions that might cause issues
        generic.write_file(self.temp_dir, "test.txt", "Test content", logger)

        # Even if staging fails, the file should be created
        assert os.path.exists(os.path.join(self.temp_dir, "test.txt"))

    def test_write_files_with_json_string_stages_files(self):
        """Test that write_files with JSON string parameter stages files."""
        import json

        logger = Mock()

        files_json = json.dumps(
            [{"path": "json1.txt", "content": "JSON content 1"}, {"path": "json2.txt", "content": "JSON content 2"}]
        )

        generic.write_files(self.temp_dir, files_json, logger)

        # Verify files are staged
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "json1.txt" in tracked_files
        assert "json2.txt" in tracked_files

    def test_list_tracked_files_shows_staged_files_immediately(self):
        """Test that list_tracked_files shows newly staged files immediately."""
        logger = Mock()

        # Get initial tracked files
        initial_files = generic.list_tracked_files(self.temp_dir)

        # Create a new file
        generic.write_file(self.temp_dir, "immediate.txt", "Immediate content", logger)

        # list_tracked_files should show the new file immediately
        updated_files = generic.list_tracked_files(self.temp_dir)
        assert len(updated_files) > len(initial_files)
        assert "immediate.txt" in updated_files

    def test_write_file_without_logger(self):
        """Test that write_file works without a logger (backward compatibility)."""
        # Should not raise an exception
        generic.write_file(self.temp_dir, "no_logger.txt", "Content without logger")

        # Verify file was created and staged
        assert os.path.exists(os.path.join(self.temp_dir, "no_logger.txt"))
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "no_logger.txt" in tracked_files

    def test_write_files_without_logger(self):
        """Test that write_files works without a logger (backward compatibility)."""
        files = [{"path": "no_logger1.txt", "content": "Content 1"}]

        # Should not raise an exception
        generic.write_files(self.temp_dir, files)

        # Verify file was created and staged
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "no_logger1.txt" in tracked_files

    def test_move_files_without_logger(self):
        """Test that move_files works without a logger (backward compatibility)."""
        # Create and commit a file
        generic.write_file(self.temp_dir, "source.txt", "Source content")
        subprocess.run(["git", "commit", "-m", "Add source file"], cwd=self.temp_dir, check=True)

        # Move the file without logger
        moves = [{"source": "source.txt", "destination": "dest.txt"}]
        generic.move_files(self.temp_dir, moves)

        # Verify file was moved and staged
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "dest.txt" in tracked_files
