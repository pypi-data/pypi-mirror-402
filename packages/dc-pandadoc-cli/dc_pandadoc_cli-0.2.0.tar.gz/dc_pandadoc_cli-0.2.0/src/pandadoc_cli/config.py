"""Configuration management for PandaDoc CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

import tomli_w
from dotenv import load_dotenv


@dataclass
class CopperConfig:
    """Copper CRM configuration."""

    api_key: str = ""
    user_email: str = ""


@dataclass
class Config:
    """Application configuration."""

    pandadoc_api_key: str = ""
    copper: CopperConfig = field(default_factory=CopperConfig)
    mapping: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls) -> Config:
        """Load configuration from env vars and config files."""
        # Load .env files
        load_dotenv()
        if Path(".env").exists():
            load_dotenv(".env")

        config = cls()

        # Load from config files (lowest to highest precedence)
        for config_path in cls._config_paths():
            if config_path.exists():
                config._merge_from_file(config_path)

        # Environment variables override config files
        config._apply_env_overrides()

        return config

    @classmethod
    def _config_paths(cls) -> list[Path]:
        """Return config file paths in order of precedence (lowest first)."""
        paths = []

        # System config (lowest)
        if os.name != "nt":
            paths.append(Path("/etc/pandadoc/config.toml"))

        # XDG user config
        xdg_config = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        paths.append(Path(xdg_config) / "pandadoc" / "config.toml")

        # Legacy user config
        paths.append(Path.home() / ".pandadoc.toml")

        # Project-local config (highest file precedence)
        paths.append(Path(".pandadoc.toml"))

        return paths

    @classmethod
    def user_config_path(cls) -> Path:
        """Return the user config file path."""
        xdg_config = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(xdg_config) / "pandadoc" / "config.toml"

    def _merge_from_file(self, path: Path) -> None:
        """Merge configuration from a TOML file."""
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except Exception:
            return

        # PandaDoc section
        pandadoc = data.get("pandadoc", {})
        if api_key := pandadoc.get("api_key"):
            self.pandadoc_api_key = api_key

        # Copper section
        copper = data.get("copper", {})
        if api_key := copper.get("api_key"):
            self.copper.api_key = api_key
        if user_email := copper.get("user_email"):
            self.copper.user_email = user_email

        # Mapping section
        mapping = data.get("mapping", {})
        if mapping:
            self.mapping.update(mapping)

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        if api_key := os.environ.get("PANDADOC_API_KEY"):
            self.pandadoc_api_key = api_key
        if api_key := os.environ.get("COPPER_API_KEY"):
            self.copper.api_key = api_key
        if user_email := os.environ.get("COPPER_USER_EMAIL"):
            self.copper.user_email = user_email

    def save(self, path: Path | None = None) -> None:
        """Save configuration to a TOML file."""
        if path is None:
            path = self.user_config_path()

        path.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, Any] = {}

        if self.pandadoc_api_key:
            data["pandadoc"] = {"api_key": self.pandadoc_api_key}

        if self.copper.api_key or self.copper.user_email:
            data["copper"] = {}
            if self.copper.api_key:
                data["copper"]["api_key"] = self.copper.api_key
            if self.copper.user_email:
                data["copper"]["user_email"] = self.copper.user_email

        if self.mapping:
            data["mapping"] = self.mapping

        with open(path, "wb") as f:
            tomli_w.dump(data, f)

    def validate_pandadoc(self) -> None:
        """Raise if PandaDoc is not configured."""
        if not self.pandadoc_api_key:
            raise ConfigError(
                "PANDADOC_API_KEY not set. Run 'pandadoc config init' or set environment variable."
            )

    def validate_copper(self) -> None:
        """Raise if Copper is not configured."""
        if not self.copper.api_key:
            raise ConfigError(
                "COPPER_API_KEY not set. Run 'pandadoc config init' or set environment variable."
            )
        if not self.copper.user_email:
            raise ConfigError(
                "COPPER_USER_EMAIL not set. Run 'pandadoc config init' or set environment variable."
            )


class ConfigError(Exception):
    """Configuration error."""

    pass


# Global config instance (lazy-loaded)
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reset_config() -> None:
    """Reset the global configuration (for testing)."""
    global _config
    _config = None
