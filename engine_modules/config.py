"""Configuration manager for the CFT Engine."""
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages engine configuration from YAML files."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}. Using defaults.")
            self.config = self._get_defaults()
            return
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}. Using defaults.")
            self.config = self._get_defaults()
    
    def save(self) -> None:
        """Save current configuration to YAML file."""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'graphics.enable_pbr')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "engine": {
                "window_title": "CFT AAA Engine",
                "window_width": 1280,
                "window_height": 720,
                "fullscreen": False,
                "vsync": True,
                "show_fps": True
            },
            "localization": {
                "default_language": "en",
                "available_languages": ["en", "es", "fr"]
            },
            "graphics": {
                "enable_pbr": True,
                "enable_hdr": True,
                "enable_post_processing": True,
                "shadow_quality": "high",
                "texture_quality": "high",
                "antialiasing": "msaa_4x"
            },
            "physics": {
                "enabled": True,
                "gravity": -9.81,
                "simulation_rate": 60,
                "debug_mode": False
            },
            "debug": {
                "show_wireframe": False,
                "show_bounds": False,
                "show_physics_shapes": False,
                "show_performance_stats": True,
                "log_level": "INFO"
            }
        }


# Global configuration instance
_config: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get the global configuration manager instance.
    
    Returns:
        ConfigManager singleton instance
    """
    global _config
    if _config is None:
        _config = ConfigManager()
    return _config
