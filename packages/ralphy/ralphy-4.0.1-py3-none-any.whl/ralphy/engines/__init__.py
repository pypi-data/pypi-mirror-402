"""AI engine implementations."""

from ralphy.engines.base import AIEngine, AIResult
from ralphy.engines.claude import ClaudeEngine
from ralphy.engines.codex import CodexEngine
from ralphy.engines.cursor import CursorEngine
from ralphy.engines.droid import DroidEngine
from ralphy.engines.opencode import OpenCodeEngine
from ralphy.engines.qwen import QwenEngine

__all__ = [
    "AIEngine",
    "AIResult",
    "ClaudeEngine",
    "CodexEngine",
    "CursorEngine",
    "DroidEngine",
    "OpenCodeEngine",
    "QwenEngine",
]


def get_engine(name: str) -> AIEngine:
    """Get an AI engine by name."""
    engines = {
        "claude": ClaudeEngine,
        "opencode": OpenCodeEngine,
        "cursor": CursorEngine,
        "codex": CodexEngine,
        "qwen": QwenEngine,
        "droid": DroidEngine,
    }
    if name not in engines:
        raise ValueError(
            f"Unknown engine: {name}. Available: {', '.join(engines.keys())}"
        )
    return engines[name]()
