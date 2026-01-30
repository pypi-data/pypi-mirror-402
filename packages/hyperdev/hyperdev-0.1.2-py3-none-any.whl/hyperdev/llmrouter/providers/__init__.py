"""Provider implementations and registry."""

from typing import Dict, Type

from ..enums import LLMProvider
from .base import BaseProvider
from .openai import OpenAIProvider
from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .openrouter import OpenRouterProvider


# Provider registry mapping enum values to provider classes
PROVIDER_REGISTRY: Dict[LLMProvider, Type[BaseProvider]] = {
    LLMProvider.OPENAI: OpenAIProvider,
    LLMProvider.CLAUDE: ClaudeProvider,
    LLMProvider.GEMINI: GeminiProvider,
    LLMProvider.OPENROUTER: OpenRouterProvider,
}


def get_provider_class(provider: LLMProvider) -> Type[BaseProvider]:
    """
    Get the provider class for a given LLM provider.

    Args:
        provider: LLMProvider enum value

    Returns:
        The provider class

    Raises:
        ValueError: If provider not in registry
    """
    if provider not in PROVIDER_REGISTRY:
        raise ValueError(f"Unknown provider: {provider}")
    return PROVIDER_REGISTRY[provider]


__all__ = [
    "BaseProvider",
    "OpenAIProvider",
    "ClaudeProvider",
    "GeminiProvider",
    "OpenRouterProvider",
    "PROVIDER_REGISTRY",
    "get_provider_class",
]
