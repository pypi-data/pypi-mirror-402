"""Tests for configuration management."""

import os
import tempfile

import pytest

from ralphy.config import (
    RalphyConfig,
    ProjectConfig,
    CommandsConfig,
    BoundariesConfig,
    detect_project,
    build_prompt,
)


def test_detect_project_unknown():
    """Test detection in a directory with no recognizable project files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            name, lang, framework, test_cmd, lint_cmd, build_cmd = detect_project()
            # Name should be the directory name
            assert name == os.path.basename(tmpdir)
            assert lang == ""
            assert framework == ""
        finally:
            os.chdir(old_cwd)


def test_detect_project_python():
    """Test detection of a Python project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a requirements.txt
        with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
            f.write("fastapi\nuvicorn\n")

        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            name, lang, framework, test_cmd, lint_cmd, build_cmd = detect_project()
            assert lang == "Python"
            assert "FastAPI" in framework
            assert test_cmd == "pytest"
            assert lint_cmd == "ruff check ."
        finally:
            os.chdir(old_cwd)


def test_detect_project_nodejs():
    """Test detection of a Node.js project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a package.json
        import json

        pkg = {
            "name": "test-project",
            "dependencies": {"react": "^18.0.0"},
            "scripts": {"test": "jest", "lint": "eslint ."},
        }
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            json.dump(pkg, f)

        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            name, lang, framework, test_cmd, lint_cmd, build_cmd = detect_project()
            assert name == "test-project"
            assert lang == "JavaScript"
            assert "React" in framework
            assert test_cmd == "npm test"
            assert lint_cmd == "npm run lint"
        finally:
            os.chdir(old_cwd)


def test_build_prompt_basic():
    """Test building a basic prompt."""
    prompt = build_prompt("Add a login button")
    assert "Add a login button" in prompt
    assert "## Task" in prompt
    assert "## Instructions" in prompt


def test_build_prompt_with_commit():
    """Test prompt includes commit instruction when auto_commit is True."""
    prompt = build_prompt("Fix bug", auto_commit=True)
    assert "Commit your changes" in prompt


def test_build_prompt_without_commit():
    """Test prompt excludes commit instruction when auto_commit is False."""
    prompt = build_prompt("Fix bug", auto_commit=False)
    assert "Commit your changes" not in prompt


def test_ralphy_config_defaults():
    """Test RalphyConfig default values."""
    config = RalphyConfig()
    assert config.project.name == ""
    assert config.project.language == ""
    assert config.rules == []
    assert config.boundaries.never_touch == []


def test_project_config():
    """Test ProjectConfig structure."""
    config = ProjectConfig(
        name="test-project",
        language="TypeScript",
        framework="Next.js",
        description="A test project",
    )
    assert config.name == "test-project"
    assert config.language == "TypeScript"
    assert config.framework == "Next.js"
    assert config.description == "A test project"


def test_commands_config():
    """Test CommandsConfig structure."""
    config = CommandsConfig(
        test="npm test",
        lint="npm run lint",
        build="npm run build",
    )
    assert config.test == "npm test"
    assert config.lint == "npm run lint"
    assert config.build == "npm run build"
