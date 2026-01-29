"""Progress monitoring and display for Ralphy."""

import sys
import threading
import time
from typing import Optional


class ProgressMonitor:
    """
    Monitors and displays progress during AI task execution.

    Shows a spinner with the current step and elapsed time.
    """

    SPINNER_CHARS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    # Step colors (ANSI)
    STEP_COLORS = {
        "Thinking": "\033[36m",  # cyan
        "Reading code": "\033[36m",  # cyan
        "Implementing": "\033[35m",  # magenta
        "Writing tests": "\033[35m",  # magenta
        "Testing": "\033[33m",  # yellow
        "Linting": "\033[33m",  # yellow
        "Staging": "\033[32m",  # green
        "Committing": "\033[32m",  # green
        "Logging": "\033[34m",  # blue
        "Updating PRD": "\033[34m",  # blue
    }
    RESET = "\033[0m"
    DIM = "\033[2m"

    def __init__(self, task: str, output_file: Optional[str] = None):
        """
        Initialize the progress monitor.

        Args:
            task: Task description to display
            output_file: Optional file to monitor for step detection
        """
        self.task = task[:40] if task else ""
        self.output_file = output_file
        self.current_step = "Thinking"
        self.start_time = time.time()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._spin_idx = 0

    def _detect_step(self) -> None:
        """Detect the current step from output file content."""
        if not self.output_file:
            return

        try:
            with open(self.output_file, "rb") as f:
                # Read last 5000 bytes
                f.seek(0, 2)  # Seek to end
                size = f.tell()
                f.seek(max(0, size - 5000))
                content = f.read().decode("utf-8", errors="ignore")

            # Detect step from content patterns
            if "git commit" in content or '"command":"git commit' in content:
                self.current_step = "Committing"
            elif "git add" in content or '"command":"git add' in content:
                self.current_step = "Staging"
            elif "progress.txt" in content:
                self.current_step = "Logging"
            elif "PRD.md" in content or "tasks.yaml" in content:
                self.current_step = "Updating PRD"
            elif any(
                kw in content
                for kw in ["lint", "eslint", "biome", "prettier", "ruff"]
            ):
                self.current_step = "Linting"
            elif any(
                kw in content
                for kw in [
                    "vitest",
                    "jest",
                    "bun test",
                    "npm test",
                    "pytest",
                    "go test",
                ]
            ):
                self.current_step = "Testing"
            elif any(
                kw in content
                for kw in [".test.", ".spec.", "__tests__", "_test.go"]
            ):
                self.current_step = "Writing tests"
            elif any(
                kw in content
                for kw in [
                    '"tool":"Write"',
                    '"tool":"Edit"',
                    '"name":"write"',
                    '"name":"edit"',
                ]
            ):
                self.current_step = "Implementing"
            elif any(
                kw in content
                for kw in [
                    '"tool":"Read"',
                    '"tool":"Glob"',
                    '"tool":"Grep"',
                    '"name":"read"',
                    '"name":"glob"',
                    '"name":"grep"',
                ]
            ):
                self.current_step = "Reading code"

        except (OSError, IOError):
            pass

    def _display_loop(self) -> None:
        """Main display loop running in a thread."""
        while self._running:
            self._detect_step()

            elapsed = int(time.time() - self.start_time)
            mins = elapsed // 60
            secs = elapsed % 60

            spinner_char = self.SPINNER_CHARS[self._spin_idx]
            self._spin_idx = (self._spin_idx + 1) % len(self.SPINNER_CHARS)

            step_color = self.STEP_COLORS.get(self.current_step, "\033[34m")  # blue default

            # Clear line and write status
            sys.stdout.write("\r\033[K")  # Clear line
            sys.stdout.write(
                f"  {spinner_char} {step_color}{self.current_step:<16}{self.RESET} │ "
                f"{self.task} {self.DIM}[{mins:02d}:{secs:02d}]{self.RESET}"
            )
            sys.stdout.flush()

            time.sleep(0.12)

    def start(self) -> None:
        """Start the progress monitor."""
        self._running = True
        self._thread = threading.Thread(target=self._display_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the progress monitor."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        # Clear the line
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()


class ParallelProgressMonitor:
    """
    Monitors progress for parallel task execution.

    Displays aggregate status of multiple agents.
    """

    SPINNER_CHARS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, batch_size: int):
        """
        Initialize the parallel progress monitor.

        Args:
            batch_size: Number of agents in the batch
        """
        self.batch_size = batch_size
        self.status_files: list[str] = []
        self.start_time = time.time()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._spin_idx = 0

    def set_status_files(self, status_files: list[str]) -> None:
        """Set the status files to monitor."""
        self.status_files = status_files

    def _read_statuses(self) -> tuple[int, int, int, int]:
        """Read all status files and return counts."""
        setting_up = 0
        running = 0
        done = 0
        failed = 0

        for status_file in self.status_files:
            try:
                with open(status_file) as f:
                    status = f.read().strip()

                if status == "setting up":
                    setting_up += 1
                elif status == "running":
                    running += 1
                elif status == "done":
                    done += 1
                elif status == "failed":
                    failed += 1
                else:
                    # Process might still be starting
                    setting_up += 1
            except (OSError, IOError):
                setting_up += 1

        return setting_up, running, done, failed

    def _display_loop(self) -> None:
        """Main display loop running in a thread."""
        while self._running:
            setting_up, running, done, failed = self._read_statuses()
            elapsed = int(time.time() - self.start_time)
            mins = elapsed // 60
            secs = elapsed % 60

            spinner_char = self.SPINNER_CHARS[self._spin_idx]
            self._spin_idx = (self._spin_idx + 1) % len(self.SPINNER_CHARS)

            # Clear line and write status
            sys.stdout.write("\r\033[K")
            sys.stdout.write(
                f"  \033[36m{spinner_char}\033[0m Agents: "
                f"\033[34m{setting_up} setup\033[0m | "
                f"\033[33m{running} running\033[0m | "
                f"\033[32m{done} done\033[0m | "
                f"\033[31m{failed} failed\033[0m | "
                f"{mins:02d}:{secs:02d} "
            )
            sys.stdout.flush()

            # Check if all done
            if done + failed == self.batch_size:
                break

            time.sleep(0.3)

    def start(self) -> None:
        """Start the progress monitor."""
        self._running = True
        self._thread = threading.Thread(target=self._display_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the progress monitor."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        # Clear the line
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    def wait_for_completion(self) -> None:
        """Wait for all agents to complete."""
        while self._running:
            _, running, done, failed = self._read_statuses()
            if done + failed == self.batch_size:
                self.stop()
                return
            time.sleep(0.5)
