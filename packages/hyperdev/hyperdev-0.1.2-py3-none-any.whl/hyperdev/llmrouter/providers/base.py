"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Iterator

from ..types import ProviderConfig, StreamChunk


class BaseProvider(ABC):
    """Abstract base class for LLM provider implementations."""

    def __init__(self, config: ProviderConfig, api_key: str):
        """
        Initialize the provider.

        Args:
            config: ProviderConfig with model and parameters
            api_key: API key for authentication
        """
        self.config = config
        self.api_key = api_key

    @abstractmethod
    def stream_chat(self, prompt: str, llm_string: str) -> Iterator[StreamChunk]:
        """
        Stream chat response from the provider.

        Args:
            prompt: User's message or prompt
            llm_string: Model identifier specific to the provider

        Yields:
            StreamChunk objects containing response content and metadata

        Raises:
            StreamingError: If streaming fails
        """
        pass

    @abstractmethod
    def validate_model(self, llm_string: str) -> bool:
        """
        Validate if the model string is supported by the provider.

        Args:
            llm_string: Model identifier to validate

        Returns:
            True if valid, False otherwise
        """
        pass
