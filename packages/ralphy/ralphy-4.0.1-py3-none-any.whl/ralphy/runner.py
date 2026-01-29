"""Main runner for Ralphy."""

import os
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional

from ralphy.config import (
    PROGRESS_FILE,
    RALPHY_DIR,
    build_prompt,
    load_config,
    log_task_history,
)
from ralphy.engines import AIEngine, AIResult, get_engine
from ralphy.engines.claude import ClaudeEngine
from ralphy.git import GitManager, WorktreeManager
from ralphy.progress import ParallelProgressMonitor, ProgressMonitor
from ralphy.tasks.base import TaskSource
from ralphy.tasks.markdown import MarkdownTaskSource
from ralphy.utils import (
    calculate_cost,
    colors,
    is_git_repo,
    log_debug,
    log_error,
    log_info,
    log_success,
    log_warn,
    notify_done,
)


class Runner:
    """Main runner for executing tasks."""

    def __init__(
        self,
        engine: Optional[AIEngine] = None,
        task_source: Optional[TaskSource] = None,
        skip_tests: bool = False,
        skip_lint: bool = False,
        auto_commit: bool = True,
        dry_run: bool = False,
        max_iterations: int = 0,
        max_retries: int = 3,
        retry_delay: int = 5,
        verbose: bool = False,
        # Branch options
        branch_per_task: bool = False,
        base_branch: Optional[str] = None,
        create_pr: bool = False,
        draft_pr: bool = False,
        # Parallel options
        parallel: bool = False,
        max_parallel: int = 3,
    ):
        """Initialize the runner."""
        self.engine = engine or ClaudeEngine()
        self.task_source = task_source
        self.skip_tests = skip_tests
        self.skip_lint = skip_lint
        self.auto_commit = auto_commit
        self.dry_run = dry_run
        self.max_iterations = max_iterations
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.verbose = verbose

        # Branch options
        self.branch_per_task = branch_per_task
        self.create_pr = create_pr
        self.draft_pr = draft_pr
        self.git_manager: Optional[GitManager] = None
        if branch_per_task or create_pr:
            self.git_manager = GitManager(
                base_branch=base_branch,
                create_pr=create_pr,
                draft_pr=draft_pr,
                verbose=verbose,
            )

        # Parallel options
        self.parallel = parallel
        self.max_parallel = max_parallel

        # Stats
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_duration_ms = 0
        self.total_actual_cost = 0.0
        self.iteration = 0
        self.task_branches: list[str] = []

    def check_requirements(self) -> bool:
        """Check that all requirements are met."""
        # Check AI engine
        if not self.engine.check_available():
            log_error(f"{self.engine.name} CLI not found.")
            log_info(self.engine.get_install_instructions())
            return False

        # Check git
        if not is_git_repo():
            log_error(
                "Not a git repository. Ralphy requires a git repository to track changes."
            )
            return False

        return True

    def run_single_task(self, task: str) -> bool:
        """Run a single brownfield task."""
        print()
        print(f"{colors.bold}{'━' * 64}{colors.reset}")
        print(f"{colors.bold}Task:{colors.reset} {task}")
        print(f"{colors.bold}{'━' * 64}{colors.reset}")
        print()

        prompt = build_prompt(task, auto_commit=self.auto_commit)

        if self.dry_run:
            log_info("DRY RUN - Would execute:")
            print(f"{colors.dim}{prompt}{colors.reset}")
            return True

        log_info(f"Running with {self.engine.name}...")

        # Run the AI engine
        if hasattr(self.engine, "run_simple"):
            result = self.engine.run_simple(prompt)
        else:
            result = self.engine.run(prompt, verbose=self.verbose)

        # Update stats
        self.total_input_tokens += result.input_tokens
        self.total_output_tokens += result.output_tokens

        # Log to history
        if result.error:
            log_task_history(task, "failed")
            log_error(f"Task failed: {result.error}")
            return False
        else:
            log_task_history(task, "completed")
            log_success("Task completed")
            return True

    def run_prd_iteration(self) -> int:
        """
        Run a single PRD iteration.

        Returns:
            0 = success, continue
            1 = error, continue to next task
            2 = all tasks complete
        """
        self.iteration += 1

        print()
        print(f"{colors.bold}>>> Task {self.iteration}{colors.reset}")

        remaining = self.task_source.count_remaining()
        completed = self.task_source.count_completed()
        print(
            f"{colors.dim}    Completed: {completed} | Remaining: {remaining}{colors.reset}"
        )
        print("-" * 44)

        # Get current task
        current_task = self.task_source.get_next_task()
        if not current_task:
            log_info("No more tasks found")
            return 2

        # Create branch if needed
        branch_name = None
        if self.branch_per_task and self.git_manager:
            branch_name = self.git_manager.create_task_branch(current_task)
            self.task_branches.append(branch_name)
            log_info(f"Working on branch: {branch_name}")

        if self.dry_run:
            prompt = self._build_prd_prompt(current_task)
            log_info("DRY RUN - Would execute:")
            print(f"{colors.dim}{prompt}{colors.reset}")
            if self.git_manager:
                self.git_manager.return_to_base_branch()
            return 0

        # Run with retry logic
        retry_count = 0
        while retry_count < self.max_retries:
            # Create temp file for output
            tmpfile = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
            tmpfile.close()

            # Start progress monitor
            monitor = ProgressMonitor(current_task, tmpfile.name)
            monitor.start()

            try:
                result = self._run_prd_task(current_task)
            finally:
                monitor.stop()
                os.unlink(tmpfile.name)

            if result.error:
                retry_count += 1
                log_error(
                    f"Error: {result.error} (attempt {retry_count}/{self.max_retries})"
                )
                if retry_count < self.max_retries:
                    log_info(f"Retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                if self.git_manager:
                    self.git_manager.return_to_base_branch()
                return 1

            # Success
            self.total_input_tokens += result.input_tokens
            self.total_output_tokens += result.output_tokens
            if result.duration_ms:
                self.total_duration_ms += result.duration_ms
            if result.actual_cost:
                self.total_actual_cost += result.actual_cost

            print(f"  {colors.green}✓{colors.reset} Done")

            if result.response:
                print()
                print(result.response)

            # Create PR if requested
            if self.create_pr and branch_name and self.git_manager:
                self.git_manager.create_pull_request(
                    branch_name, current_task, "Automated implementation by Ralphy"
                )

            # Return to base branch
            if self.git_manager:
                self.git_manager.return_to_base_branch()

            # Check for completion
            remaining = self.task_source.count_remaining()
            if remaining == 0:
                return 2

            return 0

        if self.git_manager:
            self.git_manager.return_to_base_branch()
        return 1

    def _build_prd_prompt(self, task: str) -> str:
        """Build the prompt for PRD mode."""
        config = load_config()
        prompt_parts = []

        # Add file references
        if self.task_source and hasattr(self.task_source, "file_path"):
            prompt_parts.append(f"@{self.task_source.file_path} @{PROGRESS_FILE}")
        else:
            prompt_parts.append(f"@PRD.md @{PROGRESS_FILE}")

        # Add project context and rules from config
        if config:
            if config.rules:
                prompt_parts.append(
                    "## Rules (you MUST follow these)\n" + "\n".join(config.rules)
                )
            if config.boundaries.never_touch:
                prompt_parts.append(
                    "## Boundaries - Do NOT modify these files:\n"
                    + "\n".join(config.boundaries.never_touch)
                )

        # Build instructions
        instructions = ["1. Find the highest-priority incomplete task and implement it."]
        step = 2

        if not self.skip_tests:
            instructions.append(f"{step}. Write tests for the feature.")
            instructions.append(
                f"{step + 1}. Run tests and ensure they pass before proceeding."
            )
            step += 2

        if not self.skip_lint:
            instructions.append(
                f"{step}. Run linting and ensure it passes before proceeding."
            )
            step += 1

        instructions.append(
            f"{step}. Update the PRD to mark the task as complete (change '- [ ]' to '- [x]')."
        )
        step += 1

        instructions.append(f"{step}. Append your progress to {PROGRESS_FILE}.")
        instructions.append(f"{step + 1}. Commit your changes with a descriptive message.")
        instructions.append("ONLY WORK ON A SINGLE TASK.")

        if not self.skip_tests:
            instructions.append("Do not proceed if tests fail.")
        if not self.skip_lint:
            instructions.append("Do not proceed if linting fails.")

        instructions.append(
            "If ALL tasks in the PRD are complete, output <promise>COMPLETE</promise>."
        )

        prompt_parts.append("\n".join(instructions))

        return "\n".join(prompt_parts)

    def _run_prd_task(self, task: str) -> AIResult:
        """Run a single PRD task."""
        prompt = self._build_prd_prompt(task)
        return self.engine.run(prompt, verbose=self.verbose)

    def run_prd_loop(self) -> None:
        """Run the main PRD loop until all tasks are complete."""
        if self.parallel:
            self.run_parallel_tasks()
            self.show_summary()
            notify_done()
            return

        while True:
            result_code = self.run_prd_iteration()

            if result_code == 2:
                # All tasks complete
                self.show_summary()
                notify_done()
                return

            if result_code == 1:
                # Error, but continue
                log_warn(f"Task failed after {self.max_retries} attempts, continuing...")

            # Check max iterations
            if self.max_iterations > 0 and self.iteration >= self.max_iterations:
                log_warn(f"Reached max iterations ({self.max_iterations})")
                self.show_summary()
                notify_done(f"Ralphy stopped after {self.max_iterations} iterations")
                return

            # Small delay between iterations
            time.sleep(1)

    def run_parallel_tasks(self) -> None:
        """Run tasks in parallel using worktrees."""
        log_info(
            f"Running {colors.bold}{self.max_parallel} parallel agents{colors.reset} "
            "(each in isolated worktree)..."
        )

        # Get all pending tasks
        all_tasks = self.task_source.get_all_tasks()
        if not all_tasks:
            log_info("No tasks to run")
            return

        total_tasks = len(all_tasks)
        log_info(f"Found {total_tasks} tasks to process")

        # Set up worktree base directory
        worktree_base = tempfile.mkdtemp()
        base_branch = (
            self.git_manager.base_branch
            if self.git_manager
            else GitManager.get_current_branch()
        )

        log_debug(f"Worktree base: {worktree_base}", verbose=self.verbose)
        log_info(f"Base branch: {base_branch}")

        completed_branches: list[str] = []
        batch_num = 0
        batch_start = 0

        try:
            while batch_start < total_tasks:
                batch_num += 1
                batch_end = min(batch_start + self.max_parallel, total_tasks)
                batch_size = batch_end - batch_start
                batch_tasks = all_tasks[batch_start:batch_end]

                print()
                print(f"{colors.bold}{'━' * 64}{colors.reset}")
                print(
                    f"{colors.bold}Batch {batch_num}: Spawning {batch_size} parallel agents{colors.reset}"
                )
                print(
                    f"{colors.dim}Each agent runs in its own git worktree with isolated workspace{colors.reset}"
                )
                print(f"{colors.bold}{'━' * 64}{colors.reset}")
                print()

                # Run agents in parallel
                results = self._run_parallel_batch(
                    batch_tasks, worktree_base, base_branch, batch_num
                )

                # Process results
                print()
                print(f"{colors.bold}Batch {batch_num} Results:{colors.reset}")
                for i, (task, result) in enumerate(zip(batch_tasks, results)):
                    agent_num = self.iteration + i + 1

                    if result.get("success"):
                        icon = "✓"
                        color = colors.green
                        branch = result.get("branch")
                        if branch:
                            completed_branches.append(branch)
                            branch_info = f" → {colors.cyan}{branch}{colors.reset}"
                        else:
                            branch_info = ""

                        # Mark task complete
                        self.task_source.mark_complete(task)

                        # Update token counts
                        self.total_input_tokens += result.get("input_tokens", 0)
                        self.total_output_tokens += result.get("output_tokens", 0)
                    else:
                        icon = "✗"
                        color = colors.red
                        branch_info = ""
                        error = result.get("error", "Unknown error")
                        if error:
                            branch_info = f" {colors.dim}({error}){colors.reset}"

                    print(
                        f"  {color}{icon}{colors.reset} Agent {agent_num}: "
                        f"{task[:45]}{branch_info}"
                    )

                self.iteration += batch_size
                batch_start = batch_end

                # Check max iterations
                if self.max_iterations > 0 and self.iteration >= self.max_iterations:
                    log_warn(f"Reached max iterations ({self.max_iterations})")
                    break

        finally:
            # Cleanup worktree base
            if os.path.exists(worktree_base):
                try:
                    shutil.rmtree(worktree_base)
                except OSError:
                    pass

        # Merge completed branches
        if completed_branches and not self.create_pr:
            self._merge_parallel_branches(completed_branches, base_branch)
        elif completed_branches:
            print()
            print(f"{colors.bold}Branches created by agents:{colors.reset}")
            for branch in completed_branches:
                print(f"  {colors.cyan}•{colors.reset} {branch}")

    def _run_parallel_batch(
        self,
        tasks: list[str],
        worktree_base: str,
        base_branch: str,
        batch_num: int,
    ) -> list[dict]:
        """
        Run a batch of tasks in parallel.

        Returns list of result dicts with keys: success, branch, input_tokens, output_tokens, error
        """
        results = []
        status_files = []
        processes = []

        # Start all agents
        for i, task in enumerate(tasks):
            agent_num = self.iteration + i + 1
            print(f"  {colors.cyan}◉{colors.reset} Agent {agent_num}: {task[:50]}")

            status_file = tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".status"
            )
            status_file.write("waiting")
            status_file.close()
            status_files.append(status_file.name)

            # Start agent process
            result = self._start_parallel_agent(
                task, agent_num, worktree_base, base_branch, status_file.name
            )
            processes.append(result)

        print()

        # Monitor progress
        monitor = ParallelProgressMonitor(len(tasks))
        monitor.set_status_files(status_files)
        monitor.start()

        # Wait for all processes
        final_results = []
        for i, (proc, output_file, log_file, branch_name) in enumerate(processes):
            try:
                proc.wait()

                # Read result
                success = False
                input_tokens = 0
                output_tokens = 0
                error = None

                if proc.returncode == 0:
                    # Check if commits were made
                    worktree_dir = os.path.join(worktree_base, f"agent-{self.iteration + i + 1}")
                    if os.path.exists(worktree_dir):
                        commit_count = subprocess.run(
                            ["git", "-C", worktree_dir, "rev-list", "--count", f"{base_branch}..HEAD"],
                            capture_output=True,
                            text=True,
                        )
                        if commit_count.returncode == 0 and int(commit_count.stdout.strip() or "0") > 0:
                            success = True
                        else:
                            error = "No commits created"

                    # Update status file
                    with open(status_files[i], "w") as f:
                        f.write("done" if success else "failed")

                    # Create PR if requested
                    if success and self.create_pr:
                        subprocess.run(
                            ["git", "-C", worktree_dir, "push", "-u", "origin", branch_name],
                            capture_output=True,
                        )
                        subprocess.run(
                            [
                                "gh", "pr", "create",
                                "--base", base_branch,
                                "--head", branch_name,
                                "--title", tasks[i],
                                "--body", f"Automated implementation by Ralphy (Agent {self.iteration + i + 1})",
                            ] + (["--draft"] if self.draft_pr else []),
                            capture_output=True,
                        )
                else:
                    error = "Process failed"
                    with open(status_files[i], "w") as f:
                        f.write("failed")

                final_results.append({
                    "success": success,
                    "branch": branch_name if success else None,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "error": error,
                })

            finally:
                # Cleanup temp files
                for temp_file in [output_file, log_file, status_files[i]]:
                    try:
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)
                    except OSError:
                        pass

        monitor.stop()

        # Cleanup worktrees
        for i in range(len(tasks)):
            agent_num = self.iteration + i + 1
            worktree_dir = os.path.join(worktree_base, f"agent-{agent_num}")
            if os.path.exists(worktree_dir):
                subprocess.run(
                    ["git", "worktree", "remove", "-f", worktree_dir],
                    capture_output=True,
                )

        return final_results

    def _start_parallel_agent(
        self,
        task: str,
        agent_num: int,
        worktree_base: str,
        base_branch: str,
        status_file: str,
    ) -> tuple:
        """Start a parallel agent in its own worktree."""
        from ralphy.utils import slugify

        branch_name = f"ralphy/agent-{agent_num}-{slugify(task)}"
        worktree_dir = os.path.join(worktree_base, f"agent-{agent_num}")

        # Create output files
        output_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".out"
        ).name
        log_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".log"
        ).name

        # Update status
        with open(status_file, "w") as f:
            f.write("setting up")

        # Prune stale worktrees
        subprocess.run(["git", "worktree", "prune"], capture_output=True)

        # Delete branch if exists
        subprocess.run(["git", "branch", "-D", branch_name], capture_output=True)

        # Create branch from base
        subprocess.run(["git", "branch", branch_name, base_branch], capture_output=True)

        # Remove existing worktree dir if any
        if os.path.exists(worktree_dir):
            shutil.rmtree(worktree_dir)

        # Create worktree
        subprocess.run(
            ["git", "worktree", "add", worktree_dir, branch_name], capture_output=True
        )

        # Copy PRD file to worktree
        if self.task_source and hasattr(self.task_source, "file_path"):
            if os.path.exists(self.task_source.file_path):
                shutil.copy(self.task_source.file_path, worktree_dir)

        # Ensure .ralphy/ exists in worktree
        ralphy_dir = os.path.join(worktree_dir, RALPHY_DIR)
        os.makedirs(ralphy_dir, exist_ok=True)
        progress_file = os.path.join(worktree_dir, PROGRESS_FILE)
        if not os.path.exists(progress_file):
            with open(progress_file, "w") as f:
                f.write("# Ralphy Progress Log\n\n")

        # Build prompt
        prompt = f"""You are working on a specific task. Focus ONLY on this task:

TASK: {task}

Instructions:
1. Implement this specific task completely
2. Write tests if appropriate
3. Update {PROGRESS_FILE} with what you did
4. Commit your changes with a descriptive message

Do NOT modify PRD.md or mark tasks complete - that will be handled separately.
Focus only on implementing: {task}"""

        # Update status
        with open(status_file, "w") as f:
            f.write("running")

        # Build command based on engine
        if self.engine.name == "claude":
            cmd = [
                "claude",
                "--dangerously-skip-permissions",
                "--verbose",
                "-p",
                prompt,
                "--output-format",
                "stream-json",
            ]
        elif self.engine.name == "opencode":
            cmd = ["opencode", "run", "--format", "json", prompt]
        elif self.engine.name == "cursor":
            cmd = ["agent", "--print", "--force", "--output-format", "stream-json", prompt]
        elif self.engine.name == "qwen":
            cmd = ["qwen", "--output-format", "stream-json", "--approval-mode", "yolo", "-p", prompt]
        elif self.engine.name == "droid":
            cmd = ["droid", "exec", "--output-format", "stream-json", "--auto", "medium", prompt]
        elif self.engine.name == "codex":
            cmd = ["codex", "exec", "--full-auto", "--json", prompt]
        else:
            cmd = ["claude", "--dangerously-skip-permissions", "-p", prompt]

        # Start process
        with open(output_file, "w") as out, open(log_file, "w") as log:
            env = os.environ.copy()
            if self.engine.name == "opencode":
                env["OPENCODE_PERMISSION"] = '{"*":"allow"}'

            proc = subprocess.Popen(
                cmd,
                cwd=worktree_dir,
                stdout=out,
                stderr=log,
                env=env,
            )

        return proc, output_file, log_file, branch_name

    def _merge_parallel_branches(
        self, branches: list[str], base_branch: str
    ) -> None:
        """Merge parallel branches into base branch."""
        print()
        print(f"{colors.bold}{'━' * 64}{colors.reset}")
        print(f"{colors.bold}Merging agent branches into {base_branch}...{colors.reset}")
        print()

        # Checkout base branch
        result = subprocess.run(
            ["git", "checkout", base_branch], capture_output=True, text=True
        )
        if result.returncode != 0:
            log_warn(f"Could not checkout {base_branch}; leaving branches unmerged.")
            print(f"{colors.bold}Branches created by agents:{colors.reset}")
            for branch in branches:
                print(f"  {colors.cyan}•{colors.reset} {branch}")
            return

        merge_failed = []
        for branch in branches:
            print(f"  Merging {colors.cyan}{branch}{colors.reset}...", end="")

            result = subprocess.run(
                ["git", "merge", "--no-edit", branch], capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f" {colors.green}✓{colors.reset}")
                # Delete branch after successful merge
                subprocess.run(["git", "branch", "-d", branch], capture_output=True)
            else:
                print(f" {colors.yellow}conflict{colors.reset}")
                merge_failed.append(branch)
                subprocess.run(["git", "merge", "--abort"], capture_output=True)

        if merge_failed:
            print()
            print(
                f"{colors.yellow}Some conflicts could not be resolved automatically:{colors.reset}"
            )
            for branch in merge_failed:
                print(f"  {colors.yellow}•{colors.reset} {branch}")
            print()
            print(f"{colors.dim}Resolve conflicts manually: git merge <branch>{colors.reset}")
        else:
            print()
            print(f"{colors.green}All branches merged successfully!{colors.reset}")

    def show_summary(self) -> None:
        """Show the final summary."""
        print()
        print(f"{colors.bold}{'=' * 44}{colors.reset}")
        print(
            f"{colors.green}PRD complete!{colors.reset} Finished {self.iteration} task(s)."
        )
        print(f"{colors.bold}{'=' * 44}{colors.reset}")
        print()
        print(f"{colors.bold}>>> Cost Summary{colors.reset}")

        # Some engines don't provide token usage
        if self.engine.name in ("cursor", "droid"):
            print(
                f"{colors.dim}Token usage not available (CLI doesn't expose this data){colors.reset}"
            )
            if self.total_duration_ms > 0:
                dur_sec = self.total_duration_ms // 1000
                dur_min = dur_sec // 60
                dur_sec_rem = dur_sec % 60
                if dur_min > 0:
                    print(f"Total API time: {dur_min}m {dur_sec_rem}s")
                else:
                    print(f"Total API time: {dur_sec}s")
        else:
            print(f"Input tokens:  {self.total_input_tokens}")
            print(f"Output tokens: {self.total_output_tokens}")
            print(
                f"Total tokens:  {self.total_input_tokens + self.total_output_tokens}"
            )

            # Show actual cost if available (OpenCode provides this)
            if self.total_actual_cost > 0:
                print(f"Actual cost:   ${self.total_actual_cost:.6f}")
            else:
                cost = calculate_cost(
                    self.total_input_tokens, self.total_output_tokens
                )
                print(f"Est. cost:     ${cost}")

        # Show branches if created
        if self.task_branches:
            print()
            print(f"{colors.bold}>>> Branches Created{colors.reset}")
            for branch in self.task_branches:
                print(f"  - {branch}")

        print(f"{colors.bold}{'=' * 44}{colors.reset}")
