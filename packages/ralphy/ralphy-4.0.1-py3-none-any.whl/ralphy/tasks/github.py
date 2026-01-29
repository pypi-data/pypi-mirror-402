"""GitHub issues task source implementation."""

import json
import subprocess
from typing import Optional

from ralphy.tasks.base import TaskSource
from ralphy.utils import command_exists


class GitHubTaskSource(TaskSource):
    """Task source that reads from GitHub issues."""

    def __init__(self, repo: str, label: Optional[str] = None):
        """
        Initialize with GitHub repository.

        Args:
            repo: Repository in 'owner/repo' format
            label: Optional label to filter issues
        """
        self.repo = repo
        self.label = label

    def _run_gh(self, *args: str) -> Optional[str]:
        """Run a gh CLI command and return output."""
        cmd = ["gh"] + list(args)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError:
            return None
        except FileNotFoundError:
            return None

    def _get_issues(self, state: str = "open") -> list[dict]:
        """Get issues from GitHub."""
        args = [
            "issue",
            "list",
            "--repo",
            self.repo,
            "--state",
            state,
            "--json",
            "number,title,body",
        ]
        if self.label:
            args.extend(["--label", self.label])

        output = self._run_gh(*args)
        if not output:
            return []

        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return []

    def get_next_task(self) -> Optional[str]:
        """Get the next open issue as a task."""
        issues = self._get_issues("open")
        if issues:
            issue = issues[0]
            return f"{issue['number']}:{issue['title']}"
        return None

    def get_all_tasks(self) -> list[str]:
        """Get all open issues as tasks."""
        issues = self._get_issues("open")
        return [f"{issue['number']}:{issue['title']}" for issue in issues]

    def count_remaining(self) -> int:
        """Count open issues."""
        return len(self._get_issues("open"))

    def count_completed(self) -> int:
        """Count closed issues."""
        return len(self._get_issues("closed"))

    def mark_complete(self, task: str) -> None:
        """Close a GitHub issue."""
        # Extract issue number from "number:title" format
        issue_num = task.split(":")[0]
        self._run_gh("issue", "close", issue_num, "--repo", self.repo)

    def get_issue_body(self, task: str) -> str:
        """Get the body/description of an issue."""
        issue_num = task.split(":")[0]
        output = self._run_gh(
            "issue",
            "view",
            issue_num,
            "--repo",
            self.repo,
            "--json",
            "body",
        )
        if output:
            try:
                data = json.loads(output)
                return data.get("body", "")
            except json.JSONDecodeError:
                pass
        return ""

    @staticmethod
    def check_available() -> bool:
        """Check if gh CLI is available."""
        return command_exists("gh")
