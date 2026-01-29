"""Configuration management for Boltz Lab client."""

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Config:
    """Handles configuration from multiple sources with XDG compliance."""

    def __init__(self):
        self._config: dict[str, Any] = {}
        self._config_path = self._get_config_path()
        self._load_config()

    def _get_config_path(self) -> Path:
        """Get the configuration file path following XDG Base Directory specification."""
        # Check XDG_CONFIG_HOME first
        xdg_config_home = os.getenv("XDG_CONFIG_HOME")
        config_dir = Path(xdg_config_home) / "boltz-lab" if xdg_config_home else Path.home() / ".config" / "boltz-lab"

        # Ensure directory exists
        config_dir.mkdir(parents=True, exist_ok=True)

        return config_dir / "config.json"

    def _load_config(self) -> None:
        """Load configuration from file if it exists."""
        if not self._config_path.exists():
            logger.debug(f"No config file found at {self._config_path}")
            return

        try:
            # Check file permissions (warn if too permissive)
            stat_info = self._config_path.stat()
            mode = stat_info.st_mode & 0o777
            if mode & 0o077:  # If group or others have any permissions
                logger.warning(f"Config file at {self._config_path} has permissive permissions ({oct(mode)}). Consider restricting with: chmod 600")

            with self._config_path.open("r") as f:
                self._config = json.load(f)
                logger.debug(f"Loaded config from {self._config_path}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {self._config_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading config from {self._config_path}: {e}")

    def get(self, key: str, default: Any | None = None) -> Any | None:
        """Get a configuration value."""
        return self._config.get(key, default)

    def get_api_key(self) -> str | None:
        """Get API key from config file."""
        return self.get("api_key")

    def get_endpoint(self) -> str | None:
        """Get API endpoint from config file."""
        return self.get("endpoint")

    def get_signup_url(self) -> str | None:
        """Get signup URL from config file."""
        return self.get("signup_url")

    def save_config(self, api_key: str | None = None, endpoint: str | None = None, signup_url: str | None = None) -> None:
        """Save configuration to file with proper permissions."""
        if api_key:
            self._config["api_key"] = api_key
        if endpoint:
            self._config["endpoint"] = endpoint
        if signup_url:
            self._config["signup_url"] = signup_url

        # Ensure directory exists
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with restricted permissions
        with self._config_path.open("w") as f:
            json.dump(self._config, f, indent=2)

        # Set restrictive permissions (user read/write only)
        self._config_path.chmod(0o600)

        logger.info(f"Config saved to {self._config_path}")

    @property
    def config_path(self) -> Path:
        """Get the configuration file path."""
        return self._config_path


# Global config instance (lazy initialization)
_config: Config | None = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config() -> None:
    """Reset the global config instance. Useful for testing."""
    global _config
    _config = None
