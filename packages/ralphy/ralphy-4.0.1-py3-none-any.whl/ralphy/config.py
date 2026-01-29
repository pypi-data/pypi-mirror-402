"""Configuration management for Ralphy."""

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ralphy.utils import colors, log_error, log_info, log_success, log_warn

RALPHY_DIR = ".ralphy"
CONFIG_FILE = f"{RALPHY_DIR}/config.yaml"
PROGRESS_FILE = f"{RALPHY_DIR}/progress.txt"


@dataclass
class ProjectConfig:
    """Project configuration."""

    name: str = ""
    language: str = ""
    framework: str = ""
    description: str = ""


@dataclass
class CommandsConfig:
    """Commands configuration."""

    test: str = ""
    lint: str = ""
    build: str = ""


@dataclass
class BoundariesConfig:
    """Boundaries configuration."""

    never_touch: list[str] = field(default_factory=list)


@dataclass
class RalphyConfig:
    """Full Ralphy configuration."""

    project: ProjectConfig = field(default_factory=ProjectConfig)
    commands: CommandsConfig = field(default_factory=CommandsConfig)
    rules: list[str] = field(default_factory=list)
    boundaries: BoundariesConfig = field(default_factory=BoundariesConfig)


def detect_project() -> tuple[str, str, str, str, str, str]:
    """Auto-detect project type and return (name, lang, framework, test_cmd, lint_cmd, build_cmd)."""
    project_name = os.path.basename(os.getcwd())
    lang = ""
    framework = ""
    test_cmd = ""
    lint_cmd = ""
    build_cmd = ""

    # Check for Node.js project
    if os.path.exists("package.json"):
        try:
            with open("package.json") as f:
                pkg = json.load(f)

            # Get name from package.json
            if "name" in pkg:
                project_name = pkg["name"]

            # Detect language
            if os.path.exists("tsconfig.json"):
                lang = "TypeScript"
            else:
                lang = "JavaScript"

            # Get dependencies
            deps = set()
            deps.update(pkg.get("dependencies", {}).keys())
            deps.update(pkg.get("devDependencies", {}).keys())

            # Detect frameworks
            frameworks = []
            if "next" in deps:
                frameworks.append("Next.js")
            if "nuxt" in deps:
                frameworks.append("Nuxt")
            if "@remix-run/react" in deps:
                frameworks.append("Remix")
            if "svelte" in deps:
                frameworks.append("Svelte")
            if any(d.startswith("@nestjs/") for d in deps):
                frameworks.append("NestJS")
            if "hono" in deps:
                frameworks.append("Hono")
            if "fastify" in deps:
                frameworks.append("Fastify")
            if "express" in deps:
                frameworks.append("Express")
            # Only add React/Vue if no meta-framework detected
            if not frameworks:
                if "react" in deps:
                    frameworks.append("React")
                if "vue" in deps:
                    frameworks.append("Vue")

            framework = ", ".join(frameworks)

            # Detect commands
            scripts = pkg.get("scripts", {})
            if "test" in scripts:
                test_cmd = "npm test"
                if os.path.exists("bun.lockb"):
                    test_cmd = "bun test"
            if "lint" in scripts:
                lint_cmd = "npm run lint"
            if "build" in scripts:
                build_cmd = "npm run build"

        except (json.JSONDecodeError, OSError):
            pass

    # Check for Python project
    elif (
        os.path.exists("pyproject.toml")
        or os.path.exists("requirements.txt")
        or os.path.exists("setup.py")
    ):
        lang = "Python"
        py_deps = ""

        if os.path.exists("pyproject.toml"):
            with open("pyproject.toml") as f:
                py_deps = f.read()
        if os.path.exists("requirements.txt"):
            with open("requirements.txt") as f:
                py_deps += f.read()

        py_deps_lower = py_deps.lower()
        frameworks = []
        if "fastapi" in py_deps_lower:
            frameworks.append("FastAPI")
        if "django" in py_deps_lower:
            frameworks.append("Django")
        if "flask" in py_deps_lower:
            frameworks.append("Flask")
        framework = ", ".join(frameworks)

        test_cmd = "pytest"
        lint_cmd = "ruff check ."

    # Check for Go project
    elif os.path.exists("go.mod"):
        lang = "Go"
        test_cmd = "go test ./..."
        lint_cmd = "golangci-lint run"

    # Check for Rust project
    elif os.path.exists("Cargo.toml"):
        lang = "Rust"
        test_cmd = "cargo test"
        lint_cmd = "cargo clippy"
        build_cmd = "cargo build"

    return project_name, lang, framework, test_cmd, lint_cmd, build_cmd


def init_config(force: bool = False) -> None:
    """Initialize .ralphy/ directory with config files."""
    if os.path.exists(RALPHY_DIR) and not force:
        log_warn(f"{RALPHY_DIR} already exists")
        response = input("Overwrite config? [y/N] ").strip().lower()
        if response != "y":
            return

    os.makedirs(RALPHY_DIR, exist_ok=True)

    # Detect project
    project_name, lang, framework, test_cmd, lint_cmd, build_cmd = detect_project()

    # Show what we detected
    print()
    print(f"{colors.bold}Detected:{colors.reset}")
    print(f"  Project:   {colors.cyan}{project_name}{colors.reset}")
    if lang:
        print(f"  Language:  {colors.cyan}{lang}{colors.reset}")
    if framework:
        print(f"  Framework: {colors.cyan}{framework}{colors.reset}")
    if test_cmd:
        print(f"  Test:      {colors.cyan}{test_cmd}{colors.reset}")
    if lint_cmd:
        print(f"  Lint:      {colors.cyan}{lint_cmd}{colors.reset}")
    if build_cmd:
        print(f"  Build:     {colors.cyan}{build_cmd}{colors.reset}")
    print()

    # Create config.yaml
    config_content = f'''# Ralphy Configuration
# https://github.com/michaelshimeles/ralphy

# Project info (auto-detected, edit if needed)
project:
  name: "{project_name}"
  language: "{lang or 'Unknown'}"
  framework: "{framework}"
  description: ""  # Add a brief description

# Commands (auto-detected from package.json/pyproject.toml)
commands:
  test: "{test_cmd}"
  lint: "{lint_cmd}"
  build: "{build_cmd}"

# Rules - instructions the AI MUST follow
# These are injected into every prompt
rules: []
  # Examples:
  # - "Always use TypeScript strict mode"
  # - "Follow the error handling pattern in src/utils/errors.ts"
  # - "All API endpoints must have input validation with Zod"
  # - "Use server actions instead of API routes in Next.js"

# Boundaries - files/folders the AI should not modify
boundaries:
  never_touch: []
    # Examples:
    # - "src/legacy/**"
    # - "migrations/**"
    # - "*.lock"
'''

    with open(CONFIG_FILE, "w") as f:
        f.write(config_content)

    # Create progress.txt
    with open(PROGRESS_FILE, "w") as f:
        f.write("# Ralphy Progress Log\n\n")

    log_success(f"Created {RALPHY_DIR}/")
    print()
    print(f"  {colors.cyan}{CONFIG_FILE}{colors.reset}   - Your rules and preferences")
    print(f"  {colors.cyan}{PROGRESS_FILE}{colors.reset} - Progress log (auto-updated)")
    print()
    print(f"{colors.bold}Next steps:{colors.reset}")
    print(f'  1. Add rules:  {colors.cyan}ralphy --add-rule "your rule here"{colors.reset}')
    print(f"  2. Or edit:    {colors.cyan}{CONFIG_FILE}{colors.reset}")
    print(
        f'  3. Run:        {colors.cyan}ralphy "your task"{colors.reset} or {colors.cyan}ralphy{colors.reset} (with PRD.md)'
    )


def load_config() -> Optional[RalphyConfig]:
    """Load configuration from .ralphy/config.yaml."""
    if not os.path.exists(CONFIG_FILE):
        return None

    try:
        # Try to use yq for parsing (to match shell behavior)
        # Fall back to basic YAML parsing if yq not available
        import yaml

        with open(CONFIG_FILE) as f:
            data = yaml.safe_load(f)

        if not data:
            return RalphyConfig()

        config = RalphyConfig()

        if "project" in data:
            config.project = ProjectConfig(
                name=data["project"].get("name", ""),
                language=data["project"].get("language", ""),
                framework=data["project"].get("framework", ""),
                description=data["project"].get("description", ""),
            )

        if "commands" in data:
            config.commands = CommandsConfig(
                test=data["commands"].get("test", ""),
                lint=data["commands"].get("lint", ""),
                build=data["commands"].get("build", ""),
            )

        if "rules" in data and isinstance(data["rules"], list):
            config.rules = data["rules"]

        if "boundaries" in data:
            config.boundaries = BoundariesConfig(
                never_touch=data["boundaries"].get("never_touch", []) or []
            )

        return config

    except ImportError:
        log_error("PyYAML is required. Install with: pip install pyyaml")
        return None
    except Exception as e:
        log_error(f"Failed to load config: {e}")
        return None


def show_config() -> None:
    """Display current configuration."""
    if not os.path.exists(CONFIG_FILE):
        log_warn("No config found. Run 'ralphy --init' first.")
        return

    config = load_config()
    if not config:
        return

    print()
    print(f"{colors.bold}Ralphy Configuration{colors.reset} ({CONFIG_FILE})")
    print()

    # Project info
    print(f"{colors.bold}Project:{colors.reset}")
    print(f"  Name:      {config.project.name or 'Unknown'}")
    print(f"  Language:  {config.project.language or 'Unknown'}")
    if config.project.framework:
        print(f"  Framework: {config.project.framework}")
    if config.project.description:
        print(f"  About:     {config.project.description}")
    print()

    # Commands
    print(f"{colors.bold}Commands:{colors.reset}")
    print(
        f"  Test:  {config.commands.test or f'{colors.dim}(not set){colors.reset}'}"
    )
    print(
        f"  Lint:  {config.commands.lint or f'{colors.dim}(not set){colors.reset}'}"
    )
    print(
        f"  Build: {config.commands.build or f'{colors.dim}(not set){colors.reset}'}"
    )
    print()

    # Rules
    print(f"{colors.bold}Rules:{colors.reset}")
    if config.rules:
        for rule in config.rules:
            print(f"  - {rule}")
    else:
        print(f'  {colors.dim}(none - add with: ralphy --add-rule "..."){colors.reset}')
    print()

    # Boundaries
    if config.boundaries.never_touch:
        print(f"{colors.bold}Never Touch:{colors.reset}")
        for path in config.boundaries.never_touch:
            print(f"  - {path}")
        print()


def add_rule(rule: str) -> None:
    """Add a rule to config.yaml."""
    if not os.path.exists(CONFIG_FILE):
        log_error("No config found. Run 'ralphy --init' first.")
        return

    try:
        import yaml

        with open(CONFIG_FILE) as f:
            data = yaml.safe_load(f) or {}

        if "rules" not in data or data["rules"] is None:
            data["rules"] = []

        data["rules"].append(rule)

        with open(CONFIG_FILE, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        log_success(f"Added rule: {rule}")

    except ImportError:
        log_error("PyYAML is required. Install with: pip install pyyaml")
    except Exception as e:
        log_error(f"Failed to add rule: {e}")


def ensure_ralphy_dir() -> None:
    """Ensure .ralphy directory exists with progress file."""
    os.makedirs(RALPHY_DIR, exist_ok=True)
    if not os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "w") as f:
            f.write("# Ralphy Progress Log\n\n")


def log_task_history(task: str, status: str) -> None:
    """Log a task to the progress file."""
    if not os.path.exists(PROGRESS_FILE):
        return

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    icon = "✓" if status == "completed" else "✗"

    with open(PROGRESS_FILE, "a") as f:
        f.write(f"- [{icon}] {timestamp} - {task}\n")


def build_prompt(task: str, auto_commit: bool = True) -> str:
    """Build a prompt with brownfield context."""
    config = load_config()
    prompt_parts = []

    if config:
        # Add project context
        if config.project.name or config.project.language:
            context_lines = []
            if config.project.name:
                context_lines.append(f"Project: {config.project.name}")
            if config.project.language:
                context_lines.append(f"Language: {config.project.language}")
            if config.project.framework:
                context_lines.append(f"Framework: {config.project.framework}")
            if config.project.description:
                context_lines.append(f"Description: {config.project.description}")
            if context_lines:
                prompt_parts.append("## Project Context\n" + "\n".join(context_lines))

        # Add rules
        if config.rules:
            prompt_parts.append(
                "## Rules (you MUST follow these)\n" + "\n".join(config.rules)
            )

        # Add boundaries
        if config.boundaries.never_touch:
            prompt_parts.append(
                "## Boundaries\nDo NOT modify these files/directories:\n"
                + "\n".join(config.boundaries.never_touch)
            )

    # Add the task
    prompt_parts.append(f"## Task\n{task}")

    # Add instructions
    instructions = """## Instructions
1. Implement the task described above
2. Write tests if appropriate
3. Ensure the code works correctly"""

    if auto_commit:
        instructions += "\n4. Commit your changes with a descriptive message"

    instructions += "\n\nKeep changes focused and minimal. Do not refactor unrelated code."

    prompt_parts.append(instructions)

    return "\n\n".join(prompt_parts)
