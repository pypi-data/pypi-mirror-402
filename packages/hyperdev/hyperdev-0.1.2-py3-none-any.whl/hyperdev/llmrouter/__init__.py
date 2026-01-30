"""HyperDev LLMRouter - Unified streaming interface for multiple LLM providers."""

from .chat_stream import chat_stream
from .enums import LLMProvider
from .types import StreamChunk, ProviderConfig
from .exceptions import (
    LLMRouterError,
    ConfigurationError,
    ProviderError,
    StreamingError,
    ValidationError,
)
from .utils import ensure_langfuse_installed

__version__ = "0.1.2"

__all__ = [
    "chat_stream",
    "LLMProvider",
    "StreamChunk",
    "ProviderConfig",
    "LLMRouterError",
    "ConfigurationError",
    "ProviderError",
    "StreamingError",
    "ValidationError",
    "ensure_langfuse_installed",
]
