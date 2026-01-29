"""Tests for AI engines."""

import pytest

from ralphy.engines import (
    AIEngine,
    AIResult,
    ClaudeEngine,
    CodexEngine,
    CursorEngine,
    DroidEngine,
    OpenCodeEngine,
    QwenEngine,
    get_engine,
)


def test_ai_result_defaults():
    """Test AIResult default values."""
    result = AIResult(response="test")
    assert result.response == "test"
    assert result.input_tokens == 0
    assert result.output_tokens == 0
    assert result.actual_cost is None
    assert result.duration_ms is None
    assert result.error is None


def test_ai_result_with_values():
    """Test AIResult with all values."""
    result = AIResult(
        response="test response",
        input_tokens=100,
        output_tokens=200,
        actual_cost=0.001,
        duration_ms=5000,
        error=None,
    )
    assert result.response == "test response"
    assert result.input_tokens == 100
    assert result.output_tokens == 200
    assert result.actual_cost == 0.001
    assert result.duration_ms == 5000


def test_get_engine_claude():
    """Test getting Claude engine."""
    engine = get_engine("claude")
    assert isinstance(engine, ClaudeEngine)
    assert engine.name == "claude"
    assert engine.cli_command == "claude"


def test_get_engine_opencode():
    """Test getting OpenCode engine."""
    engine = get_engine("opencode")
    assert isinstance(engine, OpenCodeEngine)
    assert engine.name == "opencode"
    assert engine.cli_command == "opencode"


def test_get_engine_cursor():
    """Test getting Cursor engine."""
    engine = get_engine("cursor")
    assert isinstance(engine, CursorEngine)
    assert engine.name == "cursor"
    assert engine.cli_command == "agent"


def test_get_engine_codex():
    """Test getting Codex engine."""
    engine = get_engine("codex")
    assert isinstance(engine, CodexEngine)
    assert engine.name == "codex"
    assert engine.cli_command == "codex"


def test_get_engine_qwen():
    """Test getting Qwen engine."""
    engine = get_engine("qwen")
    assert isinstance(engine, QwenEngine)
    assert engine.name == "qwen"
    assert engine.cli_command == "qwen"


def test_get_engine_droid():
    """Test getting Droid engine."""
    engine = get_engine("droid")
    assert isinstance(engine, DroidEngine)
    assert engine.name == "droid"
    assert engine.cli_command == "droid"


def test_get_engine_invalid():
    """Test getting an invalid engine raises error."""
    with pytest.raises(ValueError, match="Unknown engine"):
        get_engine("invalid_engine")


def test_claude_engine_install_instructions():
    """Test Claude engine install instructions."""
    engine = ClaudeEngine()
    instructions = engine.get_install_instructions()
    assert "anthropic" in instructions.lower() or "claude" in instructions.lower()


def test_opencode_engine_install_instructions():
    """Test OpenCode engine install instructions."""
    engine = OpenCodeEngine()
    instructions = engine.get_install_instructions()
    assert "opencode" in instructions.lower()


def test_cursor_engine_install_instructions():
    """Test Cursor engine install instructions."""
    engine = CursorEngine()
    instructions = engine.get_install_instructions()
    assert "cursor" in instructions.lower() or "agent" in instructions.lower()


def test_codex_engine_install_instructions():
    """Test Codex engine install instructions."""
    engine = CodexEngine()
    instructions = engine.get_install_instructions()
    assert "codex" in instructions.lower()


def test_qwen_engine_install_instructions():
    """Test Qwen engine install instructions."""
    engine = QwenEngine()
    instructions = engine.get_install_instructions()
    assert "qwen" in instructions.lower()


def test_droid_engine_install_instructions():
    """Test Droid engine install instructions."""
    engine = DroidEngine()
    instructions = engine.get_install_instructions()
    assert "factory" in instructions.lower() or "droid" in instructions.lower()
