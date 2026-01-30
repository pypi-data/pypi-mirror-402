"""Main chat_stream function for unified LLM interface."""

from pathlib import Path
from typing import Iterator, Optional, Dict, Any

from .enums import LLMProvider
from .types import StreamChunk
from .config import ConfigLoader
from .exceptions import ConfigurationError, ValidationError, ProviderError
from .providers import get_provider_class
from .integrations.langfuse import LangfuseStreamWrapper
from .utils import ensure_langfuse_installed

try:
    from .integrations.langfuse import get_langfuse_client
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False


def chat_stream(
    prompt: str,
    llm_provider: LLMProvider,
    llm_string: str,
    config_dir: Optional[Path] = None,
    langfuse_public_key: Optional[str] = None,
    langfuse_secret_key: Optional[str] = None,
    langfuse_base_url: Optional[str] = None,
    langfuse_trace_name: Optional[str] = None,
    langfuse_user_id: Optional[str] = None,
    langfuse_session_id: Optional[str] = None,
    langfuse_metadata: Optional[Dict[str, Any]] = None,
    langfuse_tags: Optional[list] = None,
) -> Iterator[StreamChunk]:
    """
    Stream chat responses from specified LLM provider.

    This function provides a unified streaming interface for multiple LLM providers,
    loading configuration from JSON files and environment variables.

    Args:
        prompt: User's message or prompt to send to the LLM
        llm_provider: LLMProvider enum value (OPENAI, CLAUDE, GEMINI, OPENROUTER)
        llm_string: Model identifier specific to the provider
                   Examples:
                   - OpenAI: "gpt-4", "gpt-3.5-turbo"
                   - Claude: "claude-sonnet-4-5-20250929"
                   - Gemini: "gemini-2.5-flash"
                   - OpenRouter: "anthropic/claude-3-sonnet"
        config_dir: Directory containing configuration JSON files.
                   Defaults to current working directory.
                   Expected files: "{provider}_chat_config.json"
        langfuse_public_key: Langfuse public API key (or set LANGFUSE_PUBLIC_KEY env var)
        langfuse_secret_key: Langfuse secret API key (or set LANGFUSE_SECRET_KEY env var)
        langfuse_base_url: Optional custom Langfuse base URL
        langfuse_trace_name: Name for the Langfuse trace
        langfuse_user_id: User identifier for Langfuse tracing
        langfuse_session_id: Session identifier for Langfuse tracing
        langfuse_metadata: Additional metadata to log to Langfuse
        langfuse_tags: Tags for organizing traces in Langfuse

    Yields:
        StreamChunk objects containing:
        - content: Text chunk of the response
        - finish_reason: Reason streaming finished (None if ongoing, "stop" if complete)
        - model: Model identifier used
        - provider: Provider name (lowercase string)

    Raises:
        ConfigurationError: If config file missing or environment variables not set
        ValidationError: If inputs are invalid
        ProviderError: If provider instantiation fails

    Example:
        >>> from hyperdev.llmrouter import chat_stream, LLMProvider
        >>> for chunk in chat_stream(
        ...     "Explain quantum computing",
        ...     LLMProvider.OPENAI,
        ...     "gpt-4",
        ...     config_dir=Path("./config")
        ... ):
        ...     print(chunk.content, end="", flush=True)

        With Langfuse tracing:
        >>> for chunk in chat_stream(
        ...     "Explain quantum computing",
        ...     LLMProvider.OPENAI,
        ...     "gpt-4",
        ...     langfuse_public_key="pk-...",
        ...     langfuse_secret_key="sk-...",
        ... ):
        ...     print(chunk.content, end="", flush=True)
    """
    # Validate inputs
    if not prompt or not isinstance(prompt, str):
        raise ValidationError("prompt must be a non-empty string")

    if not isinstance(llm_provider, LLMProvider):
        raise ValidationError(f"llm_provider must be LLMProvider enum, got {type(llm_provider)}")

    if not llm_string or not isinstance(llm_string, str):
        raise ValidationError("llm_string must be a non-empty string")

    # Set default config directory if not provided
    if config_dir is None:
        config_dir = Path.cwd()

    # Load configuration
    config_loader = ConfigLoader(config_dir)

    try:
        provider_config = config_loader.load_config(llm_provider)
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration for {llm_provider}: {e}")

    # Get API key from environment
    try:
        api_key = config_loader.get_api_key(provider_config.api_key_env_var)
    except Exception as e:
        raise ConfigurationError(f"Failed to get API key: {e}")

    # Get provider class and instantiate
    try:
        provider_class = get_provider_class(llm_provider)
        provider = provider_class(provider_config, api_key)
    except Exception as e:
        raise ProviderError(f"Failed to initialize {llm_provider} provider: {e}")

    # Validate model string
    if not provider.validate_model(llm_string):
        raise ValidationError(f"Invalid model string for {llm_provider}: {llm_string}")

    # Set up Langfuse integration if configured
    langfuse = None
    trace = None
    span = None

    if langfuse_public_key or langfuse_secret_key:
        try:
            # Auto-install langfuse if not available
            if not LANGFUSE_AVAILABLE:
                ensure_langfuse_installed(auto_install=True)
                # Reload the module after installation
                import importlib
                import hyperdev.llmrouter.integrations.langfuse as langfuse_module
                importlib.reload(langfuse_module)
                from .integrations.langfuse import get_langfuse_client as get_client_reloaded
                get_langfuse_client_func = get_client_reloaded
            else:
                get_langfuse_client_func = get_langfuse_client

            langfuse = get_langfuse_client_func(
                public_key=langfuse_public_key,
                secret_key=langfuse_secret_key,
                base_url=langfuse_base_url,
            )

            if langfuse:
                # Start trace
                trace = langfuse.start_trace(
                    name=langfuse_trace_name or f"{llm_provider.value} Chat",
                    user_id=langfuse_user_id,
                    session_id=langfuse_session_id,
                    metadata=langfuse_metadata,
                    tags=langfuse_tags,
                )

                # Start span
                span = langfuse.start_span(
                    trace,
                    name="LLM Call",
                    input_data={"prompt": prompt, "model": llm_string},
                )
        except Exception as e:
            # Don't fail if Langfuse setup fails, just log it
            import warnings

            warnings.warn(f"Failed to set up Langfuse integration: {e}")
            langfuse = None
            trace = None
            span = None

    # Stream responses
    stream = provider.stream_chat(prompt, llm_string)

    # Wrap stream with Langfuse tracing if available
    if langfuse and trace:
        stream = LangfuseStreamWrapper(
            stream,
            langfuse,
            trace,
            span,
            llm_string,
            llm_provider.value,
            prompt,
        )

    yield from stream
