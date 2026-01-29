"""Config loader service for parsing app configuration."""

import os
from pathlib import Path
from typing import Optional

import yaml

from ..models.config import AppConfig


class ConfigLoader:
    """Service to load app configuration from YAML file."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the config loader.

        Args:
            config_path: Path to config.yaml. If None, searches in order:
                1. PYSHALA_CONFIG env var
                2. config.yaml in lessons directory
                3. config.yaml in current directory
        """
        self._config: Optional[AppConfig] = None
        self._config_path = self._resolve_config_path(config_path)

    def _resolve_config_path(self, config_path: Optional[str]) -> Optional[Path]:
        """Resolve the config file path."""
        # 1. Explicit path provided
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path

        # 2. Environment variable
        env_path = os.getenv("PYSHALA_CONFIG")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path

        # 3. Config in lessons directory
        lessons_path = os.getenv("LESSONS_PATH")
        if lessons_path:
            path = Path(lessons_path) / "config.yaml"
            if path.exists():
                return path

        # 4. Config in current directory
        path = Path("config.yaml")
        if path.exists():
            return path

        # 5. Config in lessons/ subdirectory
        path = Path("lessons") / "config.yaml"
        if path.exists():
            return path

        return None

    def load(self) -> AppConfig:
        """Load the configuration.

        Returns:
            AppConfig object with loaded or default values.
        """
        if self._config is not None:
            return self._config

        if self._config_path and self._config_path.exists():
            try:
                with open(self._config_path) as f:
                    data = yaml.safe_load(f) or {}
                self._config = AppConfig.from_dict(data)
            except (OSError, yaml.YAMLError):
                self._config = AppConfig()
        else:
            self._config = AppConfig()

        return self._config

    def get_config(self) -> AppConfig:
        """Get the current configuration (loads if needed).

        Returns:
            AppConfig object.
        """
        if self._config is None:
            return self.load()
        return self._config

    def reload(self) -> AppConfig:
        """Force reload the configuration.

        Returns:
            AppConfig object with reloaded values.
        """
        self._config = None
        return self.load()


# Global config loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """Get the global config loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
        _config_loader.load()
    return _config_loader


def get_app_config() -> AppConfig:
    """Get the app configuration.

    Returns:
        AppConfig object.
    """
    return get_config_loader().get_config()
