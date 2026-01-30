"""OpenRouter provider implementation."""

from typing import Iterator

from openai import OpenAI

from ..types import ProviderConfig, StreamChunk
from ..exceptions import StreamingError
from .base import BaseProvider


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider for streaming chat responses."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, config: ProviderConfig, api_key: str):
        """
        Initialize OpenRouter provider.

        Args:
            config: ProviderConfig with model and parameters
            api_key: OpenRouter API key
        """
        super().__init__(config, api_key)
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)

    def stream_chat(self, prompt: str, llm_string: str) -> Iterator[StreamChunk]:
        """
        Stream chat response from OpenRouter.

        Args:
            prompt: User's message
            llm_string: Model identifier (e.g., "anthropic/claude-3-sonnet")

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
                            provider="openrouter",
                        )
        except Exception as e:
            raise StreamingError(f"OpenRouter streaming error: {e}")

    def validate_model(self, llm_string: str) -> bool:
        """
        Validate OpenRouter model string.

        Args:
            llm_string: Model identifier (e.g., "provider/model-name")

        Returns:
            True if model looks valid (basic check)
        """
        # OpenRouter models should have format "provider/model-name"
        if not llm_string or not isinstance(llm_string, str):
            return False
        return "/" in llm_string
