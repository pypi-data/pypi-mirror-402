"""Base class for task sources."""

from abc import ABC, abstractmethod
from typing import Optional


class TaskSource(ABC):
    """Abstract base class for task sources (PRD files, GitHub issues, etc.)."""

    @abstractmethod
    def get_next_task(self) -> Optional[str]:
        """Get the next incomplete task."""
        pass

    @abstractmethod
    def get_all_tasks(self) -> list[str]:
        """Get all incomplete tasks."""
        pass

    @abstractmethod
    def count_remaining(self) -> int:
        """Count remaining incomplete tasks."""
        pass

    @abstractmethod
    def count_completed(self) -> int:
        """Count completed tasks."""
        pass

    @abstractmethod
    def mark_complete(self, task: str) -> None:
        """Mark a task as complete."""
        pass
