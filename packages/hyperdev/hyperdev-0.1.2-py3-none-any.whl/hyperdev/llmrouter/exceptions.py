"""Custom exceptions for LLMRouter."""


class LLMRouterError(Exception):
    """Base exception for all LLMRouter errors."""

    pass


class ConfigurationError(LLMRouterError):
    """Raised when configuration is invalid or missing."""

    pass


class ProviderError(LLMRouterError):
    """Raised when a provider operation fails."""

    pass


class StreamingError(LLMRouterError):
    """Raised when streaming encounters an error."""

    pass


class ValidationError(LLMRouterError):
    """Raised when input validation fails."""

    pass
