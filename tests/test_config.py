"""Tests for configuration management."""

import pytest
from pathlib import Path
from engine_modules.config import Config, ConfigError, load_config


class TestConfig:
    """Test suite for Config class."""
    
    def test_valid_minimal_config(self):
        """Minimal valid config should load successfully."""
        config = Config({"environment": "dev"})
        assert config.environment == "dev"
        assert config.timeout == 30  # default
    
    def test_valid_full_config(self):
        """Full config with all fields should load."""
        data = {
            "environment": "prod",
            "timeout": 60,
            "base_path": "."
        }
        config = Config(data)
        assert config.environment == "prod"
        assert config.timeout == 60
        assert Path(config.get("base_path")).is_absolute()
    
    def test_missing_required_field_raises_error(self):
        """Missing required field should raise ConfigError."""
        with pytest.raises(ConfigError, match="Missing required field: environment"):
            Config({})
    
    def test_invalid_environment_raises_error(self):
        """Invalid environment value should raise ConfigError."""
        with pytest.raises(ConfigError, match="Invalid environment 'invalid'"):
            Config({"environment": "invalid"})
    
    def test_valid_environments(self):
        """All valid environments should be accepted."""
        for env in ["dev", "test", "prod"]:
            config = Config({"environment": env})
            assert config.environment == env
    
    def test_get_existing_key(self):
        """get() should return value for existing key."""
        config = Config({"environment": "dev", "custom": "value"})
        assert config.get("custom") == "value"
    
    def test_get_missing_key_returns_default(self):
        """get() should return default for missing key."""
        config = Config({"environment": "dev"})
        assert config.get("missing", "default") == "default"
    
    def test_load_config_function(self):
        """load_config helper should create Config instance."""
        config = load_config({"environment": "test"})
        assert isinstance(config, Config)
        assert config.environment == "test"
    
    def test_path_normalization(self):
        """Relative paths should be normalized to absolute."""
        config = Config({"environment": "dev", "base_path": "."})
        base_path = config.get("base_path")
        assert Path(base_path).is_absolute()
