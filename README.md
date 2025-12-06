# CFT-ENGINE0 🚀

**Professional AAA Game Engine with 10 Advanced Systems**

A complete, production-ready game engine built with Python featuring cutting-edge AAA capabilities: Global Illumination, Dynamic Weather, 3D Spatial Audio, AI with Behavior Trees, Fluid Simulation, World Streaming, Save/Load, Volumetric Effects, Water Physics, and Cinematic Tools.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org)
[![Panda3D](https://img.shields.io/badge/Panda3D-1.10.15-green.svg)](https://www.panda3d.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Systems](https://img.shields.io/badge/AAA%20Systems-10%20Implemented-red.svg)](#aaa-systems)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](#testing)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-blue.svg)](CONTRIBUTING.md)

---

## 📚 Documentation

- **[User Guide](USER_GUIDE.md)** - Complete feature documentation
- **[AAA Systems Guide](AAA_SYSTEMS_COMPLETE_GUIDE.md)** - System architecture  
- **[QA & Production](QA_PRODUCTION_READY.md)** - Testing, profiling, benchmarks
- **[Contributing](CONTRIBUTING.md)** - How to contribute
- **[Code of Conduct](CODE_OF_CONDUCT.md)** - Community guidelines

---

## ✨ AAA Systems (NEW!)

### 🌟 Professional-Grade Features

CFT-ENGINE0 now includes **10 fully implemented AAA systems** with 6,800+ lines of production code:

1. **Global Illumination & Ray Tracing** - Light probes, LPV, SSR, hardware RT detection
2. **Dynamic Weather & Day-Night Cycle** - 8 weather types, physics integration, atmospheric effects
3. **3D Spatial Audio** - Doppler effect, reverb, occlusion, audio buses
4. **AI Framework** - Behavior trees, A* navigation mesh, ML integration (ONNX/TFLite)
5. **Fluid/Cloth/Destruction** - SPH simulation, soft bodies, Voronoi fracture
6. **World Streaming & LOD** - Zone-based loading, origin shifting, memory budgets
7. **Save/Load System** - Scene/physics/AI serialization, autosave, compression
8. **Volumetric Effects** - Ray-marched fog, GPU smoke, volumetric clouds
9. **Water Simulation** - Wave physics, reflections, refraction, caustics
10. **Cinematic Tools** - Timeline sequences, camera rigs, DoF, motion blur

**Quick Start:**
```python
from engine_modules.global_illumination import create_gi_system
from engine_modules.weather_system import EnvironmentalSystem
from engine_modules.audio_system import SpatialAudioSystem

# Initialize AAA features
gi = create_gi_system(base, quality="high")
weather = EnvironmentalSystem(base)
audio = SpatialAudioSystem(base, enable_hrtf=True)

# Use them
weather.set_weather(WeatherType.RAIN, intensity=0.7)
audio.play("thunder", loop=False)
```

**See:** `examples/complete_aaa_demo.py` for full integration

---

## 🎮 Core Features

### Engine Architecture
- **Modular Design**: Plug-and-play system with independent modules for physics, rendering, animation, networking, and scripting
- **Configuration System**: YAML-based configuration with runtime settings and environment profiles
- **CLI Tools**: `manage.py` for project scaffolding, engine launching, testing, and configuration management
- **High-Level API**: Simple interfaces like `Engine.add_model()`, `Engine.enable_physics()`, `Engine.set_shader_pipeline()`

### 3D Engine (Panda3D)
- **CFT AAA Engine**: Full 3D rendering with Panda3D's scene graph
- **Advanced Bullet Physics**: Complete physics integration including:
  - Vehicles with raycast suspension, wheel physics, steering
  - Soft bodies (cloth, rope with deformation)
  - Character controller with capsule collision
  - Constraints (hinge, slider, point-to-point, cone-twist)
  - Trigger volumes with callbacks
  - Advanced shapes (box, sphere, capsule, cylinder, cone, compound)
- **Deferred PBR Rendering**: AAA-quality rendering pipeline with:
  - G-buffer architecture (positions, normals, albedo, PBR, depth)
  - Cook-Torrance BRDF with Fresnel-Schlick, GGX distribution, Smith geometry
  - Metallic/roughness workflow with ambient occlusion
  - Dynamic lighting (directional, point, spot lights)
  - Post-processing (bloom, SSAO, HDR tonemapping)
- **Skeletal Animation System**:
  - AnimationController with state machine and blending
  - IK solver with FABRIK algorithm
  - Blend trees (lerp, additive, layer blending)
  - Animation events and callbacks
- **Multilingual Support**: Built-in localization system (English, Spanish, French) with JSON/YAML translation files
- **Scene Management**: Dynamic scene switching between menu and gameplay

### Networking & Multiplayer 🌐
- **Asyncio Architecture**: WebSocket-based client-server networking
- **State Synchronization**: Real-time position and input sharing
- **Lag Compensation**: Ping/pong system for RTT measurement
- **Client Prediction**: Input buffering for smooth local movement
- **Message System**: Typed messages (connect, disconnect, state, input, spawn, chat)
- **Scalable**: Separate network update loop from physics/rendering

### Asset Pipeline 📦
- **Cloud Storage Integration**: 
  - Dropbox API support with OAuth authentication
  - Box.com integration (boxsdk)
  - Automatic download and caching
- **Format Conversion**: Automatic conversion (.obj, .fbx, .gltf → .bam)
- **Asset Cache**: MD5 checksumming, metadata tracking, dependency management
- **Search & Tagging**: Query assets by name, type, tags
- **Thumbnail Generation**: Preview images for models and textures

### Visual Scripting 🧩
- **Node-Based Editor**: Drag-and-drop visual programming
- **Node Types**:
  - Events (BeginPlay, Tick, KeyPressed)
  - Math (Add, Multiply, Compare)
  - Logic (Branch, Comparison operators)
  - Node operations (SetPosition, GetPosition)
  - Print and custom nodes
- **Python Code Generation**: Compile visual scripts to Python
- **Runtime Execution**: Attach scripts to game objects
- **Save/Load**: JSON-based graph serialization

### 2D Engine (Pygame)
- **GameEngine**: High-performance game loop with event handling at 60 FPS
- **Sprite System**: Advanced sprite class with collision detection and physics
- **Asset Manager**: Comprehensive asset loading and caching for images, sounds, fonts, sprite sheets
- **Particle Systems**: Physics-based particle effects with customizable properties
- **Dynamic Lighting**: Real-time 2D point lights with color blending
- **Post-Processing**: Bloom, vignette, chromatic aberration effects
- **Camera System**: 2D camera with scrolling and zoom
- **Procedural Textures**: Built-in texture generation

### Visual Scene Editor 🎨
- **Complete IDE**: No-code scene creation with drag-and-drop interface
- **Viewport**: Real-time 3D preview with orbit, pan, zoom camera controls
- **Scene Hierarchy**: Tree view with parent-child relationships
- **Inspector Panel**: Visual property editing (transform, materials, physics)
- **Asset Library**: Browse and add primitives, models, textures, sounds
- **Animation Timeline**: Keyframe animation with playback controls and interpolation
- **Toolbar**: Quick access to tools, primitives, and settings
- **Status Bar**: Real-time FPS, object count, physics info

### Engine Modules
- **physics.py**: PhysicsManager with vehicles, soft bodies, constraints, character controller
- **deferred_renderer.py**: DeferredRenderer with G-buffer, PBR shaders, post-processing
- **animation.py**: AnimationController with skeletal animation, IK, blend trees
- **networking.py**: NetworkClient/Server with WebSocket support
- **asset_pipeline.py**: AssetPipeline with cloud storage, caching, conversion
- **visual_scripting.py**: VisualScript with node editor and code generation
- **localization.py**: Localization with JSON/YAML translations, runtime language switching
- **rendering.py**: RenderingManager for basic lighting and materials
- **config.py**: ConfigManager for YAML-based configuration

## 📦 Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

**Dependencies include:**
- `panda3d` - 3D game engine
- `pygame` - 2D game framework
- `pytest` - Testing framework
- `pyyaml` - YAML configuration
- `websockets` - Networking support
- `dropbox` - Cloud storage integration
- `boxsdk` - Box.com integration
- `Pillow`, `numpy`, `moderngl`, `PyOpenGL` - Graphics utilities

## 🚀 Quick Start

### Launch the Visual Editor

**No-code scene creation with complete IDE:**
```bash
python editor.py
```

**Features:**
- Drag-and-drop interface for scene creation
- Real-time 3D preview with camera controls
- Visual property editing (no coding required)
- Animation timeline with keyframe editing
- Asset library with primitives and materials
- Physics and PBR toggles
- Multilingual support (en/es/fr)

**See `EDITOR_GUIDE.md` for full documentation.**

### Run Example Demos

**Basic 3D Scene** - Learn scene setup, camera, and lighting:
```bash
python examples/basic_scene_example.py
```
Controls: Arrow Keys to move, W/S to zoom, A/D to rotate, ESC to quit

**Physics Simulation** - See Bullet physics in action:
```bash
python examples/physics_example.py
```
Watch boxes and spheres fall and collide with realistic physics

**PBR Shaders** - Explore advanced materials:
```bash
python examples/pbr_shaders_example.py
```
See different material properties: metallic, rough, polished surfaces

**2D Game Demo** - Basic gameplay mechanics:
```bash
python demo_game.py
```
Controls: Arrow Keys/WASD to move, touch red enemies to score

**AAA 2D Graphics** - Advanced 2D rendering showcase:
```bash
python graphics_demo.py
```
Controls: WASD to move, SPACE for particles, 1-4 toggle effects, ESC to quit

**Full 3D Engine** - Multilingual Panda3D engine:
```bash
# English (default)
python cft_panda3d_engine.py

# Spanish
CFT_LANG=es python cft_panda3d_engine.py

# French  
CFT_LANG=fr python cft_panda3d_engine.py
```
Controls: ENTER to start, Arrow Keys to rotate model, ESC to quit

### Using the CLI Tool

The `manage.py` CLI tool helps you work with the engine:

```bash
# Create a new project
python manage.py new-project my_game

# Run the engine with language selection
python manage.py run --lang en

# Run test suite
python manage.py test

# View configuration
python manage.py config --show
```

### Create Your Own Game

**Option 1: Use the CLI** (Recommended)
```bash
python manage.py new-project my_awesome_game
cd my_awesome_game
# Edit the generated files
python main.py
```

**Option 2: Extend GameEngine (2D)**
```python
from game_engine import GameEngine, Sprite

class MyGame(GameEngine):
    def __init__(self):
        super().__init__(800, 600, "My Game")
        # Initialize your game objects
        
    def update(self):
        # Update game logic
        pass
        
    def render(self):
        super().render()
        # Render your game graphics
        pass

if __name__ == "__main__":
    game = MyGame()
    game.run()
```

**Option 3: Use Engine Modules (3D)**
```python
from direct.showbase.ShowBase import ShowBase
from engine_modules.physics import PhysicsManager
from engine_modules.rendering import RenderingManager
from engine_modules.config import get_config

class MyGame(ShowBase):
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.config = get_config()
        
        # Initialize systems
        self.physics = PhysicsManager()
        self.renderer = RenderingManager(self.render)
        self.renderer.enable_pbr()
        
        # Create your scene
        self.setup_scene()
        
    def setup_scene(self):
        # Add your game objects
        pass

if __name__ == '__main__':
    app = MyGame()
    app.run()
```

## 📚 Documentation

### Examples
See `examples/README.md` for detailed tutorials on:
- Basic scene setup
- Physics simulation
- PBR shader materials
- Camera controls
- Lighting techniques

### Configuration
Edit `config.yaml` to customize:
- Graphics settings (PBR, shadows, HDR)
- Physics parameters (gravity, timestep)
- Animation settings
- Networking options
- Debug features

Example:
```yaml
graphics:
  enable_pbr: true
  enable_hdr: true
  shadow_resolution: 2048

physics:
  gravity: -9.81
  simulation_frequency: 60
```

### Module Architecture
- `engine_modules/config.py` - Configuration management with YAML support
- `engine_modules/physics.py` - Bullet physics integration
- `engine_modules/rendering.py` - PBR shader pipeline and lighting
- `engine_modules/animation.py` - (Planned) Skeletal animation system
- `engine_modules/networking.py` - (Planned) Multiplayer networking

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_panda3d_engine.py

# Using the CLI tool
python manage.py test
```

## 📁 Project Structure

```
CFT-ENGINE0/
├── engine.py                      # Original minimal engine entry point
├── game_engine.py                 # Core pygame-based 2D graphics engine
├── asset_manager.py               # Asset loading and caching system
├── rendering.py                   # Advanced 2D rendering (particles, lighting, post-FX)
├── cft_panda3d_engine.py         # 3D engine with Panda3D and multilingual support
├── demo_game.py                   # Simple 2D game example
├── graphics_demo.py               # AAA 2D graphics showcase
├── manage.py                      # CLI tool for project management
├── config.yaml                    # Engine configuration
│
├── engine_modules/                # Modular engine components
│   ├── config.py                 # Configuration management system
│   ├── physics.py                # Bullet physics integration
│   └── rendering.py              # PBR shader pipeline and lighting
│
├── examples/                      # Example scripts and tutorials
│   ├── README.md                 # Examples documentation
│   ├── basic_scene_example.py    # Basic 3D scene setup
│   ├── physics_example.py        # Physics simulation demo
│   └── pbr_shaders_example.py    # PBR materials showcase
│
├── tests/                         # Test suite (12 tests)
│   ├── conftest.py               # Pytest configuration
│   ├── test_engine.py            # Original engine tests
│   ├── test_game_engine.py       # 2D engine tests
│   └── test_panda3d_engine.py    # 3D engine tests
│
├── assets/                        # Asset directories
│   ├── images/                   # Image assets
│   ├── sounds/                   # Audio assets
│   └── fonts/                    # Font assets
│
├── .vscode/                       # VS Code configuration
│   ├── launch.json               # 9 debug configurations
│   └── settings.json             # Python environment setup
│
├── .github/
│   └── copilot-instructions.md   # AI agent development guidelines
│
├── requirements.txt               # Python dependencies
├── architecture_test_plan.md      # Future feature roadmap
└── README.md                      # This file
```

## 🛠️ Technologies

### 2D Graphics Stack (Pygame)
- **pygame 2.6.1** - Core 2D game framework with sprite system
- **pygame-gui 0.6.14** - Advanced UI components and widgets
- **Pillow 11.2.1** - Image processing and manipulation
- **moderngl 5.12.0** - Modern OpenGL 3.3+ support
- **PyOpenGL 3.1.10** - OpenGL bindings for Python
- **numpy 2.2.5** - Numerical computations for physics and graphics

### 3D Graphics Stack (Panda3D)
- **panda3d 1.10.15** - Comprehensive 3D engine featuring:
  - Scene graph architecture
  - Bullet physics integration
  - PBR shader support
  - Advanced lighting and shadows
  - Model loading (glTF, FBX, OBJ)
  - Animation and skeletal systems
  - Audio engine
  - Networking capabilities

### Configuration & Testing
- **pyyaml 6.0.2** - YAML configuration file support
- **pytest 9.0.1** - Testing framework

### Development Environment
- **Python 3.12.1** with pip 25.1.1
- **VS Code Dev Container** (mcr.microsoft.com/devcontainers/universal:2)
- **9 Debug Configurations** for various scenarios

## 💻 Development

### Setting Up Development Environment

This project uses a VS Code dev container for consistent development:

1. **Open in GitHub Codespaces** or **VS Code with Remote Containers**
2. **Dependencies install automatically** via `requirements.txt`
3. **Python environment configured** at `/home/codespace/.python/current/bin/python`

### Running Tests

```bash
# All tests (12 passing)
python -m pytest

# Verbose output
python -m pytest -v

# Specific module
python -m pytest tests/test_panda3d_engine.py

# Coverage report
python -m pytest --cov
```

### Debugging

The project includes 9 pre-configured debug configurations in `.vscode/launch.json`:

- **Python: Current File** - Debug any Python file
- **Python: Engine** - Debug the minimal engine
- **Python: Demo Game** - Debug 2D demo
- **Python: Graphics Demo** - Debug AAA graphics showcase
- **Python: Panda3D Engine** - Debug 3D engine (English)
- **Python: Panda3D Spanish** - Debug with Spanish localization
- **Python: Panda3D French** - Debug with French localization
- **Python: Test Current File** - Debug current test file
- **Python: All Tests** - Debug entire test suite

### Code Guidelines

See `.github/copilot-instructions.md` for comprehensive development guidelines including:
- Project architecture and conventions
- Testing patterns and best practices
- Configuration management
- Module design principles
- Troubleshooting common issues

## 🎨 Creating AAA-Quality Games

### 2D Games with Advanced Graphics

```python
from game_engine import GameEngine
from asset_manager import get_asset_manager
from rendering import ParticleSystem, LightingSystem, PostProcessing

class MyGame(GameEngine):
    def __init__(self):
        super().__init__(1920, 1080, "My AAA Game")
        self.assets = get_asset_manager()
        self.lighting = LightingSystem(1920, 1080)
        self.particles = ParticleSystem(960, 540)
        
        # Load assets
        self.background = self.assets.load_image('background.png')
        self.player_sprite = self.assets.load_sprite_sheet('player.png', 32, 32)
        
    def update(self):
        # Update game systems
        self.particles.update()
        self.lighting.update()
        
    def render(self):
        super().render()
        
        # Render particles and lighting
        self.particles.render(self.screen)
        self.lighting.render(self.screen)
        
        # Apply post-processing effects
        self.screen = PostProcessing.apply_bloom(self.screen)
        self.screen = PostProcessing.apply_vignette(self.screen)

if __name__ == '__main__':
    game = MyGame()
    game.run()
```

### 3D Games with Physics and PBR

```python
from direct.showbase.ShowBase import ShowBase
from engine_modules.physics import PhysicsManager
from engine_modules.rendering import RenderingManager
from engine_modules.config import get_config
from panda3d.core import Vec3

class My3DGame(ShowBase):
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.config = get_config()
        
        # Initialize engine systems
        self.physics = PhysicsManager()
        self.renderer = RenderingManager(self.render)
        
        # Enable advanced rendering
        if self.config.get('graphics.enable_pbr'):
            self.renderer.enable_pbr()
        
        # Setup scene
        self.create_world()
        
        # Update task
        self.taskMgr.add(self.update, 'update')
    
    def create_world(self):
        # Create ground with physics
        ground = self.physics.create_ground_plane()
        
        # Add lights
        self.renderer.add_directional_light('sun', (1, 0.95, 0.8, 1), Vec3(-1, -1, -1))
        self.renderer.add_point_light('torch', (1, 0.6, 0.2, 1), Vec3(0, 0, 5))
        
        # Load and add models with physics
        # model = self.loader.loadModel('my_model.gltf')
        # self.physics.create_box(model, mass=1.0)
    
    def update(self, task):
        dt = globalClock.get_dt()
        self.physics.update(dt)
        return task.cont

if __name__ == '__main__':
    app = My3DGame()
    app.run()
```

## 🚧 Roadmap

### Completed ✅
- ✅ 2D pygame engine with sprite system
- ✅ Asset management and caching
- ✅ Advanced 2D rendering (particles, lighting, post-FX)
- ✅ 3D Panda3D engine with scene graph
- ✅ Multilingual support (en/es/fr)
- ✅ Bullet physics integration
- ✅ PBR shader foundation
- ✅ Configuration system (YAML)
- ✅ CLI management tools
- ✅ Example scripts and documentation
- ✅ Comprehensive test suite (12 tests)

### In Progress 🔄
- 🔄 Full PBR shader implementation
- 🔄 Enhanced engine integration

### Planned 📋
- 📋 Animation system with skeletal animation
- 📋 Networking module for multiplayer
- 📋 Visual debugger/inspector (F1 overlay)
- 📋 More example projects
- 📋 Asset pipeline tools
- 📋 Performance profiling tools
- 📋 Level editor integration

## 📄 License

See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Update documentation
5. Submit a pull request

For major changes, please open an issue first to discuss the proposed changes.

## 📞 Support

- Check `examples/README.md` for tutorials
- Review `architecture_test_plan.md` for design decisions
- Read `.github/copilot-instructions.md` for development guidelines
- Examine `config.yaml` for configuration options

