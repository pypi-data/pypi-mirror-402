"""Example demonstrating all LLM providers."""

from pathlib import Path
from hyperdev.llmrouter import chat_stream, LLMProvider
from hyperdev.llmrouter.exceptions import ConfigurationError, ValidationError


def stream_from_provider(provider: LLMProvider, model_string: str, config_dir: Path):
    """Stream a response from a specific provider."""
    prompt = "What is machine learning? Answer in one sentence."

    print(f"\n{'=' * 60}")
    print(f"Provider: {provider.value.upper()}")
    print(f"Model: {model_string}")
    print("-" * 60)

    try:
        for chunk in chat_stream(
            prompt=prompt,
            llm_provider=provider,
            llm_string=model_string,
            config_dir=config_dir,
        ):
            print(chunk.content, end="", flush=True)

        print("\n✓ Completed successfully\n")

    except ConfigurationError as e:
        print(f"✗ Configuration Error: {e}\n")
    except ValidationError as e:
        print(f"✗ Validation Error: {e}\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")


def main():
    """Demonstrate streaming from all providers."""
    config_dir = Path(__file__).parent.parent / "config_examples"

    print("\n" + "=" * 60)
    print("HyperDev LLMRouter - All Providers Example")
    print("=" * 60)

    providers = [
        (LLMProvider.OPENAI, "gpt-4"),
        (LLMProvider.CLAUDE, "claude-sonnet-4-5-20250929"),
        (LLMProvider.GEMINI, "gemini-2.5-flash"),
        (LLMProvider.OPENROUTER, "anthropic/claude-3-sonnet"),
    ]

    for provider, model in providers:
        stream_from_provider(provider, model, config_dir)

    print("=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
