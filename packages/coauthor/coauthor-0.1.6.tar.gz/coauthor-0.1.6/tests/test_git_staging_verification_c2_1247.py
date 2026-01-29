"""
Verification tests for automatic Git staging functionality (C2-1247).

This module provides additional verification tests for the C2-1245 implementation,
focusing on edge cases and integration scenarios.
"""

import os
import tempfile
import shutil
import subprocess
from unittest.mock import Mock
from coauthor.modules.tools import generic


class TestGitStagingVerificationC21247:
    """Additional verification tests for automatic Git staging."""

    def setup_method(self):
        """Create a temporary Git repository for testing."""
        self.temp_dir = tempfile.mkdtemp()
        # Initialize Git repository
        subprocess.run(["git", "init"], cwd=self.temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.temp_dir, check=True)

        # Create an initial commit
        initial_file = os.path.join(self.temp_dir, "README.md")
        with open(initial_file, "w", encoding="utf-8") as f:
            f.write("# Verification Test Repository\n")
        subprocess.run(["git", "add", "README.md"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.temp_dir, check=True)

    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_write_file_visibility_in_list_tracked_files(self):
        """Verify that newly created files are immediately visible via list_tracked_files."""
        logger = Mock()

        # Get initial state
        initial_files = set(generic.list_tracked_files(self.temp_dir))

        # Create multiple new files
        test_files = ["test1.py", "test2.py", "subdir/test3.py"]
        for file_path in test_files:
            generic.write_file(self.temp_dir, file_path, f"Content for {file_path}", logger)

        # Get updated state
        updated_files = set(generic.list_tracked_files(self.temp_dir))

        # Verify all new files are visible
        new_files = updated_files - initial_files
        assert len(new_files) == len(test_files)
        for file_path in test_files:
            assert file_path in updated_files

    def test_write_files_batch_staging(self):
        """Verify that write_files stages all files in a single batch operation."""
        logger = Mock()

        # Create a batch of files
        files = [
            {"path": "batch/file1.txt", "content": "Batch content 1"},
            {"path": "batch/file2.txt", "content": "Batch content 2"},
            {"path": "batch/subdir/file3.txt", "content": "Batch content 3"},
            {"path": "other/file4.txt", "content": "Batch content 4"},
        ]

        generic.write_files(self.temp_dir, files, logger)

        # Verify all files are staged
        tracked_files = generic.list_tracked_files(self.temp_dir)
        for file_info in files:
            assert file_info["path"] in tracked_files

        # Verify all are in staging area
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"], cwd=self.temp_dir, capture_output=True, text=True, check=True
        )
        staged_files = result.stdout.strip().split("\n")
        for file_info in files:
            assert file_info["path"] in staged_files

    def test_move_files_removes_old_tracks_new(self):
        """Verify that move_files properly handles Git tracking for source and destination."""
        logger = Mock()

        # Create and commit initial files
        generic.write_file(self.temp_dir, "old_location/file1.txt", "Content 1", logger)
        generic.write_file(self.temp_dir, "old_location/file2.txt", "Content 2", logger)
        subprocess.run(["git", "commit", "-m", "Add initial files"], cwd=self.temp_dir, check=True)

        # Move files to new locations
        moves = [
            {"source": "old_location/file1.txt", "destination": "new_location/file1.txt"},
            {"source": "old_location/file2.txt", "destination": "new_location/renamed.txt"},
        ]
        generic.move_files(self.temp_dir, moves, logger)

        # Verify new locations are tracked
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "new_location/file1.txt" in tracked_files
        assert "new_location/renamed.txt" in tracked_files

        # Verify old locations are not in the file system
        assert not os.path.exists(os.path.join(self.temp_dir, "old_location/file1.txt"))
        assert not os.path.exists(os.path.join(self.temp_dir, "old_location/file2.txt"))

    def test_gitignore_pattern_matching(self):
        """Verify that various .gitignore patterns are respected."""
        logger = Mock()

        # Create comprehensive .gitignore
        gitignore_content = """
# Logs
*.log
*.log.*

# Temporary files
*.tmp
temp/

# Build artifacts
build/
dist/

# Specific file
secret.key
"""
        generic.write_file(self.temp_dir, ".gitignore", gitignore_content, logger)
        subprocess.run(["git", "commit", "-m", "Add gitignore"], cwd=self.temp_dir, check=True)

        # Create files that should be ignored
        ignored_files = [
            "debug.log",
            "app.log.1",
            "data.tmp",
            "temp/cache.txt",
            "build/output.txt",
            "secret.key",
        ]

        for file_path in ignored_files:
            generic.write_file(self.temp_dir, file_path, "Ignored content", logger)

        # Verify ignored files are not tracked
        tracked_files = generic.list_tracked_files(self.temp_dir)
        for file_path in ignored_files:
            assert file_path not in tracked_files, f"{file_path} should not be tracked"

        # Create files that should be tracked
        tracked_file = "valid.txt"
        generic.write_file(self.temp_dir, tracked_file, "Valid content", logger)

        # Verify valid file is tracked
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert tracked_file in tracked_files

    def test_concurrent_file_operations(self):
        """Verify that multiple consecutive file operations all stage correctly."""
        logger = Mock()

        # Perform multiple operations in sequence
        generic.write_file(self.temp_dir, "step1.txt", "Step 1", logger)
        generic.write_files(
            self.temp_dir,
            [
                {"path": "step2a.txt", "content": "Step 2a"},
                {"path": "step2b.txt", "content": "Step 2b"},
            ],
            logger,
        )
        generic.write_file(self.temp_dir, "step3.txt", "Step 3", logger)

        # Commit the staged files
        subprocess.run(["git", "commit", "-m", "Add step files"], cwd=self.temp_dir, check=True)

        # Move files
        moves = [
            {"source": "step1.txt", "destination": "moved/step1.txt"},
            {"source": "step2a.txt", "destination": "moved/step2a.txt"},
        ]
        generic.move_files(self.temp_dir, moves, logger)

        # Verify all operations resulted in proper tracking
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "moved/step1.txt" in tracked_files
        assert "moved/step2a.txt" in tracked_files
        assert "step2b.txt" in tracked_files
        assert "step3.txt" in tracked_files

    def test_deep_nested_directory_staging(self):
        """Verify that files in deeply nested directories are staged correctly."""
        logger = Mock()

        # Create file in deep nested structure
        deep_path = "level1/level2/level3/level4/level5/deep_file.txt"
        generic.write_file(self.temp_dir, deep_path, "Deep content", logger)

        # Verify file is tracked
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert deep_path in tracked_files

        # Verify directory structure was created
        full_path = os.path.join(self.temp_dir, deep_path)
        assert os.path.exists(full_path)

    def test_special_characters_in_filenames(self):
        """Verify that files with special characters in names are staged correctly."""
        logger = Mock()

        # Create files with special characters (that are valid in most filesystems)
        special_files = [
            "file-with-dash.txt",
            "file_with_underscore.txt",
            "file.multiple.dots.txt",
            "file with spaces.txt",
        ]

        for file_path in special_files:
            generic.write_file(self.temp_dir, file_path, f"Content for {file_path}", logger)

        # Verify all are tracked
        tracked_files = generic.list_tracked_files(self.temp_dir)
        for file_path in special_files:
            assert file_path in tracked_files

    def test_empty_file_staging(self):
        """Verify that empty files are staged correctly."""
        logger = Mock()

        # Create empty file
        generic.write_file(self.temp_dir, "empty.txt", "", logger)

        # Verify file is tracked
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "empty.txt" in tracked_files

        # Verify file exists and is empty
        empty_file = os.path.join(self.temp_dir, "empty.txt")
        assert os.path.exists(empty_file)
        assert os.path.getsize(empty_file) == 0

    def test_large_batch_write_files(self):
        """Verify that large batches of files are all staged correctly."""
        logger = Mock()

        # Create a large batch of files
        num_files = 50
        files = [{"path": f"batch/file_{i:03d}.txt", "content": f"Content {i}"} for i in range(num_files)]

        generic.write_files(self.temp_dir, files, logger)

        # Verify all files are tracked
        tracked_files = generic.list_tracked_files(self.temp_dir)
        for file_info in files:
            assert file_info["path"] in tracked_files

    def test_overwrite_staged_file(self):
        """Verify that overwriting a staged but uncommitted file works correctly."""
        logger = Mock()

        # Create and stage a file
        generic.write_file(self.temp_dir, "staged.txt", "Original content", logger)

        # Verify file is staged
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"], cwd=self.temp_dir, capture_output=True, text=True, check=True
        )
        assert "staged.txt" in result.stdout

        # Overwrite the file
        generic.write_file(self.temp_dir, "staged.txt", "Updated content", logger)

        # Verify file still exists and has updated content
        with open(os.path.join(self.temp_dir, "staged.txt"), "r", encoding="utf-8") as f:
            assert f.read() == "Updated content"

        # Verify file is still tracked
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "staged.txt" in tracked_files

    def test_mixed_new_and_existing_files(self):
        """Verify correct staging behavior with mix of new and existing files."""
        logger = Mock()

        # Create and commit initial files
        generic.write_file(self.temp_dir, "existing1.txt", "Existing 1", logger)
        generic.write_file(self.temp_dir, "existing2.txt", "Existing 2", logger)
        subprocess.run(["git", "commit", "-m", "Add existing files"], cwd=self.temp_dir, check=True)

        # Use write_files with mix of new and existing files
        files = [
            {"path": "existing1.txt", "content": "Updated existing 1"},
            {"path": "new1.txt", "content": "New content 1"},
            {"path": "existing2.txt", "content": "Updated existing 2"},
            {"path": "new2.txt", "content": "New content 2"},
        ]

        generic.write_files(self.temp_dir, files, logger)

        # Verify all files are tracked
        tracked_files = generic.list_tracked_files(self.temp_dir)
        assert "existing1.txt" in tracked_files
        assert "existing2.txt" in tracked_files
        assert "new1.txt" in tracked_files
        assert "new2.txt" in tracked_files

        # Verify new files are staged
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"], cwd=self.temp_dir, capture_output=True, text=True, check=True
        )
        assert "new1.txt" in result.stdout
        assert "new2.txt" in result.stdout
