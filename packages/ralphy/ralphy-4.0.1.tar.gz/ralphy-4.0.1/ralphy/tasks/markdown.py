"""Markdown PRD task source implementation."""

import os
import re
from typing import Optional

from ralphy.tasks.base import TaskSource


class MarkdownTaskSource(TaskSource):
    """Task source that reads from markdown PRD files with checkbox syntax."""

    # Pattern for incomplete tasks: - [ ] Task description
    INCOMPLETE_PATTERN = re.compile(r"^- \[ \] (.+)$", re.MULTILINE)
    # Pattern for completed tasks: - [x] Task description
    COMPLETED_PATTERN = re.compile(r"^- \[x\] (.+)$", re.MULTILINE | re.IGNORECASE)

    def __init__(self, file_path: str = "PRD.md"):
        """Initialize with path to PRD file."""
        self.file_path = file_path

    def _read_file(self) -> str:
        """Read the PRD file contents."""
        if not os.path.exists(self.file_path):
            return ""
        with open(self.file_path) as f:
            return f.read()

    def _write_file(self, content: str) -> None:
        """Write content to the PRD file."""
        with open(self.file_path, "w") as f:
            f.write(content)

    def get_next_task(self) -> Optional[str]:
        """Get the next incomplete task."""
        content = self._read_file()
        match = self.INCOMPLETE_PATTERN.search(content)
        if match:
            return match.group(1)
        return None

    def get_all_tasks(self) -> list[str]:
        """Get all incomplete tasks."""
        content = self._read_file()
        return self.INCOMPLETE_PATTERN.findall(content)

    def count_remaining(self) -> int:
        """Count remaining incomplete tasks."""
        content = self._read_file()
        return len(self.INCOMPLETE_PATTERN.findall(content))

    def count_completed(self) -> int:
        """Count completed tasks."""
        content = self._read_file()
        return len(self.COMPLETED_PATTERN.findall(content))

    def mark_complete(self, task: str) -> None:
        """Mark a task as complete by changing [ ] to [x]."""
        content = self._read_file()

        # Escape special regex characters in the task
        escaped_task = re.escape(task)

        # Replace the incomplete checkbox with completed
        pattern = re.compile(rf"^- \[ \] {escaped_task}$", re.MULTILINE)
        new_content = pattern.sub(f"- [x] {task}", content)

        self._write_file(new_content)

    def exists(self) -> bool:
        """Check if the PRD file exists."""
        return os.path.exists(self.file_path)
