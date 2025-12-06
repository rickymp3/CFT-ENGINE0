# Music Generator Guide

**CFT-ENGINE0 AI Music Generator v1.0**

Comprehensive documentation for generating seamless loopable music tracks using AI-powered and procedural methods.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation & Setup](#installation--setup)
3. [Core Features](#core-features)
4. [Python API Reference](#python-api-reference)
5. [CLI Usage](#cli-usage)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)
8. [Performance Benchmarks](#performance-benchmarks)
9. [Examples](#examples)
10. [Advanced Usage](#advanced-usage)

---

## Quick Start

### Basic Text-to-Music Generation

Generate 5 loopable music tracks from a text description in 30 seconds:

```python
from engine_modules.music_generator import generate_loops_quick

# Simple one-liner
loops = generate_loops_quick(
    prompt="upbeat electronic dance music, 128 BPM, energetic vibes"
)

# loops is a list of file paths to generated audio files
for loop in loops:
    print(f"Generated: {loop}")
```

### Generate from Reference Audio

Create variations based on an existing audio sample:

```python
loops = generate_loops_quick(
    ref_audio_path="path/to/reference.wav",
    description="similar mood but with more bass",
    count=3
)
```

### Using the Editor UI (v1.1)

1. Open CFT Engine Editor
2. Click **🎵 Generate Music** in the Creative Hub
3. Enter music description (e.g., "ambient space theme, calm, atmospheric")
4. Select loop duration (15, 30, or 60 seconds)
5. Click **Generate** and wait for completion
6. Loops appear in Asset Library automatically

---

## Installation & Setup

### Prerequisites

- Python 3.8+
- CFT-ENGINE0 engine installed
- Optional: `requests` library for cloud API support
- Optional: `numpy` for advanced audio analysis

### Environment Variables

To use the Soundverse API for cloud generation, set these environment variables:

```bash
export SOUNDVERSE_API_KEY="your_api_key_here"
export SOUNDVERSE_ENDPOINT="https://api.soundverse.ai/v1"
```

Or configure in your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
# ~/.bashrc or ~/.zshrc
export SOUNDVERSE_API_KEY="your_api_key_here"
```

### Offline Mode (No API Key Required)

The music generator works entirely offline using procedural generation from sample libraries:

```bash
# No environment variables needed - uses samples/sounds automatically
python script.py
```

### Installing with pip

```bash
# Core requirements (already included)
pip install -r requirements.txt

# Optional: for advanced audio analysis
pip install numpy

# Optional: for cloud API support
pip install requests
```

---

## Core Features

### 1. Text-to-Music Generation

Create loopable tracks from natural language descriptions:

```python
generator = MusicGenerator()

loops = generator.generate_from_prompt(
    prompt="lo-fi hip-hop beat, chill, jazzy samples, 90 BPM",
    duration=30,
    count=5
)
```

**Supported Descriptions:**
- Mood/genre: "ambient", "energetic", "melancholic", "epic"
- Tempo: "slow" (60-90 BPM), "medium" (90-120 BPM), "fast" (120+ BPM)
- Instrumentation: "orchestral", "synth", "acoustic", "electronic"
- Style: "cinematic", "retro", "modern", "experimental"

### 2. Audio-to-Music Generation

Generate new tracks inspired by reference audio:

```python
loops = generator.generate_from_audio(
    ref_audio_path="my_track.wav",
    description="similar vibe but with faster tempo",
    duration=30,
    count=3
)
```

The API analyzes the reference audio and creates variations with similar characteristics.

### 3. Batch Generation

Create multiple variations in a single call:

```python
loops = generator.generate_loops(
    prompt="space ambient background music",
    duration=60,
    count=10  # Generate 10 variations
)
```

Each variation receives a different seed and slight prompt modifications:
- Variation 1: Original prompt
- Variation 2-10: Original prompt + "variation N"

### 4. Quality Control & Auto-Retry

The generator automatically evaluates loop seamlessness and retries if needed:

```python
generator = MusicGenerator(config={
    'quality_threshold': 0.8,  # High quality required
    'max_retries': 5           # Up to 5 attempts
})

# If first generation scores < 0.8, automatically regenerates with modified prompt
loops = generator.generate_loops(prompt="test music")
```

### 5. Offline Procedural Fallback

When the API is unavailable, generates loops from sample libraries:

```python
# No API key? Uses procedural generation automatically
generator = MusicGenerator()
loops = generator.generate_fallback(
    duration=30,
    count=5
)

# Samples stitched from: assets/sounds/ambience/, assets/sounds/sfx/, etc.
```

### 6. Loop Duration Control

Specify the length of each generated loop:

```python
# Short loops for gameplay SFX
short_loops = generator.generate_loops(
    prompt="quick action stinger",
    duration=15,  # 15 seconds
    count=5
)

# Standard music loops
standard_loops = generator.generate_loops(
    prompt="background music",
    duration=30,  # 30 seconds
    count=5
)

# Extended loops for ambience
long_loops = generator.generate_loops(
    prompt="ambient soundscape",
    duration=60,  # 60 seconds
    count=5
)
```

### 7. Audio Analysis & Seamlessness Detection

The generator analyzes generated tracks for loop continuity:

```python
analyzer = AudioAnalyzer()

# Check if a file is seamless
is_seamless, score = analyzer.analyze_loop_seamlessness("audio.wav")

print(f"Seamless: {is_seamless}")
print(f"Score: {score:.2f}/1.00")  # 0.0 = not seamless, 1.0 = perfect

# Get duration
duration = analyzer.get_audio_duration("audio.wav")
print(f"Duration: {duration:.2f} seconds")
```

---

## Python API Reference

### MusicGenerator Class

Main orchestrator for music generation.

#### Initialization

```python
from engine_modules.music_generator import MusicGenerator

generator = MusicGenerator(config={
    'endpoint': 'https://api.soundverse.ai/v1',
    'api_key': 'your_key',
    'default_duration': 30,
    'default_count': 5,
    'quality_threshold': 0.7,
    'max_retries': 3,
    'use_api': True,
    'auto_creative_mode': False,
    'sample_library_dir': 'assets/sounds',
})
```

**Config Options:**
- `endpoint`: API endpoint URL
- `api_key`: API key for cloud generation
- `default_duration`: Default loop length (15, 30, 60)
- `default_count`: Default number of loops
- `quality_threshold`: Minimum seamlessness score (0.0-1.0)
- `max_retries`: Maximum retry attempts
- `use_api`: Use cloud API (if False, uses procedural only)
- `auto_creative_mode`: Auto-generate when no prompt given
- `sample_library_dir`: Directory with sample loops

#### Methods

##### generate_loops()

```python
loops = generator.generate_loops(
    prompt: Optional[str] = None,
    ref_audio_path: Optional[str] = None,
    duration: int = 30,
    count: int = 5
) -> List[str]
```

Generate multiple music loops. If prompt is provided, uses text-to-music. If ref_audio_path is provided, uses audio-to-music. Otherwise uses fallback.

**Returns:** List of file paths to generated audio files

##### generate_from_prompt()

```python
loops = generator.generate_from_prompt(
    prompt: str,
    duration: int = 30,
    count: int = 5
) -> List[str]
```

Generate loops from text description.

##### generate_from_audio()

```python
loops = generator.generate_from_audio(
    ref_audio_path: str,
    duration: int = 30,
    count: int = 5,
    description: Optional[str] = None
) -> List[str]
```

Generate loops from reference audio.

##### generate_fallback()

```python
loops = generator.generate_fallback(
    duration: int = 30,
    count: int = 5
) -> List[str]
```

Generate loops using procedural fallback (no API required).

##### import_to_pipeline()

```python
asset_id = generator.import_to_pipeline(
    loop_path: str,
    loop: MusicLoop,
    asset_pipeline: AssetPipeline
) -> Optional[str]
```

Import generated loop to asset pipeline for use in engine.

##### set_progress_callback()

```python
def progress_callback(progress: float, message: str):
    print(f"{progress*100:.1f}%: {message}")

generator.set_progress_callback(progress_callback)

loops = generator.generate_loops(prompt="test")
# Output:
# 0.0%: Generating loop 1/5...
# 18.0%: Generating loop 2/5...
# 36.0%: Generating loop 3/5...
```

##### cancel_generation()

```python
generator.cancel_generation()
```

Cancel ongoing generation (useful for long operations).

##### get_progress()

```python
progress = generator.get_progress()  # Returns 0.0-1.0
```

Get current generation progress.

### MusicLoop Dataclass

```python
from engine_modules.music_generator import MusicLoop

loop = MusicLoop(
    file_path="/tmp/music.wav",
    duration=30,
    prompt="ambient music",
    mood="relaxing",
    genre="ambient",
    bpm=120,
    quality_score=0.85,
    is_seamless=True
)

# Serialize/deserialize
data = loop.to_dict()
loop2 = MusicLoop.from_dict(data)
```

### AudioAnalyzer Class

```python
from engine_modules.music_generator import AudioAnalyzer

analyzer = AudioAnalyzer()

# Analyze seamlessness
is_seamless, score = analyzer.analyze_loop_seamlessness("audio.wav")

# Get duration
duration = analyzer.get_audio_duration("audio.wav")
```

### SoundverseAPI Class

```python
from engine_modules.music_generator import SoundverseAPI

api = SoundverseAPI(api_key='key', endpoint='https://...')

# Generate from prompt
audio_path = api.generate_from_prompt(
    prompt="electronic music",
    duration=30,
    seed=42
)

# Generate from audio
audio_path = api.generate_from_audio(
    reference_audio_path="ref.wav",
    description="similar style",
    duration=30
)
```

### ProceduralLoopBuilder Class

```python
from engine_modules.music_generator import ProceduralLoopBuilder

builder = ProceduralLoopBuilder(sample_library_dir="assets/sounds")

# Build a procedural loop
loop_path = builder.build_loop(
    duration=30,
    mood="ambient",
    seed=42
)

# Crossfade two audio files
result = builder.crossfade_audio(
    "file1.wav",
    "file2.wav",
    fade_duration=0.5
)
```

---

## CLI Usage

### Command Format

```bash
python manage.py music [OPTIONS]
```

### Available Options

```
--prompt TEXT              Music description
--audio PATH               Reference audio file
--description TEXT         Audio description  
--duration {15,30,60}      Loop length (default: 30)
--count INT                Number of loops (default: 5)
--mood TEXT                Genre/mood (ambient, electronic, orchestral, etc.)
--language CODE            Prompt language (en, es, fr, de, ja, zh, ru)
--threshold FLOAT          Seamlessness threshold (0.0-1.0)
--max-retries INT          Max retry attempts (default: 3)
--output PATH              Output directory
--help                     Show help message
```

### Examples

#### Generate 5 ambient loops

```bash
python manage.py music --prompt "calm ambient music, peaceful"
```

#### Generate from reference audio

```bash
python manage.py music --audio my_track.wav --description "similar but faster"
```

#### Spanish prompt

```bash
python manage.py music --prompt "música de baile energética" --language es
```

#### Custom output directory

```bash
python manage.py music --prompt "epic orchestral" --output my_music/
```

#### Batch with custom settings

```bash
python manage.py music \
  --prompt "lo-fi hip hop" \
  --count 10 \
  --duration 60 \
  --threshold 0.8 \
  --output generated_music/
```

---

## Configuration

### config.yaml Reference

```yaml
music_generation:
  enabled: true
  
  api:
    provider: "soundverse"              # API provider
    endpoint: "https://..."             # API endpoint
    key: ""                             # Leave empty, use env var
    timeout: 300                        # Timeout in seconds
  
  quality:
    seamless_threshold: 0.6             # Min seamlessness (0.0-1.0)
    max_retries: 3                      # Retry attempts
  
  generation:
    default_duration: 30                # Default seconds (15, 30, 60)
    default_count: 5                    # Default loop count
    default_mood: "ambient"             # Default mood
  
  fallback:
    use_procedural: true                # Use samples when API unavailable
    procedural_seed: 42                 # Reproducibility
    sample_library_dir: "assets/sounds" # Sample location
  
  output:
    directory: "generated_music"        # Output directory
    auto_import: true                   # Import to asset library
    auto_creative_mode: false           # Auto-generate on open
  
  localization:
    detect_ui_language: true            # Use UI language
    supported_languages:                # Supported languages
      - en
      - es
      - fr
```

### Environment Variables

```bash
# API Configuration
export SOUNDVERSE_API_KEY="sk_live_..."
export SOUNDVERSE_ENDPOINT="https://api.soundverse.ai/v1"

# Offline fallback (no variables needed)
```

---

## Troubleshooting

### Issue: "API key not configured"

**Solution:** Set the `SOUNDVERSE_API_KEY` environment variable:

```bash
export SOUNDVERSE_API_KEY="your_key_here"
```

Or configure in `config.yaml`:

```yaml
music_generation:
  api:
    key: "your_key_here"
```

**Note:** Procedural fallback works without an API key.

### Issue: "Reference audio file not found"

**Solution:** Verify the file path is correct and accessible:

```python
from pathlib import Path

audio_path = "my_audio.wav"
assert Path(audio_path).exists(), f"File not found: {audio_path}"

loops = generator.generate_from_audio(audio_path)
```

### Issue: "Seamlessness below threshold after retries"

**Solution:** Lower the threshold or increase retries:

```python
generator = MusicGenerator(config={
    'quality_threshold': 0.5,  # More lenient
    'max_retries': 5           # More attempts
})
```

### Issue: Slow generation

**Solution:** Use shorter durations or reduce count:

```python
# Fast
loops = generator.generate_loops(
    prompt="test",
    duration=15,   # Short
    count=2        # Few
)

# Slow
loops = generator.generate_loops(
    prompt="test",
    duration=60,   # Long
    count=10       # Many
)
```

### Issue: "NumPy not available" warning

**Solution:** Install NumPy for advanced audio analysis:

```bash
pip install numpy
```

### Issue: No samples in procedural fallback

**Solution:** Ensure sample library exists and contains audio files:

```bash
ls assets/sounds/
# Should contain: ambience/, sfx/, ui/ directories with .wav files
```

---

## Performance Benchmarks

### Cloud API Generation (Soundverse)

| Duration | Time  | Quality |
|----------|-------|---------|
| 15s      | 8-15s | High    |
| 30s      | 15-30s| High    |
| 60s      | 30-60s| High    |

### Procedural Generation (Offline)

| Duration | Time   | Quality |
|----------|--------|---------|
| 15s      | <0.5s  | Medium  |
| 30s      | <1s    | Medium  |
| 60s      | <2s    | Medium  |

### Batch Generation

- 5 loops × 30s: ~2-3 minutes (cloud) or ~3-5 seconds (offline)
- 10 loops × 30s: ~4-6 minutes (cloud) or ~5-10 seconds (offline)

### Analysis Performance

- Seamlessness check: ~0.1-0.2 seconds per file
- Duration detection: ~50ms per file

---

## Examples

### Example 1: Create Dynamic Game Music

```python
from engine_modules.music_generator import MusicGenerator

generator = MusicGenerator()

# Generate loops for different game states
loops = {
    'menu': generator.generate_from_prompt("calm ambient menu music", duration=30, count=3),
    'gameplay': generator.generate_from_prompt("upbeat action music, 140 BPM", duration=30, count=5),
    'boss': generator.generate_from_prompt("epic orchestral boss theme", duration=60, count=2),
    'lose': generator.generate_from_prompt("sad melancholic loss theme", duration=20, count=1),
}

for state, loop_list in loops.items():
    print(f"{state}: {len(loop_list)} loops generated")
    for loop in loop_list:
        print(f"  - {loop}")
```

### Example 2: Style-Based Generation

```python
# Generate loops in different styles
styles = [
    "lo-fi hip-hop, jazzy samples, 90 BPM",
    "synthwave, 80s retro, neon vibes",
    "ambient drone, minimalist, ethereal",
    "electronic dance, progressive, 128 BPM",
]

all_loops = []
for style in styles:
    loops = generator.generate_from_prompt(style, duration=30, count=2)
    all_loops.extend(loops)

print(f"Generated {len(all_loops)} loops in {len(styles)} styles")
```

### Example 3: Batch Processing with Progress

```python
def show_progress(progress: float, message: str):
    bar_length = 40
    filled = int(bar_length * progress)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f"\r[{bar}] {progress*100:.1f}% - {message}", end='')

generator = MusicGenerator()
generator.set_progress_callback(show_progress)

print("Generating 20 loops...")
loops = generator.generate_loops(
    prompt="cinematic orchestral soundtrack",
    duration=45,
    count=20
)

print(f"\n✓ Generated {len(loops)} loops")
```

### Example 4: Asset Pipeline Integration

```python
from engine_modules.asset_pipeline import AssetPipeline

# Initialize pipeline
pipeline = AssetPipeline()

# Generate and import
loops = generator.generate_loops(prompt="ambient music")

for i, loop_path in enumerate(loops):
    loop = MusicLoop(
        file_path=loop_path,
        duration=30,
        prompt="ambient music",
        mood="relaxing"
    )
    
    asset_id = generator.import_to_pipeline(loop_path, loop, pipeline)
    print(f"Loop {i+1} imported as: {asset_id}")
```

---

## Advanced Usage

### Custom Configuration Loading

```python
import yaml

# Load custom config
with open('my_music_config.yaml') as f:
    config = yaml.safe_load(f)['music_generation']

generator = MusicGenerator(config=config)
```

### Using Different Sample Libraries

```python
# Specify custom sample directory
builder = ProceduralLoopBuilder(
    sample_library_dir="my_custom_samples/"
)

loops = builder.build_loop(duration=30, mood="custom")
```

### Parallel Generation

```python
import threading

def generate_async(prompt: str, name: str):
    gen = MusicGenerator()
    loops = gen.generate_loops(prompt=prompt, count=5)
    print(f"{name}: Generated {len(loops)} loops")

# Run multiple generators in parallel
threads = [
    threading.Thread(target=generate_async, args=("ambient", "Thread1")),
    threading.Thread(target=generate_async, args=("electronic", "Thread2")),
    threading.Thread(target=generate_async, args=("orchestral", "Thread3")),
]

for t in threads:
    t.start()

for t in threads:
    t.join()
```

### Custom Quality Evaluation

```python
# Use stricter quality requirements
generator = MusicGenerator(config={
    'quality_threshold': 0.9,  # Very high quality
    'max_retries': 10          # Many attempts
})

loops = generator.generate_loops(
    prompt="music",
    count=3
)

# Check quality of each loop
for loop_path in loops:
    is_seamless, score = analyzer.analyze_loop_seamlessness(loop_path)
    print(f"Quality: {score:.2f} ({'✓' if is_seamless else '✗'})")
```

---

## Support & Resources

- **Documentation:** See [MUSIC_GENERATOR_IMPLEMENTATION.md](MUSIC_GENERATOR_IMPLEMENTATION.md)
- **API Reference:** [Soundverse AI Docs](https://help.soundverse.ai)
- **Issues:** Report bugs in the CFT-ENGINE0 repository
- **Contribution:** Pull requests welcome!

---

**Status:** ✅ Production Ready

**Version:** 1.0  
**Last Updated:** January 6, 2025  
**License:** MIT

