"""Enumeration definitions for LLMRouter."""

from enum import StrEnum, auto


class LLMProvider(StrEnum):
    """Enumeration of supported LLM providers."""

    OPENAI = auto()      # "openai"
    CLAUDE = auto()      # "claude"
    GEMINI = auto()      # "gemini"
    OPENROUTER = auto()  # "openrouter"

    def __str__(self) -> str:
        """Return the lowercase string value of the provider."""
        return self.value
