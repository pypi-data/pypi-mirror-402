import os
import pytest
from coauthor.utils.git import (
    is_git_tracked,
    get_git_diff,
    get_files_by_last_commit
)

@pytest.fixture
def temp_repo(tmp_path):
    # Create a temporary Git repository
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    os.chdir(repo_path)
    
    # Initialize Git repo
    os.system("git init")
    
    # Create some files
    (repo_path / "file1.txt").write_text("content1")
    (repo_path / "file2.txt").write_text("content2")
    
    # Add and commit
    os.system("git add file1.txt")
    os.system('git commit -m "Add file1"')
    os.system("git add file2.txt")
    os.system('git commit -m "Add file2"')
    
    return repo_path

def test_is_git_tracked(temp_repo):
    assert is_git_tracked(str(temp_repo / "file1.txt")) == True
    assert is_git_tracked(str(temp_repo / "nonexistent.txt")) == False
    assert is_git_tracked(str(temp_repo / "file3.txt")) == False  # Untracked

def test_get_git_diff(temp_repo):
    # No changes
    assert get_git_diff(str(temp_repo / "file1.txt")) == ""
    
    # Modify file
    (temp_repo / "file1.txt").write_text("modified content")
    diff = get_git_diff(str(temp_repo / "file1.txt"))
    assert "modified content" in diff
    assert "content1" in diff

def test_get_files_by_last_commit(temp_repo):
    files = get_files_by_last_commit(str(temp_repo))
    assert len(files) == 2
    assert files[0][0] == "file2.txt"  # More recent
    assert files[1][0] == "file1.txt"
