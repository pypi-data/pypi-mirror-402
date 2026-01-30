"""
Example: Using HyperDev LLMRouter with Langfuse Integration

This example demonstrates how to use Langfuse for comprehensive LLM call tracking.
Langfuse allows you to monitor, debug, and analyze all LLM calls.

Prerequisites:
1. Install with Langfuse support: pip install 'hyperdev[langfuse]'
2. Sign up at https://langfuse.com
3. Get your API keys from Project Settings
4. Set environment variables:
   export LANGFUSE_PUBLIC_KEY="pk_..."
   export LANGFUSE_SECRET_KEY="sk_..."
   export OPENAI_API_KEY="sk-..."
"""

from pathlib import Path
from hyperdev.llmrouter import chat_stream, LLMProvider


def example_basic_tracing():
    """Basic example with automatic Langfuse tracing."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Langfuse Tracing")
    print("=" * 70)

    config_dir = Path(__file__).parent.parent / "config_examples"

    # Enable tracing with environment variables
    # (assumes LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set)
    for chunk in chat_stream(
        "What is machine learning?",
        LLMProvider.OPENAI,
        "gpt-4",
        config_dir=config_dir,
    ):
        print(chunk.content, end="", flush=True)

    print("\n✓ Trace logged to Langfuse\n")


def example_with_user_context():
    """Example with user and session tracking."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Tracing with User Context")
    print("=" * 70)

    config_dir = Path(__file__).parent.parent / "config_examples"

    # Log with user and session information
    for chunk in chat_stream(
        "Explain neural networks",
        LLMProvider.OPENAI,
        "gpt-4",
        config_dir=config_dir,
        langfuse_user_id="user_alice",
        langfuse_session_id="session_2025_01_21",
        langfuse_metadata={
            "feature": "ai_tutoring",
            "topic": "deep_learning",
        },
        langfuse_tags=["education", "ai"],
    ):
        print(chunk.content, end="", flush=True)

    print("\n✓ Trace with user context logged to Langfuse\n")


def example_multi_provider_comparison():
    """Example comparing multiple providers with Langfuse tracking."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Multi-Provider Comparison with Tracing")
    print("=" * 70)

    config_dir = Path(__file__).parent.parent / "config_examples"

    prompt = "What is quantum computing in simple terms?"

    providers = [
        (LLMProvider.OPENAI, "gpt-4"),
        (LLMProvider.CLAUDE, "claude-sonnet-4-5-20250929"),
    ]

    for provider, model in providers:
        print(f"\n{provider.value.upper()} Response:")
        print("-" * 70)

        for chunk in chat_stream(
            prompt,
            provider,
            model,
            config_dir=config_dir,
            langfuse_trace_name=f"QC Explanation - {provider.value}",
            langfuse_metadata={
                "comparison": True,
                "topic": "quantum_computing",
            },
            langfuse_tags=["comparison", "quantum"],
        ):
            print(chunk.content, end="", flush=True)

        print("\n")


def example_with_custom_metadata():
    """Example with detailed custom metadata."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Detailed Metadata Logging")
    print("=" * 70)

    config_dir = Path(__file__).parent.parent / "config_examples"

    from datetime import datetime

    for chunk in chat_stream(
        "Summarize the history of artificial intelligence",
        LLMProvider.OPENAI,
        "gpt-4",
        config_dir=config_dir,
        langfuse_trace_name="AI History Summary",
        langfuse_user_id="researcher_bob",
        langfuse_session_id="research_session_2025",
        langfuse_metadata={
            "timestamp": datetime.now().isoformat(),
            "request_type": "summary",
            "domain": "history",
            "language": "english",
            "output_format": "paragraph",
            "detail_level": "comprehensive",
        },
        langfuse_tags=["research", "history", "ai", "summary"],
    ):
        print(chunk.content, end="", flush=True)

    print("\n✓ Detailed metadata trace logged\n")


def example_error_handling():
    """Example showing graceful error handling."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Error Handling with Langfuse")
    print("=" * 70)

    config_dir = Path(__file__).parent.parent / "config_examples"

    try:
        for chunk in chat_stream(
            "What is blockchain?",
            LLMProvider.OPENAI,
            "gpt-4",
            config_dir=config_dir,
            # Langfuse tracing (will gracefully fail if keys missing)
            langfuse_user_id="user_charlie",
            langfuse_tags=["blockchain"],
        ):
            print(chunk.content, end="", flush=True)

        print("\n✓ Request completed\n")

    except Exception as e:
        print(f"\n✗ Error occurred: {e}\n")
        print("Note: Langfuse failures won't break your application")


def example_production_setup():
    """Example showing production-ready setup."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Production-Ready Setup")
    print("=" * 70)

    import os

    config_dir = Path(__file__).parent.parent / "config_examples"

    def get_response_with_tracing(
        user_id: str,
        prompt: str,
        metadata: dict = None,
    ) -> str:
        """Get LLM response with automatic tracing."""
        response = ""

        for chunk in chat_stream(
            prompt,
            LLMProvider.OPENAI,
            "gpt-4",
            config_dir=config_dir,
            langfuse_user_id=user_id,
            langfuse_session_id=os.getenv("SESSION_ID", "default"),
            langfuse_metadata=metadata or {},
            langfuse_tags=["production"],
        ):
            response += chunk.content

        return response

    # Use in your application
    response = get_response_with_tracing(
        user_id="prod_user_123",
        prompt="Explain microservices architecture",
        metadata={
            "app": "documentation_generator",
            "version": "2.0",
        },
    )

    print(response)
    print("\n✓ Production trace logged\n")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("HyperDev LLMRouter - Langfuse Integration Examples")
    print("=" * 70)
    print("\nNote: These examples require Langfuse API keys to be set")
    print("Set environment variables:")
    print("  export LANGFUSE_PUBLIC_KEY='pk_...'")
    print("  export LANGFUSE_SECRET_KEY='sk_...'")
    print("  export OPENAI_API_KEY='sk-...'")

    try:
        # Basic tracing (uses environment variables)
        example_basic_tracing()

        # With user context
        example_with_user_context()

        # Multi-provider comparison
        example_multi_provider_comparison()

        # Custom metadata
        example_with_custom_metadata()

        # Error handling
        example_error_handling()

        # Production setup
        example_production_setup()

        print("\n" + "=" * 70)
        print("✓ All examples completed!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Check your Langfuse dashboard at https://langfuse.com")
        print("2. View the traces for all your LLM calls")
        print("3. Analyze latency, tokens, and metadata")
        print("4. Set up alerts for slow or expensive calls")
        print("\nFor more info, see LANGFUSE_INTEGRATION.md")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n✗ Example failed: {e}")
        print("\nMake sure:")
        print("1. API keys are set as environment variables")
        print("2. Langfuse is installed: pip install 'hyperdev[langfuse]'")
        print("3. Config files exist in config_examples/")


if __name__ == "__main__":
    main()
