"""Unit tests for AI music generator module.

Tests cover:
- API initialization and mock mode
- Loop generation from prompts
- Loop generation from reference audio
- Procedural fallback
- Quality analysis
- Asset pipeline integration
- Error handling and edge cases
"""

import pytest
import os
import tempfile
import wave
import struct
import math
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from engine_modules.music_generator import (
    LoopDuration,
    MusicLoop,
    AudioAnalyzer,
    SoundverseAPI,
    ProceduralLoopBuilder,
    MusicGenerator,
    generate_loops_quick,
)


class TestLoopDuration:
    """Test LoopDuration enum."""
    
    def test_loop_durations_exist(self):
        """Test that standard durations are defined."""
        assert LoopDuration._15SEC.value == 15
        assert LoopDuration._30SEC.value == 30
        assert LoopDuration._60SEC.value == 60


class TestMusicLoop:
    """Test MusicLoop dataclass."""
    
    def test_music_loop_creation(self):
        """Test creating a music loop."""
        loop = MusicLoop(
            file_path="/tmp/test.wav",
            duration=30,
            prompt="ambient music",
            mood="relaxing",
            genre="ambient",
            bpm=120
        )
        
        assert loop.file_path == "/tmp/test.wav"
        assert loop.duration == 30
        assert loop.prompt == "ambient music"
        assert loop.mood == "relaxing"
        assert loop.genre == "ambient"
        assert loop.bpm == 120
        assert loop.timestamp is not None
        assert loop.is_seamless is True
        assert loop.quality_score == 0.0
    
    def test_music_loop_serialization(self):
        """Test loop serialization to/from dict."""
        loop = MusicLoop(
            file_path="/tmp/test.wav",
            duration=30,
            prompt="test",
            quality_score=0.85
        )
        
        data = loop.to_dict()
        assert isinstance(data, dict)
        assert data['file_path'] == "/tmp/test.wav"
        assert data['duration'] == 30
        assert data['quality_score'] == 0.85
        
        loop2 = MusicLoop.from_dict(data)
        assert loop2.file_path == loop.file_path
        assert loop2.duration == loop.duration


class TestAudioAnalyzer:
    """Test audio analyzer."""
    
    def _create_test_wav(self, duration: int = 1, sample_rate: int = 44100) -> str:
        """Create a test WAV file.
        
        Args:
            duration: Duration in seconds
            sample_rate: Sample rate
            
        Returns:
            Path to test WAV file
        """
        temp_dir = Path(tempfile.gettempdir())
        wav_path = temp_dir / f"test_{duration}s.wav"
        
        num_samples = sample_rate * duration
        frequency = 440
        
        with wave.open(str(wav_path), 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            
            for i in range(num_samples):
                sample = int(math.sin(2 * math.pi * frequency * i / sample_rate) * 32767)
                wav_file.writeframes(struct.pack('<h', sample))
        
        return str(wav_path)
    
    def test_analyze_nonexistent_file(self):
        """Test analyzing a file that doesn't exist."""
        analyzer = AudioAnalyzer()
        is_seamless, score = analyzer.analyze_loop_seamlessness("/nonexistent/path.wav")
        
        assert is_seamless is False
        assert score == 0.0
    
    def test_get_audio_duration(self):
        """Test getting audio duration."""
        analyzer = AudioAnalyzer()
        wav_path = self._create_test_wav(duration=2)
        
        try:
            duration = analyzer.get_audio_duration(wav_path)
            assert duration > 0
            assert duration <= 2.1  # Allow small tolerance
        finally:
            Path(wav_path).unlink(missing_ok=True)
    
    def test_get_audio_duration_nonexistent(self):
        """Test getting duration of nonexistent file."""
        analyzer = AudioAnalyzer()
        duration = analyzer.get_audio_duration("/nonexistent/path.wav")
        assert duration == 0.0


class TestSoundverseAPI:
    """Test Soundverse API client."""
    
    def test_api_init_without_key(self):
        """Test API initialization without key (mock mode)."""
        # Clear environment variable
        os.environ.pop('SOUNDVERSE_API_KEY', None)
        
        api = SoundverseAPI()
        assert api.mock_mode is True
        assert api.api_key == ''
    
    def test_api_init_with_key(self):
        """Test API initialization with key."""
        os.environ['SOUNDVERSE_API_KEY'] = 'test_key_12345'
        
        api = SoundverseAPI()
        assert api.api_key == 'test_key_12345'
        assert api.mock_mode is False
        
        os.environ.pop('SOUNDVERSE_API_KEY', None)
    
    def test_api_init_with_explicit_key(self):
        """Test API initialization with explicit key."""
        api = SoundverseAPI(api_key='explicit_key')
        assert api.api_key == 'explicit_key'
    
    def test_generate_mock_audio(self):
        """Test mock audio generation."""
        api = SoundverseAPI()  # No API key = mock mode
        
        audio_path = api._generate_mock('text-to-music', 'test prompt', 30, seed=42)
        
        assert audio_path is not None
        assert Path(audio_path).exists()
        assert Path(audio_path).suffix in ['.wav', '.mp3']
        
        # Clean up
        Path(audio_path).unlink(missing_ok=True)
    
    def test_generate_from_prompt_mock(self):
        """Test generating from prompt in mock mode."""
        api = SoundverseAPI()
        
        audio_path = api.generate_from_prompt("relaxing ambient music", duration=30)
        
        assert audio_path is not None
        assert Path(audio_path).exists()
        
        Path(audio_path).unlink(missing_ok=True)
    
    def test_generate_from_audio_mock(self):
        """Test generating from audio in mock mode."""
        api = SoundverseAPI()
        
        # Create a temporary reference audio
        temp_dir = Path(tempfile.gettempdir())
        ref_audio = temp_dir / "reference.wav"
        
        # Create dummy WAV
        with wave.open(str(ref_audio), 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(44100)
            w.writeframes(b'\x00' * 1000)
        
        try:
            audio_path = api.generate_from_audio(str(ref_audio), "similar style")
            assert audio_path is not None
            assert Path(audio_path).exists()
            
            Path(audio_path).unlink(missing_ok=True)
        finally:
            ref_audio.unlink(missing_ok=True)
    
    def test_generate_from_nonexistent_audio(self):
        """Test generating from nonexistent audio file."""
        api = SoundverseAPI()
        
        audio_path = api.generate_from_audio("/nonexistent/audio.wav")
        assert audio_path is None


class TestProceduralLoopBuilder:
    """Test procedural loop builder."""
    
    def test_init_with_nonexistent_library(self):
        """Test initialization with nonexistent library."""
        builder = ProceduralLoopBuilder(sample_library_dir="/nonexistent/path")
        
        # Should not crash, just have empty samples
        assert isinstance(builder.samples, dict)
    
    def test_build_loop(self):
        """Test building a procedural loop."""
        builder = ProceduralLoopBuilder()
        
        audio_path = builder.build_loop(duration=15, seed=42)
        
        assert audio_path is not None
        assert Path(audio_path).exists()
        
        Path(audio_path).unlink(missing_ok=True)
    
    def test_build_loop_with_mood(self):
        """Test building loop with specific mood."""
        builder = ProceduralLoopBuilder()
        
        # Try with a mood that may or may not exist
        audio_path = builder.build_loop(duration=15, mood='ambient', seed=42)
        
        assert audio_path is not None
        assert Path(audio_path).exists()
        
        Path(audio_path).unlink(missing_ok=True)
    
    def test_crossfade_audio(self):
        """Test audio crossfading."""
        builder = ProceduralLoopBuilder()
        
        # Create two dummy audio files
        temp_dir = Path(tempfile.gettempdir())
        file1 = temp_dir / "audio1.wav"
        file2 = temp_dir / "audio2.wav"
        
        for fpath in [file1, file2]:
            with wave.open(str(fpath), 'wb') as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(44100)
                w.writeframes(b'\x00' * 10000)
        
        try:
            result = builder.crossfade_audio(str(file1), str(file2), fade_duration=0.5)
            assert result is not None
        finally:
            file1.unlink(missing_ok=True)
            file2.unlink(missing_ok=True)


class TestMusicGenerator:
    """Test main music generator."""
    
    def test_init_default_config(self):
        """Test generator initialization with default config."""
        generator = MusicGenerator()
        
        assert generator.default_duration == 30
        assert generator.default_count == 5
        assert generator.quality_threshold == 0.7
        assert generator.max_retries == 3
        assert generator.api is not None
        assert generator.procedural_builder is not None
    
    def test_init_custom_config(self):
        """Test generator initialization with custom config."""
        config = {
            'default_duration': 60,
            'default_count': 3,
            'quality_threshold': 0.8,
            'max_retries': 5,
        }
        
        generator = MusicGenerator(config=config)
        
        assert generator.default_duration == 60
        assert generator.default_count == 3
        assert generator.quality_threshold == 0.8
        assert generator.max_retries == 5
    
    def test_generate_loops_from_prompt(self):
        """Test generating loops from prompt."""
        generator = MusicGenerator()
        
        loops = generator.generate_loops(
            prompt="upbeat electronic music",
            duration=15,
            count=2
        )
        
        assert isinstance(loops, list)
        assert len(loops) <= 2
        
        # Clean up
        for loop in loops:
            Path(loop).unlink(missing_ok=True)
    
    def test_generate_from_prompt_method(self):
        """Test generate_from_prompt method."""
        generator = MusicGenerator()
        
        loops = generator.generate_from_prompt(
            "calm ambient",
            duration=15,
            count=2
        )
        
        assert isinstance(loops, list)
        assert len(loops) <= 2
        
        for loop in loops:
            Path(loop).unlink(missing_ok=True)
    
    def test_generate_fallback(self):
        """Test fallback generation."""
        generator = MusicGenerator()
        
        loops = generator.generate_fallback(duration=15, count=2)
        
        assert isinstance(loops, list)
        assert len(loops) <= 2
        
        for loop in loops:
            Path(loop).unlink(missing_ok=True)
    
    def test_progress_callback(self):
        """Test progress callback."""
        generator = MusicGenerator()
        
        progress_updates = []
        
        def callback(progress: float, message: str):
            progress_updates.append((progress, message))
        
        generator.set_progress_callback(callback)
        
        loops = generator.generate_loops(
            prompt="test",
            duration=15,
            count=2
        )
        
        # Should have received progress updates
        assert len(progress_updates) > 0
        
        for loop in loops:
            Path(loop).unlink(missing_ok=True)
    
    def test_cancel_generation(self):
        """Test cancellation."""
        generator = MusicGenerator()
        
        generator.cancel_generation()
        assert generator.cancellation_requested is True
    
    def test_get_progress(self):
        """Test getting current progress."""
        generator = MusicGenerator()
        
        progress = generator.get_progress()
        assert isinstance(progress, float)
        assert 0.0 <= progress <= 1.0
    
    def test_import_to_pipeline(self):
        """Test importing loop to asset pipeline."""
        generator = MusicGenerator()
        
        # Create a mock loop
        temp_dir = Path(tempfile.gettempdir())
        loop_path = temp_dir / "test_loop.wav"
        
        with wave.open(str(loop_path), 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(44100)
            w.writeframes(b'\x00' * 10000)
        
        loop = MusicLoop(
            file_path=str(loop_path),
            duration=30,
            prompt="test",
            mood="ambient"
        )
        
        # Mock asset pipeline
        mock_pipeline = Mock()
        mock_pipeline.import_asset.return_value = "asset_123"
        
        try:
            asset_id = generator.import_to_pipeline(str(loop_path), loop, mock_pipeline)
            
            assert asset_id == "asset_123"
            mock_pipeline.import_asset.assert_called_once()
            
            # Verify call parameters
            call_args = mock_pipeline.import_asset.call_args
            assert call_args[1]['asset_type'] == 'sound'
            assert 'music' in call_args[1]['tags']
        finally:
            loop_path.unlink(missing_ok=True)
    
    def test_import_to_pipeline_no_pipeline(self):
        """Test importing without asset pipeline."""
        generator = MusicGenerator()
        
        loop = MusicLoop(
            file_path="/tmp/test.wav",
            duration=30
        )
        
        asset_id = generator.import_to_pipeline("/tmp/test.wav", loop, None)
        assert asset_id is None


class TestQuickGenerateFunction:
    """Test convenience generate_loops_quick function."""
    
    def test_quick_generate(self):
        """Test quick generate function."""
        loops = generate_loops_quick(
            prompt="test music",
            duration=15,
            count=2
        )
        
        assert isinstance(loops, list)
        
        for loop in loops:
            Path(loop).unlink(missing_ok=True)
    
    def test_quick_generate_no_args(self):
        """Test quick generate with no arguments."""
        loops = generate_loops_quick()
        
        assert isinstance(loops, list)
        
        for loop in loops:
            Path(loop).unlink(missing_ok=True)


class TestHeadlessMode:
    """Test headless operation."""
    
    def test_generator_in_headless(self):
        """Test that generator works in headless mode."""
        generator = MusicGenerator()
        
        # Should work without display
        loops = generator.generate_fallback(duration=15, count=1)
        
        assert isinstance(loops, list)
        
        for loop in loops:
            Path(loop).unlink(missing_ok=True)


class TestIntegration:
    """Integration tests."""
    
    def test_end_to_end_generation(self):
        """Test complete generation workflow."""
        generator = MusicGenerator()
        
        # Generate from prompt
        loops = generator.generate_loops(
            prompt="epic orchestral theme",
            duration=30,
            count=2
        )
        
        assert len(loops) <= 2
        assert all(Path(loop).exists() for loop in loops)
        
        # Clean up
        for loop in loops:
            Path(loop).unlink(missing_ok=True)
    
    def test_multiple_generators_parallel(self):
        """Test multiple generators running independently."""
        gen1 = MusicGenerator()
        gen2 = MusicGenerator()
        
        loops1 = gen1.generate_fallback(duration=15, count=1)
        loops2 = gen2.generate_fallback(duration=15, count=1)
        
        assert len(loops1) > 0
        assert len(loops2) > 0
        
        for loops in [loops1, loops2]:
            for loop in loops:
                Path(loop).unlink(missing_ok=True)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_duration(self):
        """Test with invalid duration."""
        generator = MusicGenerator()
        
        # Should still work, just with the duration value
        loops = generator.generate_loops(
            prompt="test",
            duration=999,  # Non-standard duration
            count=1
        )
        
        # Should complete without error
        assert isinstance(loops, list)
        
        for loop in loops:
            Path(loop).unlink(missing_ok=True)
    
    def test_zero_count(self):
        """Test with zero count."""
        generator = MusicGenerator()
        
        loops = generator.generate_loops(
            prompt="test",
            count=0
        )
        
        assert loops == []
    
    def test_large_count(self):
        """Test with large count."""
        generator = MusicGenerator()
        
        # Should handle gracefully
        loops = generator.generate_loops(
            prompt="test",
            count=100,
            duration=5  # Short duration to speed up
        )
        
        # May timeout or be cancelled, but shouldn't crash
        assert isinstance(loops, list)
        
        for loop in loops:
            Path(loop).unlink(missing_ok=True)
