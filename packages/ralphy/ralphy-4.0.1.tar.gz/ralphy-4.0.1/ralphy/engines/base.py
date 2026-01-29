"""Base class for AI engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIResult:
    """Result from an AI engine run."""

    response: str
    input_tokens: int = 0
    output_tokens: int = 0
    actual_cost: Optional[float] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class AIEngine(ABC):
    """Abstract base class for AI engines."""

    name: str = "base"
    cli_command: str = ""

    @abstractmethod
    def run(self, prompt: str, verbose: bool = False) -> AIResult:
        """
        Run the AI engine with the given prompt.

        Args:
            prompt: The prompt to send to the AI
            verbose: Whether to enable verbose output

        Returns:
            AIResult with response and token usage
        """
        pass

    @abstractmethod
    def check_available(self) -> bool:
        """Check if the AI CLI tool is available."""
        pass

    @abstractmethod
    def get_install_instructions(self) -> str:
        """Return instructions for installing the CLI tool."""
        pass
