"""YAML task source implementation."""

import os
from typing import Optional

import yaml

from ralphy.tasks.base import TaskSource


class YamlTaskSource(TaskSource):
    """Task source that reads from YAML task files."""

    def __init__(self, file_path: str = "tasks.yaml"):
        """Initialize with path to YAML file."""
        self.file_path = file_path

    def _read_data(self) -> dict:
        """Read and parse the YAML file."""
        if not os.path.exists(self.file_path):
            return {"tasks": []}
        with open(self.file_path) as f:
            data = yaml.safe_load(f) or {}
        if "tasks" not in data:
            data["tasks"] = []
        return data

    def _write_data(self, data: dict) -> None:
        """Write data to the YAML file."""
        with open(self.file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_next_task(self) -> Optional[str]:
        """Get the next incomplete task."""
        data = self._read_data()
        for task in data.get("tasks", []):
            if not task.get("completed", False):
                return task.get("title", "")
        return None

    def get_all_tasks(self) -> list[str]:
        """Get all incomplete tasks."""
        data = self._read_data()
        return [
            task.get("title", "")
            for task in data.get("tasks", [])
            if not task.get("completed", False)
        ]

    def count_remaining(self) -> int:
        """Count remaining incomplete tasks."""
        data = self._read_data()
        return sum(
            1 for task in data.get("tasks", []) if not task.get("completed", False)
        )

    def count_completed(self) -> int:
        """Count completed tasks."""
        data = self._read_data()
        return sum(1 for task in data.get("tasks", []) if task.get("completed", False))

    def mark_complete(self, task_title: str) -> None:
        """Mark a task as complete."""
        data = self._read_data()
        for task in data.get("tasks", []):
            if task.get("title") == task_title:
                task["completed"] = True
                break
        self._write_data(data)

    def exists(self) -> bool:
        """Check if the YAML file exists."""
        return os.path.exists(self.file_path)

    def get_parallel_group(self, task_title: str) -> int:
        """Get the parallel group for a task (0 = no group)."""
        data = self._read_data()
        for task in data.get("tasks", []):
            if task.get("title") == task_title:
                return task.get("parallel_group", 0)
        return 0

    def get_tasks_in_group(self, group: int) -> list[str]:
        """Get all incomplete tasks in a parallel group."""
        data = self._read_data()
        return [
            task.get("title", "")
            for task in data.get("tasks", [])
            if not task.get("completed", False)
            and task.get("parallel_group", 0) == group
        ]

    def get_unique_groups(self) -> list[int]:
        """Get all unique parallel groups with incomplete tasks."""
        data = self._read_data()
        groups = set()
        for task in data.get("tasks", []):
            if not task.get("completed", False):
                groups.add(task.get("parallel_group", 0))
        return sorted(groups)
