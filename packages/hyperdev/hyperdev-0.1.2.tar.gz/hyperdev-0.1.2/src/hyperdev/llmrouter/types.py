"""Type definitions and Pydantic models for LLMRouter."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class StreamChunk(BaseModel):
    """Represents a chunk of streamed response."""

    content: str = Field(..., description="The text content of this chunk")
    finish_reason: Optional[str] = Field(
        None, description="Finish reason if stream ended (e.g., 'stop', 'max_tokens')"
    )
    model: str = Field(..., description="The model identifier used")
    provider: str = Field(..., description="The provider name (e.g., 'openai', 'claude')")


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    model: str = Field(..., description="Model identifier for the provider")
    api_key_env_var: str = Field(
        ..., description="Environment variable name for the API key"
    )
    max_tokens: int = Field(
        default=1024, description="Maximum tokens to generate", ge=1
    )
    temperature: float = Field(
        default=0.7, description="Sampling temperature", ge=0.0, le=2.0
    )
    additional_params: Dict[str, Any] = Field(
        default_factory=dict, description="Additional provider-specific parameters"
    )

    class Config:
        """Pydantic configuration."""
        extra = "allow"  # Allow extra fields for provider-specific config
