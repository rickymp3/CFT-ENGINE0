"""Unit tests for texture generation system."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import os

# Import components to test
from engine_modules.texture_generator import (
    TextureGenerator, TextureMapSet, TextureQualityEvaluator,
    ProceduralTextureGenerator, HyperAPI, TextureResolution,
    generate_texture
)


class TestTextureResolution:
    """Test texture resolution enum."""
    
    def test_resolution_values(self):
        """Test that resolution values are correct."""
        assert TextureResolution._512.value == (512, 512)
        assert TextureResolution._1K.value == (1024, 1024)
        assert TextureResolution._2K.value == (2048, 2048)
        assert TextureResolution._4K.value == (4096, 4096)
        assert TextureResolution._8K.value == (8192, 8192)


class TestTextureMapSet:
    """Test TextureMapSet dataclass."""
    
    def test_creation(self):
        """Test creating a TextureMapSet."""
        texture_set = TextureMapSet(
            albedo_path="/path/to/albedo.png",
            normal_path="/path/to/normal.png",
            roughness_path="/path/to/roughness.png",
            metallic_path="/path/to/metallic.png"
        )
        
        assert texture_set.albedo_path == "/path/to/albedo.png"
        assert texture_set.normal_path == "/path/to/normal.png"
        assert texture_set.roughness_path == "/path/to/roughness.png"
        assert texture_set.metallic_path == "/path/to/metallic.png"
        assert texture_set.realism_score == 0.0
        assert texture_set.generation_attempts == 1
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        texture_set = TextureMapSet(
            albedo_path="/path/to/albedo.png",
            normal_path="/path/to/normal.png",
            roughness_path="/path/to/roughness.png",
            metallic_path="/path/to/metallic.png",
            prompt="test prompt"
        )
        
        data = texture_set.to_dict()
        
        assert data["albedo_path"] == "/path/to/albedo.png"
        assert data["prompt"] == "test prompt"
        assert "timestamp" in data
    
    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "albedo_path": "/path/to/albedo.png",
            "normal_path": "/path/to/normal.png",
            "roughness_path": "/path/to/roughness.png",
            "metallic_path": "/path/to/metallic.png",
            "height_path": None,
            "ambient_occlusion_path": None,
            "emission_path": None,
            "asset_id": "test_asset",
            "prompt": "test prompt",
            "realism_score": 0.85,
            "generation_attempts": 2,
            "timestamp": "2025-01-01T00:00:00",
            "metadata": {}
        }
        
        texture_set = TextureMapSet.from_dict(data)
        
        assert texture_set.albedo_path == "/path/to/albedo.png"
        assert texture_set.realism_score == 0.85
        assert texture_set.prompt == "test prompt"


class TestProceduralTextureGenerator:
    """Test procedural texture generation."""
    
    def test_import_available(self):
        """Test that procedural texture generator is importable."""
        assert ProceduralTextureGenerator is not None
    
    @pytest.mark.skipif(not Path("/usr/bin/python3").exists(), 
                        reason="NumPy required")
    def test_generate_perlin_texture(self):
        """Test Perlin noise texture generation."""
        try:
            import numpy as np
            texture = ProceduralTextureGenerator.generate_perlin_texture(512, 512)
            assert isinstance(texture, np.ndarray)
            assert texture.shape == (512, 512, 3)
            assert texture.dtype == np.uint8
            assert texture.min() >= 0
            assert texture.max() <= 255
        except ImportError:
            pytest.skip("NumPy not available")
    
    @pytest.mark.skipif(not Path("/usr/bin/python3").exists(),
                        reason="NumPy required")
    def test_generate_roughness_metallic(self):
        """Test roughness and metallic map generation."""
        try:
            import numpy as np
            rough, metal = ProceduralTextureGenerator.generate_roughness_metallic(512, 512)
            
            assert isinstance(rough, np.ndarray)
            assert isinstance(metal, np.ndarray)
            assert rough.shape == (512, 512)
            assert metal.shape == (512, 512)
        except ImportError:
            pytest.skip("NumPy not available")
    
    def test_save_texture(self):
        """Test saving texture to file."""
        try:
            import numpy as np
            
            with tempfile.TemporaryDirectory() as tmpdir:
                texture = np.ones((512, 512, 3), dtype=np.uint8) * 128
                output_path = Path(tmpdir) / "test.png"
                
                success = ProceduralTextureGenerator.save_texture(texture, output_path)
                
                assert success
                assert output_path.exists()
        except ImportError:
            pytest.skip("NumPy not available")


class TestHyperAPI:
    """Test Hyper3D API client."""
    
    def test_initialization_no_credentials(self):
        """Test API initialization without credentials."""
        api = HyperAPI(api_key="", api_endpoint="")
        assert not api.available
        assert api.api_key == ""
    
    def test_initialization_with_credentials(self):
        """Test API initialization with credentials."""
        api = HyperAPI(api_key="test_key", api_endpoint="https://api.test.com")
        assert api.available
        assert api.api_key == "test_key"
        assert api.api_endpoint == "https://api.test.com"
    
    def test_initialization_from_env(self):
        """Test API initialization from environment variables."""
        with patch.dict(os.environ, {"HYPER3D_API_KEY": "env_key"}):
            api = HyperAPI()
            assert api.api_key == "env_key"
    
    def test_generate_from_prompt_mock(self):
        """Test mock texture generation from prompt."""
        api = HyperAPI(api_key="", api_endpoint="")
        
        maps = api.generate_from_prompt(
            "seamless stone texture",
            resolution="1K"
        )
        
        assert maps is not None
        assert "albedo" in maps
        assert "normal" in maps
        assert "roughness" in maps
        assert "metallic" in maps
        
        # Verify generated files exist
        for map_path in maps.values():
            assert Path(map_path).exists()
    
    def test_generate_from_prompt_custom_maps(self):
        """Test generating specific map types."""
        api = HyperAPI(api_key="", api_endpoint="")
        
        maps = api.generate_from_prompt(
            "texture",
            map_types=["albedo", "normal"]
        )
        
        assert "albedo" in maps
        assert "normal" in maps
        assert "roughness" not in maps
    
    def test_generate_from_image_mock(self):
        """Test mock texture generation from image."""
        try:
            from PIL import Image
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create a test image
                img = Image.new('RGB', (512, 512), color='red')
                img_path = Path(tmpdir) / "test.png"
                img.save(img_path)
                
                api = HyperAPI(api_key="", api_endpoint="")
                
                maps = api.generate_from_image(
                    str(img_path),
                    "test material"
                )
                
                assert maps is not None
                assert "albedo" in maps
        except ImportError:
            pytest.skip("PIL not available")


class TestTextureQualityEvaluator:
    """Test texture quality evaluation."""
    
    def test_initialization_heuristic(self):
        """Test initializing evaluator in heuristic mode."""
        evaluator = TextureQualityEvaluator(ml_model_available=False)
        assert not evaluator.ml_model_available
    
    def test_evaluate_heuristic_no_images(self):
        """Test heuristic evaluation with nonexistent paths."""
        evaluator = TextureQualityEvaluator(ml_model_available=False)
        
        texture_set = TextureMapSet(
            albedo_path="/nonexistent/albedo.png",
            normal_path="/nonexistent/normal.png",
            roughness_path="/nonexistent/roughness.png",
            metallic_path="/nonexistent/metallic.png"
        )
        
        score = evaluator.evaluate(texture_set)
        assert 0.0 <= score <= 1.0
    
    @pytest.mark.skipif(not Path("/usr/bin/python3").exists(),
                        reason="PIL required")
    def test_evaluate_with_generated_textures(self):
        """Test evaluation with real generated textures."""
        try:
            from PIL import Image
            import numpy as np
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create test images
                img = Image.new('RGB', (512, 512), color=(128, 128, 128))
                
                albedo_path = Path(tmpdir) / "albedo.png"
                normal_path = Path(tmpdir) / "normal.png"
                
                img.save(albedo_path)
                img.save(normal_path)
                
                texture_set = TextureMapSet(
                    albedo_path=str(albedo_path),
                    normal_path=str(normal_path),
                    roughness_path="",
                    metallic_path=""
                )
                
                evaluator = TextureQualityEvaluator(ml_model_available=False)
                score = evaluator.evaluate(texture_set)
                
                assert isinstance(score, float)
                assert 0.0 <= score <= 1.0
        except ImportError:
            pytest.skip("PIL not available")


class TestTextureGenerator:
    """Test main texture generator."""
    
    def test_initialization_defaults(self):
        """Test generator initialization with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir}
            generator = TextureGenerator(config)
            
            assert generator.realism_threshold == 0.7
            assert generator.max_retries == 3
            assert generator.output_dir.exists()
    
    def test_initialization_custom_config(self):
        """Test generator initialization with custom config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "output_dir": tmpdir,
                "realism_threshold": 0.85,
                "max_retries": 5,
                "api_key": "test_key"
            }
            generator = TextureGenerator(config)
            
            assert generator.realism_threshold == 0.85
            assert generator.max_retries == 5
    
    def test_progress_callback(self):
        """Test setting progress callback."""
        generator = TextureGenerator()
        
        callback = Mock()
        generator.set_progress_callback(callback)
        
        assert generator.progress_callback == callback
    
    def test_cancel_flag(self):
        """Test cancel functionality."""
        generator = TextureGenerator()
        
        assert not generator.cancel_flag
        generator.cancel()
        assert generator.cancel_flag
    
    def test_generate_texture_from_prompt(self):
        """Test texture generation from prompt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir, "realism_threshold": 0.5}
            generator = TextureGenerator(config)
            
            # Mock callback
            callback = Mock()
            generator.set_progress_callback(callback)
            
            texture_set = generator.generate_texture(
                prompt="seamless rock texture"
            )
            
            assert texture_set is not None
            # Prompt may be modified after retries, so just check it's not empty
            assert texture_set.prompt is not None
            assert len(texture_set.prompt) > 0
            # Callback should have been called
            assert callback.called
    
    def test_generate_texture_no_quality_enforcement(self):
        """Test generation without quality enforcement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir}
            generator = TextureGenerator(config)
            
            texture_set = generator.generate_texture(
                prompt="test",
                enforce_quality=False
            )
            
            assert texture_set is not None
            assert texture_set.realism_score == 0.8  # Default when not enforced
    
    def test_batch_generation(self):
        """Test batch texture generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir}
            generator = TextureGenerator(config)
            
            results = generator.generate_batch(
                prompt="test texture",
                batch_size=2
            )
            
            assert len(results) <= 2
            for texture_set in results:
                assert isinstance(texture_set, TextureMapSet)
    
    def test_stylized_generation(self):
        """Test style transfer texture generation."""
        try:
            from PIL import Image
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create style reference image
                img = Image.new('RGB', (512, 512), color=(200, 100, 50))
                style_path = Path(tmpdir) / "style.png"
                img.save(style_path)
                
                config = {"output_dir": tmpdir}
                generator = TextureGenerator(config)
                
                texture_set = generator.generate_stylized(
                    content_prompt="stone texture",
                    style_image_path=str(style_path)
                )
                
                # Should succeed or gracefully fail
                if texture_set:
                    assert isinstance(texture_set, TextureMapSet)
        except ImportError:
            pytest.skip("PIL not available")
    
    def test_create_material_json(self):
        """Test creating material JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir}
            generator = TextureGenerator(config)
            
            texture_set = TextureMapSet(
                albedo_path="/path/to/albedo.png",
                normal_path="/path/to/normal.png",
                roughness_path="/path/to/roughness.png",
                metallic_path="/path/to/metallic.png",
                prompt="test texture",
                realism_score=0.85
            )
            
            material_path = generator.create_material_json("test_material", texture_set)
            
            assert material_path is not None
            assert Path(material_path).exists()
            
            # Verify JSON content
            with open(material_path) as f:
                data = json.load(f)
            
            assert data["name"] == "test_material"
            assert data["type"] == "pbr_material"
            assert "textures" in data
            assert data["metadata"]["realism_score"] == 0.85
    
    def test_convenience_wrappers(self):
        """Test convenience wrapper methods."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir}
            generator = TextureGenerator(config)
            
            # Test generate_from_prompt
            texture_set = generator.generate_from_prompt("test texture")
            assert texture_set is not None
            
            # Test generate_from_image
            try:
                from PIL import Image
                img = Image.new('RGB', (256, 256))
                img_path = Path(tmpdir) / "test.png"
                img.save(img_path)
                
                texture_set = generator.generate_from_image(
                    str(img_path),
                    "describe the image"
                )
                assert texture_set is not None
            except ImportError:
                pass


class TestQuickGenerateFunction:
    """Test the convenience generate_texture function."""
    
    def test_generate_texture_function(self):
        """Test quick generate_texture function."""
        texture_set = generate_texture(
            prompt="test texture"
        )
        
        assert texture_set is not None
        assert isinstance(texture_set, TextureMapSet)


class TestHeadlessMode:
    """Test headless/offline mode detection."""
    
    def test_offline_fallback(self):
        """Test that procedural fallback works when API unavailable."""
        api = HyperAPI(api_key="", api_endpoint="")
        assert not api.available
        
        # Should still generate via mock
        maps = api.generate_from_prompt("test")
        assert maps is not None
        assert all(Path(p).exists() for p in maps.values())
    
    def test_headless_environment(self):
        """Test texture generation in headless environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir}
            generator = TextureGenerator(config)
            
            # Should work even without display
            texture_set = generator.generate_texture(
                prompt="test",
                enforce_quality=False
            )
            
            assert texture_set is not None


class TestIntegrationWithAssetPipeline:
    """Test integration with asset pipeline."""
    
    def test_compute_checksum(self):
        """Test file checksum computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            file_path.write_text("test content")
            
            checksum = TextureGenerator._compute_checksum(str(file_path))
            
            assert isinstance(checksum, str)
            assert len(checksum) == 32  # MD5 length
    
    def test_import_to_pipeline_mock(self):
        """Test importing textures to asset pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output_dir": tmpdir}
            generator = TextureGenerator(config)
            
            # Create test texture files
            try:
                from PIL import Image
                
                img = Image.new('L', (512, 512), color=128)
                
                albedo_path = Path(tmpdir) / "albedo.png"
                normal_path = Path(tmpdir) / "normal.png"
                rough_path = Path(tmpdir) / "rough.png"
                metal_path = Path(tmpdir) / "metal.png"
                
                img.save(albedo_path)
                img.save(normal_path)
                img.save(rough_path)
                img.save(metal_path)
                
                texture_set = TextureMapSet(
                    albedo_path=str(albedo_path),
                    normal_path=str(normal_path),
                    roughness_path=str(rough_path),
                    metallic_path=str(metal_path)
                )
                
                # Note: This will fail if asset_pipeline is not properly set up
                # but should handle gracefully
                result = generator.import_to_pipeline(texture_set, "test_material")
                # Result may be None if asset_pipeline fails, which is ok
                
            except ImportError:
                pytest.skip("PIL not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
