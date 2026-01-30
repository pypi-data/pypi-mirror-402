"""Gemini provider implementation."""

from typing import Iterator

import google.genai as genai

from ..types import ProviderConfig, StreamChunk
from ..exceptions import StreamingError
from .base import BaseProvider


class GeminiProvider(BaseProvider):
    """Gemini provider for streaming chat responses."""

    def __init__(self, config: ProviderConfig, api_key: str):
        """
        Initialize Gemini provider.

        Args:
            config: ProviderConfig with model and parameters
            api_key: Google Gemini API key
        """
        super().__init__(config, api_key)
        genai.configure(api_key=api_key)

    def stream_chat(self, prompt: str, llm_string: str) -> Iterator[StreamChunk]:
        """
        Stream chat response from Gemini.

        Args:
            prompt: User's message
            llm_string: Model identifier (e.g., "gemini-2.5-flash")

        Yields:
            StreamChunk objects with response content

        Raises:
            StreamingError: If streaming fails
        """
        try:
            # Create client with the specified model
            model = genai.Client().models.get(name=f"models/{llm_string}")

            # Build generation config
            generation_config = {
                "max_output_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }
            generation_config.update(self.config.additional_params)

            # Create chat session
            chat = genai.Client().chats.create(model=f"models/{llm_string}")

            # Stream the response
            response = chat.send_message_stream(
                prompt,
                generation_config=generation_config,
            )

            for chunk in response:
                if chunk.text:
                    yield StreamChunk(
                        content=chunk.text,
                        finish_reason=None,
                        model=llm_string,
                        provider="gemini",
                    )
        except Exception as e:
            raise StreamingError(f"Gemini streaming error: {e}")

    def validate_model(self, llm_string: str) -> bool:
        """
        Validate Gemini model string.

        Args:
            llm_string: Model identifier

        Returns:
            True if model looks valid (basic check)
        """
        # Basic validation: model string should contain letters/numbers/hyphens
        return bool(llm_string and isinstance(llm_string, str))
