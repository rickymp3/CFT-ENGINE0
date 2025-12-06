# Texture Generator Guide

## Overview

The CFT-ENGINE0 Texture Generator is a comprehensive system for creating photorealistic PBR (Physically Based Rendering) texture sets from text descriptions or reference images. It features:

- **AI-Driven Generation**: Use cloud-based APIs (Hyper3D, Scenario) for photorealistic textures
- **Quality Enforcement**: Automatic quality evaluation with retry mechanism
- **Procedural Fallback**: Generate seamless textures procedurally when offline
- **Batch Generation**: Create multiple texture variations
- **Style Transfer**: Blend content with style from reference images
- **Multilingual Support**: Describe textures in 50+ languages
- **Editor Integration**: Generate textures directly from the UI
- **Asset Pipeline Integration**: Auto-import to library and material system

## Quick Start

### Basic Text-to-Texture

```bash
python manage.py texture --prompt "seamless stone wall, weathered"
```

### Image-to-Texture

```bash
python manage.py texture --image /path/to/reference.png --description "similar material, higher resolution"
```

### Generate Multiple Variations

```bash
python manage.py texture --prompt "brick texture" --batch 3
```

### Style Transfer

```bash
python manage.py texture --prompt "stone texture" --style /path/to/style.png
```

## Installation & Configuration

### 1. Install Dependencies

```bash
pip install -r requirements.txt
# Optional ML-based evaluation:
pip install torch torchvision
```

### 2. Configure API Keys

Set environment variables for cloud texture services:

```bash
export HYPER3D_API_KEY="your_api_key_here"
export HYPER3D_ENDPOINT="https://api.hyper3d.ai/v1"
```

Or configure in `config.yaml`:

```yaml
texture_generation:
  api:
    key: "your_api_key"
    endpoint: "https://api.hyper3d.ai/v1"
```

### 3. Offline Mode

The system automatically falls back to procedural generation when:
- No API key is configured
- Network is unavailable
- API requests fail

```bash
# Force procedural mode (no API calls)
python manage.py texture --prompt "texture" --no-quality-check
```

## Features in Detail

### 1. AI-Powered Generation

#### Supported Services

- **Hyper3D** (Primary)
  - High-quality photorealistic textures
  - Supports seamless/tileable generation
  - Supports character rigging (optional)
  - Supports style transfer

- **Scenario** (Fallback)
  - Fast generation
  - Custom model support
  - CC-licensed outputs

- **Local Models** (Future)
  - Stable Diffusion
  - ComfyUI integration
  - Offline-capable

#### Text Prompts

Write detailed, specific prompts:

```
Good: "Aged copper with patina, weathered verdigris, high-res 4K, seamless"
Better: "Industrial aged copper sheet, thick verdigris patina, oxidized green-blue stains, worn edges, tileable texture, 8K, professional quality"
```

**Prompt Tips:**
- Include material type (metal, stone, fabric, etc.)
- Describe surface conditions (weathered, polished, scratched)
- Specify desired resolution explicitly
- Use "seamless" or "tileable" for repeating textures
- Add style descriptors (industrial, nature, artistic)
- Mention quality (4K, 8K, professional)

### 2. Quality Control

#### Understanding Realism Scores

Textures are evaluated on a 0.0-1.0 scale:

```
0.0-0.2: Very low quality (extremely basic)
0.2-0.4: Low quality (acceptable for background)
0.4-0.6: Medium quality (usable with touch-ups)
0.6-0.8: Good quality (production-ready)
0.8-1.0: Excellent quality (photorealistic)
```

#### Threshold Setting

Set minimum acceptable quality:

```bash
# Strict quality (only photorealistic)
python manage.py texture --prompt "..." --threshold 0.85

# Relaxed quality (faster generation)
python manage.py texture --prompt "..." --threshold 0.5
```

#### Automatic Retry

When quality falls below threshold:

1. Prompt is refined with quality modifiers
2. Generation retries with modified prompt
3. After MAX_RETRIES, returns best attempt
4. User is notified of quality issues

```bash
# Allow more retry attempts
python manage.py texture --prompt "..." --max-retries 5
```

### 3. Resolution Options

Generate at different resolutions for different use cases:

| Resolution | Use Case | Performance |
|-----------|----------|------------|
| **512x512** | Quick previews, distant objects | Very Fast |
| **1K (1024x1024)** | Small objects, UI | Fast |
| **2K (2048x2048)** | Standard meshes, close-up (Recommended) | ~30-60s |
| **4K (4096x4096)** | Large surfaces, high-detail | ~60-120s |
| **8K (8192x8192)** | Cinematic, hero assets | ~120-180s |

```bash
# Generate 2K texture (default)
python manage.py texture --prompt "..." --resolution 2K

# Ultra-high quality
python manage.py texture --prompt "..." --resolution 8K
```

### 4. Texture Map Types

Generate specific PBR maps:

| Map | Purpose | Range |
|-----|---------|-------|
| **Albedo** | Base color (no lighting) | 0-255 RGB |
| **Normal** | Surface detail direction | Directional vectors (RGB) |
| **Roughness** | Surface smoothness | 0 (mirror) - 255 (rough) |
| **Metallic** | Metal vs non-metal | 0 (non-metal) - 255 (metal) |
| **Height** | Surface elevation | 0 (low) - 255 (high) |
| **Ambient Occlusion** | Surface shadows | Grayscale |
| **Emission** | Self-illumination | RGB with intensity |

```bash
# Standard maps (default)
python manage.py texture --prompt "..." --maps albedo normal roughness metallic

# With height map
python manage.py texture --prompt "..." --maps albedo normal roughness metallic height

# Minimal set (faster)
python manage.py texture --prompt "..." --maps albedo roughness
```

### 5. Batch Generation

Create multiple texture variations in one batch:

```bash
# Generate 5 variations of stone texture
python manage.py texture --prompt "stone texture" --batch 5
```

**What Batch Generation Does:**
- Creates N texture variations
- Modifies prompt slightly for each (variation markers)
- Different random seeds for variation
- Returns all successful generations
- Useful for comparing quality/styles

### 6. Style Transfer

Combine content prompt with style reference:

```bash
# "Make this like that"
python manage.py texture \
  --prompt "rock texture" \
  --style /path/to/reference_style.png
```

**How It Works:**
1. Analyzes style reference image
2. Extracts color, lighting, detail patterns
3. Applies to generated content
4. Creates coherent stylized texture

**Example Use Cases:**
- Match textures to a specific art direction
- Create consistent visual style across materials
- Adapt textures to existing game aesthetic

### 7. Multilingual Support

Describe textures in your language:

```bash
# English (default)
python manage.py texture --prompt "stone wall" --language en

# Spanish
python manage.py texture --prompt "pared de piedra" --language es

# French
python manage.py texture --prompt "mur de pierre" --language fr

# Japanese
python manage.py texture --prompt "石の壁" --language ja

# Chinese
python manage.py texture --prompt "石墙" --language zh
```

**Supported Languages:**
- en (English)
- es (Español)
- fr (Français)
- de (Deutsch)
- ja (日本語)
- zh (中文)
- ru (Русский)
- And 40+ more via API

### 8. Editor Integration

Generate textures directly in the visual editor:

1. Click **"Generate Texture"** in Asset Library panel
2. Choose generation mode:
   - **From Text**: Describe desired texture
   - **From Image**: Upload reference image
   - **Style Transfer**: Blend with style
   - **Batch**: Multiple variations

3. Configure options:
   - Resolution (2K recommended)
   - Map types
   - Quality threshold
   - Material name

4. Click **"Generate"**
5. Monitor progress bar
6. Material auto-imports to library

### 9. Output & Import

Generated textures are automatically:

1. **Saved to disk** in `generated_textures/` directory
2. **Registered** in asset pipeline metadata
3. **Converted** to PNG format
4. **Tagged** for filtering/search
5. **Material JSON created** with PBR parameters

#### Output Structure

```
generated_textures/
├── stone_wall_0/
│   ├── albedo.png           (Base color)
│   ├── normal.png           (Surface detail)
│   ├── roughness.png        (Smoothness)
│   ├── metallic.png         (Metallicity)
│   └── material.json        (Material definition)
├── brick_texture_0/
│   ├── ...
```

#### Material JSON Example

```json
{
  "name": "stone_wall",
  "type": "pbr_material",
  "shader": "pbr",
  "textures": {
    "albedo": "generated_textures/stone_wall_0/albedo.png",
    "normal": "generated_textures/stone_wall_0/normal.png",
    "roughness": "generated_textures/stone_wall_0/roughness.png",
    "metallic": "generated_textures/stone_wall_0/metallic.png"
  },
  "parameters": {
    "metallic_factor": 0.5,
    "roughness_factor": 0.5,
    "ambient_occlusion_strength": 1.0
  },
  "metadata": {
    "generated_from": "stone wall, weathered",
    "realism_score": 0.87,
    "generation_timestamp": "2025-01-06T12:34:56"
  }
}
```

## Python API

### Basic Usage

```python
from engine_modules.texture_generator import TextureGenerator

# Initialize
generator = TextureGenerator(config={
    "realism_threshold": 0.8,
    "max_retries": 3
})

# Generate from prompt
texture_set = generator.generate_from_prompt(
    prompt="seamless stone texture",
    resolution="2K"
)

# Access texture maps
print(f"Albedo: {texture_set.albedo_path}")
print(f"Normal: {texture_set.normal_path}")
print(f"Quality: {texture_set.realism_score:.2f}")
```

### Batch Generation

```python
# Generate multiple variations
results = generator.generate_batch(
    prompt="rock texture",
    batch_size=5,
    resolution="2K"
)

for i, texture_set in enumerate(results):
    print(f"Variation {i}: {texture_set.realism_score:.2f}")
```

### Style Transfer

```python
# Generate with style
texture_set = generator.generate_stylized(
    content_prompt="stone texture",
    style_image_path="/path/to/style.png",
    resolution="2K"
)
```

### Progress Tracking

```python
def on_progress(stage, pct, message):
    print(f"[{pct:.0%}] {stage}: {message}")

generator.set_progress_callback(on_progress)

# Then call generate_texture, generate_batch, etc.
```

### Asset Pipeline Integration

```python
# Import to asset pipeline
asset_ids = generator.import_to_pipeline(
    texture_set=texture_set,
    material_name="stone_wall"
)

# asset_ids = {
#   "albedo": "texture/stone_wall/albedo",
#   "normal": "texture/stone_wall/normal",
#   ...
# }

# Create material JSON
material_path = generator.create_material_json(
    material_name="stone_wall",
    texture_set=texture_set
)
```

### Procedural Fallback

```python
from engine_modules.texture_generator import ProceduralTextureGenerator

# Generate Perlin noise texture
noise_texture = ProceduralTextureGenerator.generate_perlin_texture(
    width=2048,
    height=2048,
    scale=0.05,
    octaves=4,
    seed=42
)

# Generate normal map from height
normal_map = ProceduralTextureGenerator.generate_normal_from_height(noise_texture)

# Save to file
ProceduralTextureGenerator.save_texture(
    noise_texture,
    Path("output.png")
)
```

### Quality Evaluation

```python
from engine_modules.texture_generator import TextureQualityEvaluator

evaluator = TextureQualityEvaluator(ml_model_available=False)

score = evaluator.evaluate(texture_set)
print(f"Realism score: {score:.2f}")

# With ML (requires PyTorch)
evaluator_ml = TextureQualityEvaluator(ml_model_available=True)
score = evaluator_ml.evaluate(texture_set)
```

## Configuration

### config.yaml

```yaml
texture_generation:
  # API Settings
  api:
    provider: "hyper3d"
    endpoint: "https://api.hyper3d.ai/v1"
    key: ""  # Set via HYPER3D_API_KEY environment variable
    timeout: 300

  # Quality Control
  quality:
    realism_threshold: 0.7
    max_retries: 3
    use_ml_evaluation: false

  # Default Settings
  generation:
    default_resolution: "2K"
    default_map_types:
      - albedo
      - normal
      - roughness
      - metallic
    default_batch_size: 1

  # Fallback/Offline
  fallback:
    use_procedural: true
    procedural_seed: 42
    seamless: true

  # Output
  output:
    directory: "generated_textures"
    auto_import: true
    create_material_json: true

  # Localization
  localization:
    detect_ui_language: true
    supported_languages:
      - en
      - es
      - fr
      - de
      - ja
      - zh
      - ru
```

## Troubleshooting

### API Errors

**Problem:** "API key not configured"
```bash
# Solution: Set environment variable
export HYPER3D_API_KEY="your_key"

# Or configure in config.yaml
# Or pass via Python API
```

**Problem:** "API timeout"
```bash
# Solution: Increase timeout
python manage.py texture --prompt "..." 
# Internally increases timeout to 300 seconds (5 minutes)
```

### Quality Below Threshold

**Problem:** Realism score < 0.7, retries exhausted
```bash
# Solution 1: Improve prompt
python manage.py texture --prompt "ultra high detail, photorealistic, 4K professional quality" --threshold 0.6

# Solution 2: Lower threshold
python manage.py texture --prompt "..." --threshold 0.6

# Solution 3: Increase retries
python manage.py texture --prompt "..." --max-retries 5
```

### Out of Memory

**Problem:** Large resolution causes OOM error
```bash
# Solution: Use smaller resolution
python manage.py texture --prompt "..." --resolution 2K

# Or generate in batches with smaller batch size
python manage.py texture --prompt "..." --batch 1
```

### Slow Generation

**Problem:** Generation taking too long
```bash
# Solution 1: Use lower resolution
python manage.py texture --prompt "..." --resolution 1K

# Solution 2: Skip quality enforcement
python manage.py texture --prompt "..." --no-quality-check

# Solution 3: Use fewer maps
python manage.py texture --prompt "..." --maps albedo roughness
```

### Offline Mode Issues

**Problem:** Procedural textures look too simple
```bash
# Solution 1: Use higher octaves for Perlin noise
# (Configure in texture_generator.py ProceduralTextureGenerator)

# Solution 2: Wait for API to be available
# Quality will improve significantly with cloud generation

# Solution 3: Create manual reference textures
# Use those with style transfer
```

## Performance Benchmarks

### Generation Time

| Resolution | Single GPU | Without GPU |
|-----------|-----------|-----------|
| 512x512 | ~15s | ~30s |
| 1K | ~20s | ~45s |
| 2K | ~30-60s | ~90-180s |
| 4K | ~60-120s | ~180-360s |
| 8K | ~120-180s | ~360-600s |

### Procedural Generation (Local)

| Resolution | Time |
|-----------|------|
| 512x512 | <1s |
| 1K | <2s |
| 2K | <5s |
| 4K | ~10s |
| 8K | ~20s |

## License & Attribution

### Cloud Service Credits

- **Hyper3D**: Requires valid API key and subscription
- **Scenario**: Supports open-source attribution
- **Stable Diffusion**: Check local model licensing

### Generated Assets

Generated textures ownership:
- Belongs to project creator
- Respect API service terms of service
- Credit AI service if required by ToS
- Check commercial licensing

### Code

Texture Generator module is part of CFT-ENGINE0 (MIT License).

## Examples

### Example 1: Game Environment

```bash
# Create realistic stone wall
python manage.py texture \
  --prompt "ancient stone castle wall, weathered moss covered cracks" \
  --resolution 2K \
  --threshold 0.75

# Create metal door frame
python manage.py texture \
  --prompt "oxidized iron metal frame, rusty edges, scratches" \
  --resolution 1K \
  --maps albedo normal roughness metallic

# Create wood floor
python manage.py texture \
  --prompt "old wooden floor planks, worn scratches, natural grain" \
  --batch 2 \
  --resolution 2K
```

### Example 2: Character Materials

```bash
# Fabric clothing
python manage.py texture \
  --prompt "linen fabric cloth, natural weave texture" \
  --resolution 2K

# Leather boots
python manage.py texture \
  --prompt "aged leather material, creases wrinkles, dark brown" \
  --resolution 2K \
  --batch 3
```

### Example 3: Style-Consistent Set

```bash
# Create base style reference
# cyberpunk_style.png - neon/tech aesthetic

# Generate multiple materials in that style
python manage.py texture --prompt "metal surface" --style cyberpunk_style.png
python manage.py texture --prompt "plastic panel" --style cyberpunk_style.png
python manage.py texture --prompt "glass surface" --style cyberpunk_style.png
```

## Future Enhancements

Planned features:

- [ ] Local model support (Stable Diffusion)
- [ ] Character-aware generation
- [ ] Animated texture generation
- [ ] Material preset system
- [ ] Web API for remote generation
- [ ] Real-time preview in editor
- [ ] Texture blending/mixing
- [ ] Resolution upscaling (ESRGAN)
- [ ] Batch optimization pipeline
- [ ] Cloud rendering acceleration

## Support

For issues, questions, or feature requests:

1. Check [ARCHITECTURE_VALIDATION.md](ARCHITECTURE_VALIDATION.md) for system overview
2. Review error messages and troubleshooting above
3. Check environment variables and API keys
4. Verify `config.yaml` settings
5. Test procedural fallback (offline mode)

## Additional Resources

- [Asset Pipeline Guide](AI_ASSET_GENERATION_GUIDE.md)
- [Editor Integration Guide](EDITOR_GUIDE.md)
- [Configuration Reference](CONFIG_REFERENCE.md)
- [Python API Documentation](engine_modules/texture_generator.py)

---

**Generated with ❤️ for CFT-ENGINE0**

Last Updated: January 2025
