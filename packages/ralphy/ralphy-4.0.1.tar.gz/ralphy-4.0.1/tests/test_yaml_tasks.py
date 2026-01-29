"""Tests for YAML task source."""

import os
import tempfile

import pytest

from ralphy.tasks.yaml import YamlTaskSource


@pytest.fixture
def temp_yaml():
    """Create a temporary YAML task file for testing."""
    content = """tasks:
  - title: First task
    completed: false
  - title: Second task
    completed: false
  - title: Completed task
    completed: true
  - title: Third task
    completed: false
    parallel_group: 1
  - title: Fourth task
    completed: false
    parallel_group: 1
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


def test_yaml_get_next_task(temp_yaml):
    """Test getting the next incomplete task."""
    source = YamlTaskSource(temp_yaml)
    assert source.get_next_task() == "First task"


def test_yaml_get_all_tasks(temp_yaml):
    """Test getting all incomplete tasks."""
    source = YamlTaskSource(temp_yaml)
    tasks = source.get_all_tasks()
    assert len(tasks) == 4
    assert "First task" in tasks
    assert "Second task" in tasks
    assert "Third task" in tasks
    assert "Fourth task" in tasks
    # Completed task should not be in the list
    assert "Completed task" not in tasks


def test_yaml_count_remaining(temp_yaml):
    """Test counting remaining tasks."""
    source = YamlTaskSource(temp_yaml)
    assert source.count_remaining() == 4


def test_yaml_count_completed(temp_yaml):
    """Test counting completed tasks."""
    source = YamlTaskSource(temp_yaml)
    assert source.count_completed() == 1


def test_yaml_mark_complete(temp_yaml):
    """Test marking a task as complete."""
    source = YamlTaskSource(temp_yaml)

    # Mark first task complete
    source.mark_complete("First task")

    # Verify it's marked
    assert source.count_remaining() == 3
    assert source.count_completed() == 2

    # Next task should be Second task
    assert source.get_next_task() == "Second task"


def test_yaml_exists():
    """Test file existence check."""
    source = YamlTaskSource("nonexistent.yaml")
    assert source.exists() is False


def test_yaml_exists_with_file(temp_yaml):
    """Test file existence check with existing file."""
    source = YamlTaskSource(temp_yaml)
    assert source.exists() is True


def test_yaml_empty_file():
    """Test with empty file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("")
        f.flush()

        source = YamlTaskSource(f.name)
        assert source.get_next_task() is None
        assert source.count_remaining() == 0
        assert source.count_completed() == 0

    os.unlink(f.name)


def test_yaml_parallel_groups(temp_yaml):
    """Test getting parallel groups."""
    source = YamlTaskSource(temp_yaml)

    # Third and Fourth tasks are in group 1
    assert source.get_parallel_group("Third task") == 1
    assert source.get_parallel_group("Fourth task") == 1

    # First task has no group (defaults to 0)
    assert source.get_parallel_group("First task") == 0


def test_yaml_get_tasks_in_group(temp_yaml):
    """Test getting tasks in a parallel group."""
    source = YamlTaskSource(temp_yaml)

    # Get tasks in group 1
    group1_tasks = source.get_tasks_in_group(1)
    assert len(group1_tasks) == 2
    assert "Third task" in group1_tasks
    assert "Fourth task" in group1_tasks


def test_yaml_get_unique_groups(temp_yaml):
    """Test getting unique parallel groups."""
    source = YamlTaskSource(temp_yaml)
    groups = source.get_unique_groups()

    # Should have group 0 (default) and group 1
    assert 0 in groups
    assert 1 in groups


def test_yaml_no_tasks_key():
    """Test YAML file without tasks key."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("other_key: value\n")
        f.flush()

        source = YamlTaskSource(f.name)
        assert source.get_next_task() is None
        assert source.count_remaining() == 0

    os.unlink(f.name)
