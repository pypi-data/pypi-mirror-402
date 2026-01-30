"""OpenAI provider implementation."""

from typing import Iterator

from openai import OpenAI

from ..types import ProviderConfig, StreamChunk
from ..exceptions import StreamingError
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI provider for streaming chat responses."""

    def __init__(self, config: ProviderConfig, api_key: str):
        """
        Initialize OpenAI provider.

        Args:
            config: ProviderConfig with model and parameters
            api_key: OpenAI API key
        """
        super().__init__(config, api_key)
        self.client = OpenAI(api_key=api_key)

    def stream_chat(self, prompt: str, llm_string: str) -> Iterator[StreamChunk]:
        """
        Stream chat response from OpenAI.

        Args:
            prompt: User's message
            llm_string: Model identifier (e.g., "gpt-4", "gpt-3.5-turbo")

        Yields:
            StreamChunk objects with response content

        Raises:
            StreamingError: If streaming fails
        """
        try:
            # Build parameters
            params = {
                "model": llm_string,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "stream": True,
            }

            # Add any additional parameters
            params.update(self.config.additional_params)

            # Stream the response
            with self.client.chat.completions.create(**params) as stream:
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        finish_reason = chunk.choices[0].finish_reason
                        yield StreamChunk(
                            content=chunk.choices[0].delta.content,
                            finish_reason=finish_reason,
                            model=llm_string,
                            provider="openai",
                        )
        except Exception as e:
            raise StreamingError(f"OpenAI streaming error: {e}")

    def validate_model(self, llm_string: str) -> bool:
        """
        Validate OpenAI model string.

        Args:
            llm_string: Model identifier

        Returns:
            True if model looks valid (basic check)
        """
        # Basic validation: model string should contain letters/numbers/hyphens
        return bool(llm_string and isinstance(llm_string, str))
