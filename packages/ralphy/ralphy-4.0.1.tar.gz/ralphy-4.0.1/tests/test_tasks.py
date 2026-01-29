"""Tests for task sources."""

import os
import tempfile

import pytest

from ralphy.tasks.markdown import MarkdownTaskSource


@pytest.fixture
def temp_prd():
    """Create a temporary PRD file for testing."""
    content = """# Test PRD

## Tasks

- [ ] First task
- [ ] Second task
- [x] Completed task
- [ ] Third task
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


def test_markdown_get_next_task(temp_prd):
    """Test getting the next incomplete task."""
    source = MarkdownTaskSource(temp_prd)
    assert source.get_next_task() == "First task"


def test_markdown_get_all_tasks(temp_prd):
    """Test getting all incomplete tasks."""
    source = MarkdownTaskSource(temp_prd)
    tasks = source.get_all_tasks()
    assert tasks == ["First task", "Second task", "Third task"]


def test_markdown_count_remaining(temp_prd):
    """Test counting remaining tasks."""
    source = MarkdownTaskSource(temp_prd)
    assert source.count_remaining() == 3


def test_markdown_count_completed(temp_prd):
    """Test counting completed tasks."""
    source = MarkdownTaskSource(temp_prd)
    assert source.count_completed() == 1


def test_markdown_mark_complete(temp_prd):
    """Test marking a task as complete."""
    source = MarkdownTaskSource(temp_prd)

    # Mark first task complete
    source.mark_complete("First task")

    # Verify it's marked
    assert source.count_remaining() == 2
    assert source.count_completed() == 2

    # Next task should be Second task
    assert source.get_next_task() == "Second task"


def test_markdown_exists():
    """Test file existence check."""
    source = MarkdownTaskSource("nonexistent.md")
    assert source.exists() is False


def test_markdown_exists_with_file(temp_prd):
    """Test file existence check with existing file."""
    source = MarkdownTaskSource(temp_prd)
    assert source.exists() is True


def test_markdown_empty_file():
    """Test with empty file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("")
        f.flush()

        source = MarkdownTaskSource(f.name)
        assert source.get_next_task() is None
        assert source.count_remaining() == 0
        assert source.count_completed() == 0

    os.unlink(f.name)


def test_markdown_special_chars_in_task():
    """Test tasks with special regex characters."""
    content = """# PRD

- [ ] Fix bug in src/utils.ts (issue #123)
- [ ] Add feature [beta]
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()

        source = MarkdownTaskSource(f.name)
        tasks = source.get_all_tasks()
        assert len(tasks) == 2
        assert "Fix bug in src/utils.ts (issue #123)" in tasks
        assert "Add feature [beta]" in tasks

        # Mark task with special chars complete
        source.mark_complete("Fix bug in src/utils.ts (issue #123)")
        assert source.count_remaining() == 1

    os.unlink(f.name)
