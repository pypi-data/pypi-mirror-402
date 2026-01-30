"""Langfuse integration for LLM tracing and analytics."""

from typing import Optional, Dict, Any, Iterator
import time
from datetime import datetime

from ..types import StreamChunk
from ..exceptions import LLMRouterError


class LangfuseIntegration:
    """Integration with Langfuse for LLM tracing and analytics."""

    def __init__(
        self,
        public_key: str,
        secret_key: str,
        base_url: Optional[str] = None,
    ):
        """
        Initialize Langfuse integration.

        Args:
            public_key: Langfuse public API key
            secret_key: Langfuse secret API key
            base_url: Optional custom Langfuse base URL
        """
        try:
            from langfuse import Langfuse
        except ImportError:
            raise ImportError(
                "langfuse is not installed. Install it with: pip install langfuse"
            )

        self.public_key = public_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            base_url=base_url,
        )
        self.enabled = True

    def start_trace(
        self,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[list] = None,
    ):
        """
        Start a new trace in Langfuse.

        Args:
            name: Name of the trace
            user_id: Optional user identifier
            session_id: Optional session identifier
            metadata: Optional metadata dictionary
            tags: Optional list of tags

        Returns:
            Trace object from Langfuse
        """
        return self.client.trace(
            name=name,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata,
            tags=tags,
        )

    def start_span(
        self,
        trace,
        name: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        level: str = "DEFAULT",
    ):
        """
        Start a span within a trace.

        Args:
            trace: Parent trace object
            name: Name of the span
            input_data: Optional input data
            metadata: Optional metadata
            level: Log level (DEFAULT, DEBUG, INFO, WARNING, ERROR)

        Returns:
            Span object from Langfuse
        """
        return trace.span(
            name=name,
            input=input_data,
            metadata=metadata,
            level=level,
        )

    def log_generation(
        self,
        trace,
        name: str,
        model: str,
        provider: str,
        input_text: str,
        output_text: str,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None,
        latency_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a generation (LLM call) to Langfuse.

        Args:
            trace: Parent trace object
            name: Name of the generation
            model: Model name used
            provider: Provider name
            input_text: Input/prompt text
            output_text: Generated output text
            tokens_in: Optional input token count
            tokens_out: Optional output token count
            latency_ms: Optional latency in milliseconds
            metadata: Optional additional metadata
        """
        generation_metadata = {
            "model": model,
            "provider": provider,
            **(metadata or {}),
        }

        return trace.generation(
            name=name,
            model=model,
            input=input_text,
            output=output_text,
            usage={
                "input": tokens_in,
                "output": tokens_out,
            } if tokens_in or tokens_out else None,
            end_time=datetime.utcnow(),
            metadata=generation_metadata,
        )

    def end_trace(self, trace):
        """
        End a trace in Langfuse.

        Args:
            trace: Trace object to end
        """
        trace.end()

    def flush(self):
        """Flush any pending events to Langfuse."""
        self.client.flush()

    def close(self):
        """Close the Langfuse client."""
        try:
            self.client.flush()
        except Exception:
            pass


def get_langfuse_client(
    public_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Optional[LangfuseIntegration]:
    """
    Get a Langfuse integration client.

    Args:
        public_key: Langfuse public key (can use env var LANGFUSE_PUBLIC_KEY)
        secret_key: Langfuse secret key (can use env var LANGFUSE_SECRET_KEY)
        base_url: Optional custom Langfuse URL

    Returns:
        LangfuseIntegration instance or None if keys not provided

    Raises:
        ImportError: If langfuse package not installed
    """
    import os

    # Get keys from arguments or environment
    public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        return None

    return LangfuseIntegration(
        public_key=public_key,
        secret_key=secret_key,
        base_url=base_url,
    )


class LangfuseStreamWrapper:
    """Wrapper for streaming responses with Langfuse tracing."""

    def __init__(
        self,
        stream: Iterator[StreamChunk],
        langfuse: Optional[LangfuseIntegration],
        trace,
        span,
        model: str,
        provider: str,
        input_text: str,
    ):
        """
        Initialize stream wrapper.

        Args:
            stream: Original stream iterator
            langfuse: LangfuseIntegration instance
            trace: Langfuse trace object
            span: Langfuse span object
            model: Model identifier
            provider: Provider name
            input_text: Original input text
        """
        self.stream = stream
        self.langfuse = langfuse
        self.trace = trace
        self.span = span
        self.model = model
        self.provider = provider
        self.input_text = input_text
        self.accumulated_output = ""
        self.start_time = time.time()
        self.token_count = 0

    def __iter__(self):
        """Iterate through stream chunks."""
        return self

    def __next__(self) -> StreamChunk:
        """Get next chunk from stream."""
        try:
            chunk = next(self.stream)
            self.accumulated_output += chunk.content
            self.token_count += 1

            return chunk
        except StopIteration:
            # Stream ended, log to Langfuse if available
            if self.langfuse:
                try:
                    latency_ms = (time.time() - self.start_time) * 1000
                    self.langfuse.log_generation(
                        self.trace,
                        name=f"{self.provider.upper()} Generation",
                        model=self.model,
                        provider=self.provider,
                        input_text=self.input_text,
                        output_text=self.accumulated_output,
                        tokens_out=self.token_count,
                        latency_ms=latency_ms,
                    )
                except Exception as e:
                    # Don't fail the stream if Langfuse logging fails
                    pass

                # End span and trace
                if self.span:
                    try:
                        self.span.end()
                    except Exception:
                        pass

                if self.trace:
                    try:
                        self.langfuse.end_trace(self.trace)
                    except Exception:
                        pass

            raise
