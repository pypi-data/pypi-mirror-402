"""Utility functions for HyperDev LLMRouter."""

import subprocess
import sys
from typing import Optional


def ensure_langfuse_installed(auto_install: bool = True) -> bool:
    """
    Check if langfuse is installed, and optionally install it.

    This function checks if the langfuse package is available. If not, it can
    automatically install it using pip. This is useful when users want to use
    Langfuse integration without explicitly installing the optional dependency.

    Args:
        auto_install: If True, attempt to install langfuse if not found.
                     If False, just check availability.

    Returns:
        True if langfuse is available (or was successfully installed),
        False if not available and auto_install is False.

    Raises:
        RuntimeError: If installation fails.
    """
    try:
        import langfuse  # noqa: F401
        return True
    except ImportError:
        if not auto_install:
            return False

        return _install_langfuse()


def _install_langfuse() -> bool:
    """
    Attempt to install langfuse package.

    Returns:
        True if installation succeeded, False otherwise.

    Raises:
        RuntimeError: If installation fails with a clear error message.
    """
    import os

    # Check if we're in an interactive environment
    is_interactive = sys.stdin.isatty() if hasattr(sys.stdin, "isatty") else False

    if is_interactive:
        print("\n" + "=" * 70)
        print("Langfuse integration is enabled but not installed")
        print("=" * 70)
        print("\nWould you like to install it now?")
        print("  Command: pip install langfuse")
        print("\nInstall now? (y/n): ", end="", flush=True)

        try:
            response = input().strip().lower()
            if response not in ("y", "yes"):
                raise RuntimeError(
                    "Langfuse installation cancelled by user. "
                    "Install it manually with: pip install 'hyperdev[langfuse]'"
                )
        except EOFError:
            # No input available in interactive mode
            pass

    print("\nInstalling langfuse...")

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "langfuse"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("✓ Langfuse installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to install langfuse. "
            f"Install it manually with: pip install 'hyperdev[langfuse]'\n"
            f"Error: {e}"
        ) from e


def check_langfuse_credentials(
    public_key: Optional[str] = None,
    secret_key: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """
    Check and retrieve Langfuse credentials from arguments or environment.

    Args:
        public_key: Langfuse public key (or None to check env var)
        secret_key: Langfuse secret key (or None to check env var)

    Returns:
        Tuple of (public_key, secret_key) if both are available, (None, None) otherwise.
    """
    import os

    public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")

    if public_key and secret_key:
        return public_key, secret_key

    return None, None
