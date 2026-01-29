"""Tests for git utilities."""

import subprocess
import pytest

from ralphy.git import GitManager
from ralphy.utils import slugify


def test_slugify_basic():
    """Test basic slugification."""
    assert slugify("Add a login button") == "add-a-login-button"


def test_slugify_special_chars():
    """Test slugification of special characters."""
    assert slugify("Fix bug #123 (urgent)") == "fix-bug-123-urgent"


def test_slugify_max_length():
    """Test slugification with max length."""
    long_text = "This is a very long task description that should be truncated"
    result = slugify(long_text, max_length=20)
    assert len(result) <= 20
    assert result == "this-is-a-very-long-"


def test_slugify_trailing_dashes():
    """Test that slugify removes trailing dashes."""
    assert slugify("test-task--") == "test-task"
    assert slugify("--test--task--") == "test-task"


def test_slugify_unicode():
    """Test slugification of unicode characters."""
    # Unicode gets converted to dashes
    result = slugify("Add café feature")
    assert "caf" in result


def test_git_manager_get_current_branch():
    """Test getting current branch."""
    branch = GitManager.get_current_branch()
    # Should return a string (either branch name or 'main' as fallback)
    assert isinstance(branch, str)
    assert len(branch) > 0


def test_git_manager_run_git():
    """Test running git commands."""
    result = GitManager.run_git("--version")
    assert result.returncode == 0
    assert "git" in result.stdout.lower()


def test_git_manager_initialization():
    """Test GitManager initialization."""
    manager = GitManager(
        base_branch="develop",
        create_pr=True,
        draft_pr=True,
        verbose=True,
    )
    assert manager.base_branch == "develop"
    assert manager.create_pr is True
    assert manager.draft_pr is True
    assert manager.verbose is True
    assert manager.task_branches == []


def test_git_manager_default_branch():
    """Test GitManager uses current branch as default."""
    manager = GitManager()
    # Should use current branch
    current = GitManager.get_current_branch()
    assert manager.base_branch == current
