"""Command-line interface for Ralphy."""

import argparse
import os
import sys

from ralphy import __version__
from ralphy.config import (
    RALPHY_DIR,
    add_rule,
    ensure_ralphy_dir,
    init_config,
    show_config,
)
from ralphy.engines import get_engine
from ralphy.runner import Runner
from ralphy.tasks.github import GitHubTaskSource
from ralphy.tasks.markdown import MarkdownTaskSource
from ralphy.tasks.yaml import YamlTaskSource
from ralphy.utils import colors, command_exists, is_git_repo, log_error, log_info


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="ralphy",
        description="Ralphy - Autonomous AI Coding Loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Brownfield mode (single tasks in existing projects)
  ralphy --init                       # Initialize config
  ralphy "add dark mode toggle"       # Run single task
  ralphy "fix the login bug" --cursor # Single task with Cursor

  # PRD mode (task lists)
  ralphy                              # Run with Claude Code
  ralphy --codex                      # Run with Codex CLI
  ralphy --branch-per-task --create-pr  # Feature branch workflow
  ralphy --parallel --max-parallel 4  # Run 4 tasks concurrently
  ralphy --yaml tasks.yaml            # Use YAML task file
  ralphy --github owner/repo          # Fetch from GitHub issues

PRD Formats:
  Markdown (PRD.md):
    - [ ] Task description

  YAML (tasks.yaml):
    tasks:
      - title: Task description
        completed: false
        parallel_group: 1  # Optional: tasks with same group run in parallel

  GitHub Issues:
    Uses open issues from the specified repository
""",
    )

    # Config commands
    config_group = parser.add_argument_group("Config & Setup")
    config_group.add_argument(
        "--init",
        action="store_true",
        help="Initialize .ralphy/ with smart defaults",
    )
    config_group.add_argument(
        "--config",
        action="store_true",
        help="Show current configuration",
    )
    config_group.add_argument(
        "--add-rule",
        metavar="RULE",
        help='Add a rule to config (e.g., "Always use Zod")',
    )

    # Single task mode
    parser.add_argument(
        "task",
        nargs="?",
        help="Single task to run (brownfield mode)",
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Don't auto-commit after task completion",
    )

    # AI engine options
    engine_group = parser.add_argument_group("AI Engine Options")
    engine_group.add_argument(
        "--claude",
        action="store_const",
        const="claude",
        dest="engine",
        help="Use Claude Code (default)",
    )
    engine_group.add_argument(
        "--opencode",
        action="store_const",
        const="opencode",
        dest="engine",
        help="Use OpenCode",
    )
    engine_group.add_argument(
        "--cursor",
        "--agent",
        action="store_const",
        const="cursor",
        dest="engine",
        help="Use Cursor agent",
    )
    engine_group.add_argument(
        "--codex",
        action="store_const",
        const="codex",
        dest="engine",
        help="Use Codex CLI",
    )
    engine_group.add_argument(
        "--qwen",
        action="store_const",
        const="qwen",
        dest="engine",
        help="Use Qwen-Code",
    )
    engine_group.add_argument(
        "--droid",
        action="store_const",
        const="droid",
        dest="engine",
        help="Use Factory Droid",
    )

    # Workflow options
    workflow_group = parser.add_argument_group("Workflow Options")
    workflow_group.add_argument(
        "--no-tests",
        action="store_true",
        help="Skip writing and running tests",
    )
    workflow_group.add_argument(
        "--no-lint",
        action="store_true",
        help="Skip linting",
    )
    workflow_group.add_argument(
        "--fast",
        action="store_true",
        help="Skip both tests and linting",
    )

    # Execution options
    exec_group = parser.add_argument_group("Execution Options")
    exec_group.add_argument(
        "--max-iterations",
        type=int,
        default=0,
        metavar="N",
        help="Stop after N iterations (0 = unlimited)",
    )
    exec_group.add_argument(
        "--max-retries",
        type=int,
        default=3,
        metavar="N",
        help="Max retries per task on failure (default: 3)",
    )
    exec_group.add_argument(
        "--retry-delay",
        type=int,
        default=5,
        metavar="N",
        help="Seconds between retries (default: 5)",
    )
    exec_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )

    # Parallel execution
    parallel_group = parser.add_argument_group("Parallel Execution")
    parallel_group.add_argument(
        "--parallel",
        action="store_true",
        help="Run independent tasks in parallel",
    )
    parallel_group.add_argument(
        "--max-parallel",
        type=int,
        default=3,
        metavar="N",
        help="Max concurrent tasks (default: 3)",
    )

    # Git branch options
    git_group = parser.add_argument_group("Git Branch Options")
    git_group.add_argument(
        "--branch-per-task",
        action="store_true",
        help="Create a new git branch for each task",
    )
    git_group.add_argument(
        "--base-branch",
        metavar="NAME",
        help="Base branch to create task branches from (default: current)",
    )
    git_group.add_argument(
        "--create-pr",
        action="store_true",
        help="Create a pull request after each task (requires gh CLI)",
    )
    git_group.add_argument(
        "--draft-pr",
        action="store_true",
        help="Create PRs as drafts",
    )

    # PRD source options
    prd_group = parser.add_argument_group("PRD Source Options")
    prd_group.add_argument(
        "--prd",
        metavar="FILE",
        default="PRD.md",
        help="PRD file path (default: PRD.md)",
    )
    prd_group.add_argument(
        "--yaml",
        metavar="FILE",
        help="Use YAML task file instead of markdown",
    )
    prd_group.add_argument(
        "--github",
        metavar="REPO",
        help="Fetch tasks from GitHub issues (e.g., owner/repo)",
    )
    prd_group.add_argument(
        "--github-label",
        metavar="TAG",
        help="Filter GitHub issues by label",
    )

    # Other options
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show debug output",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Ralphy v{__version__}",
    )

    return parser


def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle --init
    if args.init:
        init_config()
        return

    # Handle --config
    if args.config:
        show_config()
        return

    # Handle --add-rule
    if args.add_rule:
        add_rule(args.add_rule)
        return

    # Handle --fast
    skip_tests = args.no_tests or args.fast
    skip_lint = args.no_lint or args.fast

    # Get engine
    engine_name = args.engine or "claude"
    engine = get_engine(engine_name)

    # Check engine availability
    if not engine.check_available():
        log_error(f"{engine.name} CLI not found.")
        log_info(engine.get_install_instructions())
        sys.exit(1)

    # Check git repo
    if not is_git_repo():
        log_error("Not a git repository. Ralphy requires a git repository.")
        sys.exit(1)

    # Single task mode (brownfield)
    if args.task:
        _run_single_task(args, engine, skip_tests, skip_lint)
        return

    # PRD mode
    _run_prd_mode(args, engine, skip_tests, skip_lint)


def _run_single_task(args, engine, skip_tests: bool, skip_lint: bool) -> None:
    """Run in single task (brownfield) mode."""
    # Show banner
    print(f"{colors.bold}{'=' * 44}{colors.reset}")
    print(f"{colors.bold}Ralphy{colors.reset} - Single Task Mode")
    print(f"Engine: {_get_engine_display(engine.name)}")

    if os.path.exists(RALPHY_DIR):
        print(f"Config: {colors.green}{RALPHY_DIR}/{colors.reset}")
    else:
        print(f"Config: {colors.dim}none (run --init to configure){colors.reset}")

    print(f"{colors.bold}{'=' * 44}{colors.reset}")

    runner = Runner(
        engine=engine,
        skip_tests=skip_tests,
        skip_lint=skip_lint,
        auto_commit=not args.no_commit,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    ensure_ralphy_dir()

    success = runner.run_single_task(args.task)
    sys.exit(0 if success else 1)


def _run_prd_mode(args, engine, skip_tests: bool, skip_lint: bool) -> None:
    """Run in PRD mode."""
    # Determine task source
    if args.github:
        if not command_exists("gh"):
            log_error("GitHub CLI (gh) is required. Install from https://cli.github.com/")
            sys.exit(1)
        task_source = GitHubTaskSource(args.github, args.github_label)
        source_type = "github"
        source_display = args.github
    elif args.yaml:
        task_source = YamlTaskSource(args.yaml)
        if not task_source.exists():
            log_error(f"{args.yaml} not found in current directory")
            log_info("Create a tasks.yaml file with tasks in YAML format")
            sys.exit(1)
        source_type = "yaml"
        source_display = args.yaml
    else:
        task_source = MarkdownTaskSource(args.prd)
        if not task_source.exists():
            log_error(f"{args.prd} not found in current directory")
            log_info("Create a PRD.md file with tasks marked as '- [ ] Task description'")
            sys.exit(1)
        source_type = "markdown"
        source_display = args.prd

    # Check for gh CLI if --create-pr is used
    if args.create_pr and not command_exists("gh"):
        log_error("GitHub CLI (gh) is required for --create-pr. Install from https://cli.github.com/")
        sys.exit(1)

    # Set max_iterations for dry-run if not specified
    max_iterations = args.max_iterations
    if args.dry_run and max_iterations == 0:
        max_iterations = 1

    # Show banner
    print(f"{colors.bold}{'=' * 44}{colors.reset}")
    print(f"{colors.bold}Ralphy{colors.reset} - Running until PRD is complete")
    print(f"Engine: {_get_engine_display(engine.name)}")
    print(f"Source: {colors.cyan}{source_type}{colors.reset} ({source_display})")

    if os.path.exists(RALPHY_DIR):
        print(f"Config: {colors.green}{RALPHY_DIR}/{colors.reset} (rules loaded)")

    # Show mode flags
    mode_parts = []
    if skip_tests:
        mode_parts.append("no-tests")
    if skip_lint:
        mode_parts.append("no-lint")
    if args.dry_run:
        mode_parts.append("dry-run")
    if args.parallel:
        mode_parts.append(f"parallel:{args.max_parallel}")
    if args.branch_per_task:
        mode_parts.append("branch-per-task")
    if args.create_pr:
        mode_parts.append("create-pr")
    if max_iterations > 0:
        mode_parts.append(f"max:{max_iterations}")

    if mode_parts:
        print(f"Mode: {colors.yellow}{' '.join(mode_parts)}{colors.reset}")

    print(f"{colors.bold}{'=' * 44}{colors.reset}")

    runner = Runner(
        engine=engine,
        task_source=task_source,
        skip_tests=skip_tests,
        skip_lint=skip_lint,
        auto_commit=True,
        dry_run=args.dry_run,
        max_iterations=max_iterations,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
        verbose=args.verbose,
        # Branch options
        branch_per_task=args.branch_per_task,
        base_branch=args.base_branch,
        create_pr=args.create_pr,
        draft_pr=args.draft_pr,
        # Parallel options
        parallel=args.parallel,
        max_parallel=args.max_parallel,
    )

    ensure_ralphy_dir()
    runner.run_prd_loop()


def _get_engine_display(name: str) -> str:
    """Get colored display name for an engine."""
    displays = {
        "claude": f"{colors.magenta}Claude Code{colors.reset}",
        "opencode": f"{colors.cyan}OpenCode{colors.reset}",
        "cursor": f"{colors.yellow}Cursor Agent{colors.reset}",
        "codex": f"{colors.blue}Codex{colors.reset}",
        "qwen": f"{colors.green}Qwen-Code{colors.reset}",
        "droid": f"{colors.magenta}Factory Droid{colors.reset}",
    }
    return displays.get(name, name)


if __name__ == "__main__":
    main()
