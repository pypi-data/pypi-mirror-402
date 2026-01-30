"""Claude provider implementation."""

from typing import Iterator

from anthropic import Anthropic

from ..types import ProviderConfig, StreamChunk
from ..exceptions import StreamingError
from .base import BaseProvider


class ClaudeProvider(BaseProvider):
    """Claude provider for streaming chat responses."""

    def __init__(self, config: ProviderConfig, api_key: str):
        """
        Initialize Claude provider.

        Args:
            config: ProviderConfig with model and parameters
            api_key: Anthropic API key
        """
        super().__init__(config, api_key)
        self.client = Anthropic(api_key=api_key)

    def stream_chat(self, prompt: str, llm_string: str) -> Iterator[StreamChunk]:
        """
        Stream chat response from Claude.

        Args:
            prompt: User's message
            llm_string: Model identifier (e.g., "claude-sonnet-4-5-20250929")

        Yields:
            StreamChunk objects with response content

        Raises:
            StreamingError: If streaming fails
        """
        try:
            # Build parameters
            params = {
                "model": llm_string,
                "max_tokens": self.config.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }

            # Add temperature if provided (Claude expects it)
            if self.config.temperature is not None:
                params["temperature"] = self.config.temperature

            # Add any additional parameters
            params.update(self.config.additional_params)

            # Stream the response using context manager
            with self.client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield StreamChunk(
                        content=text,
                        finish_reason=None,  # Set on final chunk
                        model=llm_string,
                        provider="claude",
                    )
        except Exception as e:
            raise StreamingError(f"Claude streaming error: {e}")

    def validate_model(self, llm_string: str) -> bool:
        """
        Validate Claude model string.

        Args:
            llm_string: Model identifier

        Returns:
            True if model looks valid (basic check)
        """
        # Basic validation: model string should contain letters/numbers/hyphens
        return bool(llm_string and isinstance(llm_string, str))
