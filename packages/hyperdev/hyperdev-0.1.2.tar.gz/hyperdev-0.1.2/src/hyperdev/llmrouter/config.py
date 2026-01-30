"""Configuration management for LLMRouter."""

import os
import json
from pathlib import Path
from typing import Optional

from .enums import LLMProvider
from .types import ProviderConfig
from .exceptions import ConfigurationError


class ConfigLoader:
    """Loads and manages provider configurations from JSON files."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize ConfigLoader.

        Args:
            config_dir: Directory containing config files. Defaults to current working directory.
        """
        self.config_dir = config_dir or Path.cwd()
        if not self.config_dir.is_dir():
            raise ConfigurationError(f"Config directory does not exist: {self.config_dir}")

    def load_config(self, provider: LLMProvider) -> ProviderConfig:
        """
        Load configuration for a provider from JSON file.

        Args:
            provider: The LLMProvider enum value

        Returns:
            ProviderConfig with loaded configuration

        Raises:
            ConfigurationError: If config file not found or invalid
        """
        config_file = self.config_dir / f"{provider}_chat_config.json"

        if not config_file.exists():
            raise ConfigurationError(
                f"Config file not found: {config_file}. "
                f"Expected file: {provider}_chat_config.json"
            )

        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in {config_file}: {e}")
        except IOError as e:
            raise ConfigurationError(f"Error reading {config_file}: {e}")

        try:
            config = ProviderConfig(**config_data)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration in {config_file}: {e}")

        return config

    def get_api_key(self, env_var: str) -> str:
        """
        Get API key from environment variable.

        Args:
            env_var: Name of the environment variable

        Returns:
            The API key value

        Raises:
            ConfigurationError: If environment variable not set
        """
        api_key = os.getenv(env_var)
        if not api_key:
            raise ConfigurationError(
                f"Environment variable '{env_var}' not set. "
                f"Please set it before using the chat_stream function."
            )
        return api_key
