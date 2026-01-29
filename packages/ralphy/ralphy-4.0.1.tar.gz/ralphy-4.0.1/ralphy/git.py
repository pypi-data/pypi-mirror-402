"""Git utilities for branch management and PR creation."""

import subprocess
from typing import Optional

from ralphy.utils import command_exists, log_debug, log_info, log_warn, slugify


class GitManager:
    """Manages git operations for Ralphy."""

    def __init__(
        self,
        base_branch: Optional[str] = None,
        create_pr: bool = False,
        draft_pr: bool = False,
        verbose: bool = False,
    ):
        """
        Initialize the git manager.

        Args:
            base_branch: Branch to create task branches from (defaults to current)
            create_pr: Whether to create PRs after tasks
            draft_pr: Create PRs as drafts
            verbose: Enable verbose logging
        """
        self.base_branch = base_branch or self.get_current_branch()
        self.create_pr = create_pr
        self.draft_pr = draft_pr
        self.verbose = verbose
        self.task_branches: list[str] = []

    @staticmethod
    def run_git(*args: str, check: bool = False) -> subprocess.CompletedProcess:
        """Run a git command."""
        cmd = ["git"] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True, check=check)

    @staticmethod
    def get_current_branch() -> str:
        """Get the current git branch name."""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return "main"

    def create_task_branch(self, task: str) -> str:
        """
        Create a new branch for a task.

        Args:
            task: Task description to use for branch name

        Returns:
            The created branch name
        """
        branch_name = f"ralphy/{slugify(task)}"
        log_debug(
            f"Creating branch: {branch_name} from {self.base_branch}",
            verbose=self.verbose,
        )

        # Stash any changes
        stash_result = self.run_git("stash", "list")
        stash_before = stash_result.stdout.split("\n")[0] if stash_result.stdout else ""

        self.run_git("stash", "push", "-m", "ralphy-autostash")

        stash_result = self.run_git("stash", "list")
        stash_after = stash_result.stdout.split("\n")[0] if stash_result.stdout else ""
        stashed = stash_after != stash_before and "ralphy-autostash" in stash_after

        # Checkout base branch and pull latest
        self.run_git("checkout", self.base_branch)
        self.run_git("pull", "origin", self.base_branch)

        # Create or checkout the branch
        result = self.run_git("checkout", "-b", branch_name)
        if result.returncode != 0:
            # Branch might already exist
            self.run_git("checkout", branch_name)

        # Pop stash if we stashed
        if stashed:
            self.run_git("stash", "pop")

        self.task_branches.append(branch_name)
        return branch_name

    def create_pull_request(
        self, branch: str, task: str, body: str = "Automated PR created by Ralphy"
    ) -> Optional[str]:
        """
        Create a pull request for a branch.

        Args:
            branch: Branch name
            task: Task description for PR title
            body: PR body text

        Returns:
            PR URL if successful, None otherwise
        """
        if not command_exists("gh"):
            log_warn("GitHub CLI (gh) not available, skipping PR creation")
            return None

        log_info(f"Creating pull request for {branch}...")

        # Push branch
        result = self.run_git("push", "-u", "origin", branch)
        if result.returncode != 0:
            log_warn(f"Failed to push branch {branch}")
            return None

        # Create PR
        cmd = [
            "gh",
            "pr",
            "create",
            "--base",
            self.base_branch,
            "--head",
            branch,
            "--title",
            task,
            "--body",
            body,
        ]
        if self.draft_pr:
            cmd.append("--draft")

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            log_warn(f"Failed to create PR for {branch}")
            return None

        pr_url = result.stdout.strip()
        log_info(f"PR created: {pr_url}")
        return pr_url

    def return_to_base_branch(self) -> None:
        """Return to the base branch."""
        self.run_git("checkout", self.base_branch)

    def merge_branch(self, branch: str, delete_after: bool = True) -> bool:
        """
        Merge a branch into the current branch.

        Args:
            branch: Branch to merge
            delete_after: Delete branch after successful merge

        Returns:
            True if merge succeeded, False otherwise
        """
        result = self.run_git("merge", "--no-edit", branch)
        if result.returncode != 0:
            return False

        if delete_after:
            self.run_git("branch", "-d", branch)

        return True

    def abort_merge(self) -> None:
        """Abort current merge."""
        self.run_git("merge", "--abort")

    def get_conflicted_files(self) -> list[str]:
        """Get list of files with merge conflicts."""
        result = self.run_git("diff", "--name-only", "--diff-filter=U")
        if result.returncode == 0 and result.stdout:
            return [f for f in result.stdout.strip().split("\n") if f]
        return []

    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        result = self.run_git("status", "--porcelain")
        return bool(result.stdout.strip())


class WorktreeManager:
    """Manages git worktrees for parallel execution."""

    def __init__(self, base_dir: str, base_branch: str, verbose: bool = False):
        """
        Initialize the worktree manager.

        Args:
            base_dir: Base directory for worktrees
            base_branch: Base branch to create worktrees from
            verbose: Enable verbose logging
        """
        self.base_dir = base_dir
        self.base_branch = base_branch
        self.verbose = verbose
        self.worktrees: list[tuple[str, str]] = []  # (dir, branch) pairs

    def create_worktree(self, task: str, agent_num: int) -> tuple[str, str]:
        """
        Create an isolated worktree for a parallel agent.

        Args:
            task: Task description
            agent_num: Agent number for unique naming

        Returns:
            Tuple of (worktree_dir, branch_name)
        """
        import os

        branch_name = f"ralphy/agent-{agent_num}-{slugify(task)}"
        worktree_dir = os.path.join(self.base_dir, f"agent-{agent_num}")

        log_debug(f"Creating worktree: {worktree_dir}", verbose=self.verbose)

        # Prune stale worktrees
        GitManager.run_git("worktree", "prune")

        # Delete branch if exists
        GitManager.run_git("branch", "-D", branch_name)

        # Create branch from base
        result = GitManager.run_git("branch", branch_name, self.base_branch)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create branch {branch_name}")

        # Remove existing worktree dir if any
        if os.path.exists(worktree_dir):
            import shutil

            shutil.rmtree(worktree_dir)

        # Create worktree
        result = GitManager.run_git("worktree", "add", worktree_dir, branch_name)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create worktree at {worktree_dir}")

        self.worktrees.append((worktree_dir, branch_name))
        return worktree_dir, branch_name

    def cleanup_worktree(self, worktree_dir: str, branch_name: str) -> bool:
        """
        Clean up a worktree.

        Args:
            worktree_dir: Worktree directory
            branch_name: Branch name

        Returns:
            True if cleanup succeeded
        """
        import os

        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "-C", worktree_dir, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout.strip():
            log_warn(f"Worktree has uncommitted changes: {worktree_dir}")
            return False

        # Remove worktree
        GitManager.run_git("worktree", "remove", "-f", worktree_dir)

        return True

    def cleanup_all(self) -> None:
        """Clean up all worktrees."""
        import os
        import shutil

        for worktree_dir, branch_name in self.worktrees:
            if os.path.exists(worktree_dir):
                self.cleanup_worktree(worktree_dir, branch_name)

        # Remove base directory if empty
        if os.path.exists(self.base_dir):
            try:
                if not os.listdir(self.base_dir):
                    shutil.rmtree(self.base_dir)
            except OSError:
                pass
