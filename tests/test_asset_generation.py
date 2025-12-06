"""Tests for AI asset generation system."""

import pytest
from pathlib import Path
from engine_modules.asset_generation import (
    AssetGenerationConfig,
    PhotorealismEvaluator,
    AssetGenerationAPI,
    AssetGenerator,
    GeneratedAsset
)


class TestAssetGenerationConfig:
    """Test asset generation configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = AssetGenerationConfig()
        assert config.max_retries == 3
        assert config.api_key is None
    
    def test_config_from_env(self, monkeypatch):
        """Test configuration from environment variables."""
        monkeypatch.setenv("MESHY_API_KEY", "test_key_123")
        config = AssetGenerationConfig.from_env()
        assert config.api_key == "test_key_123"


class TestAssetGenerator:
    """Test main asset generator."""
    
    def test_initialization(self):
        """Test generator initialization."""
        generator = AssetGenerator()
        assert generator.api is not None
        assert generator.evaluator is not None


class TestGeneratedAsset:
    """Test GeneratedAsset class."""
    
    def test_create_asset(self):
        """Test creating asset instance."""
        asset = GeneratedAsset(
            asset_id="test_123",
            model_path="/path/to/model.glb",
            texture_paths=["/path/to/albedo.png"],
            realism_score=0.95,
            generation_attempts=1,
            has_rig=True,
            metadata={"source": "meshy"}
        )
        assert asset.asset_id == "test_123"
        assert asset.realism_score == 0.95
        assert asset.has_rig is True
    
    def test_asset_to_dict(self):
        """Test converting asset to dictionary."""
        asset = GeneratedAsset(
            asset_id="test_456",
            model_path="/model.glb",
            texture_paths=["/albedo.png", "/normal.png"],
            realism_score=0.88,
            generation_attempts=2,
            has_rig=False,
            metadata={}
        )
        data = asset.to_dict()
        assert data["asset_id"] == "test_456"
        assert data["realism_score"] == 0.88
        assert data["generation_attempts"] == 2
        assert data["has_rig"] is False
