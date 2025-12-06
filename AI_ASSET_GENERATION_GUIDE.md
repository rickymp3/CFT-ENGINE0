# AI Asset Generation & Random Scene System

## Overview

The CFT-ENGINE0 system now includes a complete AI-driven asset generation and random scene pipeline:

1. **Photorealistic Asset Generation** - Generate 3D models with PBR textures from text/image prompts
2. **Quality Enforcement** - Automatic retry with photorealism scoring until threshold met
3. **Random Scene Generation** - One-click generation of complete scenes with narrative and assets
4. **Editor Integration** - "🎲 Random" button in the visual editor toolbar

## Features

### Asset Generation System (`engine_modules/asset_generation.py`)

- **API Integration**: Support for Meshy.ai, Scenario, Kaedim with mock fallback
- **Photorealism Scoring**: Heuristic evaluator based on file size, texture presence, resolution
- **Quality Enforcement**: Retry loop (max 3 attempts) with refined prompts
- **Procedural Fallback**: Generates placeholder assets when APIs unavailable
- **PBR Support**: Automatic generation of albedo, normal, roughness, metallic textures
- **Character Rigging**: Optional automatic rigging for character models

**Configuration** (via environment variables):
```bash
export REALISM_THRESHOLD=0.9          # Quality threshold (0.0-1.0)
export MAX_ASSET_RETRIES=3            # Max generation attempts
export MESHY_API_KEY=your_key         # For Meshy.ai integration
export SCENARIO_API_KEY=your_key      # For Scenario integration
export ASSET_STYLE=photorealistic     # Asset style (default: photorealistic)
export ASSET_RESOLUTION=4k            # Output resolution (default: 4k)
```

**Usage**:
```python
from engine_modules.asset_generation import AssetGenerator

generator = AssetGenerator()

# Generate asset from image reference with quality enforcement
asset = generator.generate_asset_from_reference(
    ref_image_path="/path/to/reference.jpg",
    description="A photorealistic oak tree with detailed bark",
    enforce_quality=True  # Retry until quality threshold met
)

print(f"Asset ID: {asset.asset_id}")
print(f"Model: {asset.model_path}")
print(f"Quality Score: {asset.realism_score:.2f}")
print(f"Generation Attempts: {asset.generation_attempts}")
print(f"Textures: {asset.texture_paths}")
```

### Random Scene Generator (`engine_modules/random_scene.py`)

Generates complete scenes through a 6-step pipeline:

1. **Prompt Selection** - Choose from 15 curated scene templates
2. **Reference Image Search** - Find 3 matching images from asset library
3. **Narrative Generation** - Create story/beats with visual context via LLM
4. **Asset Generation** - Generate photorealistic asset for each beat
5. **Scene Assembly** - Position objects with random locations and lighting
6. **Environment Setup** - Configure lighting based on scene mood

**Scene Templates** (15 available):
- Hero explores abandoned factory
- Ancient temple in mystical jungle
- Futuristic cyberp unk marketplace
- Snowy mountain fortress
- Underwater ruins
- And 10 more...

**Configuration**:
```bash
export MAX_SCENE_ASSETS=5             # Assets per scene (default: 5)
export MAX_SCENE_BEATS=4              # Story beats (default: 4)
export OPENAI_API_KEY=your_key        # For narrative generation
```

**Usage**:
```python
from engine_modules.random_scene import RandomSceneGenerator

generator = RandomSceneGenerator()

# Synchronous generation (blocking)
result = generator.generate_random_scene()
print(f"Prompt: {result['prompt']}")
print(f"Story Beats: {len(result['story']['beats'])}")
print(f"Generated Assets: {len(result['assets'])}")

# Asynchronous generation with progress
def progress(stage, progress_pct, message):
    print(f"[{progress_pct:.0%}] {stage}: {message}")

def on_complete(result):
    if result:
        print(f"✓ Generated {len(result['assets'])} assets")
    else:
        print("✗ Generation cancelled")

generator.set_progress_callback(progress)
generator.generate_random_scene_async(on_complete)

# Cancel generation
generator.cancel()
```

### Editor Integration

**New Toolbar Button**: The "🎲 Random" button in the editor triggers scene generation:

```python
# In editor.py SceneEditor class
def generate_random_scene(self):
    """Generate a random photorealistic scene using AI pipeline."""
    generator = RandomSceneGenerator(asset_manager=None)
    
    def progress_callback(stage, progress, message):
        # Display progress to user
        percentage = int(progress * 100)
        print(f"[{percentage}%] {stage}: {message}")
    
    def completion_callback(result):
        if result:
            # Instantiate scene in viewport
            self._instantiate_generated_scene(result)
    
    generator.set_progress_callback(progress_callback)
    generator.generate_random_scene_async(completion_callback)

def _instantiate_generated_scene(self, scene_result):
    """Load generated assets and build scene in viewport."""
    # Adds objects to hierarchy, applies lighting, etc.
```

## Visual Reference Support

Stories now support image references that guide asset generation:

```python
from engine_modules.story_generator import StoryGraph

story = StoryGraph()
story.add_beat("hero_arrives", "Hero arrives at the ancient temple")

# Attach visual reference to beat
story.attach_image("hero_arrives", "/path/to/temple_reference.jpg")

# Link generated asset to beat
story.attach_generated_asset("hero_arrives", "asset_12345")

# Retrieve references
ref_image = story.get_image("hero_arrives")
assets = story.get_beat("hero_arrives").generated_assets
```

## Headless Environment Support

The system now fully supports headless environments (CI/CD, servers):

- **Pygame**: SDL_VIDEODRIVER=dummy automatically set when no display
- **Panda3D**: Offscreen rendering configured in test fixtures
- **Asset Generation**: Works without GPU/display (CPU-based or API calls)
- **Tests**: 86 non-stress tests pass in headless mode (12 stress tests need GPU)

## API Key Setup (Production)

### Meshy.ai (Recommended for 3D Models)
```bash
export MESHY_API_KEY="xxx-yyy-zzz"
```
Features: Fast generation, good topology, automatic rigging

### Scenario (Image-to-Model)
```bash
export SCENARIO_API_KEY="xxx-yyy-zzz"
```
Features: Reference-based generation, consistent styling

### Kaedim (Photogrammetry)
```bash
export KAEDIM_API_KEY="xxx-yyy-zzz"
```
Features: Highest photorealism, slow, expensive

### OpenAI (For Narrative)
```bash
export OPENAI_API_KEY="sk-..."
```
Required for story generation with LLM

## Quality Assurance

### Photorealism Scoring
The PhotorealismEvaluator rates assets on:
- **Model Size** (KB): Larger = more detailed
- **Texture Presence** (count): 3 textures (albedo, normal, roughness) = best
- **Texture Resolution** (pixels): Higher = better quality
- **File Integrity** (format): Valid GLB + PNG validates structure

Formula: `score = (model_kb/200 + textures*0.2 + resolution/4k) / 3`

Target: REALISM_THRESHOLD = 0.9 (90% quality minimum)

### Retry Logic
When enforce_quality=True:
1. Generate asset (Attempt 1)
2. Evaluate photorealism score
3. If score < threshold: refine prompt and retry (max MAX_RETRIES times)
4. Return best asset or procedural fallback

**Example progression**:
- Attempt 1: "A tree" → score 0.65 ❌
- Attempt 2: "A detailed photorealistic oak tree" → score 0.82 ❌  
- Attempt 3: "A highly detailed photorealistic oak tree with bark detail" → score 0.94 ✓

## Testing

### Run All Tests (except stress)
```bash
python -m pytest -k 'not stress' -v
# Result: 86 passed
```

### Run Asset Generation Tests
```bash
python -m pytest tests/test_asset_generation.py -v
# Tests: Config, API, Generator, GeneratedAsset
```

### Run Story Generator Tests
```bash
python -m pytest tests/test_story_generator.py -v
# Tests: 26 passing tests for narrative system
```

## Performance Notes

- **Asset Generation**: 30-180 seconds per asset depending on API
- **Scene Assembly**: 1-5 seconds
- **Progress Callbacks**: Enable UI updates without blocking
- **Threading**: Long operations run in background threads
- **Caching**: Generated assets cached in `generated_assets/` directory

## Commercial Use

### Licensing Considerations

For commercial products using this system:

1. **Meshy.ai Assets**: Requires commercial license agreement
   - Include attribution: "Assets generated via Meshy.ai"
   - Follow Meshy terms of service

2. **Scenario Models**: Check licensing terms for commercial use
   - May require commercial subscription
   - Review generated asset usage rights

3. **Custom Assets**: Own any procedural fallback assets
   - No external dependencies

4. **Character Rigging**: Auto-rigging may have IP implications
   - Consider licensing rigging tools separately

## Troubleshooting

### "No API key for meshy" warning
This is normal - the system falls back to procedural assets. Provide API keys to enable real generation:
```bash
export MESHY_API_KEY="your_key_here"
```

### Generation taking too long
- Check MAX_SCENE_ASSETS (too many assets = longer generation)
- Check API rate limits (may be throttled)
- Reduce MAX_SCENE_BEATS to 2-3 for faster iteration

### Low quality scores
- Increase MAX_RETRIES (more attempts = better quality)
- Lower REALISM_THRESHOLD if needed (0.7-0.8 for speed, 0.9+ for quality)
- Provide better reference images
- Use more detailed descriptions

## Future Enhancements

Planned improvements for future versions:

1. **Local Model Support**: RunwayML, Stable Diffusion for offline generation
2. **Mesh Optimization**: LOD generation, polygon reduction
3. **Material Blending**: Smart PBR texture layering
4. **Animation Rigging**: Full character skeletal animation
5. **Performance Metrics**: Automatic FPS/memory profiling
6. **Batch Processing**: Generate multiple assets in parallel
7. **ML-Based Scoring**: Real ML model for quality evaluation (current: heuristic)
8. **Asset Versioning**: Track generation history and variations

## See Also

- [USER_GUIDE.md](USER_GUIDE.md) - Editor usage
- [STORY_GENERATOR_GUIDE.md](STORY_GENERATOR_GUIDE.md) - Narrative system
- [engine_modules/asset_generation.py](engine_modules/asset_generation.py) - API reference
- [engine_modules/random_scene.py](engine_modules/random_scene.py) - Scene generator code
