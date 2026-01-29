#!/usr/bin/env python3
"""
Manual test script for Git staging functionality (C2-1245).
This script can be run independently to verify the implementation.
"""

import os
import tempfile
import shutil
import subprocess
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from coauthor.modules.tools import generic


class MockLogger:
    """Simple mock logger for testing."""
    def debug(self, msg):
        print(f"[DEBUG] {msg}")
    
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def warning(self, msg):
        print(f"[WARNING] {msg}")


def setup_git_repo():
    """Create a temporary Git repository for testing."""
    temp_dir = tempfile.mkdtemp()
    print(f"Created temp directory: {temp_dir}")
    
    # Initialize Git repository
    subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True)
    
    # Create an initial commit
    initial_file = os.path.join(temp_dir, "README.md")
    with open(initial_file, "w", encoding="utf-8") as f:
        f.write("# Test Repository\n")
    subprocess.run(["git", "add", "README.md"], cwd=temp_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, check=True)
    
    return temp_dir


def test_write_file_stages_new_file(temp_dir, logger):
    """Test that write_file automatically stages a new file."""
    print("\n=== Test: write_file stages new file ===")
    
    # Create a new file
    generic.write_file(temp_dir, "newfile.txt", "New content", logger)
    
    # Verify file exists
    assert os.path.exists(os.path.join(temp_dir, "newfile.txt")), "File should exist"
    print("✓ File created successfully")
    
    # Verify file is staged
    tracked_files = generic.list_tracked_files(temp_dir)
    assert "newfile.txt" in tracked_files, f"File should be in tracked files: {tracked_files}"
    print(f"✓ File is tracked: {tracked_files}")
    
    # Verify file is in staging area
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=temp_dir,
        capture_output=True,
        text=True,
        check=True
    )
    assert "newfile.txt" in result.stdout, "File should be in staging area"
    print("✓ File is in staging area")
    
    print("✓✓✓ Test PASSED")


def test_write_files_stages_multiple(temp_dir, logger):
    """Test that write_files stages multiple new files."""
    print("\n=== Test: write_files stages multiple files ===")
    
    files = [
        {"path": "file1.txt", "content": "Content 1"},
        {"path": "file2.txt", "content": "Content 2"},
        {"path": "subdir/file3.txt", "content": "Content 3"}
    ]
    
    generic.write_files(temp_dir, files, logger)
    
    # Verify all files are tracked
    tracked_files = generic.list_tracked_files(temp_dir)
    assert "file1.txt" in tracked_files, "file1.txt should be tracked"
    assert "file2.txt" in tracked_files, "file2.txt should be tracked"
    assert "subdir/file3.txt" in tracked_files, "subdir/file3.txt should be tracked"
    
    print(f"✓ All files tracked: {tracked_files}")
    print("✓✓✓ Test PASSED")


def test_move_files_stages_new_location(temp_dir, logger):
    """Test that move_files stages files at new location."""
    print("\n=== Test: move_files stages at new location ===")
    
    # Create and commit a file
    generic.write_file(temp_dir, "original.txt", "Original content", logger)
    subprocess.run(["git", "commit", "-m", "Add original file"], cwd=temp_dir, check=True)
    
    # Move the file
    moves = [{"source": "original.txt", "destination": "moved.txt"}]
    result = generic.move_files(temp_dir, moves, logger)
    
    assert "Moved to moved.txt" in result["original.txt"], f"Move should succeed: {result}"
    print(f"✓ File moved: {result}")
    
    # Verify new file is tracked
    tracked_files = generic.list_tracked_files(temp_dir)
    assert "moved.txt" in tracked_files, f"Moved file should be tracked: {tracked_files}"
    print(f"✓ Moved file is tracked: {tracked_files}")
    
    print("✓✓✓ Test PASSED")


def test_gitignore_respected(temp_dir, logger):
    """Test that .gitignore rules are respected."""
    print("\n=== Test: .gitignore is respected ===")
    
    # Create .gitignore
    gitignore_path = os.path.join(temp_dir, ".gitignore")
    with open(gitignore_path, "w", encoding="utf-8") as f:
        f.write("*.log\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=temp_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Add gitignore"], cwd=temp_dir, check=True)
    
    # Try to create an ignored file
    generic.write_file(temp_dir, "test.log", "Log content", logger)
    
    # Verify file exists but is not tracked
    assert os.path.exists(os.path.join(temp_dir, "test.log")), "File should exist"
    tracked_files = generic.list_tracked_files(temp_dir)
    assert "test.log" not in tracked_files, f".log file should not be tracked: {tracked_files}"
    
    print("✓ .gitignore rules respected")
    print("✓✓✓ Test PASSED")


def test_non_git_directory(logger):
    """Test graceful handling when not in a Git repository."""
    print("\n=== Test: Non-Git directory graceful handling ===")
    
    non_git_dir = tempfile.mkdtemp()
    try:
        # Should not raise an exception
        generic.write_file(non_git_dir, "test.txt", "Content", logger)
        
        # Verify file was created
        assert os.path.exists(os.path.join(non_git_dir, "test.txt")), "File should be created"
        print("✓ File created in non-Git directory")
        print("✓✓✓ Test PASSED")
    finally:
        shutil.rmtree(non_git_dir)


def main():
    """Run all tests."""
    print("=" * 60)
    print("Git Staging Functionality Tests (C2-1245)")
    print("=" * 60)
    
    logger = MockLogger()
    temp_dir = None
    
    try:
        temp_dir = setup_git_repo()
        
        # Run tests
        test_write_file_stages_new_file(temp_dir, logger)
        test_write_files_stages_multiple(temp_dir, logger)
        test_move_files_stages_new_location(temp_dir, logger)
        test_gitignore_respected(temp_dir, logger)
        test_non_git_directory(logger)
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓✓✓")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗✗✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗✗✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\nCleaned up temp directory: {temp_dir}")


if __name__ == "__main__":
    sys.exit(main())
