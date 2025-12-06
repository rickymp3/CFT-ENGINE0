"""
Configuration management for CFT-ENGINE0.

Provides two layers:
- `Config`: validates and normalizes in-memory configuration dictionaries
- `ConfigManager`: loads/saves YAML configs and offers dot-notation access
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""


class Config:
    """Validates and normalizes configuration dictionaries."""

    REQUIRED_FIELDS = ["environment"]
    VALID_ENVIRONMENTS = ["dev", "test", "prod"]

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self._validate()
        self._normalize()

    def _validate(self) -> None:
        for field in self.REQUIRED_FIELDS:
            if field not in self.data:
                raise ConfigError(f"Missing required field: {field}")

        env = self.data.get("environment")
        if env not in self.VALID_ENVIRONMENTS:
            raise ConfigError(
                f"Invalid environment '{env}'. Must be one of: {', '.join(self.VALID_ENVIRONMENTS)}"
            )

    def _normalize(self) -> None:
        self.data.setdefault("timeout", 30)

        if "base_path" in self.data:
            self.data["base_path"] = str(Path(self.data["base_path"]).resolve())

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    @property
    def environment(self) -> str:
        return self.data["environment"]

    @property
    def timeout(self) -> int:
        return self.data["timeout"]


def load_config(data: Dict[str, Any]) -> Config:
    """Construct and validate a Config instance from a raw dict."""
    return Config(data)


class ConfigManager:
    """Manages engine configuration persisted in YAML files."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from YAML, falling back to defaults."""
        if not self.config_path.exists():
            logger.warning("Config file not found: %s. Using defaults.", self.config_path)
            self.config = self._get_defaults()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as fh:
                self.config = yaml.safe_load(fh) or {}
            logger.info("Loaded configuration from %s", self.config_path)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to load config: %s. Using defaults.", exc)
            self.config = self._get_defaults()

    def save(self) -> None:
        """Persist the current configuration to YAML."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as fh:
                yaml.dump(self.config, fh, default_flow_style=False, sort_keys=False)
            logger.info("Saved configuration to %s", self.config_path)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to save config: %s", exc)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., graphics.enable_pbr)."""
        parts = key.split(".")
        value: Any = self.config

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation."""
        parts = key.split(".")
        cursor = self.config

        for part in parts[:-1]:
            if part not in cursor or not isinstance(cursor[part], dict):
                cursor[part] = {}
            cursor = cursor[part]

        cursor[parts[-1]] = value

    def _get_defaults(self) -> Dict[str, Any]:
        """Default configuration scaffold used when no file is present."""
        return {
            "engine": {
                "window_title": "CFT AAA Engine",
                "window_width": 1280,
                "window_height": 720,
                "fullscreen": False,
                "vsync": True,
                "show_fps": True,
            },
            "localization": {
                "default_language": "en",
                "available_languages": ["en", "es", "fr"],
            },
            "graphics": {
                "enable_pbr": True,
                "enable_hdr": True,
                "enable_post_processing": True,
                "shadow_quality": "high",
                "texture_quality": "high",
                "antialiasing": "msaa_4x",
            },
            "physics": {
                "enabled": True,
                "gravity": -9.81,
                "simulation_rate": 60,
                "debug_mode": False,
            },
            "debug": {
                "show_wireframe": False,
                "show_bounds": False,
                "show_physics_shapes": False,
                "show_performance_stats": True,
                "log_level": "INFO",
            },
        }


_config: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get the global ConfigManager singleton."""
    global _config
    if _config is None:
        _config = ConfigManager()
    return _config
