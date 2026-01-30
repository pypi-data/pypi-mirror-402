"""Basic usage example of HyperDev LLMRouter."""

from pathlib import Path
from hyperdev.llmrouter import chat_stream, LLMProvider


def main():
    """Demonstrate basic streaming with OpenAI."""
    # Use config from the config_examples directory
    config_dir = Path(__file__).parent.parent / "config_examples"

    print("Using OpenAI GPT-4 to explain quantum computing:\n")
    print("-" * 60)

    try:
        for chunk in chat_stream(
            prompt="Explain quantum computing in 2-3 sentences",
            llm_provider=LLMProvider.OPENAI,
            llm_string="gpt-4",
            config_dir=config_dir,
        ):
            # Stream each chunk of content
            print(chunk.content, end="", flush=True)

        print("\n" + "-" * 60)
        print("\nStreaming completed successfully!")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
