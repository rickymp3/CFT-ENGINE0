# CFT-ENGINE0 Quick Reference

## 🎯 Quick Commands

```bash
# Visual Editor (No-Code Scene Creation)
python editor.py                       # Launch visual scene editor
python manage.py editor                # Alternative launch method

# Run Examples
python examples/basic_scene_example.py     # 3D scene basics
python examples/physics_example.py         # Physics simulation
python examples/pbr_shaders_example.py     # PBR materials

# Run Demos
python demo_game.py                        # Simple 2D game
python graphics_demo.py                    # 2D AAA graphics
python cft_panda3d_engine.py              # 3D multilingual engine

# CLI Tools
python manage.py new-project <name>        # Create new project
python manage.py run --lang en            # Run engine
python manage.py editor                    # Launch visual editor
python manage.py test                      # Run tests
python manage.py config --show             # View config

# Testing
python -m pytest                           # Run all tests
python -m pytest -v                        # Verbose output
python -m pytest tests/test_engine.py      # Specific file
```

## 🏗️ Code Templates

### 2D Game (Pygame)
```python
from game_engine import GameEngine

class MyGame(GameEngine):
    def __init__(self):
        super().__init__(800, 600, "My Game")
        
    def update(self):
        pass  # Your logic
        
    def render(self):
        super().render()
        # Your rendering

if __name__ == "__main__":
    MyGame().run()
```

### 3D Game (Panda3D)
```python
from direct.showbase.ShowBase import ShowBase
from engine_modules.physics import PhysicsManager
from engine_modules.rendering import RenderingManager

class MyGame(ShowBase):
    def __init__(self):
        super().__init__()
        self.physics = PhysicsManager()
        self.renderer = RenderingManager(self.render)
        self.renderer.enable_pbr()
        self.taskMgr.add(self.update, 'update')
    
    def update(self, task):
        dt = globalClock.get_dt()
        self.physics.update(dt)
        return task.cont

if __name__ == '__main__':
    MyGame().run()
```

## 🔧 Common Tasks

### Add Physics to Object
```python
# Box
self.physics.create_box(model_node, mass=1.0)

# Sphere
self.physics.create_sphere(model_node, radius=0.5, mass=1.0)

# Ground
ground = self.physics.create_ground_plane()
```

### Add Lights
```python
# Ambient
self.renderer.add_ambient_light('ambient', (0.3, 0.3, 0.4, 1))

# Sun
self.renderer.add_directional_light('sun', (1, 0.95, 0.8, 1), Vec3(-1, -1, -1))

# Point light
self.renderer.add_point_light('torch', (1, 0.6, 0.2, 1), Vec3(0, 0, 5))
```

### Load Configuration
```python
from engine_modules.config import get_config

config = get_config()
pbr_enabled = config.get('graphics.enable_pbr')
gravity = config.get('physics.gravity')
```

### Asset Loading (2D)
```python
from asset_manager import get_asset_manager

assets = get_asset_manager()
sprite = assets.load_image('player.png')
sound = assets.load_sound('jump.wav')
font = assets.load_font('arial.ttf', 24)
```

## 📁 Important Files

| File | Purpose |
|------|---------|
| `editor.py` | **Visual scene editor (no-code)** |
| `EDITOR_GUIDE.md` | **Complete editor documentation** |
| `config.yaml` | Engine configuration |
| `engine_modules/physics.py` | Physics system |
| `engine_modules/rendering.py` | Rendering/PBR |
| `engine_modules/config.py` | Config management |
| `engine_modules/animation_timeline.py` | Timeline animation |
| `manage.py` | CLI tool |
| `examples/README.md` | Tutorial documentation |
| `.vscode/launch.json` | Debug configurations |

## 🐛 Debug Configurations

Press **F5** in VS Code and select:
- **Python: Current File** - Any Python file
- **Python: Panda3D Engine** - 3D engine (English)
- **Python: Panda3D Spanish** - Spanish localization
- **Python: Demo Game** - 2D demo
- **Python: All Tests** - Full test suite

## ⚙️ Configuration Quick Edit

```yaml
# config.yaml
graphics:
  enable_pbr: true        # Toggle PBR
  enable_hdr: true        # Toggle HDR
  shadow_resolution: 2048 # Shadow quality

physics:
  gravity: -9.81          # Earth gravity
  simulation_frequency: 60 # Physics Hz

debug:
  show_fps: true          # FPS counter
  wireframe: false        # Wireframe mode
  show_physics: true      # Physics debug
```

## 🎮 Controls Reference

### Basic Scene Example
- **Arrow Keys**: Move camera
- **W/S**: Zoom in/out
- **A/D**: Rotate camera
- **ESC**: Quit

### Physics Example
- **ESC**: Quit

### PBR Shaders Example
- **ESC**: Quit

### Demo Game (2D)
- **Arrow Keys / WASD**: Move player
- **ESC**: Quit

### Graphics Demo (2D)
- **Arrow Keys / WASD**: Move player
- **SPACE**: Particle burst
- **1**: Toggle particles
- **2**: Toggle lighting
- **3**: Toggle bloom
- **4**: Toggle vignette
- **ESC**: Quit

### Panda3D Engine (3D)
- **ENTER**: Start game / Load model
- **Arrow Left/Right**: Rotate model
- **ESC**: Quit

## 📚 Documentation Links

- **Main README**: `README.md` - Full project overview
- **Examples Guide**: `examples/README.md` - Tutorial walkthroughs
- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md` - Feature list
- **Architecture Plan**: `architecture_test_plan.md` - Design roadmap
- **Dev Guidelines**: `.github/copilot-instructions.md` - AI agent guide

## 🔍 Troubleshooting

### Import Errors
```bash
# Always run from project root
cd /workspaces/CFT-ENGINE0
python examples/basic_scene_example.py
```

### Test Failures
```bash
# Clear cache and rerun
rm -rf __pycache__ tests/__pycache__
python -m pytest
```

### Model Loading Issues
```bash
# Check if models exist
ls /home/codespace/.python/current/lib/python3.12/site-packages/panda3d/models/

# Fallback: Examples handle missing models gracefully
```

### Environment Issues
```bash
# Verify Python path
which python
# Should be: /home/codespace/.python/current/bin/python

# Check dependencies
pip list | grep -E "panda3d|pygame|pytest"
```

## 🚀 Project Workflow

1. **Start**: `python manage.py new-project my_game`
2. **Develop**: Edit generated files
3. **Test**: `python manage.py test`
4. **Debug**: Press F5, select configuration
5. **Run**: `python manage.py run`
6. **Configure**: Edit `config.yaml`

## 📊 Project Stats

- **12 Tests** (100% passing)
- **3 Example Scripts**
- **9 Debug Configs**
- **8 Dependencies**
- **3 Languages** (en/es/fr)
- **2 Engines** (2D pygame, 3D Panda3D)

## 🎓 Learning Path

1. ⭐ **Start**: Run `examples/basic_scene_example.py`
2. 🔬 **Physics**: Run `examples/physics_example.py`
3. 🎨 **Graphics**: Run `examples/pbr_shaders_example.py`
4. 🎮 **2D Game**: Study `demo_game.py`
5. 🌟 **3D Game**: Study `cft_panda3d_engine.py`
6. 🏗️ **Build**: Create your own with `manage.py new-project`

---

**Quick help**: Run `python manage.py --help` for CLI usage
