"""Utility functions for logging, colors, and notifications."""

import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class Colors:
    """Terminal color codes."""

    red: str = ""
    green: str = ""
    yellow: str = ""
    blue: str = ""
    magenta: str = ""
    cyan: str = ""
    bold: str = ""
    dim: str = ""
    reset: str = ""

    @classmethod
    def detect(cls) -> "Colors":
        """Detect if terminal supports colors and return appropriate instance."""
        if not sys.stdout.isatty():
            return cls()

        # Check for color support
        term = os.environ.get("TERM", "")
        if "color" in term or "xterm" in term or "256" in term:
            return cls(
                red="\033[31m",
                green="\033[32m",
                yellow="\033[33m",
                blue="\033[34m",
                magenta="\033[35m",
                cyan="\033[36m",
                bold="\033[1m",
                dim="\033[2m",
                reset="\033[0m",
            )

        return cls()


# Global colors instance
colors = Colors.detect()


def log_info(message: str) -> None:
    """Log an info message."""
    print(f"{colors.blue}[INFO]{colors.reset} {message}")


def log_success(message: str) -> None:
    """Log a success message."""
    print(f"{colors.green}[OK]{colors.reset} {message}")


def log_warn(message: str) -> None:
    """Log a warning message."""
    print(f"{colors.yellow}[WARN]{colors.reset} {message}")


def log_error(message: str) -> None:
    """Log an error message to stderr."""
    print(f"{colors.red}[ERROR]{colors.reset} {message}", file=sys.stderr)


def log_debug(message: str, verbose: bool = False) -> None:
    """Log a debug message if verbose mode is enabled."""
    if verbose:
        print(f"{colors.dim}[DEBUG] {message}{colors.reset}")


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to a slug suitable for branch names."""
    import re

    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:max_length]


def command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(cmd) is not None


def notify_done(message: str = "Ralphy has completed all tasks!") -> None:
    """Send a notification when tasks are done."""
    system = platform.system()

    if system == "Darwin":  # macOS
        # Play sound
        try:
            subprocess.run(
                ["afplay", "/System/Library/Sounds/Glass.aiff"],
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            pass

        # Show notification
        try:
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'display notification "{message}" with title "Ralphy"',
                ],
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            pass

    elif system == "Linux":
        # Try notify-send
        try:
            subprocess.run(
                ["notify-send", "Ralphy", message],
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            pass

        # Try paplay for sound
        try:
            subprocess.run(
                ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            pass


def notify_error(message: str = "Ralphy encountered an error") -> None:
    """Send an error notification."""
    system = platform.system()

    if system == "Darwin":
        try:
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'display notification "{message}" with title "Ralphy - Error"',
                ],
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            pass

    elif system == "Linux":
        try:
            subprocess.run(
                ["notify-send", "-u", "critical", "Ralphy - Error", message],
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            pass


def calculate_cost(input_tokens: int, output_tokens: int) -> Optional[str]:
    """Calculate estimated cost based on token usage."""
    # Claude pricing: $3/M input, $15/M output
    cost = (input_tokens * 0.000003) + (output_tokens * 0.000015)
    return f"{cost:.4f}"


def is_git_repo() -> bool:
    """Check if current directory is a git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


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
